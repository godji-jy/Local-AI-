"""Local AI: ตัวเปิดแอป

โครงสร้างโปรเจกต์
  backend/   แบ็กเอนด์ (ไม่มีโค้ดหน้าจอ): config.py = ค่าตั้งค่าทั้งหมด
  frontend/  หน้าจอ Gradio: style.py = ธีม/CSS, ui.py = การจัดวาง
รัน:  python app.py
"""
import os

# ต้องตั้งก่อน import gradio ไม่งั้นไม่มีผล
os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"

import threading

from backend.config import WARM_UP
from backend.ollama_client import warm_up
from frontend.ui import build_demo

demo, launch_kwargs = build_demo()


if __name__ == "__main__":
    HOST, PORT = "127.0.0.1", 7860
    demo.queue()

    # โหลดโมเดลล่วงหน้าเบื้องหลัง ระหว่างที่หน้าต่างกำลังเปิด
    if WARM_UP:
        threading.Thread(target=warm_up, daemon=True).start()

    try:
        import webview        # pip install pywebview
    except ImportError:
        webview = None

    if webview is None:
        print("[Local AI] ไม่พบ pywebview -> เปิดในเบราว์เซอร์แทน "
              "(อยากได้หน้าต่างโปรแกรม: pip install pywebview)")
        demo.launch(server_name=HOST, server_port=PORT, share=False, **launch_kwargs)
    else:
        # เปิดเซิร์ฟเวอร์เบื้องหลัง แล้วแสดงในหน้าต่างโปรแกรมของ Windows
        demo.launch(
            server_name=HOST,
            server_port=PORT,
            share=False,
            inbrowser=False,
            prevent_thread_lock=True,
            **launch_kwargs,
        )
        webview.create_window(
            "Local AI",
            f"http://{HOST}:{PORT}",
            width=1100,
            height=820,
            resizable=True,
            min_size=(420, 600),
            maximized=True,
        )
        webview.start()       # ปิดหน้าต่างแล้วโปรแกรมจะจบการทำงาน
        demo.close()