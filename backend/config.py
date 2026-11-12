"""ค่าตั้งค่าทั้งหมดของโปรแกรม: แก้ที่ไฟล์นี้ที่เดียว (โมเดล, NUM_CTX, ขีดจำกัดต่างๆ, โฟลเดอร์)"""

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent   # โฟลเดอร์หลักของโปรเจกต์ (ที่มี app.py)
DB_DIR = BASE_DIR / "chroma_db"          # สร้างโดย add_knowledge.py
CHATS_DIR = BASE_DIR / "chats"           # ประวัติแชต (ไฟล์ .json ต่อ 1 แชต)

OLLAMA_URL = "http://127.0.0.1:11434"
MODEL = "qwen3.5:2b-q4_K_M"
EMBED_MODEL = "bge-m3"

# ---------------------------------------------------------
# ตั้งค่า (ปรับได้)
# ---------------------------------------------------------
# ชุดค่านี้จูนสำหรับ: Intel i5-11400H (6 คอร์) + RAM 16 GB + RTX 3050 Laptop (VRAM 4 GB)
#
# เป้าหมายคือให้โมเดลอยู่บน GPU "ทั้งหมด" เพราะเร็วที่สุด
#   ตรวจด้วยคำสั่ง  ollama ps  ช่อง PROCESSOR ต้องเป็น "100% GPU"
#   - ถ้าขึ้นเป็นสัดส่วน CPU/GPU แปลว่า NUM_CTX ใหญ่เกิน VRAM -> ลดลง
#   - ถ้าเป็น 100% GPU และ nvidia-smi ยังเหลือ VRAM -> ค่อยๆ เพิ่ม NUM_CTX (12288, 16384)
#
# NUM_CTX = ที่ว่างรวมของ prompt + ประวัติ + ข้อมูลที่ค้นมา + คำตอบ
# ต้องเท่ากันทุกการเรียก ถ้าเปลี่ยนไปมา Ollama จะโหลดโมเดลใหม่ทุกครั้ง (ช้า)
NUM_CTX = 8192
MAX_TOKENS_FAST = 3072       # คำตอบสูงสุดโหมดปกติ
MAX_TOKENS_THINK = 5120      # โหมดคิดลึก (token ที่ใช้คิดนับรวมด้วย)

NUM_THREAD = 6               # จำนวนเธรด CPU = จำนวนคอร์จริง (i5-11400H มี 6 คอร์) ตั้ง None = ให้ Ollama เลือก
NUM_GPU = None               # จำนวนเลเยอร์ของโมเดลแชตบน GPU: None = อัตโนมัติ, 0 = รันบน CPU ล้วน
EMBED_ON_CPU = True          # ให้ bge-m3 (ค้นเว็บ/ไฟล์/ฐานความรู้) รันบน CPU เหลือ VRAM ให้โมเดลแชต
KEEP_ALIVE = "10m"           # ค้างโมเดลไว้ในหน่วยความจำนานเท่าไหร่หลังใช้งานล่าสุด (กันโหลดซ้ำ)
WARM_UP = True               # โหลดโมเดลล่วงหน้าตอนเปิดแอป คำถามแรกจะไม่ต้องรอ
STREAM_INTERVAL = 0.05       # อัปเดตข้อความบนหน้าจอทุกกี่วินาที (ลดภาระหน้าจอ ลื่นขึ้น)

# ประวัติแชตที่ส่งให้โมเดล (ยิ่งเยอะ AI ยิ่งจำบทสนทนาได้นาน แต่ใช้ NUM_CTX มากขึ้น)
HISTORY_MESSAGES = 4
HISTORY_CHARS = 1000

# ไฟล์ที่แนบในแชต
FILE_TYPES = [
    ".txt", ".md", ".pdf", ".docx", ".csv", ".json", ".log", ".xml",
    ".yaml", ".yml", ".ini", ".html", ".css", ".js", ".ts", ".py",
    ".java", ".c", ".cpp", ".cs", ".go", ".rs", ".sql", ".sh",
]
MAX_FILES = 10                # แนบได้กี่ไฟล์พร้อมกัน
MAX_FILE_MB = 50             # ขนาดไฟล์สูงสุดต่อไฟล์
FILE_STORE_CHARS = 600_000   # เก็บข้อความต่อไฟล์ไม่เกินกี่ตัวอักษร
FILE_FULL_CHARS = 5000       # รวมไม่เกินนี้ = ส่งทั้งไฟล์ / เกิน = เลือกเฉพาะส่วนที่ตรงคำถาม
FILE_CHUNK_CHARS = 1200      # ขนาดชิ้นเมื่อไฟล์ยาว
FILE_TOP_CHUNKS = 5          # จำนวนชิ้นที่ส่งให้โมเดลเมื่อไฟล์ยาว

# รูปภาพที่แนบ/วางจากคลิปบอร์ด (ต้องใช้โมเดลที่อ่านรูปได้)
IMAGE_TYPES = [".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"]
MAX_IMAGES = 3               # แนบรูปได้กี่รูปพร้อมกัน
IMAGE_MAX_SIDE = 640        # ย่อรูปให้ด้านยาวสุดไม่เกินกี่พิกเซล

# รูปที่ดึงจากไฟล์เอกสาร (PDF / Word) มาใช้ประกอบคำตอบ
DOC_IMAGES = True            # False = ปิดฟีเจอร์ดึงรูปจากไฟล์ทั้งหมด
MAX_DOC_IMAGES = 20          # ดึงรูปได้สูงสุดกี่รูปต่อไฟล์
MAX_SCAN_PAGES = 80          # PDF: สแกนหารูปไม่เกินกี่หน้า
MIN_DOC_IMAGE_SIDE = 100     # ข้ามรูปที่ด้านสั้นเล็กกว่านี้ (ไอคอน/โลโก้/เส้นตกแต่ง)
DOC_IMAGES_PER_ANSWER = 3    # รูปจากไฟล์ที่ส่งให้ AI ดู + โชว์ใต้คำตอบ ต่อ 1 คำตอบ
DOC_IMG_DIR = BASE_DIR / "doc_images"   # เก็บสำเนารูปที่ดึงมา (ไว้โชว์ในแชต)
VISION_MODEL = "gemma3:4b"            # โมเดลสำรองที่อ่านรูปได้ (ใช้เมื่อ MODEL อ่านรูปไม่ได้) เช่น "qwen2.5vl:7b"

# โหมดทำงานกับไฟล์ (Cowork): ให้ AI อ่าน/สร้าง/แก้ไฟล์ในโฟลเดอร์ทำงาน (แตะนอกโฟลเดอร์นี้ไม่ได้)
WORKSPACE_DIR = BASE_DIR / "workspace"   # โฟลเดอร์ทำงานเริ่มต้น (เปลี่ยนได้ในช่องตั้งค่าบนหน้าจอ)
MAX_AGENT_STEPS = 6                      # AI เรียกเครื่องมือต่อเนื่องได้สูงสุดกี่รอบต่อ 1 คำสั่ง
TOOL_RESULT_CHARS = 3000                 # ผลลัพธ์ของเครื่องมือแต่ละครั้งยาวสุดกี่ตัวอักษร (ให้พอดีกับ NUM_CTX)
AGENT_CHAR_BUDGET = int(NUM_CTX * 1.5)   # ข้อความสะสมเกินนี้ -> ให้ AI สรุปเลย ไม่เรียกเครื่องมือเพิ่ม
WRITE_MAX_CHARS = 200_000                # ไฟล์ที่ AI เขียนยาวสุดกี่ตัวอักษร
WRITE_TYPES = [t for t in FILE_TYPES if t not in (".pdf", ".docx")]   # ชนิดไฟล์ที่ AI สร้าง/แก้ได้ (ไม่มี .exe .bat .ps1)
PROTECTED_NAMES = {".backups", ".git", ".venv", "chats", "chroma_db", "__pycache__"}   # AI แตะไม่ได้

# ประวัติแชต: บันทึกอัตโนมัติ ปิดแอปแล้วเปิดใหม่ยังอยู่
HISTORY_LIST_MAX = 30        # แสดงรายการแชตล่าสุดกี่อัน (ที่เหลือยังอยู่ในโฟลเดอร์ chats)
AUTO_RESUME_LAST_CHAT = True # เปิดแอปแล้วเปิดแชตล่าสุดต่อให้เลย (False = เริ่มที่หน้าต้อนรับ)

SEARCH_MAX_RESULTS = 6
FETCH_PAGES = 3
PAGE_CHARS = 8000
CHUNK_CHARS = 700
WEB_TOP_PASSAGES = 4
SNIPPET_CHARS = 300
PASSAGE_CHARS = 700

KB_TOP = 3
KB_MAX_DISTANCE = 0.55

HTTP_HEADERS = {"User-Agent": "LocalAI/1.0 (local Gradio app)"}
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "th,en;q=0.8",
}

LANG_THAI = "ไทย (Thai)"
LANG_EN = "English"
LANG_AUTO = "อัตโนมัติ (Auto)"

# ---------------------------------------------------------
# โมเดลเขียนโค้ด (แยกหน้าที่จากโมเดลทั่วไป)
# ---------------------------------------------------------
# คำถามเกี่ยวกับโค้ดจะถูกส่งให้ CODE_MODEL ตอบ ส่วนคำถามทั่วไปใช้ MODEL (ติดตั้ง: ollama pull qwen2.5-coder:3b)
# ฐานความรู้ ค้นเว็บ และไฟล์แนบ ใช้ร่วมกันทั้งสองโมเดล / ตั้งเป็น "" เพื่อปิด (ใช้ MODEL ตัวเดียว)
# หมายเหตุ: VRAM 4 GB วางได้ทีละโมเดลแชต สลับโมเดลครั้งแรกจะรอโหลดราว 3-10 วินาที
CODE_MODEL = "qwen2.5-coder:3b"
CODE_TEMPERATURE = 0.3       # งานโค้ดควรนิ่งกว่างานทั่วไป (โมเดลทั่วไปใช้ 0.7)

# ตัวเลือก "โมเดล" บนหน้าจอ
MODE_AUTO = "ตามคำถาม (Auto)"
MODE_GENERAL = "ทั่วไป (General)"
MODE_CODE = "เขียนโค้ด (Coding)"