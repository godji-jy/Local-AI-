"""ข้อความและภาพ SVG/HTML บนหน้าจอ (แถบบน, ฉากต้อนรับ, การ์ดสถานะ)"""

from datetime import datetime
import math
import random

from backend.config import (
    EMBED_MODEL,
    LANG_AUTO,
    LANG_EN,
    MODEL,
)


def get_page_text(language):
    if language == LANG_EN:
        return {
            "tagline": "Ask anything. Learn something.",
            "description": (
                "Programming, science, AI, automation and general "
                "knowledge. Runs locally on your computer."
            ),
            "placeholder": "Ask Local AI anything...",
        }

    if language == LANG_AUTO:
        return {
            "tagline": "ถามได้ทุกเรื่อง · Ask anything",
            "description": (
                "การเรียน วิทยาศาสตร์ คอมพิวเตอร์ AI และการเขียนโปรแกรม "
                "ทำงานภายในเครื่องของคุณ"
            ),
            "placeholder": "พิมพ์คำถามของคุณ... / Ask anything...",
        }

    return {
        "tagline": "ถามอะไรก็ได้ เรียนรู้ได้ทุกวัน",
        "description": (
            "การเรียน วิทยาศาสตร์ คอมพิวเตอร์ การเขียนโปรแกรม AI "
            "และ Automation ทำงานภายในเครื่องของคุณ"
        ),
        "placeholder": "พิมพ์คำถามของคุณ...",
    }


def make_topbar(language):
    """แถบบน: ชื่อแอป + ชิป ด้านซ้าย / วันที่ ปี ไอคอนวงจุดหมุน ด้านขวา"""
    now = datetime.now()
    model_label = f"{MODEL} · Local" if language == LANG_EN else f"{MODEL} · รันในเครื่อง"
    dots = "".join(
        f'<circle cx="{10 + 7 * math.cos(math.radians(a))}" cy="{10 + 7 * math.sin(math.radians(a))}" r="1.5" fill="#f2b233"/>'
        for a in (-90, -18, 54, 126, 198)
    )
    return f"""
    <div id="topbar" style="display:flex;align-items:center;justify-content:space-between;
         padding:20px 36px 14px;color:#e9e7e1;">
        <div style="display:flex;align-items:center;gap:12px;">
            <span style="font-size:15px;font-weight:500;letter-spacing:.22em;">LOCAL AI</span>
            <span style="font-size:9px;letter-spacing:.12em;color:#f2b233;border:1px solid rgba(242,178,51,.55);
                  padding:2px 7px;border-radius:3px;">OFFLINE</span>
        </div>
        <div style="display:flex;align-items:center;gap:20px;font-size:13px;">
            <span style="font-size:11px;color:#8a8780;letter-spacing:.04em;">{model_label}</span>
            <span style="color:#8a8780;">{now.strftime("%a")} · {now.day} {now.strftime("%B")}</span>
            <span>{now.year}</span>
            <svg width="20" height="20" viewBox="0 0 20 20">
                <g>{dots}
                <animateTransform attributeName="transform" type="rotate" from="0 10 10" to="360 10 10"
                    dur="18s" repeatCount="indefinite"/></g>
            </svg>
        </div>
    </div>
    """


def section_label(text):
    return (
        '<div style="font-size:10px;font-weight:500;letter-spacing:.12em;text-transform:uppercase;'
        f'color:#8a8780;padding:12px 4px 2px;">{text}</div>'
    )


def _terrain_svg():
    """ภูเขาโครงลวดแบบโลว์โพลี (สร้างครั้งเดียว ค่าคงที่ ไม่สุ่มใหม่ทุกครั้ง)"""
    rnd = random.Random(11)
    rows, cols = 9, 21
    pts = []
    for r in range(rows):
        base = 292 + r * 22
        amp = 78 - r * 7
        row = []
        for c in range(cols):
            x = -20 + c * 42
            n = (math.sin(c * 0.55 + r * 0.9) + math.sin(c * 1.3 + r * 2.1) * 0.5 + rnd.random() * 0.7 + 1.2) / 3.4
            row.append((x, base - amp * n))
        pts.append(row)
    out = []
    for r, row in enumerate(pts):
        op = 0.16 + r * 0.045
        out.append(
            f'<polyline points="{" ".join(f"{x:.0f},{y:.0f}" for x, y in row)}" '
            f'fill="none" stroke="#ffffff" stroke-opacity="{op:.2f}" stroke-width="0.9"/>'
        )
        if r + 1 < rows:
            nxt = pts[r + 1]
            d = []
            for c in range(cols):
                d.append(f"M{row[c][0]:.0f},{row[c][1]:.0f}L{nxt[c][0]:.0f},{nxt[c][1]:.0f}")
                if c + 1 < cols:
                    d.append(f"M{row[c][0]:.0f},{row[c][1]:.0f}L{nxt[c + 1][0]:.0f},{nxt[c + 1][1]:.0f}")
            out.append(
                f'<path d="{"".join(d)}" fill="none" stroke="#ffffff" '
                f'stroke-opacity="{op * 0.55:.2f}" stroke-width="0.6"/>'
            )
    return "".join(out)


_TERRAIN = _terrain_svg()


def make_header(language):
    """ฉากต้อนรับสไตล์ HUD: ภูเขาโครงลวด + กรอบเอียง 2 บาน + รูปทรงทองเคลื่อนไหวเบาๆ + ไม้บรรทัดล่าง"""
    t = get_page_text(language)
    ticks = "".join(
        f'<line x1="{40 + i * 12}" y1="{574 if i % 5 else 568}" x2="{40 + i * 12}" y2="580" />'
        for i in range(61)
    )
    nums = "".join(
        f'<text x="{40 + i * 60}" y="596" text-anchor="middle">0{i}</text>' for i in range(0, 13) if i < 10
    )
    svg = r"""
    <div id="hero" style="width:100%;">
    <svg viewBox="0 0 800 610" preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg"
         style="display:block;width:100%;height:calc(100vh - 240px);min-height:300px;">
        <defs>
            <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
                <feGaussianBlur stdDeviation="3.2" result="b"/>
                <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
            </filter>
            <linearGradient id="fadeT" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0" stop-color="#07080a" stop-opacity="1"/>
                <stop offset="1" stop-color="#07080a" stop-opacity="0"/>
            </linearGradient>
        </defs>

        <!-- ภูเขาโครงลวด (ขยับช้าๆ) -->
        <g>
            <animateTransform attributeName="transform" type="translate" values="0 0;-10 0;0 0"
                dur="22s" repeatCount="indefinite"/>
            @@TERRAIN@@
        </g>
        <rect x="0" y="180" width="800" height="90" fill="url(#fadeT)"/>

        <!-- กรอบเอียงซ้าย -->
        <polygon points="30,110 340,172 340,402 30,470" fill="rgba(7,8,10,.62)"
                 stroke="#d9d6cf" stroke-opacity=".55" stroke-width="1"/>
        <text x="52" y="222" font-family="Prompt, sans-serif" font-size="46" font-weight="300" fill="#f4f1ea">01</text>
        <text x="52" y="436" font-family="Prompt, sans-serif" font-size="10" fill="#f4f1ea" letter-spacing="1.2">MODEL · @@MODEL@@</text>
        <text x="52" y="452" font-family="Prompt, sans-serif" font-size="9" fill="#8a8780">ข้อมูลอยู่ในเครื่องคุณ · ไม่ส่งออกนอกเครื่อง</text>
        <!-- รูปทรงทองซ้าย: ห้าเหลี่ยมซ้อนแกว่งเป็นพัด -->
        <g transform="translate(240 290)" filter="url(#glow)" fill="none" stroke="#f2b233" stroke-width="1.6" stroke-linejoin="round">
            <g><animateTransform attributeName="transform" type="rotate" values="-5;5;-5" dur="9s" repeatCount="indefinite"/>
                <polygon points="-18,-85 38,-42 30,60 -30,88 -52,10"/></g>
            <g><animateTransform attributeName="transform" type="rotate" values="-2;8;-2" dur="9s" begin="-1.5s" repeatCount="indefinite"/>
                <polygon points="-18,-85 38,-42 30,60 -30,88 -52,10" stroke-opacity=".85"/></g>
            <g><animateTransform attributeName="transform" type="rotate" values="2;11;2" dur="9s" begin="-3s" repeatCount="indefinite"/>
                <polygon points="-18,-85 38,-42 30,60 -30,88 -52,10" stroke-opacity=".6"/></g>
            <g><animateTransform attributeName="transform" type="rotate" values="6;14;6" dur="9s" begin="-4.5s" repeatCount="indefinite"/>
                <polygon points="-18,-85 38,-42 30,60 -30,88 -52,10" stroke-opacity=".4"/></g>
        </g>

        <!-- กรอบเอียงขวา -->
        <polygon points="460,172 770,110 770,470 460,402" fill="rgba(7,8,10,.62)"
                 stroke="#d9d6cf" stroke-opacity=".55" stroke-width="1"/>
        <text x="488" y="222" font-family="Prompt, sans-serif" font-size="46" font-weight="300" fill="#f4f1ea">02</text>
        <text x="488" y="368" font-family="Prompt, sans-serif" font-size="10" fill="#f4f1ea" letter-spacing="1.2">RAG · @@EMBED@@</text>
        <text x="488" y="384" font-family="Prompt, sans-serif" font-size="9" fill="#8a8780">ค้นเว็บ · ไฟล์ · ฐานความรู้</text>
        <!-- รูปทรงทองขวา: วงรีซ้อนหมุนช้าๆ -->
        <g transform="translate(640 280)" filter="url(#glow)" fill="none" stroke="#f2b233" stroke-width="1.6">
            <g><animateTransform attributeName="transform" type="rotate" values="-18;-6;-18" dur="11s" repeatCount="indefinite"/>
                <ellipse rx="82" ry="52"/></g>
            <g><animateTransform attributeName="transform" type="rotate" values="-8;4;-8" dur="11s" begin="-2s" repeatCount="indefinite"/>
                <ellipse rx="82" ry="52" stroke-opacity=".8"/></g>
            <g><animateTransform attributeName="transform" type="rotate" values="2;14;2" dur="11s" begin="-4s" repeatCount="indefinite"/>
                <ellipse rx="82" ry="52" stroke-opacity=".6"/></g>
            <g><animateTransform attributeName="transform" type="rotate" values="12;24;12" dur="11s" begin="-6s" repeatCount="indefinite"/>
                <ellipse rx="82" ry="52" stroke-opacity=".4"/></g>
        </g>

        <!-- ข้อความตรงกลาง -->
        <text x="400" y="505" text-anchor="middle" fill="#f2b233" font-family="Prompt, sans-serif"
              font-size="11" letter-spacing="5">LOCAL AI</text>
        <text x="400" y="538" text-anchor="middle" fill="#f4f1ea" font-family="Prompt, sans-serif"
              font-size="26" font-weight="300">@@TAGLINE@@</text>

        <!-- ไม้บรรทัดล่าง + ตัวชี้เคลื่อนที่ -->
        <g stroke="#8a8780" stroke-opacity=".7" stroke-width="1">@@TICKS@@</g>
        <g font-family="Prompt, sans-serif" font-size="8" fill="#8a8780">@@NUMS@@</g>
        <g>
            <animateTransform attributeName="transform" type="translate" values="-150 0;150 0;-150 0"
                dur="16s" repeatCount="indefinite"/>
            <circle cx="400" cy="574" r="9" fill="#07080a" stroke="#f2b233" stroke-width="1.3"/>
            <circle cx="400" cy="574" r="2.4" fill="#f2b233"/>
        </g>
        <text x="400" y="560" text-anchor="middle" font-family="Prompt, sans-serif" font-size="9"
              fill="#8a8780">@@DESC@@</text>
    </svg>
    </div>
    """
    return (
        svg.replace("@@TERRAIN@@", _TERRAIN)
        .replace("@@MODEL@@", MODEL)
        .replace("@@EMBED@@", EMBED_MODEL)
        .replace("@@TAGLINE@@", t["tagline"])
        .replace("@@DESC@@", t["description"])
        .replace("@@TICKS@@", ticks)
        .replace("@@NUMS@@", nums)
    )


def make_status_card():
    """การ์ดสถานะระบบ (อ่านอย่างเดียว) มีวงแหวนทองหมุนช้าๆ"""
    def row(k, v):
        return (
            '<div class="kv"><span>' + k + '</span><span>' + v + '</span></div>'
        )
    ring = (
        '<svg width="26" height="26" viewBox="0 0 26 26" fill="none" stroke="#f2b233" stroke-width="1.2">'
        '<g transform="translate(13 13)">'
        '<ellipse rx="10" ry="6"><animateTransform attributeName="transform" type="rotate" '
        'values="0;180;360" dur="8s" repeatCount="indefinite"/></ellipse>'
        '<ellipse rx="10" ry="6" stroke-opacity=".5"><animateTransform attributeName="transform" '
        'type="rotate" values="60;240;420" dur="8s" repeatCount="indefinite"/></ellipse>'
        '<circle r="1.6" fill="#f2b233" stroke="none"/></g></svg>'
    )
    return (
        '<div id="status-card" class="hudcard"><div class="hudhead">' + ring +
        '<span>SYSTEM · LOCAL</span><i class="blink"></i></div>'
        + row("Model", MODEL) + row("Embed", EMBED_MODEL) + row("Server", "Ollama")
        + row("Network", "Offline-first") + "</div>"
    )


def make_tips_card():
    """การ์ดคีย์ลัด มีคลื่นสัญญาณเคลื่อนไหวเบาๆ"""
    def row(k, v):
        return '<div class="kv"><span class="key">' + k + '</span><span>' + v + '</span></div>'
    wave = (
        '<svg width="46" height="18" viewBox="0 0 46 18" fill="none" stroke="#f2b233" stroke-width="1.2">'
        '<path d="M0 9 Q5.75 0 11.5 9 T23 9 T34.5 9 T46 9"><animate attributeName="d" dur="3s" '
        'repeatCount="indefinite" values="M0 9 Q5.75 0 11.5 9 T23 9 T34.5 9 T46 9;'
        'M0 9 Q5.75 18 11.5 9 T23 9 T34.5 9 T46 9;M0 9 Q5.75 0 11.5 9 T23 9 T34.5 9 T46 9"/></path></svg>'
    )
    return (
        '<div id="tips-card" class="hudcard"><div class="hudhead"><span>SHORTCUTS</span>'
        '<span style="margin-left:auto;">' + wave + '</span></div>'
        + row("Enter", "ส่งข้อความ") + row("Shift + Enter", "ขึ้นบรรทัดใหม่")
        + row("Ctrl + V", "วางรูป/ไฟล์") + "</div>"
    )