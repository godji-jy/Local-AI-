"""ธีม Gradio, CSS และสคริปต์เลื่อนตามคำตอบ"""

import gradio as gr


THEME = gr.themes.Base(
    primary_hue="amber",
    neutral_hue="zinc",
    radius_size=gr.themes.sizes.radius_sm,
    font=["Prompt", "Segoe UI", "sans-serif"],
).set(
    body_background_fill="#07080a",
    body_background_fill_dark="#07080a",
    body_text_color="#e9e7e1",
    body_text_color_dark="#e9e7e1",
    background_fill_primary="#07080a",
    background_fill_primary_dark="#07080a",
    background_fill_secondary="#0d0f12",
    background_fill_secondary_dark="#0d0f12",
    block_background_fill="transparent",
    block_background_fill_dark="transparent",
    block_border_width="0px",
    border_color_primary="rgba(255,255,255,.18)",
    border_color_primary_dark="rgba(255,255,255,.18)",
    input_background_fill="#0d0f12",
    input_background_fill_dark="#0d0f12",
    input_border_color="rgba(255,255,255,.25)",
    input_border_color_dark="rgba(255,255,255,.25)",
    button_primary_background_fill="#f2b233",
    button_primary_background_fill_dark="#f2b233",
    button_primary_background_fill_hover="#ffc94d",
    button_primary_background_fill_hover_dark="#ffc94d",
    button_primary_text_color="#0a0a0a",
    button_primary_text_color_dark="#0a0a0a",
)


def _svg_icon(inner):
    """ไอคอนเส้นสีทอง (SVG data-URI) สำหรับใช้เป็นพื้นหลังของ ::before"""
    return (
        'url("data:image/svg+xml;utf8,<svg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 24 24\' '
        'fill=\'none\' stroke=\'%23f2b233\' stroke-width=\'1.6\' stroke-linecap=\'round\' '
        'stroke-linejoin=\'round\'>' + inner + '</svg>")'
    )


_ICONS = {
    "search": "<circle cx='11' cy='11' r='6'/><path d='M16 16l5 5'/>",
    "db": "<ellipse cx='12' cy='6' rx='8' ry='3'/><path d='M4 6v6c0 1.7 3.6 3 8 3s8-1.3 8-3V6M4 12v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6'/>",
    "think": "<path d='M12 3l8 4.5v9L12 21l-8-4.5v-9z'/><circle cx='12' cy='12' r='2.2'/>",
    "folder": "<path d='M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z'/>",
    "pencil": "<path d='M4 20l1-4L16 5l3 3L8 19z'/><path d='M14 7l3 3'/>",
    "plus": "<path d='M12 5v14M5 12h14'/>",
    "trash": "<path d='M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13M10 11v6M14 11v6'/>",
    "x": "<path d='M6 6l12 12M18 6L6 18'/>",
    "spark": "<path d='M12 3l2.2 5.8L20 11l-5.8 2.2L12 19l-2.2-5.8L4 11l5.8-2.2z'/>",
    "image": "<rect x='3' y='4' width='18' height='16' rx='2'/><circle cx='9' cy='10' r='1.8'/><path d='M21 16l-5-5-8 9'/>",
    "code": "<path d='M8 8l-5 4 5 4M16 8l5 4-5 4M14 5l-4 14'/>",
    "flask": "<path d='M9 3h6M10 3v6l-5 9a2 2 0 0 0 1.8 3h10.4A2 2 0 0 0 19 18l-5-9V3'/><path d='M7.5 15h9'/>",
}

_I = {k: _svg_icon(v) for k, v in _ICONS.items()}

CSS_ICONS = f"""
#new-btn::before        {{ background-image: {_I["plus"]}; }}
#pcard-1::before        {{ background-image: {_I["spark"]}; }}
#pcard-2::before        {{ background-image: {_I["code"]}; }}
#pcard-3::before        {{ background-image: {_I["flask"]}; }}
#delete-btn::before     {{ background-image: {_I["trash"]}; }}
#open-ws-btn::before    {{ background-image: {_I["folder"]}; }}
#clear-btn::before      {{ background-image: {_I["x"]}; }}
#chips .form > div:nth-of-type(1) label::before {{ background-image: {_I["search"]}; }}
#chips .form > div:nth-of-type(2) label::before {{ background-image: {_I["db"]}; }}
#chips .form > div:nth-of-type(3) label::before {{ background-image: {_I["think"]}; }}
#chips .form > div:nth-of-type(4) label::before {{ background-image: {_I["folder"]}; }}
#chips .form > div:nth-of-type(5) label::before {{ background-image: {_I["pencil"]}; }}
#chips .form > div:nth-of-type(6) label::before {{ background-image: {_I["image"]}; }}
"""

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600&display=swap');

:root { --gold: #f2b233; --gold-soft: rgba(242,178,51,.14); --line: rgba(255,255,255,.2);
        --dim: #8a8780; --ink: #e9e7e1; }

/* ---------- พื้นหลังดำ + แสงบน + ดาวจางๆ ที่ลอยช้าๆ ---------- */
.gradio-container {
    max-width: 100% !important; width: 100% !important; margin: 0 !important; padding: 0 !important;
    color: var(--ink);
    background:
        radial-gradient(ellipse 60% 40% at 50% 0%, rgba(242,178,51,.07), transparent 70%),
        radial-gradient(1.2px 1.2px at 20px 30px, rgba(255,255,255,.55), transparent 60%) 0 0 / 160px 130px,
        radial-gradient(1px 1px at 90px 80px, rgba(255,255,255,.4), transparent 60%) 0 0 / 220px 170px,
        #07080a !important;
    animation: drift 120s linear infinite;
}
@keyframes drift { to { background-position: 0 0, 160px 130px, -220px 170px, 0 0; } }
footer { display: none !important; }

/* ---------- ล็อกหน้าเว็บไม่ให้เลื่อน ---------- */
html, body, gradio-app { height: 100% !important; overflow: hidden !important; background: #07080a !important; }
.gradio-container { box-sizing: border-box !important; height: 100vh !important; min-height: 0 !important; overflow: hidden !important; }
#chatbot, #chatbot .bubble-wrap, #chatbot .wrapper { overscroll-behavior: contain; }
@media (max-height: 600px) {
    html, body, gradio-app { overflow: auto !important; }
    .gradio-container { height: auto !important; overflow: visible !important; }
}
* { scrollbar-width: thin; scrollbar-color: rgba(242,178,51,.45) transparent; }
*::-webkit-scrollbar { width: 6px; height: 6px; }
*::-webkit-scrollbar-thumb { background: rgba(242,178,51,.45); border-radius: 6px; }
*::-webkit-scrollbar-track { background: transparent; }

/* ---------- โครงหน้า 3 คอลัมน์ ---------- */
#app-grid {
    display: flex !important; flex-wrap: nowrap !important; align-items: stretch;
    gap: 28px !important; height: calc(100vh - 107px); padding: 0 36px 24px !important;
    background: transparent !important; border: none !important; box-shadow: none !important;
}
#left, #main, #right, #history-card, #settings-card { flex-wrap: nowrap !important; }
#left  { flex: 0 0 240px !important; min-width: 240px !important; max-width: 240px; gap: 4px !important; overflow-y: auto; min-height: 0; }
#right { flex: 0 0 250px !important; min-width: 250px !important; max-width: 250px; gap: 8px !important; overflow-y: auto; min-height: 0; }
#main  { flex: 1 1 0 !important; min-width: 0 !important; gap: 12px !important; background: transparent !important; }
#cards-box { flex: 1 1 0 !important; min-height: 0; background: transparent !important; border: none !important; }

/* ---------- ไอคอน (::before) ใช้ร่วมกันทุกปุ่ม ---------- */
#new-btn::before, .pcard::before, #delete-btn::before, #open-ws-btn::before, #clear-btn::before {
    content: "" !important; display: inline-block !important; flex: none;
    width: 17px; height: 17px; margin-right: 10px;
    background-repeat: no-repeat; background-position: center; background-size: contain;
}
#new-btn::before { filter: brightness(0); }                 /* ไอคอนดำบนปุ่มทอง */
#delete-btn::before, #open-ws-btn::before, #clear-btn::before { width: 14px; height: 14px; margin-right: 8px; }

/* ---------- ปุ่มเมนูซ้าย ---------- */
#new-btn, #new-btn button, .pcard, button.pcard {
    display: flex !important; align-items: center !important; justify-content: flex-start !important;
    width: 100% !important; min-height: 44px !important; padding: 0 14px !important; margin: 0 !important;
    border-radius: 4px !important; box-shadow: none !important; font-size: 14px !important;
    text-align: left !important; transition: background .2s, border-color .2s, transform .2s;
}
.pcard, button.pcard {
    position: relative; background: transparent !important; color: var(--ink) !important;
    border: 1px solid transparent !important; font-weight: 400 !important;
}
.pcard:hover { background: var(--gold-soft) !important; border-color: rgba(242,178,51,.45) !important; transform: translateX(3px); }
.pcard::after { position: absolute; right: 12px; font-size: 10px; letter-spacing: .1em; color: var(--dim); }
#pcard-1::after { content: "01"; } #pcard-2::after { content: "02"; } #pcard-3::after { content: "03"; }
#new-btn, #new-btn button {
    background: var(--gold) !important; color: #0a0a0a !important; border: none !important;
    font-weight: 600 !important; margin-bottom: 6px !important;
}
#new-btn:hover, #new-btn button:hover { background: #ffc94d !important; }

/* ---------- รายการเลือก (ประวัติ / ภาษา) ---------- */
#history-card, #settings-card { background: transparent !important; border: none !important; padding: 0 !important; gap: 4px !important; }
#settings-card .block, #settings-card .form, #history-card .block, #history-card .form {
    background: transparent !important; border: none !important; box-shadow: none !important; padding: 0 !important;
}
.listradio .wrap {
    display: flex !important; flex-direction: column !important; flex-wrap: nowrap !important;
    align-items: stretch !important; gap: 2px !important; background: transparent !important; border: none !important;
}
#history-radio .wrap { max-height: 30vh; overflow-y: auto; }
.listradio label {
    display: flex !important; align-items: center; background: transparent !important;
    border: 1px solid transparent !important; border-left: 2px solid transparent !important;
    border-radius: 4px !important; padding: 9px 12px !important; font-size: 13px !important;
    color: var(--ink) !important; cursor: pointer; transition: background .2s;
}
.listradio label:hover { background: rgba(255,255,255,.05) !important; }
.listradio label:has(input:checked) {
    background: var(--gold-soft) !important; border-left-color: var(--gold) !important;
}
.listradio label:has(input:checked), .listradio label:has(input:checked) * { color: #ffd98a !important; }
#history-radio label span { display: block; max-width: 190px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.listradio input[type="radio"], #chips input[type="checkbox"] {
    -webkit-appearance: none !important; appearance: none !important;
    width: 0 !important; height: 0 !important; margin: 0 !important; opacity: 0; position: absolute;
}

/* ---------- ปุ่มเล็กแบบเส้นขอบ ---------- */
#delete-btn, #delete-btn button, #open-ws-btn, #open-ws-btn button, #clear-btn {
    display: flex !important; align-items: center !important; justify-content: center !important;
    background: transparent !important; color: var(--ink) !important;
    border: 1px solid var(--line) !important; border-radius: 4px !important;
    font-size: 12px !important; box-shadow: none !important; transition: border-color .2s, background .2s;
}
#delete-btn:hover, #open-ws-btn:hover, #clear-btn:hover { border-color: var(--gold) !important; background: var(--gold-soft) !important; }

/* ---------- ไทล์ตัวเลือก ---------- */
#chips { display: block !important; }
#chips > .form, #chips .form {
    display: grid !important; grid-template-columns: 1fr 1fr; gap: 8px !important; flex-wrap: nowrap !important;
    min-width: 0 !important; width: 100% !important; background: transparent !important;
    border: none !important; box-shadow: none !important;
}
#chips .block { min-width: 0 !important; padding: 0 !important; border: none !important; overflow: visible !important; }
#chips .form > :last-child:nth-child(odd) { grid-column: span 2; }
#chips label {
    position: relative; overflow: hidden; display: flex !important; align-items: flex-end;
    width: 100%; min-height: 84px; box-sizing: border-box; padding: 36px 12px 10px !important;
    background: rgba(255,255,255,.025) !important; color: var(--ink) !important;
    border: 1px solid var(--line) !important; border-radius: 4px !important;
    font-size: 11px !important; line-height: 1.45; cursor: pointer; transition: border-color .2s, background .2s;
}
#chips label::before {
    content: ""; position: absolute; top: 10px; left: 12px; width: 18px; height: 18px;
    background-repeat: no-repeat; background-position: center; background-size: contain;
}
#chips label:hover { border-color: rgba(242,178,51,.6) !important; }
#chips label:has(input:checked) { background: var(--gold-soft) !important; border-color: var(--gold) !important; }
#chips label:has(input:checked), #chips label:has(input:checked) * { color: #ffd98a !important; }
#chips label:has(input:checked)::after {          /* แสงสแกนวิ่งผ่านไทล์ที่เปิดใช้ */
    content: ""; position: absolute; top: 0; bottom: 0; width: 40%; left: -50%;
    background: linear-gradient(90deg, transparent, rgba(242,178,51,.22), transparent);
    animation: sweep 3.6s ease-in-out infinite;
}
@keyframes sweep { 0% { left: -50%; } 60%, 100% { left: 110%; } }

#workspace-box textarea, #workspace-box input {
    background: #0d0f12 !important; color: var(--ink) !important;
    border: 1px solid var(--line) !important; border-radius: 4px !important;
    font-size: 11px !important; padding: 8px 12px !important;
}
#workspace-box textarea:focus, #workspace-box input:focus { border-color: var(--gold) !important; }

/* ---------- การ์ดข้อมูล (HTML) ---------- */
.hudcard {
    position: relative; overflow: hidden; border: 1px solid var(--line); border-radius: 4px;
    padding: 12px 14px 6px; background: rgba(255,255,255,.025);
}
.hudcard::after {                                   /* เส้นสแกนวิ่งลงช้าๆ */
    content: ""; position: absolute; left: 0; right: 0; top: -40%; height: 40%; pointer-events: none;
    background: linear-gradient(180deg, transparent, rgba(242,178,51,.08), transparent);
    animation: scan 7s linear infinite;
}
@keyframes scan { to { top: 110%; } }
.hudhead { display: flex; align-items: center; gap: 8px; font-size: 10px; letter-spacing: .12em; color: var(--ink); margin-bottom: 6px; }
.hudhead .blink { margin-left: auto; width: 6px; height: 6px; border-radius: 50%; background: var(--gold); animation: blink 2s ease-in-out infinite; }
@keyframes blink { 50% { opacity: .25; } }
.kv { display: flex; justify-content: space-between; gap: 10px; padding: 7px 0; font-size: 12px; border-top: 1px solid rgba(255,255,255,.1); }
.kv span:first-child { color: var(--dim); }
.kv .key { color: var(--ink); border: 1px solid var(--line); border-radius: 3px; padding: 0 6px; font-size: 11px; }
.kv .key + span { color: var(--dim); }

/* ---------- กล่องแชต ---------- */
#chatbot, #chatbot .bubble-wrap, #chatbot .wrapper, #chatbot .message-wrap, #chatbot .message-row {
    background: transparent !important; border: none !important; border-radius: 0 !important; box-shadow: none !important;
}
#chatbot { height: calc(100vh - 240px) !important; min-height: 280px; }
#chatbot .bubble-wrap { padding: 6px 6px !important; }
#chatbot .message { font-size: 15px !important; line-height: 1.75 !important; }
#chatbot .message.user, #chatbot .message.bot { padding: 10px 16px !important; max-width: 900px !important; box-shadow: none !important; }
#chatbot .message:not(.user):not(.bot) {
    padding: 0 !important; max-width: none !important; width: auto !important;
    background: transparent !important; border: none !important; box-shadow: none !important;
}
#chatbot .message.user { background: var(--gold-soft) !important; border: 1px solid rgba(242,178,51,.6) !important; border-radius: 6px !important; }
#chatbot .message.user, #chatbot .message.user * { color: #fff3d6 !important; }
#chatbot .message.bot  { background: rgba(255,255,255,.045) !important; border: 1px solid rgba(255,255,255,.2) !important; border-radius: 6px !important; }
#chatbot .message.bot, #chatbot .message.bot * { color: var(--ink) !important; }
#chatbot .message.bot em { font-size: 12px !important; color: #8a8780 !important; }
#chatbot .message.bot div { border: none !important; background: transparent !important; box-shadow: none !important; }
#chatbot .message p { margin: 0 0 .6em; }
#chatbot .message p:last-child { margin-bottom: 0; }
#chatbot .message.bot img {
    display: block !important; max-width: min(360px, 100%); max-height: 250px; width: auto; height: auto;
    object-fit: contain; border: 1px solid rgba(242,178,51,.55); border-radius: 4px;
    margin: 10px 0 2px; background: #0d0f12;
}
#chatbot .message.bot code {
    background: rgba(255,255,255,.14) !important; color: #ffffff !important;
    border: 1px solid rgba(255,255,255,.12) !important; border-radius: 3px !important;
    padding: 1px 6px !important; font-size: .9em !important;
}
#chatbot pre { background: #0d0f12 !important; border: 1px solid rgba(255,255,255,.16) !important; border-radius: 4px !important; padding: 12px 14px !important; }
#chatbot .message.bot pre code { background: transparent !important; border: none !important; padding: 0 !important; border-radius: 0 !important; font-size: .92em !important; }
#chatbot .message.bot a { color: var(--gold) !important; }
#chatbot .message.bot th, #chatbot .message.bot td { border-color: rgba(255,255,255,.2) !important; }
#chatbot .icon-button-wrapper, #chatbot .icon-buttons { background: transparent !important; border: none !important; box-shadow: none !important; }
#chatbot button {
    background: #14161a !important; color: var(--ink) !important; border: 1px solid rgba(255,255,255,.3) !important;
    border-radius: 4px !important; opacity: 1 !important; box-shadow: none !important;
}
#chatbot button:hover { background: var(--gold) !important; border-color: var(--gold) !important; }
#chatbot button:hover, #chatbot button:hover * { color: #0a0a0a !important; }
#chatbot button svg, #chatbot button svg * { color: var(--ink) !important; }
#chatbot button:hover svg, #chatbot button:hover svg * { color: #0a0a0a !important; }

/* ---------- ไฟล์แนบ ---------- */
#attach-info, #attach-info * { color: #c9c6be !important; font-size: 12px; }
#attach-info p { margin: 0; }
#clear-btn { padding: 4px 12px !important; }

/* ---------- ช่องพิมพ์ ---------- */
#input-row {
    position: relative; background: rgba(13,15,18,.92) !important;
    border: 1px solid rgba(255,255,255,.28) !important; border-radius: 6px !important;
    padding: 4px 6px !important; box-shadow: none !important; transition: border-color .2s, box-shadow .2s;
}
#input-row:focus-within { border-color: var(--gold) !important; box-shadow: 0 0 18px rgba(242,178,51,.18) !important; }
#input-row::after {                                 /* เส้นทองวิ่งไปมาตามขอบบน */
    content: ""; position: absolute; top: -1px; left: 0; height: 1px; width: 22%; pointer-events: none;
    background: linear-gradient(90deg, transparent, var(--gold), transparent);
    animation: edge 6s ease-in-out infinite alternate;
}
@keyframes edge { to { left: 78%; } }
#input-row > div, #input-row .wrapper { background: transparent !important; border: none !important; border-radius: 4px !important; box-shadow: none !important; }
#input-row textarea { background: transparent !important; color: var(--ink) !important; border-radius: 4px !important; padding: 12px 12px !important; }
#input-row textarea::placeholder { color: var(--dim) !important; }
#input-row button { background: var(--gold) !important; border-radius: 4px !important; }
#input-row button, #input-row button * { color: #0a0a0a !important; }
#input-row button:hover { background: #ffc94d !important; }
""" + CSS_ICONS

# เลื่อนตามคำตอบลงไปเฉพาะตอนที่ผู้ใช้อยู่ท้ายแชต ถ้าเลื่อนขึ้นไปอ่านจะไม่ดึงกลับ
HEAD_JS = """
<script>
(function () {
  let want = true, queued = false;
  const box = () => document.querySelector('#chatbot .bubble-wrap');
  const near = el => el.scrollHeight - el.scrollTop - el.clientHeight < 80;
  const inChat = t => { const el = box(); return el && el.contains(t); };

  // ผู้ใช้เลื่อนขึ้น/ลากเอง -> หยุดตาม
  document.addEventListener('wheel', e => { if (e.deltaY < 0 && inChat(e.target)) want = false; },
                            { capture: true, passive: true });
  document.addEventListener('touchmove', e => { if (inChat(e.target)) want = false; },
                            { capture: true, passive: true });
  // เลื่อนลงมาถึงท้ายแชตเอง -> กลับมาตามต่อ
  document.addEventListener('scroll', e => {
    const el = box(); if (el && e.target === el && near(el)) want = true;
  }, true);
  // ส่งข้อความใหม่ / เปิดแชตเก่า -> ตามไปท้ายแชตเสมอ
  document.addEventListener('keydown', e => {
    if (e.key === 'Enter' && e.target.closest && e.target.closest('#input-row')) want = true;
  }, true);
  document.addEventListener('click', e => {
    if (e.target.closest && e.target.closest('#input-row button, .pcard, #history-card label')) want = true;
  }, true);

  new MutationObserver(() => {
    if (queued) return; queued = true;
    requestAnimationFrame(() => {
      queued = false;
      const el = box(); if (el && want) el.scrollTop = el.scrollHeight;
    });
  }).observe(document.body, { childList: true, subtree: true, characterData: true });
})();
</script>
"""