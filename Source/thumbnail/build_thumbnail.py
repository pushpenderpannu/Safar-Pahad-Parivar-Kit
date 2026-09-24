import base64, os
from playwright.sync_api import sync_playwright

from pathlib import Path as _P
SRC = str(_P(__file__).resolve().parents[1])
BASE = os.path.join(SRC, "_build", "thumbnail"); os.makedirs(os.path.join(BASE, "out"), exist_ok=True); os.makedirs(os.path.join(BASE, "thumbs"), exist_ok=True)
FB = os.path.join(SRC, "fonts")
PO = FB
def b64(p): return base64.b64encode(open(p,"rb").read()).decode()
deva800=b64(os.path.join(FB,"deva-800.woff2"))
deva700=b64(os.path.join(FB,"deva-700.woff2"))
popB=b64(os.path.join(PO,"pop-700.ttf"))
popM=b64(os.path.join(PO,"pop-500.ttf"))
bg="data:image/jpeg;base64,"+b64(os.path.join(SRC,"assets","bg_b.jpg"))

FONTS=f"""
@font-face{{font-family:'Deva';font-weight:800;src:url(data:font/woff2;base64,{deva800}) format('woff2');}}
@font-face{{font-family:'Deva';font-weight:700;src:url(data:font/woff2;base64,{deva700}) format('woff2');}}
@font-face{{font-family:'Pop';font-weight:700;src:url(data:font/ttf;base64,{popB}) format('truetype');}}
@font-face{{font-family:'Pop';font-weight:500;src:url(data:font/ttf;base64,{popM}) format('truetype');}}
"""

def html(sub):
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
    {FONTS}
    *{{margin:0;padding:0;box-sizing:border-box;}}
    html,body{{width:1280px;height:720px;overflow:hidden;background:#03091a;}}
    .stage{{position:relative;width:1280px;height:720px;overflow:hidden;
      background:url('{bg}') center/cover no-repeat;}}
    .scrim{{position:absolute;inset:0;background:
      radial-gradient(130% 95% at 50% 22%, rgba(3,9,22,.72) 0%, rgba(3,9,22,.22) 44%, rgba(3,9,22,0) 68%),
      linear-gradient(0deg, rgba(3,9,22,.5) 0%, rgba(3,9,22,0) 42%);}}
    .content{{position:absolute;top:0;height:100%;width:100%;display:flex;flex-direction:column;
      align-items:center;text-align:center;justify-content:flex-start;padding-top:54px;}}
    .kicker{{display:flex;align-items:center;justify-content:center;gap:14px;font-family:'Pop';font-weight:700;
      font-size:19px;letter-spacing:.32em;color:rgba(255,255,255,.92);margin-bottom:14px;
      text-shadow:0 2px 12px rgba(0,0,0,.6);}}
    .bar{{display:inline-block;width:46px;height:3px;background:#F4B03E;border-radius:2px;}}
    .title{{font-family:'Deva';font-weight:800;font-size:132px;line-height:1.22;color:#fff;
      text-shadow:0 8px 40px rgba(0,0,0,.6),0 3px 10px rgba(0,0,0,.5);letter-spacing:.005em;}}
    .sub{{font-family:'Deva';font-weight:700;font-size:41px;color:#F4B03E;margin-top:14px;line-height:1.4;
      text-shadow:0 3px 18px rgba(0,0,0,.6);}}
    </style></head><body>
    <div class="stage"><div class="scrim"></div>
      <div class="content">
        <div class="kicker"><span class="bar"></span>UTTARAKHAND · INDIA<span class="bar"></span></div>
        <h1 class="title">दारमा वैली</h1>
        <div class="sub">{sub}</div>
      </div>
    </div></body></html>"""

def render(sub, outname):
    hp=os.path.join(BASE,"thumb_tmp.html"); open(hp,"w",encoding="utf-8").write(html(sub))
    with sync_playwright() as p:
        b=p.chromium.launch()
        pg=b.new_page(viewport={"width":1280,"height":720}, device_scale_factor=2)
        pg.goto("file://"+hp); pg.wait_for_timeout(400)
        pg.screenshot(path=os.path.join(BASE,"out",outname), clip={"x":0,"y":0,"width":1280,"height":720})
        b.close()
    print("rendered", outname)

os.makedirs(os.path.join(BASE,"out"), exist_ok=True)
render("पंचाचूली · भारत–नेपाल बॉर्डर", "Thumb_Darma_A.png")
render("जहाँ भारत मिलता है नेपाल से", "Thumb_Darma_B.png")

# YouTube-ready jpgs
from PIL import Image
for tag in ["A","B"]:
    im=Image.open(os.path.join(BASE,"out",f"Thumb_Darma_{tag}.png")).convert("RGB").resize((1280,720),Image.LANCZOS)
    q=92
    while q>=80:
        im.save(os.path.join(BASE,"out",f"Thumb_Darma_{tag}_YouTube.jpg"),quality=q,optimize=True)
        if os.path.getsize(os.path.join(BASE,"out",f"Thumb_Darma_{tag}_YouTube.jpg"))<=2_000_000: break
        q-=3
    t=Image.open(os.path.join(BASE,"out",f"Thumb_Darma_{tag}.png")).convert("RGB"); t.thumbnail((900,900))
    t.save(os.path.join(BASE,"thumbs",f"Darma_{tag}.jpg"),quality=88)
print("done")
