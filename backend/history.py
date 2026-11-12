"""ประวัติแชต: บันทึก/อ่าน/ลบไฟล์ .json ในโฟลเดอร์ chats (ไม่มีโค้ดหน้าจอ)"""

from datetime import datetime
import json
import os
import re
import threading
import uuid

from .config import CHATS_DIR, HISTORY_LIST_MAX
from .text_utils import content_to_text


# ---------- ประวัติแชต (บันทึกลงดิสก์) ----------
CHAT_ID_RE = re.compile(r"^\d{8}-\d{6}-[0-9a-f]{4}$")

_chat_lock = threading.Lock()


def chat_file(chat_id):
    """ตรวจรูปแบบ id ก่อนใช้ กันค่าแปลกปลอมจากฝั่งเบราว์เซอร์ (ไม่ให้เขียน/ลบไฟล์นอกโฟลเดอร์ chats)"""
    if not isinstance(chat_id, str) or not CHAT_ID_RE.match(chat_id):
        return None

    return CHATS_DIR / f"{chat_id}.json"


def read_chat(chat_id):
    path = chat_file(chat_id)

    if path is None or not path.exists():
        return None

    try:
        with _chat_lock:
            data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[Local AI] read chat {chat_id}: {type(e).__name__}: {e}")
        return None

    return data if isinstance(data, dict) else None


def list_chats():
    """รายการแชตทั้งหมด เรียงจากอัปเดตล่าสุด"""
    items = []

    if not CHATS_DIR.exists():
        return items

    for path in CHATS_DIR.glob("*.json"):
        data = read_chat(path.stem)

        if data:
            items.append({
                "id": path.stem,
                "title": str(data.get("title") or "แชตใหม่"),
                "updated": str(data.get("updated") or ""),
            })

    items.sort(key=lambda c: c["updated"], reverse=True)
    return items


def chat_choices(current_id=None):
    """ตัวเลือกของรายการประวัติ (ชื่อที่แสดง, id)"""
    items = list_chats()
    shown = items[:HISTORY_LIST_MAX]

    # แชตที่เปิดอยู่ต้องอยู่ในรายการเสมอ แม้จะเก่ากว่าที่แสดง
    if current_id and all(c["id"] != current_id for c in shown):
        current = next((c for c in items if c["id"] == current_id), None)
        if current:
            shown.append(current)

    return [(f"{c['updated'][5:16]} · {c['title']}", c["id"]) for c in shown]


def save_chat(history, chat_id):
    """บันทึกแชตปัจจุบันลงไฟล์ (เรียกหลังตอบเสร็จทุกครั้ง)
    คืนค่า (chat_id, บันทึกสำเร็จหรือไม่) ถ้าไม่มีข้อความให้บันทึกหรือบันทึกไม่ได้ จะคืน (chat_id เดิม, False)"""
    messages = []

    for m in history or []:
        if isinstance(m, dict) and m.get("role") in ("user", "assistant"):
            text = content_to_text(m.get("content", ""))
            if text:
                messages.append({"role": m["role"], "content": text})

    if not messages:
        return chat_id, False

    path = chat_file(chat_id)

    if path is None:
        chat_id = datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:4]
        path = chat_file(chat_id)

    old = read_chat(chat_id) or {}
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    first_user = next((m["content"] for m in messages if m["role"] == "user"), "")
    title = re.sub(r"\s+", " ", first_user).strip()
    title = (title[:40] + "…") if len(title) > 40 else (title or "แชตใหม่")

    data = {
        "id": chat_id,
        "title": old.get("title") or title,
        "created": old.get("created") or now,
        "updated": now,
        "messages": messages,
    }

    try:
        CHATS_DIR.mkdir(exist_ok=True)
        tmp = path.with_suffix(".tmp")

        with _chat_lock:
            # เขียนไฟล์ชั่วคราวก่อนแล้วค่อยสลับ กันไฟล์พังถ้าปิดโปรแกรมกลางคัน
            tmp.write_text(
                json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8"
            )
            os.replace(tmp, path)

    except Exception as e:
        print(f"[Local AI] save chat: {type(e).__name__}: {e}")
        return chat_id, False

    return chat_id, True


def chat_exists(chat_id):
    path = chat_file(chat_id)
    return path is not None and path.exists()


def delete_chat(chat_id):
    """ลบไฟล์แชต (ข้อผิดพลาดของระบบไฟล์ถูกโยนขึ้นไปให้ผู้เรียกจัดการ)"""
    path = chat_file(chat_id)

    if path is None:
        raise ValueError("chat id ไม่ถูกต้อง")

    with _chat_lock:
        path.unlink()