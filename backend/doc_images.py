"""รูปที่ฝังอยู่ในไฟล์ PDF / Word: ดึงออกมา เลือกรูปที่เกี่ยวกับคำถาม ส่งให้โมเดลอ่านรูป แล้ววางลงในคำตอบ"""

import base64
import hashlib
import io
import re
from pathlib import Path
from urllib.parse import quote

from .config import (
    DOC_IMAGES,
    DOC_IMG_DIR,
    IMAGE_MAX_SIDE,
    MAX_DOC_IMAGES,
    MAX_SCAN_PAGES,
    MIN_DOC_IMAGE_SIDE,
)

# URL ที่เบราว์เซอร์ใช้ขอไฟล์รูป ขึ้นกับเวอร์ชันของ Gradio จึงให้หน้าจอเป็นคนกำหนดผ่าน set_file_url_prefix()
# (แบ็กเอนด์จะได้ไม่ต้อง import gradio)
_file_url_prefix = "/gradio_api/file="


def set_file_url_prefix(prefix):
    global _file_url_prefix
    _file_url_prefix = prefix


def _doc_image_entry(data, taken, label, page):
    """รูปดิบ 1 รูปจากไฟล์ -> (ย่อให้โมเดลอ่าน + เก็บสำเนาไว้โชว์) หรือ None ถ้าเล็ก/ซ้ำ/ไม่ใช่รูปเนื้อหา"""
    from PIL import Image

    digest = hashlib.sha1(data).hexdigest()[:16]

    if digest in taken:
        return None

    with Image.open(io.BytesIO(data)) as image:
        w, h = image.size

        if min(w, h) < MIN_DOC_IMAGE_SIDE or max(w, h) > 12 * min(w, h):
            return None

        if image.mode in ("RGBA", "LA", "P"):
            image = image.convert("RGBA")
            flat = Image.new("RGB", image.size, "white")
            flat.paste(image, mask=image.split()[-1])
            image = flat
        else:
            image = image.convert("RGB")

        view = image.copy()
        view.thumbnail((IMAGE_MAX_SIDE, IMAGE_MAX_SIDE))
        buffer = io.BytesIO()
        view.save(buffer, format="JPEG", quality=88)
        b64 = base64.b64encode(buffer.getvalue()).decode("ascii")

        show = image.copy()
        show.thumbnail((720, 720))
        DOC_IMG_DIR.mkdir(exist_ok=True)
        file = DOC_IMG_DIR / f"{digest}.jpg"
        show.save(file, format="JPEG", quality=82)

    return {"b64": b64, "file": str(file), "label": label, "page": page, "hash": digest}


def extract_doc_images(path):
    """ดึงรูปที่ฝังอยู่ใน PDF / Word คืนค่า list ของรูป (ว่างถ้าไม่มี หรือดึงไม่ได้)"""
    if not DOC_IMAGES:
        return []

    suffix = path.suffix.lower()
    out, taken = [], set()

    try:
        if suffix == ".pdf":
            from pypdf import PdfReader

            reader = PdfReader(str(path))

            for pi, page in enumerate(reader.pages, start=1):
                if pi > MAX_SCAN_PAGES or len(out) >= MAX_DOC_IMAGES:
                    break

                try:
                    pics = list(page.images)
                except Exception:
                    continue

                for pic in pics:
                    if len(out) >= MAX_DOC_IMAGES:
                        break

                    try:
                        entry = _doc_image_entry(pic.data, taken, f"{path.name} · หน้า {pi}", pi)
                    except Exception:
                        continue

                    if entry:
                        taken.add(entry["hash"])
                        out.append(entry)

        elif suffix == ".docx":
            import docx

            document = docx.Document(str(path))

            for rel in document.part.rels.values():
                if len(out) >= MAX_DOC_IMAGES:
                    break

                if "image" not in rel.reltype or rel.is_external:
                    continue

                try:
                    entry = _doc_image_entry(
                        rel.target_part.blob, taken, f"{path.name} · รูปที่ {len(out) + 1}", None
                    )
                except Exception:
                    continue

                if entry:
                    taken.add(entry["hash"])
                    out.append(entry)

    except Exception as e:
        print(f"[Local AI] extract images {path.name}: {type(e).__name__}: {e}")

    return out


def pick_doc_images(docs, file_context, file_partial, message, limit):
    """เลือกรูปจากไฟล์ที่เกี่ยวกับคำถาม: หน้าที่ผู้ใช้ระบุ > หน้าที่ถูกเลือกมาตอบ > รูปอื่น"""
    if limit <= 0:
        return []

    pages = {int(n) for n in re.findall(r"\[หน้า (\d+)\]", file_context or "")}
    asked = {int(n) for n in re.findall(r"(?:หน้า|page|p\.)\s*(\d+)", message or "", re.I)}
    cands = []

    for f in docs:
        for im in f.get("images") or []:
            rank = 0 if im.get("page") in asked else (1 if im.get("page") in pages else 2)
            cands.append((rank, len(cands), im))

    if file_partial and any(c[0] < 2 for c in cands):
        cands = [c for c in cands if c[0] < 2]

    cands.sort(key=lambda c: (c[0], c[1]))

    picked, seen = [], set()

    for _, _, im in cands:                 # รูปเดียวกันที่อยู่ในหลายไฟล์ เอาแค่รูปเดียว
        if im["hash"] not in seen:
            seen.add(im["hash"])
            picked.append(im)

    return picked[:limit]


def doc_image_instruction(pics, start, is_en):
    lines = "\n".join(f"- #{start + i}: {p['label']}" for i, p in enumerate(pics))

    if is_en:
        return (
            "\n\nThe attached image(s) numbered below were extracted from the user's files:\n"
            f"{lines}\n"
            "Use an image only when it really supports what you are explaining. Put the marker "
            "[[image N]] on its own line, right where that image belongs in your answer (once per "
            "image, directly after the sentence it illustrates). Never guess things that are not "
            "visible; if an image is unrelated to the question, leave it out.\n"
        )

    return (
        "\n\nรูปภาพที่ส่งมาตามหมายเลขด้านล่างถูกดึงมาจากไฟล์ที่ผู้ใช้แนบ:\n"
        f"{lines}\n"
        "ใช้รูปเฉพาะเมื่อมันช่วยอธิบายเนื้อหานั้นจริงๆ ให้พิมพ์เครื่องหมาย [[รูปที่ N]] "
        "ในบรรทัดของตัวเอง ตรงตำแหน่งในคำตอบที่รูปนั้นควรอยู่ (ใส่รูปละครั้ง "
        "ต่อท้ายประโยคที่รูปนั้นประกอบ) ห้ามเดาสิ่งที่ไม่ปรากฏในรูป "
        "ถ้ารูปไม่เกี่ยวกับคำถามให้ไม่ต้องใส่\n"
    )


_DOC_IMG_MARK = re.compile(
    r"\[{1,2}\s*(?:รูปที่|รูป|image|img|figure|fig\.?)\s*#?(\d+)\s*\]{1,2}", re.I
)
_DOC_IMG_MD = re.compile(r"!\[[^\]\n]*\]\([^)\n]*file=[^)\n]*\)")
_DOC_IMG_CAP = re.compile(r"^\*(?:รูปที่|Image) \d+: [^\n]*\*[ \t]*$", re.M)


def strip_doc_images(text):
    """เอารูป/คำบรรยายรูปออกจากข้อความก่อนส่งประวัติกลับให้โมเดล (กัน URL ปนเข้าไปในบริบท)"""
    text = _DOC_IMG_MD.sub("", text or "")
    return re.sub(r"\n{3,}", "\n\n", _DOC_IMG_CAP.sub("", text)).strip()


def _doc_image_block(pic, n, is_en):
    prefix = _file_url_prefix
    word = "Image" if is_en else "รูปที่"
    url = prefix + quote(Path(pic["file"]).as_posix(), safe="/:")
    return f"![{word} {n}]({url})\n*{word} {n}: {pic['label']}*"


def place_doc_images(text, pics, start, is_en, final=False):
    """แทนที่เครื่องหมาย [[รูปที่ N]] ในคำตอบด้วยรูปจริง ณ ตำแหน่งนั้น
    คืนค่า (ข้อความ, มีรูปถูกวางแล้วหรือไม่)
    ถ้าโมเดลไม่ใส่เครื่องหมาย แต่เขียนอ้างถึง "รูปที่ N" ในย่อหน้าไหน ก็วางรูปต่อท้ายย่อหน้านั้น"""
    if not pics:
        return text, False

    placed = set()

    def put(m):
        i = int(m.group(1)) - start

        if 0 <= i < len(pics) and i not in placed:
            placed.add(i)
            return "\n\n" + _doc_image_block(pics[i], start + i, is_en) + "\n\n"

        return ""

    text = _DOC_IMG_MARK.sub(put, text)

    if not final:                                  # ตัดเครื่องหมายที่พิมพ์ค้างอยู่ท้ายข้อความ
        text = re.sub(r"\[{1,2}[^\]\n]{0,24}$", "", text)

    paras = text.split("\n\n")

    for i in range(len(pics)):
        if i in placed:
            continue

        n = start + i
        pattern = re.compile(rf"(?:รูปที่|รูป|image|figure|img)\s*#?{n}(?!\d)", re.I)

        for k, para in enumerate(paras):
            if "![" not in para and pattern.search(para):
                paras.insert(k + 1, _doc_image_block(pics[i], n, is_en))
                placed.add(i)
                break

    text = re.sub(r"\n{3,}", "\n\n", "\n\n".join(paras)).strip()
    return text, bool(placed)


def doc_images_markdown(pics, start, is_en):
    """บล็อกรูปที่แสดงใต้คำตอบ (อยู่หลังเส้นคั่น จึงไม่ถูกส่งกลับไปเป็นประวัติให้โมเดล)"""
    prefix = _file_url_prefix
    imgs = " ".join(
        f"![{'Image' if is_en else 'รูปที่'} {start + i}]"
        f"({prefix}{quote(Path(p['file']).as_posix(), safe='/:')})"
        for i, p in enumerate(pics)
    )
    caps = " · ".join(
        f"{'Image' if is_en else 'รูปที่'} {start + i}: {p['label']}"
        for i, p in enumerate(pics)
    )
    head = "**Images from your files:**" if is_en else "**รูปจากไฟล์ที่แนบ:**"
    return f"{head}\n\n{imgs}\n\n*{caps}*"