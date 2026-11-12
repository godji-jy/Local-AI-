"""แหล่งความรู้: ฐานความรู้ในเครื่อง (ChromaDB) + ค้นหาเว็บ + จัดรูปแบบบริบท/แหล่งอ้างอิง"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from urllib.parse import quote

import numpy as np
import requests

from .config import (
    BROWSER_HEADERS,
    DB_DIR,
    FETCH_PAGES,
    HTTP_HEADERS,
    KB_MAX_DISTANCE,
    KB_TOP,
    PAGE_CHARS,
    PASSAGE_CHARS,
    SEARCH_MAX_RESULTS,
    SNIPPET_CHARS,
    WEB_TOP_PASSAGES,
)
from .ollama_client import embed, ollama_quick
from .text_utils import (
    SOURCE_SPLIT,
    chunk_text,
    clean_text,
    content_to_text,
)
from .doc_images import strip_doc_images


def rank_passages(query, passages, top_k):
    if len(passages) <= top_k:
        return passages

    try:
        vectors = np.array(
            embed([query] + [p["text"] for p in passages]), dtype=float
        )
        q, m = vectors[0], vectors[1:]
        scores = (m @ q) / (np.linalg.norm(m, axis=1) * np.linalg.norm(q) + 1e-9)
        order = np.argsort(-scores)[:top_k]
        return [passages[i] for i in order]

    except Exception as e:
        print(f"[Local AI] rank error: {type(e).__name__}: {e}")
        return passages[:top_k]


_kb_collection = None


def get_kb():
    global _kb_collection

    if _kb_collection is None:
        import chromadb

        client = chromadb.PersistentClient(path=str(DB_DIR))
        _kb_collection = client.get_collection("knowledge")

    return _kb_collection


def search_knowledge(query):
    try:
        collection = get_kb()

        if collection.count() == 0:
            return []

        result = collection.query(
            query_embeddings=[embed([query])[0]],
            n_results=KB_TOP,
            include=["documents", "metadatas", "distances"],
        )

    except Exception as e:
        print(f"[Local AI] knowledge base: {type(e).__name__}: {e}")
        return []

    passages = []

    for doc, meta, dist in zip(
        result["documents"][0],
        result["metadatas"][0],
        result["distances"][0],
    ):
        if dist <= KB_MAX_DISTANCE:
            passages.append({
                "text": doc,
                "title": (meta or {}).get("source", "knowledge"),
                "url": None,
            })

    return passages


def search_duckduckgo(query, is_thai):
    try:
        from ddgs import DDGS
    except ImportError:
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            print("[Local AI] ไม่พบแพ็กเกจ ddgs  ->  pip install ddgs")
            return []

    results = []

    try:
        with DDGS() as ddgs:
            found = ddgs.text(
                query,
                region="th-th" if is_thai else "us-en",
                max_results=SEARCH_MAX_RESULTS,
            )

            for r in found or []:
                url = r.get("href") or r.get("url") or ""
                if not url:
                    continue

                results.append({
                    "title": clean_text(r.get("title"), 120) or url,
                    "url": url,
                    "snippet": clean_text(r.get("body"), SNIPPET_CHARS),
                })

    except Exception as e:
        print(f"[Local AI] DuckDuckGo error: {type(e).__name__}: {e}")

    return results


def search_wikipedia(query, is_thai):
    lang = "th" if is_thai else "en"

    try:
        response = requests.get(
            f"https://{lang}.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "generator": "search",
                "gsrsearch": query,
                "gsrlimit": SEARCH_MAX_RESULTS,
                "prop": "extracts",
                "exintro": 1,
                "explaintext": 1,
                "exchars": SNIPPET_CHARS,
                "format": "json",
                "formatversion": 2,
            },
            headers=HTTP_HEADERS,
            timeout=15,
        )
        response.raise_for_status()
        pages = (response.json().get("query") or {}).get("pages") or []

    except Exception as e:
        print(f"[Local AI] Wikipedia error: {type(e).__name__}: {e}")
        return []

    pages.sort(key=lambda p: p.get("index", 0))

    results = []
    for p in pages:
        title = p.get("title") or ""
        if not title:
            continue

        results.append({
            "title": f"{title} - Wikipedia",
            "url": f"https://{lang}.wikipedia.org/wiki/"
                   + quote(title.replace(" ", "_")),
            "snippet": clean_text(p.get("extract"), SNIPPET_CHARS),
        })

    return results


def web_search(query, is_thai):
    results = search_duckduckgo(query, is_thai)

    if not results:
        results = search_wikipedia(query, is_thai)

    return results


def fetch_page_text(url):
    try:
        import trafilatura
    except ImportError:
        print("[Local AI] ไม่พบแพ็กเกจ trafilatura  ->  pip install trafilatura")
        return ""

    try:
        response = requests.get(url, headers=BROWSER_HEADERS, timeout=8)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "").lower()
        if "html" not in content_type or len(response.content) > 3_000_000:
            return ""

        text = trafilatura.extract(
            response.content,
            include_comments=False,
            include_tables=True,
            favor_recall=True,
        )
        return (text or "")[:PAGE_CHARS]

    except Exception as e:
        print(f"[Local AI] fetch {url[:60]}: {type(e).__name__}")
        return ""


def make_search_query(message, history):
    # คำถามสั้นและยังไม่มีบริบทก่อนหน้า ใช้ค้นตรงๆ ได้เลย ประหยัดเวลาเรียกโมเดลอีกรอบ
    if not history and len(message) <= 40:
        return message

    today = datetime.now().strftime("%Y-%m-%d")

    recent = []
    for item in history[-4:]:
        if isinstance(item, dict) and item.get("role") in ("user", "assistant"):
            text = strip_doc_images(content_to_text(item.get("content", "")).split(SOURCE_SPLIT)[0])
            if text:
                recent.append(f"{item['role']}: {text[:300]}")

    system = (
        "You convert a user's question into ONE web search query.\n"
        f"Today is {today}.\n"
        "Rules:\n"
        "- Output only the query. No quotes, no explanation.\n"
        "- Maximum 10 words.\n"
        "- Keep names, product names and key technical terms exactly.\n"
        "- Use English for international or technical topics; "
        "use Thai for Thailand-specific topics.\n"
        "- If the question is a follow-up, use the conversation to make "
        "the query self-contained.\n"
        "- If the user wants the latest or current information, include the year."
    )

    user = ("\n".join(recent) + "\n\n" if recent else "") + f"Question: {message}"

    try:
        text = ollama_quick(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ]
        )
        lines = text.strip().splitlines()
        query = lines[0].strip(" \"'`") if lines else ""
    except Exception as e:
        print(f"[Local AI] query rewrite: {type(e).__name__}: {e}")
        query = ""

    return query if 2 <= len(query) <= 150 else message[:200]


def web_passages(query, is_thai):
    results = web_search(query, is_thai)

    if not results:
        return []

    to_fetch = results[:FETCH_PAGES]

    with ThreadPoolExecutor(max_workers=FETCH_PAGES) as pool:
        texts = list(pool.map(fetch_page_text, [r["url"] for r in to_fetch]))

    passages = []

    for r, text in zip(to_fetch, texts):
        pieces = chunk_text(text) if text else []

        if not pieces and r["snippet"]:
            pieces = [r["snippet"]]

        for piece in pieces:
            passages.append({"text": piece, "title": r["title"], "url": r["url"]})

    for r in results[FETCH_PAGES:]:
        if r["snippet"]:
            passages.append(
                {"text": r["snippet"], "title": r["title"], "url": r["url"]}
            )

    return rank_passages(query, passages, WEB_TOP_PASSAGES)


def source_index(sources, title, url):
    for i, s in enumerate(sources, start=1):
        if s["title"] == title and s["url"] == url:
            return i

    sources.append({"title": title, "url": url})
    return len(sources)


def build_context(passages, sources):
    blocks = []

    for p in passages:
        n = source_index(sources, p["title"], p["url"])
        blocks.append(f"[{n}] {p['title']}\n{p['text'][:PASSAGE_CHARS]}")

    return "\n\n".join(blocks)


def format_sources(sources, asked, is_en):
    if not asked:
        return ""

    if not sources:
        return (
            f"{SOURCE_SPLIT}*No relevant material was found, so this answer "
            "is based on the model's own knowledge.*"
            if is_en
            else f"{SOURCE_SPLIT}*ไม่พบข้อมูลที่เกี่ยวข้อง จึงตอบจากความรู้ของโมเดลเอง*"
        )

    lines = []
    for i, s in enumerate(sources, start=1):
        if s["url"]:
            lines.append(f"{i}. [{s['title']}]({s['url']})")
        else:
            lines.append(f"{i}. 📚 {s['title']}")

    head = "**Sources:**" if is_en else "**แหล่งข้อมูล:**"
    return f"{SOURCE_SPLIT}{head}\n" + "\n".join(lines)


def grounding_instruction(context, is_en):
    today = datetime.now().strftime("%Y-%m-%d")

    if is_en:
        return f"""

REFERENCE MATERIAL (today is {today}):
{context}

How to use the reference material:
- Base factual claims on it and mark them with [n], using the numbers above.
- Read ALL the passages and cover every relevant point, not just the first one.
- Write in your own words. Never copy sentences or paste fragments.
- If sources disagree, say so. If the material does not contain the answer,
  say that clearly, then answer from general knowledge and label that part
  as general knowledge.
- Do not write a source list. It is added automatically.
"""

    return f"""

เอกสารอ้างอิง (วันนี้คือ {today}):
{context}

วิธีใช้เอกสารอ้างอิง:
- ข้อเท็จจริงให้อ้างอิงจากเอกสารข้างต้น และใส่เลข [n] กำกับตามหมายเลขที่ให้ไว้
- อ่านให้ครบทุกชิ้น และตอบให้ครอบคลุมทุกประเด็นที่เกี่ยวข้อง ไม่ใช่แค่ชิ้นแรก
- เรียบเรียงด้วยภาษาของตัวเอง ห้ามคัดลอกประโยคหรือวางเป็นท่อนๆ
- ถ้าแหล่งข้อมูลขัดแย้งกันให้บอกตรงๆ ถ้าเอกสารไม่มีคำตอบให้บอกชัดเจน
  แล้วตอบจากความรู้ทั่วไปโดยระบุว่าเป็นความรู้ทั่วไป
- ห้ามเขียนรายการแหล่งข้อมูลเอง ระบบจะต่อให้อัตโนมัติ
"""