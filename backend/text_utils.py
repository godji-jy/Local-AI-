"""ฟังก์ชันจัดการข้อความล้วนๆ (ไม่ติดต่อเครือข่าย/ดิสก์)"""

import re

from .config import CHUNK_CHARS, LANG_EN, LANG_THAI


THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)

TAG_RE = re.compile(r"<[^>]+>")

SOURCE_SPLIT = "\n\n---\n"


def strip_think(text):
    text = THINK_RE.sub("", text or "")
    if "<think>" in text:
        text = text.split("<think>", 1)[0]
    return text.strip()


def content_to_text(content):
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text", "")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts).strip()

    return ""


def detect_prompt_language(message):
    if any("\u0e00" <= ch <= "\u0e7f" for ch in message):
        return LANG_THAI
    return LANG_EN


def clean_text(text, limit=None):
    text = TAG_RE.sub("", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit] if limit else text


def chunk_text(text, size=CHUNK_CHARS):
    chunks, current = [], ""

    for line in (text or "").splitlines():
        line = re.sub(r"[ \t]+", " ", line).strip()
        if not line:
            continue

        while len(line) > size:
            if current:
                chunks.append(current)
                current = ""
            chunks.append(line[:size])
            line = line[size:]

        if current and len(current) + len(line) + 1 > size:
            chunks.append(current)
            current = line
        else:
            current = f"{current} {line}" if current else line

    if current:
        chunks.append(current)

    return [c for c in chunks if len(c) >= 40]