"""ตัวประสานหลักของแบ็กเอนด์: chat() รับคำถาม -> ค้น/อ่านไฟล์ -> ถามโมเดล -> ส่งคำตอบทีละช่วง"""

import time

from .attachments import build_file_context, file_instruction, image_instruction
from .config import (
    CODE_MODEL,
    DOC_IMAGES,
    DOC_IMAGES_PER_ANSWER,
    FILE_FULL_CHARS,
    HISTORY_CHARS,
    HISTORY_MESSAGES,
    LANG_AUTO,
    LANG_EN,
    LANG_THAI,
    MAX_IMAGES,
    MODE_AUTO,
    STREAM_INTERVAL,
)
from .cowork import agent_run
from .knowledge import (
    build_context,
    format_sources,
    grounding_instruction,
    make_search_query,
    search_knowledge,
    web_passages,
)
from .ollama_client import (
    error_message,
    no_vision_message,
    ollama_stream,
    pick_vision_model,
)
from .prompts import CODING_PROMPT_EN, CODING_PROMPT_TH, PROMPTS
from .text_utils import (
    SOURCE_SPLIT,
    content_to_text,
    detect_prompt_language,
    strip_think,
)
from .doc_images import (
    doc_image_instruction,
    doc_images_markdown,
    pick_doc_images,
    place_doc_images,
    strip_doc_images,
)
from .router import choose_model


def chat(message, history, language, use_search, use_kb, deep_think, files=None,
         cowork=False, allow_write=False, workspace="", doc_pics=True, model_mode=MODE_AUTO):
    message = (message or "").strip()
    history = history or []
    files = files or []
    docs = [f for f in files if f.get("kind", "doc") == "doc"]
    images = [f for f in files if f.get("kind") == "image"]

    if language not in PROMPTS:
        language = LANG_THAI

    ui_is_en = language == LANG_EN

    if not message:
        yield "Please enter a question." if ui_is_en else "กรุณาพิมพ์คำถามก่อน"
        return

    start_time = time.perf_counter()

    work_language = (
        detect_prompt_language(message) if language == LANG_AUTO else language
    )
    work_is_en = work_language == LANG_EN

    # คำถามสั้นๆ ที่ต่อเนื่องจากเดิม ให้เอาคำถามก่อนหน้ามาประกอบการค้น
    base_query = message
    if len(message) < 25:
        previous = [
            content_to_text(h.get("content", ""))
            for h in history
            if isinstance(h, dict) and h.get("role") == "user"
        ]
        if previous:
            base_query = previous[-1][:200] + " " + message

    try:
        sources = []
        context_parts = []

        if use_kb:
            yield (
                "📚 Searching your knowledge base..."
                if ui_is_en
                else "📚 กำลังค้นฐานความรู้ในเครื่อง..."
            )

            kb_passages = search_knowledge(base_query)

            if kb_passages:
                context_parts.append(build_context(kb_passages, sources))

        if use_search:
            yield (
                "🔎 Preparing the search..."
                if ui_is_en
                else "🔎 กำลังเตรียมคำค้นหา..."
            )

            query = make_search_query(message, history)

            yield (
                f"🔎 Searching: {query}"
                if ui_is_en
                else f"🔎 กำลังค้นหาและอ่านเว็บ: {query}"
            )

            web = web_passages(query, is_thai=not work_is_en)

            if web:
                context_parts.append(build_context(web, sources))

        # ไฟล์ที่แนบมา
        file_context, file_partial = "", False

        if docs:
            if sum(len(f["text"]) for f in docs) > FILE_FULL_CHARS:
                yield (
                    "📎 Reading your files..."
                    if ui_is_en
                    else "📎 กำลังอ่านไฟล์ที่แนบ..."
                )

            file_context, file_partial = build_file_context(docs, base_query)

        # ถ้ามีไฟล์แนบ ไม่ต้องบอกว่า "ตอบจากความรู้ของโมเดลเอง" เพียงเพราะค้นเว็บ/ฐานความรู้ไม่เจอ
        asked = bool(use_kb or use_search) and (bool(sources) or not files)
        sources_text = format_sources(sources, asked, ui_is_en)

        system_prompt = PROMPTS[language]

        if file_context:
            system_prompt += file_instruction(file_context, file_partial, work_is_en)

        if context_parts:
            system_prompt += grounding_instruction(
                "\n\n".join(context_parts), work_is_en
            )

        # โหมด Cowork: ให้ AI ทำงานกับไฟล์ในโฟลเดอร์ทำงานผ่านเครื่องมือ (ไม่ใช้รูปที่แนบ)
        if cowork:
            yield from agent_run(
                system_prompt, message, history, ui_is_en, work_is_en,
                bool(deep_think), workspace, bool(allow_write),
            )
            return

        # เลือกโมเดลตามหน้าที่: คำถามโค้ด -> โมเดลเขียนโค้ด / อย่างอื่น -> โมเดลทั่วไป
        route_model, route_kind, route_note = choose_model(
            model_mode, message, history, files, bool(images), ui_is_en
        )
        use_coder = route_kind == "code"

        if use_coder:
            system_prompt += CODING_PROMPT_EN if work_is_en else CODING_PROMPT_TH

        # รูปที่ดึงจากไฟล์ที่แนบ (PDF/Word) มาประกอบคำตอบ (โมเดลเขียนโค้ดอ่านรูปไม่ได้ จึงข้ามเมื่อใช้โมเดลนั้น)
        doc_shots = []

        if doc_pics and DOC_IMAGES and docs and not use_coder:
            doc_shots = pick_doc_images(
                docs, file_context, file_partial, message,
                min(DOC_IMAGES_PER_ANSWER, MAX_IMAGES - len(images)),
            )

        # มีรูปแนบ -> ต้องใช้โมเดลที่อ่านรูปได้
        chat_model = route_model
        sent_shots = list(doc_shots)

        if images or doc_shots:
            chat_model = pick_vision_model()

            if not chat_model:
                if images:
                    yield no_vision_message(ui_is_en)
                    return

                chat_model = route_model      # ไม่มีโมเดลอ่านรูป: ตอบด้วยข้อความ แต่ยังโชว์รูปใต้คำตอบ
                sent_shots = []

            if images:
                system_prompt += image_instruction(work_is_en)

            if sent_shots:
                system_prompt += doc_image_instruction(sent_shots, len(images) + 1, work_is_en)

        messages = [{"role": "system", "content": system_prompt}]

        # มีไฟล์แนบ -> ลดประวัติลง เพื่อเหลือที่ว่างให้เนื้อหาไฟล์
        history_n = min(4, HISTORY_MESSAGES) if files else HISTORY_MESSAGES
        history_chars = min(1000, HISTORY_CHARS) if files else HISTORY_CHARS

        for item in history[-history_n:]:
            if not isinstance(item, dict):
                continue

            role = item.get("role")
            content = content_to_text(item.get("content", ""))
            content = strip_doc_images(content.split(SOURCE_SPLIT)[0])

            if role in ("user", "assistant") and content:
                messages.append({
                    "role": role,
                    "content": content[-history_chars:],
                })

        user_message = {"role": "user", "content": message}

        if images or sent_shots:
            user_message["images"] = [im["b64"] for im in images] + [
                im["b64"] for im in sent_shots
            ]

        messages.append(user_message)

        if use_coder:
            yield (
                f"💻 Coding model is answering ({CODE_MODEL})... the first time may wait for the model to load"
                if ui_is_en
                else f"💻 โมเดลเขียนโค้ดกำลังตอบ ({CODE_MODEL})... ครั้งแรกอาจรอโหลดโมเดลสักครู่"
            )
        else:
            yield "🧠 Thinking..." if ui_is_en else "🧠 กำลังคิดคำตอบ..."

        answer = ""
        reason = ""
        last_push = 0.0

        for kind, piece in ollama_stream(
            messages, think=bool(deep_think) and not use_coder, model=chat_model
        ):
            if kind == "content":
                answer += piece

                # อัปเดตหน้าจอเป็นช่วงๆ ไม่ใช่ทุก token (ลดภาระ ทำให้ลื่นขึ้น)
                now = time.perf_counter()
                if now - last_push >= STREAM_INTERVAL:
                    visible = strip_think(answer)
                    if doc_shots and visible:
                        visible, _ = place_doc_images(
                            visible, doc_shots, len(images) + 1, ui_is_en
                        )
                    if visible:
                        yield visible
                        last_push = now

            elif kind == "done":
                reason = piece

        answer = strip_think(answer)

        if not answer:
            if reason == "length":
                yield (
                    "The model ran out of tokens while thinking. Turn off "
                    "Deep think or raise MAX_TOKENS_THINK."
                    if ui_is_en
                    else "AI ใช้ token หมดระหว่างคิด ลองปิดโหมดคิดลึก "
                         "หรือเพิ่มค่า MAX_TOKENS_THINK"
                )
            else:
                yield (
                    "The model did not produce an answer. Please try again."
                    if ui_is_en
                    else "AI ยังสร้างคำตอบไม่ได้ กรุณาลองถามใหม่"
                )
            return

        # คำตอบชนเพดาน token จึงถูกตัด ให้แจ้งผู้ใช้
        if reason == "length":
            answer += (
                "\n\n*(⚠️ The answer was cut off at the length limit. "
                "Ask me to continue.)*"
                if ui_is_en
                else "\n\n*(⚠️ คำตอบถูกตัดเพราะยาวถึงเพดานที่ตั้งไว้ "
                     "พิมพ์ \"ต่อ\" เพื่อให้ตอบต่อ)*"
            )

        elapsed = time.perf_counter() - start_time
        print(
            f"[Local AI] {elapsed:.1f}s | sources: {len(sources)} | "
            f"think: {bool(deep_think)}"
        )

        pics_text = ""

        if doc_shots:
            answer, placed_any = place_doc_images(
                answer, doc_shots, len(images) + 1, ui_is_en, final=True
            )

            # โมเดลไม่ได้ใส่รูปตรงไหนเลย -> โชว์รูปทั้งหมดไว้ท้ายคำตอบแทน (ไม่ให้รูปหาย)
            if not placed_any:
                pics_text = (SOURCE_SPLIT if not sources_text else "\n\n") + doc_images_markdown(
                    doc_shots, len(images) + 1, ui_is_en
                )

        # บอกผู้ใช้ว่าใครตอบ (โมเดลเขียนโค้ด) หรือเตือนว่าใช้โมเดลสำรองเพราะยังไม่ได้ติดตั้ง
        note = route_note

        if use_coder:
            note = (
                f"*💻 Answered by the coding model: {CODE_MODEL}*"
                if ui_is_en
                else f"*💻 ตอบโดยโมเดลเขียนโค้ด: {CODE_MODEL}*"
            )

        tail = sources_text + pics_text

        if note:
            tail = (tail + "\n\n" + note) if tail else (SOURCE_SPLIT + note)

        yield answer + tail

    except Exception as e:
        yield error_message(e, ui_is_en)