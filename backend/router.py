"""เลือกโมเดลตามประเภทคำถาม: โมเดลทั่วไป (MODEL) หรือโมเดลเขียนโค้ด (CODE_MODEL)

ทำงานด้วยกฎง่ายๆ ที่เร็วและไม่เสียเวลาเรียกโมเดลเพิ่ม (ดูคำสำคัญ บล็อกโค้ด ข้อความ error
ชื่อไฟล์โค้ด และคำถามต่อเนื่องจากคำตอบที่เป็นโค้ด) ผลไม่ได้แม่นยำ 100% จึงมีโหมดบังคับเลือกเองได้
"""

import re

from .config import (
    CODE_MODEL,
    MODE_AUTO,
    MODE_CODE,
    MODE_GENERAL,
    MODEL,
)
from .ollama_client import model_installed

# ชื่อไฟล์ที่เป็นโค้ด (แนบไฟล์พวกนี้ = ถามเรื่องโค้ด)
CODE_SUFFIXES = {
    ".py", ".js", ".ts", ".java", ".c", ".cpp", ".cs", ".go", ".rs", ".sql", ".sh", ".html", ".css",
}

# คำที่บอกชัดว่าเป็นเรื่องโค้ด (เจอคำเดียวก็พอ)
_STRONG_EN = re.compile(
    r"\b(python|javascript|typescript|java|golang|rust|php|sql|html|css|react|vue|node\.?js|"
    r"django|flask|fastapi|pandas|numpy|regex|bash|powershell|docker|git|traceback|stack ?trace|"
    r"syntax ?error|compile[rd]?|debug(ging)?|refactor|algorithm|unit ?tests?|pip install|npm)\b"
    r"|(?<![a-z])(c\+\+|c#)",
    re.I,
)
_STRONG_TH = re.compile(
    r"โค้ด|เขียนโปรแกรม|โปรแกรมมิ่ง|บั๊ก|ดีบัก|คอมไพล์|สคริปต์|อัลกอริทึม|ไลบรารี|แพ็กเกจ|รีแฟกเตอร์|"
    r"ชุดคำสั่ง|แก้\s*error|error\s*ของ"
)
_TRACEBACK = re.compile(r"Traceback \(most recent call last\)|\b\w+(Error|Exception)\b:")
# หน้าตาของโค้ดจริงที่ไม่ต้องมีคำว่า "โค้ด"/ชื่อภาษาอยู่ในประโยค
# คำสั่ง SQL ต้องเป็นตัวพิมพ์ใหญ่ (หรือ select * from) ไม่งั้นประโยคอังกฤษธรรมดาอย่าง
# "select a book from the list" จะถูกเข้าใจผิดว่าเป็นโค้ด
_SQL = re.compile(
    r"\bSELECT\b.+\bFROM\b|\bINSERT\s+INTO\b|\bUPDATE\s+\w+\s+SET\b|\bDELETE\s+FROM\b|"
    r"\b(CREATE|ALTER|DROP)\s+TABLE\b",
    re.S,
)
_CODE_SYNTAX = re.compile(
    r"\bselect\s*\*\s*from\b|\bdef\s+\w+\s*\(|console\.log|#include\s*<|public\s+static\s+void|"
    r"System\.out|<\?php|=>\s*\{|\bfor\s*\(.+;.+;.+\)",
    re.I | re.S,
)
_FILENAME = re.compile(r"\b[\w\-]+\.(py|js|ts|jsx|tsx|java|cpp|cs|go|rs|sql|sh|html|css|php|rb)\b", re.I)

# คำที่กำกวม (อยู่ในเรื่องอื่นได้) ต้องเจออย่างน้อย 2 คำถึงจะนับ
_WEAK = re.compile(
    r"\b(function|class|variable|loop|array|api|json|library|package|script|code|error|exception|bug|"
    r"database|query|server)\b|ฟังก์ชัน|ฐานข้อมูล|ข้อผิดพลาด|โปรแกรม|เซิร์ฟเวอร์",
    re.I,
)

FOLLOW_UP_CHARS = 40       # ข้อความสั้นกว่านี้ที่ต่อจากคำตอบที่เป็นโค้ด ถือว่ายังคุยเรื่องโค้ดอยู่


def looks_like_code_request(message, history=None, files=None):
    """เดาว่าคำถามนี้เกี่ยวกับโค้ดหรือไม่"""
    message = message or ""

    if "```" in message or _TRACEBACK.search(message) or _FILENAME.search(message) or _CODE_SYNTAX.search(message) or _SQL.search(message):
        return True

    if _STRONG_EN.search(message) or _STRONG_TH.search(message):
        return True

    if len(_WEAK.findall(message)) >= 2:
        return True

    for f in files or []:
        name = str(f.get("name", "")).lower()
        if f.get("kind", "doc") == "doc" and any(name.endswith(s) for s in CODE_SUFFIXES):
            return True

    # "แก้ให้หน่อย" / "ต่อ" / "ขออีกแบบ" หลังจากที่เพิ่งตอบเป็นโค้ด
    if len(message.strip()) <= FOLLOW_UP_CHARS:
        for item in reversed(history or []):
            if isinstance(item, dict) and item.get("role") == "assistant":
                content = item.get("content", "")
                text = content if isinstance(content, str) else str(content)
                return "```" in text

    return False


def choose_model(mode, message, history, files, has_images, is_en):
    """เลือกโมเดลสำหรับคำตอบ คืนค่า (ชื่อโมเดล, ชนิด "general"/"code", ข้อความแจ้งผู้ใช้ หรือ None)"""
    if not CODE_MODEL or mode == MODE_GENERAL:
        return MODEL, "general", None

    # รูปที่แนบต้องให้โมเดลที่อ่านรูปได้ดู โมเดลเขียนโค้ดอ่านรูปไม่ได้
    if has_images:
        return MODEL, "general", None

    wants_code = mode == MODE_CODE or (
        mode == MODE_AUTO and looks_like_code_request(message, history, files)
    )

    if not wants_code:
        return MODEL, "general", None

    if not model_installed(CODE_MODEL):
        note = (
            f"⚠️ Coding model `{CODE_MODEL}` is not installed, so `{MODEL}` answered instead. "
            f"Install it with: `ollama pull {CODE_MODEL}`"
            if is_en
            else f"⚠️ ยังไม่ได้ติดตั้งโมเดลเขียนโค้ด `{CODE_MODEL}` จึงใช้ `{MODEL}` ตอบแทน "
                 f"ติดตั้งด้วย: `ollama pull {CODE_MODEL}`"
        )
        return MODEL, "general", note

    return CODE_MODEL, "code", None
