"""ตัวจัดการเหตุการณ์ของหน้าจอ: เชื่อมปุ่ม/ช่องกรอกกับแบ็กเอนด์ (ไฟล์นี้เท่านั้นที่ผสม gradio กับ backend)"""

import time

import gradio as gr

from backend.attachments import add_attachments
from backend.chat_service import chat
from backend.config import AUTO_RESUME_LAST_CHAT, LANG_EN, MODE_AUTO
from backend.cowork import WorkspaceError, open_workspace_folder
from backend.history import (
    chat_choices,
    chat_exists,
    delete_chat,
    list_chats,
    read_chat,
    save_chat,
)
from .visuals import get_page_text, make_header, make_topbar


def update_language(language):
    t = get_page_text(language)
    return (
        make_topbar(language),
        make_header(language),
        gr.update(placeholder=t["placeholder"]),
    )


EMPTY_BOX = {"text": "", "files": []}


def respond(value, history, language, use_search, use_kb, deep_think, files,
            cowork=False, allow_write=False, workspace="", doc_pics=True, model_mode=MODE_AUTO):
    # ช่องพิมพ์แบบ Multimodal ส่งค่ามาเป็น {"text": ..., "files": [...]}
    if isinstance(value, dict):
        message = (value.get("text") or "").strip()
    else:
        message = (value or "").strip()

    history = history or []
    files = files or []

    # แนบไฟล์/รูปแต่ไม่พิมพ์อะไร -> ให้สรุปหรืออธิบายสิ่งที่แนบ
    if not message and files:
        message = (
            "Please summarize or describe what I attached."
            if language == LANG_EN
            else "ช่วยสรุปหรืออธิบายสิ่งที่แนบมาให้หน่อย"
        )

    if not message:
        yield history, EMPTY_BOX
        return

    shown = history + [{"role": "user", "content": message}]
    yield shown, EMPTY_BOX

    # ช่องพิมพ์ล้างครั้งเดียวตอนส่ง หลังจากนั้นไม่แตะอีก (gr.update() = ไม่เปลี่ยนค่า)
    # ไม่งั้นข้อความที่ผู้ใช้พิมพ์ระหว่างที่ AI กำลังตอบจะถูกล้างทุกครั้งที่คำตอบยาวขึ้น
    for partial in chat(
        message, history, language, use_search, use_kb, deep_think, files,
        cowork, allow_write, workspace, doc_pics, model_mode,
    ):
        yield shown + [{"role": "assistant", "content": partial}], gr.update()


def hide_intro():
    # ซ่อนหน้าต้อนรับ แล้วแสดงกล่องแชต
    return gr.update(visible=False), gr.update(visible=True)


DELETE_LABEL = "ลบแชตนี้"

DELETE_CONFIRM_LABEL = "กดอีกครั้งเพื่อยืนยันลบ"

DELETE_CONFIRM_SECONDS = 6


def file_panel(files, notes):
    """ข้อความรายการสิ่งที่แนบ + ปุ่มล้าง"""
    lines = []

    for f in files:
        if f.get("kind") == "image":
            lines.append(f"🖼️ **{f['name']}**")
        else:
            n_pics = len(f.get("images") or [])
            pics = f" · 🖼️ {n_pics} รูป" if n_pics else ""
            lines.append(f"📎 **{f['name']}** · {len(f['text']):,} ตัวอักษร{pics}")

    lines += notes

    return (
        gr.update(value="  \n".join(lines), visible=bool(lines)),
        gr.update(visible=bool(files)),
    )


def ingest(value, current):
    """รับไฟล์/รูปจากช่องพิมพ์ (แนบหรือกด Ctrl+V) เก็บเข้ารายการ แล้วเหลือไว้แต่ข้อความ"""
    value = value if isinstance(value, dict) else {"text": value or "", "files": []}
    paths = value.get("files") or []

    if not paths:
        return current or [], gr.update(), gr.update(), gr.update()

    files, notes = add_attachments(paths, current)
    info, clear = file_panel(files, notes)

    return files, info, clear, {"text": value.get("text") or "", "files": []}


def clear_files():
    return [], gr.update(value="", visible=False), gr.update(visible=False)


def history_update(current_id=None):
    return gr.update(choices=chat_choices(current_id), value=current_id)


def open_chat(selected_id, chat_id, files):
    """เปิดแชตเก่าจากรายการประวัติ (ไฟล์แนบของแชตเก่าไม่ถูกเก็บไว้)"""
    data = read_chat(selected_id)

    if not data:
        return (
            gr.update(), gr.update(), chat_id, files, gr.update(), gr.update(),
        )

    messages = [
        {"role": m["role"], "content": m["content"]}
        for m in data.get("messages", [])
        if isinstance(m, dict)
        and m.get("role") in ("user", "assistant")
        and isinstance(m.get("content"), str)
    ]

    return (
        gr.update(value=messages, visible=True),     # chatbot
        gr.update(visible=False),                    # หน้าต้อนรับ
        selected_id,                                 # chat_id_state
        [],                                          # files_state
        gr.update(value="", visible=False),          # attach_info
        gr.update(visible=False),                    # clear_btn
    )


def reset_ui():
    """กลับไปหน้าต้อนรับ แชตใหม่ว่างๆ"""
    return (
        gr.update(value=[], visible=False),          # chatbot
        gr.update(visible=True),                     # หน้าต้อนรับ
        None,                                        # chat_id_state
        [],                                          # files_state
        gr.update(value="", visible=False),          # attach_info
        gr.update(visible=False),                    # clear_btn
        EMPTY_BOX,                                   # ช่องพิมพ์
        gr.update(choices=chat_choices(), value=None),   # รายการประวัติ
    )


def new_chat():
    return reset_ui()


def delete_step(chat_id, armed_at, files):
    """ลบแชตปัจจุบัน: กดครั้งแรกขอยืนยัน กดอีกครั้งภายในไม่กี่วินาทีจึงลบจริง"""
    keep = (
        gr.update(), gr.update(), chat_id, files,
        gr.update(), gr.update(), gr.update(), gr.update(),
    )
    if not chat_exists(chat_id):
        return (0.0, gr.update(value=DELETE_LABEL), *keep)

    now = time.time()

    if not armed_at or now - armed_at > DELETE_CONFIRM_SECONDS:
        return (now, gr.update(value=DELETE_CONFIRM_LABEL), *keep)

    try:
        delete_chat(chat_id)
    except Exception as e:
        print(f"[Local AI] delete chat: {type(e).__name__}: {e}")
        return (0.0, gr.update(value=DELETE_LABEL), *keep)

    return (0.0, gr.update(value=DELETE_LABEL), *reset_ui())


def on_load():
    """เปิดแอป: เติมรายการประวัติ และเปิดแชตล่าสุดต่อให้เลย (ถ้าเปิดใช้)"""
    items = list_chats()

    if AUTO_RESUME_LAST_CHAT and items:
        last = items[0]["id"]
        return (*open_chat(last, None, []), history_update(last))

    return (
        gr.update(), gr.update(), None, [],
        gr.update(), gr.update(), history_update(None),
    )


def save_chat_handler(history, chat_id):
    """ผูกกับหน้าจอ: บันทึกแชต (backend) แล้วอัปเดตรายการประวัติ"""
    chat_id, saved = save_chat(history, chat_id)
    return chat_id, (history_update(chat_id) if saved else gr.update())


def open_workspace(raw):
    """ปุ่ม 'เปิดโฟลเดอร์': เปิดโฟลเดอร์ทำงานใน File Explorer"""
    try:
        shown = open_workspace_folder(raw)
    except WorkspaceError as e:
        gr.Warning(str(e))
        return

    if shown:
        gr.Info(shown)