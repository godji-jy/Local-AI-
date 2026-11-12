"""การจัดวางหน้าจอและผูกเหตุการณ์: build_demo() สร้างหน้าจอ Gradio ทั้งหมด"""

import gradio as gr

from backend.config import (
    DOC_IMG_DIR,
    FILE_TYPES,
    IMAGE_TYPES,
    LANG_AUTO,
    LANG_EN,
    LANG_THAI,
    MODE_AUTO,
    MODE_CODE,
    MODE_GENERAL,
    WORKSPACE_DIR,
)
from backend.history import chat_choices
from .handlers import (
    DELETE_LABEL,
    clear_files,
    delete_step,
    hide_intro,
    ingest,
    new_chat,
    on_load,
    open_chat,
    open_workspace,
    respond,
    save_chat_handler,
    update_language,
)
from .style import CSS, HEAD_JS, THEME
from .visuals import (
    get_page_text,
    make_header,
    make_status_card,
    make_tips_card,
    make_topbar,
    section_label,
)
from backend.doc_images import set_file_url_prefix


GR_MAJOR = int(gr.__version__.split(".")[0])

POPULAR = [
    ("อธิบาย AI", "อธิบาย Machine Learning ให้เข้าใจง่ายสำหรับผู้เริ่มต้น"),
    ("เขียนโค้ด Python", "ช่วยเขียนโค้ด Python อ่านไฟล์ CSV และสรุปข้อมูล"),
    ("วิทยาศาสตร์", "อธิบายหลักการทำงานของแบตเตอรี่ลิเธียมไอออน"),
]


def build_demo():
    """สร้างหน้าจอทั้งหมด คืนค่า (demo, launch_kwargs)"""
    blocks_kwargs = {"title": "Local AI"}

    launch_kwargs = {}

    # autoscroll=False: ปิดตัวเลื่อนอัตโนมัติของ Gradio (มันดีดลงล่างทุกครั้งที่คำตอบยาวขึ้น
    # ทำให้เลื่อนขึ้นไปอ่านไม่ได้) แล้วใช้สคริปต์ด้านล่างแทน
    chatbot_kwargs = {
        "elem_id": "chatbot", "show_label": False, "visible": False, "autoscroll": False,
    }

    # ให้เบราว์เซอร์โหลดรูปที่ดึงจากไฟล์ได้ (แบ็กเอนด์สร้างลิงก์รูปตามเวอร์ชันของ Gradio)
    DOC_IMG_DIR.mkdir(exist_ok=True)
    launch_kwargs["allowed_paths"] = [str(DOC_IMG_DIR)]
    set_file_url_prefix("/gradio_api/file=" if GR_MAJOR >= 5 else "/file=")

    if GR_MAJOR >= 6:
        launch_kwargs.update(theme=THEME, css=CSS, head=HEAD_JS)
    else:
        blocks_kwargs.update(theme=THEME, css=CSS, head=HEAD_JS)
        chatbot_kwargs["type"] = "messages"

    with gr.Blocks(**blocks_kwargs) as demo:
        topbar = gr.HTML(make_topbar(LANG_THAI))

        with gr.Row(elem_id="app-grid"):

            # ---- ซ้าย: แชตใหม่ / หัวข้อแนะนำ / ประวัติ ----
            with gr.Column(elem_id="left", scale=0, min_width=240):
                new_btn = gr.Button("แชตใหม่", elem_id="new-btn")

                gr.HTML(section_label("หัวข้อแนะนำ / Topics"))
                card_btns = [
                    gr.Button(title, elem_classes="pcard", elem_id=f"pcard-{i}", min_width=160)
                    for i, (title, _) in enumerate(POPULAR, start=1)
                ]

                with gr.Column(elem_id="history-card"):
                    gr.HTML(section_label("ประวัติแชต / History"))
                    history_radio = gr.Radio(
                        choices=chat_choices(),
                        value=None,
                        show_label=False,
                        interactive=True,
                        elem_id="history-radio",
                        elem_classes="listradio",
                    )
                    delete_btn = gr.Button(
                        DELETE_LABEL, size="sm", variant="secondary", elem_id="delete-btn",
                    )
                gr.HTML(make_status_card())

            # ---- กลาง: ฉากต้อนรับ / แชต / ช่องพิมพ์ ----
            with gr.Column(elem_id="main", scale=1, min_width=420):
                with gr.Column(elem_id="cards-box") as cards_box:     # ซ่อนเมื่อเริ่มแชต
                    header = gr.HTML(make_header(LANG_THAI))

                chatbot = gr.Chatbot(**chatbot_kwargs)

                files_state = gr.State([])            # ไฟล์ที่แนบไว้ในแชตนี้
                chat_id_state = gr.State(None)        # id ของแชตที่เปิดอยู่ (None = แชตใหม่ ยังไม่ได้บันทึก)
                armed_state = gr.State(0.0)           # เวลาที่กดลบครั้งแรก (ใช้ยืนยันการลบ)

                with gr.Row():
                    attach_info = gr.Markdown("", visible=False, elem_id="attach-info")
                    clear_btn = gr.Button(
                        "ล้างไฟล์/รูป", visible=False, size="sm",
                        elem_id="clear-btn", scale=0, min_width=110,
                    )

                # ช่องพิมพ์ที่แนบไฟล์ได้ และกด Ctrl+V วางรูป/ไฟล์ที่คัดลอกไว้ได้
                box = gr.MultimodalTextbox(
                    placeholder=get_page_text(LANG_THAI)["placeholder"],
                    show_label=False,
                    lines=1,
                    max_lines=5,
                    file_count="multiple",
                    file_types=FILE_TYPES + IMAGE_TYPES,
                    sources=["upload"],
                    container=False,
                    elem_id="input-row",
                )

            # ---- ขวา: ตั้งค่า ----
            with gr.Column(elem_id="right", scale=0, min_width=250):
                with gr.Column(elem_id="settings-card"):
                    gr.HTML(section_label("ภาษา / Language"))
                    language = gr.Radio(
                        choices=[LANG_THAI, LANG_EN, LANG_AUTO],
                        value=LANG_THAI,
                        show_label=False,
                        elem_id="lang-radio",
                        elem_classes="listradio",
                    )

                    gr.HTML(section_label("โมเดล / Model"))
                    model_mode = gr.Radio(
                        choices=[MODE_AUTO, MODE_GENERAL, MODE_CODE],
                        value=MODE_AUTO,
                        show_label=False,
                        elem_id="model-radio",
                        elem_classes="listradio",
                    )

                    gr.HTML(section_label("เครื่องมือ / Tools"))
                    with gr.Row(elem_id="chips"):
                        use_search = gr.Checkbox(label="ค้นหาเว็บ", value=False)
                        use_kb = gr.Checkbox(label="ใช้ฐานความรู้ในเครื่อง", value=False)
                        deep_think = gr.Checkbox(label="คิดลึก (ช้ากว่า)", value=False)
                        cowork = gr.Checkbox(label="โหมดทำงานกับไฟล์ (Cowork)", value=False)
                        allow_write = gr.Checkbox(label="อนุญาตสร้าง/แก้ไฟล์", value=True)
                        doc_pics = gr.Checkbox(label="ดึงรูปจากไฟล์มาประกอบคำตอบ", value=True)

                    gr.HTML(section_label("โฟลเดอร์ทำงาน Cowork: AI แตะได้เฉพาะในโฟลเดอร์นี้"))
                    workspace_tb = gr.Textbox(
                        value=str(WORKSPACE_DIR),
                        show_label=False,
                        lines=1,
                        max_lines=1,
                        elem_id="workspace-box",
                    )
                    open_ws_btn = gr.Button(
                        "เปิดโฟลเดอร์", size="sm", variant="secondary", elem_id="open-ws-btn",
                    )
                gr.HTML(make_tips_card())

        chat_inputs = [
            box, chatbot, language, use_search, use_kb, deep_think, files_state,
            cowork, allow_write, workspace_tb, doc_pics, model_mode,
        ]

        box.submit(hide_intro, outputs=[cards_box, chatbot], queue=False).then(
            ingest,
            inputs=[box, files_state],
            outputs=[files_state, attach_info, clear_btn, box],
            queue=False,
        ).then(respond, inputs=chat_inputs, outputs=[chatbot, box]).then(
            save_chat_handler,
            inputs=[chatbot, chat_id_state],
            outputs=[chat_id_state, history_radio],
            queue=False,
        )

        for btn, (_, prompt) in zip(card_btns, POPULAR):
            btn.click(lambda p=prompt: {"text": p, "files": []}, outputs=box, queue=False).then(
                hide_intro, outputs=[cards_box, chatbot], queue=False
            ).then(respond, inputs=chat_inputs, outputs=[chatbot, box]).then(
                save_chat_handler,
                inputs=[chatbot, chat_id_state],
                outputs=[chat_id_state, history_radio],
                queue=False,
            )

        clear_btn.click(
            clear_files,
            outputs=[files_state, attach_info, clear_btn],
        )

        open_ws_btn.click(open_workspace, inputs=[workspace_tb], queue=False)

        reset_outputs = [
            chatbot, cards_box, chat_id_state, files_state,
            attach_info, clear_btn, box, history_radio,
        ]

        new_btn.click(new_chat, outputs=reset_outputs, queue=False)

        history_radio.input(
            open_chat,
            inputs=[history_radio, chat_id_state, files_state],
            outputs=[chatbot, cards_box, chat_id_state, files_state, attach_info, clear_btn],
            queue=False,
        )

        delete_btn.click(
            delete_step,
            inputs=[chat_id_state, armed_state, files_state],
            outputs=[armed_state, delete_btn, *reset_outputs],
            queue=False,
        )

        demo.load(
            on_load,
            outputs=[chatbot, cards_box, chat_id_state, files_state,
                     attach_info, clear_btn, history_radio],
            queue=False,
        )

        language.change(
            update_language,
            inputs=[language],
            outputs=[topbar, header, box],
            queue=False,
        )

    return demo, launch_kwargs