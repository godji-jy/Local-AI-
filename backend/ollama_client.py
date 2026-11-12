"""ตัวเชื่อมต่อ Ollama: แชต, สตรีม, embedding, โหลดโมเดลล่วงหน้า, ตรวจโมเดลอ่านรูป"""

import json

import requests

from .config import (
    CODE_MODEL,
    CODE_TEMPERATURE,
    EMBED_MODEL,
    EMBED_ON_CPU,
    KEEP_ALIVE,
    MAX_TOKENS_FAST,
    MAX_TOKENS_THINK,
    MODEL,
    NUM_CTX,
    NUM_GPU,
    NUM_THREAD,
    OLLAMA_URL,
    VISION_MODEL,
)
from .text_utils import strip_think


def base_options():
    """ตัวเลือกฮาร์ดแวร์ที่ต้องเหมือนกันทุกการเรียก (ไม่งั้น Ollama อาจโหลดโมเดลใหม่)"""
    options = {"num_ctx": NUM_CTX}

    if NUM_THREAD:
        options["num_thread"] = NUM_THREAD

    if NUM_GPU is not None:
        options["num_gpu"] = NUM_GPU

    return options


def ollama_options(think):
    if think:
        temperature, top_p, num_predict = 0.6, 0.95, MAX_TOKENS_THINK
    else:
        temperature, top_p, num_predict = 0.7, 0.8, MAX_TOKENS_FAST

    return {
        **base_options(),
        "temperature": temperature,
        "top_p": top_p,
        "top_k": 20,
        "num_predict": num_predict,
    }


def ollama_quick(messages, num_predict=60):
    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": MODEL,
            "messages": messages,
            "stream": False,
            "think": False,
            "keep_alive": KEEP_ALIVE,
            "options": {
                **base_options(),
                "temperature": 0.2,
                "num_predict": num_predict,
            },
        },
        timeout=(10, 120),
    )
    response.raise_for_status()
    data = response.json()
    return strip_think((data.get("message") or {}).get("content"))


def ollama_stream(messages, think, model=None):
    model = model or MODEL

    options = ollama_options(think)

    if CODE_MODEL and model == CODE_MODEL:
        options["temperature"] = CODE_TEMPERATURE      # งานโค้ดใช้ค่าสุ่มต่ำกว่า

    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "keep_alive": KEEP_ALIVE,
        "options": options,
    }

    # โมเดลสำรองอาจไม่รองรับโหมดคิด จึงส่ง think เฉพาะโมเดลหลักหรือเมื่อผู้ใช้เปิดคิดลึก
    if model == MODEL or think or "qwen3.5" in model:
        payload["think"] = think

    with requests.post(
        f"{OLLAMA_URL}/api/chat",
        json=payload,
        timeout=(10, 300),
        stream=True,
    ) as response:
        # อ่านสาเหตุจริงที่ Ollama ส่งมา (เช่น out of memory) ก่อนโยนข้อผิดพลาด
        if response.status_code >= 400:
            try:
                detail = response.json().get("error", "")
            except Exception:
                detail = response.text[:300]

            error = requests.exceptions.HTTPError(
                f"{response.status_code} {detail}", response=response
            )
            error.detail = f"{response.status_code}: {detail}"
            raise error

        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue

            data = json.loads(line)

            if data.get("error"):
                raise RuntimeError(data["error"])

            msg = data.get("message") or {}

            if msg.get("thinking"):
                yield "thinking", msg["thinking"]

            if msg.get("content"):
                yield "content", msg["content"]

            if data.get("done"):
                print(f"[Local AI] prompt tokens: {data.get('prompt_eval_count')} / ctx {NUM_CTX} | output: {data.get('eval_count')}")
                yield "done", data.get("done_reason") or ""
                break


def embed_payload(texts):
    payload = {
        "model": EMBED_MODEL,
        "input": texts,
        "keep_alive": KEEP_ALIVE,
    }

    if EMBED_ON_CPU:
        payload["options"] = {"num_gpu": 0}

    return payload


def embed(texts):
    vectors = []

    for start in range(0, len(texts), 32):
        response = requests.post(
            f"{OLLAMA_URL}/api/embed",
            json=embed_payload(texts[start:start + 32]),
            timeout=(10, 120),
        )
        response.raise_for_status()
        vectors.extend(response.json()["embeddings"])

    return vectors


def warm_up():
    """โหลดโมเดลเข้าหน่วยความจำล่วงหน้า (ทำเบื้องหลังตอนเปิดแอป) คำถามแรกจะไม่ต้องรอโหลด"""
    try:
        requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": MODEL,
                "prompt": "",
                "stream": False,
                "keep_alive": KEEP_ALIVE,
                "options": base_options(),
            },
            timeout=300,
        ).raise_for_status()
        print(f"[Local AI] โหลดโมเดล {MODEL} ล่วงหน้าเสร็จแล้ว")
    except Exception as e:
        print(f"[Local AI] โหลดโมเดลล่วงหน้าไม่สำเร็จ ({type(e).__name__}) จะโหลดตอนถามครั้งแรกแทน")
        return

    try:
        requests.post(
            f"{OLLAMA_URL}/api/embed",
            json=embed_payload(["warm up"]),
            timeout=120,
        ).raise_for_status()
    except Exception as e:
        print(f"[Local AI] โหลด {EMBED_MODEL} ล่วงหน้าไม่สำเร็จ ({type(e).__name__})")


def error_message(exc, is_en):
    if isinstance(exc, requests.exceptions.ConnectionError):
        return (
            "Cannot connect to Ollama. Make sure Ollama is running."
            if is_en
            else "เชื่อมต่อ Ollama ไม่ได้ กรุณาตรวจสอบว่า Ollama เปิดอยู่"
        )

    if isinstance(exc, requests.exceptions.Timeout):
        return (
            "The AI request timed out. Please try again."
            if is_en
            else "AI ใช้เวลานานเกินไป กรุณาลองใหม่"
        )

    if isinstance(exc, requests.exceptions.HTTPError):
        detail = getattr(exc, "detail", "") or str(exc)
        print(f"[Local AI] HTTP error: {detail}")
        return (
            f"Ollama returned an API error.\n\n**Reason from Ollama:** {detail}\n\n"
            f"Check that '{MODEL}' and '{EMBED_MODEL}' are installed "
            "(`ollama list`), Ollama is up to date, and NUM_CTX is not too "
            "large for your RAM/VRAM."
            if is_en
            else f"Ollama ตอบกลับด้วยข้อผิดพลาด\n\n**สาเหตุจาก Ollama:** {detail}\n\n"
                 f"ตรวจว่าติดตั้งโมเดล '{MODEL}' และ '{EMBED_MODEL}' แล้ว "
                 "(`ollama list`) อัปเดต Ollama เป็นรุ่นล่าสุด "
                 "และ NUM_CTX ไม่ใหญ่เกินสำหรับ RAM/VRAM ของเครื่อง"
        )

    print(f"[Local AI] {type(exc).__name__}: {exc}")
    return (
        f"An error occurred: {type(exc).__name__}: {exc}"
        if is_en
        else f"เกิดข้อผิดพลาด: {type(exc).__name__}: {exc}"
    )


def raise_for_ollama(response):
    """อ่านสาเหตุจริงที่ Ollama ส่งมา แล้วโยน HTTPError ที่มี .detail"""
    if response.status_code < 400:
        return

    try:
        detail = response.json().get("error", "")
    except Exception:
        detail = response.text[:300]

    error = requests.exceptions.HTTPError(f"{response.status_code} {detail}", response=response)
    error.detail = f"{response.status_code}: {detail}"
    raise error


def ollama_agent_step(messages, tools, think):
    """เรียกโมเดล 1 รอบ (ไม่สตรีม) พร้อมเครื่องมือ คืนค่า message ที่โมเดลตอบ"""
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "think": bool(think),
        "keep_alive": KEEP_ALIVE,
        "options": ollama_options(think),
    }

    if tools:
        payload["tools"] = tools

    response = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=(10, 300))
    raise_for_ollama(response)

    return response.json().get("message") or {}


# ---------- โมเดลที่อ่านรูปได้ ----------
_vision_cache = {}


def has_vision(model):
    if model in _vision_cache:
        return _vision_cache[model]

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/show", json={"model": model}, timeout=10
        )
        response.raise_for_status()
        capabilities = response.json().get("capabilities")

        # Ollama รุ่นเก่าไม่บอก capabilities -> ลองส่งรูปไปเลย
        ok = True if capabilities is None else ("vision" in capabilities)

    except requests.exceptions.HTTPError:
        ok = False                     # ไม่มีโมเดลนี้ในเครื่อง

    _vision_cache[model] = ok
    return ok


def pick_vision_model():
    for name in (MODEL, VISION_MODEL):
        if name and has_vision(name):
            return name

    return ""


def no_vision_message(is_en):
    if is_en:
        return (
            f"The model '{MODEL}' cannot read images. Install a vision model "
            "(e.g. `ollama pull qwen2.5vl:7b`) and set its name in VISION_MODEL "
            "in backend/config.py, or press 'Clear files' to ask with text only."
        )

    return (
        f"โมเดล '{MODEL}' อ่านรูปภาพไม่ได้ ให้ติดตั้งโมเดลที่รองรับรูป "
        "(เช่น `ollama pull qwen2.5vl:7b`) แล้วใส่ชื่อไว้ที่ VISION_MODEL ใน backend/config.py "
        "หรือกด ✖ ล้างไฟล์ เพื่อถามเฉพาะข้อความ"
    )


# ---------- ตรวจว่าโมเดลติดตั้งในเครื่องแล้วหรือยัง ----------

_installed_cache = set()


def model_installed(model):
    """True ถ้าโมเดลมีใน Ollama แล้ว (จำเฉพาะผลที่ 'มี' เพื่อให้ติดตั้งเพิ่มแล้วใช้ได้ทันทีโดยไม่ต้องรีสตาร์ท)"""
    if model in _installed_cache:
        return True

    response = requests.post(
        f"{OLLAMA_URL}/api/show", json={"model": model}, timeout=10
    )

    if response.status_code == 404:
        return False

    response.raise_for_status()
    _installed_cache.add(model)
    return True