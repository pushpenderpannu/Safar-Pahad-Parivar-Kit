import base64, os
from pathlib import Path as _P
SRC = str(_P(__file__).resolve().parents[1])      # <kit>/Source
KIT = str(_P(__file__).resolve().parents[2])      # <kit>
from playwright.sync_api import sync_playwright
S = SRC
OUT = os.path.join(KIT, "Brand"); os.makedirs(OUT, exist_ok=True)
FB = os.path.join(SRC, "fonts"); PO = FB
b64 = lambda p: base64.b64encode(open(p, "rb").read()).decode()
F = {w: b64(os.path.join(FB, f"deva-{w}.woff2")) for w in (500, 700, 800)}
FONTS = "".join(f"@font-face{{font-family:'Deva';font-weight:{w};src:url(data:font/woff2;base64,{d}) format('woff2');}}" for w, d in F.items())
FONTS += f"@font-face{{font-family:'Pop';font-weight:700;src:url(data:font/ttf;base64,{b64(os.path.join(PO,'pop-700.ttf'))}) format('truetype');}}"
FONTS += f"@font-face{{font-family:'Pop';font-weight:500;src:url(data:font/ttf;base64,{b64(os.path.join(PO,'pop-500.ttf'))}) format('truetype');}}"
BG_A = "data:image/jpeg;base64," + b64(os.path.join(S, "assets/bg_a.jpg"))
BG_B = "data:image/jpeg;base64," + b64(os.path.join(S, "assets/bg_b.jpg"))

GOLD, NAVY, SNOW = "#F4B03E", "#07122B", "#F5F8FC"

def mark(color=SNOW, gold=GOLD, sw=6):
    return f"""<svg viewBox="0 0 200 130" xmlns="http://www.w3.org/2000/svg">
      <circle cx="150" cy="30" r="11" fill="{gold}"/>
      <path d="M8 118 L58 60 L78 82 L103 26 L133 76 L148 60 L192 118" fill="none" stroke="{color}"
            stroke-width="{sw}" stroke-linejoin="round" stroke-linecap="round"/>
      <path d="M86 62 L95 70 L103 60 L111 70 L121 62" fill="none" stroke="{color}" stroke-width="{sw*0.6}"
            stroke-linejoin="round" stroke-linecap="round"/>
      <path d="M100 124 C 82 112, 120 104, 101 92 C 88 86, 110 82, 103 76" fill="none" stroke="{gold}"
            stroke-width="{sw*0.75}" stroke-linecap="round" stroke-dasharray="0.1 {sw*1.6}"/>
    </svg>"""

def wordmark(size=64, color=SNOW, sub=True):
    return f"""<div style="text-align:center">
      <div style="font-family:Deva;font-weight:800;font-size:{size}px;color:{color};line-height:1.25;white-space:nowrap">
        सफ़र <span style="color:{GOLD}">·</span> पहाड़ <span style="color:{GOLD}">·</span> परिवार</div>
      {f'<div style="font-family:Pop;font-weight:500;font-size:{size*0.26:.0f}px;letter-spacing:.42em;color:{color};opacity:.8;margin-top:{size*0.1:.0f}px">SAFAR · PAHAD · PARIVAR</div>' if sub else ''}
    </div>"""

def page(body, w, h, bg="transparent"):
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{FONTS}
    *{{margin:0;padding:0;box-sizing:border-box}} html,body{{width:{w}px;height:{h}px;background:{bg};overflow:hidden}}
    </style></head><body>{body}</body></html>"""

def shot(html, w, h, name, transparent=False, scale=2):
    _b = os.path.join(SRC, "_build", "brand"); os.makedirs(_b, exist_ok=True)
    p = os.path.join(_b, name.replace(".png", ".html")); open(p, "w", encoding="utf-8").write(html)
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=scale)
        pg.goto("file://" + p); pg.wait_for_timeout(350)
        pg.screenshot(path=os.path.join(OUT, name), omit_background=transparent); b.close()
    print("ok", name)

# 1. Logo lockup (transparent) - for watermark / overlays
shot(page(f"""<div style="width:900px;height:560px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:18px">
     <div style="width:300px">{mark()}</div>{wordmark(70)}</div>""", 900, 560), 900, 560, "logo_lockup_light.png", transparent=True)
shot(page(f"""<div style="width:900px;height:560px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:18px">
     <div style="width:300px">{mark(NAVY)}</div>{wordmark(70, NAVY)}</div>""", 900, 560), 900, 560, "logo_lockup_dark.png", transparent=True)
shot(page(f"""<div style="width:400px;height:260px;display:flex;align-items:center;justify-content:center"><div style="width:380px">{mark()}</div></div>""", 400, 260),
     400, 260, "logo_mark_only.png", transparent=True)

# 2. Brand board
sw = lambda c, n, t: f"""<div style="display:flex;flex-direction:column;gap:8px;align-items:flex-start">
   <div style="width:150px;height:90px;border-radius:14px;background:{c};border:1px solid rgba(255,255,255,.15)"></div>
   <div style="font-family:Pop;font-weight:700;font-size:17px;color:#fff">{n}</div>
   <div style="font-family:Pop;font-weight:500;font-size:14px;color:#9fb0c8">{c} · {t}</div></div>"""
board = f"""<div style="width:1600px;height:900px;background:{NAVY};padding:64px 80px;display:flex;flex-direction:column;gap:40px;color:#fff">
  <div style="display:flex;align-items:center;gap:36px"><div style="width:220px">{mark()}</div>{wordmark(62)}</div>
  <div style="display:flex;gap:80px">
    <div style="flex:1">
      <div style="font-family:Pop;font-weight:700;font-size:16px;letter-spacing:.3em;color:{GOLD};margin-bottom:18px">TYPE</div>
      <div style="font-family:Deva;font-weight:800;font-size:58px;line-height:1.3">मुंस्यारी — शीर्षक</div>
      <div style="font-family:Pop;font-weight:500;font-size:15px;color:#9fb0c8;margin-bottom:14px">Noto Sans Devanagari ExtraBold · titles</div>
      <div style="font-family:Deva;font-weight:500;font-size:30px;line-height:1.5">सबटाइटल और छोटा टेक्स्ट ऐसा दिखेगा</div>
      <div style="font-family:Pop;font-weight:500;font-size:15px;color:#9fb0c8;margin-bottom:14px">Noto Sans Devanagari Medium · subtitles, body</div>
      <div style="font-family:Pop;font-weight:700;font-size:30px;letter-spacing:.28em">MUNSIYARI · 2,200 M</div>
      <div style="font-family:Pop;font-weight:500;font-size:15px;color:#9fb0c8">Poppins Bold · English labels, numbers</div>
    </div>
    <div>
      <div style="font-family:Pop;font-weight:700;font-size:16px;letter-spacing:.3em;color:{GOLD};margin-bottom:18px">COLOUR</div>
      <div style="display:grid;grid-template-columns:repeat(3,auto);gap:26px 30px">
        {sw(GOLD,'Himalayan Gold','accents, sun, path')}{sw(NAVY,'Night Navy','cards, scrims')}{sw(SNOW,'Snow','main text')}
        {sw('#3E7CB1','Glacier Blue','map water, info')}{sw('#5C8A4E','Pine Green','map forest, B-roll')}{sw('#C8553D','Prayer-flag Red','alerts, callouts')}
      </div>
    </div>
  </div></div>"""
shot(page(board, 1600, 900, NAVY), 1600, 900, "brand_board.png", scale=1)

# 3. Watermark mock (bottom-right, 55% opacity) on a frame
wm = f"""<div style="width:1280px;height:720px;background:url('{BG_A}') center/cover;position:relative">
  <div style="position:absolute;right:34px;bottom:26px;opacity:.72;display:flex;align-items:center;gap:10px;filter:drop-shadow(0 1px 3px rgba(0,0,0,.65)) drop-shadow(0 0 8px rgba(7,18,43,.45))">
    <div style="width:54px">{mark(sw=8)}</div>
    <div style="font-family:Deva;font-weight:700;font-size:17px;color:#fff;text-shadow:0 1px 6px rgba(0,0,0,.5)">सफ़र · पहाड़ · परिवार</div>
  </div></div>"""
shot(page(wm, 1280, 720), 1280, 720, "mock_watermark.png")

# 4. Intro card
intro = f"""<div style="width:1280px;height:720px;background:url('{BG_B}') center/cover;position:relative">
  <div style="position:absolute;inset:0;background:radial-gradient(90% 80% at 50% 45%, rgba(7,18,43,.35), rgba(7,18,43,.8))"></div>
  <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px">
    <div style="width:230px">{mark()}</div>{wordmark(64)}
    <div style="font-family:Pop;font-weight:500;font-size:14px;letter-spacing:.35em;color:{GOLD};margin-top:10px">PRESENTS</div>
  </div></div>"""
shot(page(intro, 1280, 720), 1280, 720, "mock_intro.png")

# 5. End card (YouTube end-screen safe: two video slots + subscribe circle)
end = f"""<div style="width:1280px;height:720px;background:url('{BG_B}') center/cover;position:relative;filter:none">
  <div style="position:absolute;inset:0;background:rgba(7,18,43,.78);backdrop-filter:blur(6px)"></div>
  <div style="position:absolute;left:0;right:0;top:44px;display:flex;flex-direction:column;align-items:center">
    <div style="font-family:Deva;font-weight:800;font-size:46px;color:#fff">फिर मिलेंगे, अगले सफ़र पर</div>
    <div style="font-family:Pop;font-weight:500;font-size:14px;letter-spacing:.35em;color:{GOLD};margin-top:4px">SEE YOU ON THE NEXT JOURNEY</div>
  </div>
  <div style="position:absolute;left:86px;top:210px;width:480px;height:270px;border:2px dashed rgba(255,255,255,.45);border-radius:14px;display:flex;align-items:center;justify-content:center;font-family:Pop;color:rgba(255,255,255,.55)">NEXT VIDEO</div>
  <div style="position:absolute;left:714px;top:210px;width:480px;height:270px;border:2px dashed rgba(255,255,255,.45);border-radius:14px;display:flex;align-items:center;justify-content:center;font-family:Pop;color:rgba(255,255,255,.55)">BEST FOR YOU</div>
  <div style="position:absolute;left:0;right:0;bottom:44px;display:flex;align-items:center;justify-content:center;gap:22px">
    <div style="width:150px;height:150px;border-radius:50%;border:2px dashed rgba(255,255,255,.45);display:flex;align-items:center;justify-content:center;font-family:Pop;font-size:13px;color:rgba(255,255,255,.55)">SUBSCRIBE</div>
    <div><div style="width:120px">{mark()}</div>
      <div style="font-family:Pop;font-weight:700;font-size:20px;color:#fff;margin-top:6px">@safar.pahad.parivar</div></div>
  </div></div>"""
shot(page(end, 1280, 720), 1280, 720, "mock_endcard.png")
