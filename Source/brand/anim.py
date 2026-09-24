import base64, os, subprocess, shutil, sys
from pathlib import Path as _P
SRC = str(_P(__file__).resolve().parents[1])      # <kit>/Source
KIT = str(_P(__file__).resolve().parents[2])      # <kit>
from playwright.sync_api import sync_playwright
S = SRC
OUT = os.path.join(KIT, "Graphics"); os.makedirs(OUT, exist_ok=True)
BUILD = os.path.join(SRC, "_build", "anim"); os.makedirs(BUILD, exist_ok=True)
FB = os.path.join(SRC, "fonts"); PO = FB
b64 = lambda p: base64.b64encode(open(p, "rb").read()).decode()
FONTS = "".join(f"@font-face{{font-family:'Deva';font-weight:{w};src:url(data:font/woff2;base64,{b64(os.path.join(FB, f'deva-{w}.woff2'))}) format('woff2');}}" for w in (500, 700, 800))
FONTS += f"@font-face{{font-family:'Pop';font-weight:700;src:url(data:font/ttf;base64,{b64(os.path.join(PO,'pop-700.ttf'))}) format('truetype');}}"
FONTS += f"@font-face{{font-family:'Pop';font-weight:500;src:url(data:font/ttf;base64,{b64(os.path.join(PO,'pop-500.ttf'))}) format('truetype');}}"
GOLD, NAVY, SNOW = "#F4B03E", "#07122B", "#F5F8FC"

MARK = f"""<svg id="mark" viewBox="0 0 200 130" xmlns="http://www.w3.org/2000/svg" style="overflow:visible">
  <circle id="sun" cx="150" cy="30" r="11" fill="{GOLD}"/>
  <path id="ridge" d="M8 118 L58 60 L78 82 L103 26 L133 76 L148 60 L192 118" fill="none" stroke="{SNOW}"
        stroke-width="6" stroke-linejoin="round" stroke-linecap="round"/>
  <path id="snow" d="M86 62 L95 70 L103 60 L111 70 L121 62" fill="none" stroke="{SNOW}" stroke-width="3.6"
        stroke-linejoin="round" stroke-linecap="round"/>
  <path id="trail" d="M100 124 C 82 112, 120 104, 101 92 C 88 86, 110 82, 103 76" fill="none" stroke="none"/>
  <g id="dots"></g></svg>"""

COMMON_JS = """
const clamp=(x)=>Math.max(0,Math.min(1,x));
const seg=(t,a,b)=>clamp((t-a)/(b-a));
const ease=(x)=>1-Math.pow(1-x,3);
const back=(x)=>{const c=1.7;return 1+ (c+1)*Math.pow(x-1,3)+c*Math.pow(x-1,2);};
function setupMark(){
  for (const id of ['ridge','snow']){const p=document.getElementById(id);const L=p.getTotalLength();
     p.style.strokeDasharray=L; p.dataset.L=L; p.style.strokeDashoffset=L;}
  const tr=document.getElementById('trail'); const L=tr.getTotalLength(); const g=document.getElementById('dots');
  const n=9; for(let i=0;i<n;i++){const pt=tr.getPointAtLength(L*i/(n-1));
     const c=document.createElementNS('http://www.w3.org/2000/svg','circle');
     c.setAttribute('cx',pt.x);c.setAttribute('cy',pt.y);c.setAttribute('r',2.3);c.setAttribute('fill','%s');
     c.setAttribute('opacity',0); g.appendChild(c);}
}
function drawMark(t,t0){
  const r=document.getElementById('ridge'), s=document.getElementById('snow');
  r.style.strokeDashoffset=r.dataset.L*(1-ease(seg(t,t0,t0+1.3)));
  s.style.strokeDashoffset=s.dataset.L*(1-ease(seg(t,t0+1.0,t0+1.5)));
  const dots=document.querySelectorAll('#dots circle');
  dots.forEach((d,i)=>{d.setAttribute('opacity',ease(seg(t,t0+1.3+i*0.08,t0+1.45+i*0.08)));});
  const su=document.getElementById('sun'); const k=seg(t,t0+1.6,t0+2.2);
  su.setAttribute('opacity',k); su.setAttribute('cy',30+14*(1-ease(k))); su.setAttribute('r',11*(0.6+0.4*back(k)));
}
""" % GOLD

def page(body, css, js, w, h):
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{FONTS}
    *{{margin:0;padding:0;box-sizing:border-box}} html,body{{width:{w}px;height:{h}px;background:transparent;overflow:hidden}}
    {css}</style></head><body>{body}<script>{COMMON_JS}{js}</script></body></html>"""

def render(name, html, w, h, dur, fps=30, anim_until=None, scale=2):
    """Render frames 0..anim_until (sec) then clone last frame to reach dur."""
    fdir = os.path.join(BUILD, name + "_frames"); shutil.rmtree(fdir, ignore_errors=True); os.makedirs(fdir)
    hp = os.path.join(BUILD, name + ".html"); open(hp, "w", encoding="utf-8").write(html)
    anim_until = anim_until or dur
    n = int(round(anim_until * fps))
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=scale)
        pg.goto("file://" + hp); pg.wait_for_timeout(500); pg.evaluate("setup()")
        for i in range(n):
            pg.evaluate(f"render({i/fps})")
            pg.screenshot(path=os.path.join(fdir, f"{i:05d}.png"), omit_background=True)
        b.close()
    out = os.path.join(OUT, name + ".mov")
    pad = max(0.0, dur - anim_until)
    vf = f"tpad=stop_mode=clone:stop_duration={pad}" if pad > 0 else "null"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(fps), "-i", os.path.join(fdir, "%05d.png"),
                    "-vf", vf, "-c:v", "png", "-pix_fmt", "rgba", out], check=True)
    print(name, "frames", n, "->", out, os.path.getsize(out) // 1024, "KB")
    return fdir

W, H = 1920, 1080

# ---------------- INTRO (5s) ----------------
intro_body = f"""<div id="scrim"></div><div id="wrap">
  <div id="markbox">{MARK}</div>
  <div id="deva">सफ़र <span class="g">·</span> पहाड़ <span class="g">·</span> परिवार</div>
  <div id="lat">SAFAR · PAHAD · PARIVAR</div>
  <div id="pre">PRESENTS</div></div>"""
intro_css = f"""#scrim{{position:absolute;inset:0;background:radial-gradient(85% 80% at 50% 48%, rgba(7,18,43,.30), rgba(7,18,43,.82));opacity:0}}
#wrap{{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center}}
#markbox{{width:340px}} #deva{{font-family:Deva;font-weight:800;font-size:96px;color:{SNOW};line-height:1.25;margin-top:22px;opacity:0;white-space:nowrap}}
.g{{color:{GOLD}}} #lat{{font-family:Pop;font-weight:500;font-size:25px;color:{SNOW};opacity:0;margin-top:10px}}
#pre{{font-family:Pop;font-weight:500;font-size:21px;letter-spacing:.35em;color:{GOLD};margin-top:26px;opacity:0}}
#deva,#lat,#pre{{text-shadow:0 3px 18px rgba(0,0,0,.45)}}"""
intro_js = """
function setup(){setupMark();}
function render(t){
  const out=1-seg(t,4.3,5.0);
  document.getElementById('scrim').style.opacity=ease(seg(t,0,0.6))*out;
  drawMark(t,0.3);
  document.getElementById('mark').style.opacity=out;
  const d=document.getElementById('deva'), k=ease(seg(t,2.3,3.0));
  d.style.opacity=k*out; d.style.transform=`translateY(${18*(1-k)}px)`;
  const l=document.getElementById('lat'), k2=ease(seg(t,2.8,3.5));
  l.style.opacity=0.85*k2*out; l.style.letterSpacing=(0.8-0.38*k2)+'em';
  document.getElementById('pre').style.opacity=ease(seg(t,3.3,3.8))*out;
}"""
render("SPP_Intro_5s_4K", page(intro_body, intro_css, intro_js, W, H), W, H, dur=5.0)

# ---------------- END CARD (15s, animates 2.2s then holds) ----------------
box = lambda x, lab_d, lab_e, idn: f"""<div class="slot" id="{idn}" style="left:{x}px">
   <div class="lab"><span class="ld">{lab_d}</span><span class="le">{lab_e}</span></div><div class="frame"></div></div>"""
end_body = f"""<div id="scrim"></div>
  <div id="head"><div id="h1">फिर मिलेंगे, अगले सफ़र पर</div><div id="h2">SEE YOU ON THE NEXT JOURNEY</div></div>
  {box(130,'अगला वीडियो','NEXT VIDEO','s1')}{box(1070,'आपके लिए','FOR YOU','s2')}
  <div id="foot"><div id="ring"></div>
    <div id="brand"><div id="markbox">{MARK}</div><div id="handle">@safar.pahad.parivar</div></div></div>"""
end_css = f"""#scrim{{position:absolute;inset:0;background:rgba(7,18,43,.82);opacity:0}}
#head{{position:absolute;left:0;right:0;top:64px;text-align:center}}
#h1{{font-family:Deva;font-weight:800;font-size:68px;color:{SNOW};opacity:0}}
#h2{{font-family:Pop;font-weight:500;font-size:21px;letter-spacing:.35em;color:{GOLD};margin-top:6px;opacity:0}}
.slot{{position:absolute;top:300px;width:720px;opacity:0}}
.lab{{display:flex;gap:14px;align-items:baseline;margin-bottom:12px}}
.ld{{font-family:Deva;font-weight:700;font-size:30px;color:{SNOW}}} .le{{font-family:Pop;font-weight:500;font-size:17px;letter-spacing:.25em;color:{GOLD}}}
.frame{{width:720px;height:405px;border-radius:20px;border:3px solid rgba(245,248,252,.55);box-shadow:0 0 40px rgba(244,176,62,.15), inset 0 0 0 1px rgba(255,255,255,.08);background:rgba(255,255,255,.04)}}
#foot{{position:absolute;left:0;right:0;bottom:70px;display:flex;align-items:center;justify-content:center;gap:40px}}
#ring{{width:200px;height:200px;border-radius:50%;border:3px solid rgba(245,248,252,.55);opacity:0}}
#brand{{opacity:0}} #markbox{{width:170px}} #handle{{font-family:Pop;font-weight:700;font-size:30px;color:{SNOW};margin-top:8px}}"""
end_js = """
function setup(){setupMark();}
function render(t){
  document.getElementById('scrim').style.opacity=ease(seg(t,0,0.6));
  const a=ease(seg(t,0.3,1.0)); const h1=document.getElementById('h1'); h1.style.opacity=a; h1.style.transform=`translateY(${16*(1-a)}px)`;
  document.getElementById('h2').style.opacity=ease(seg(t,0.6,1.2));
  ['s1','s2'].forEach((id,i)=>{const k=ease(seg(t,0.8+i*0.15,1.5+i*0.15)); const e=document.getElementById(id);
     e.style.opacity=k; e.style.transform=`scale(${0.96+0.04*k})`;});
  const r=ease(seg(t,1.2,1.8)); const ring=document.getElementById('ring'); ring.style.opacity=r; ring.style.transform=`scale(${0.85+0.15*back(r)})`;
  document.getElementById('brand').style.opacity=ease(seg(t,1.3,1.9));
  drawMark(t,0.2);
}"""
render("SPP_EndCard_15s_4K", page(end_body, end_css, end_js, W, H), W, H, dur=15.0, anim_until=2.6)

# ---------------- WATERMARKS (static full-frame PNGs) ----------------
def wm(w, h, css_pos, name, size=1.0):
    body = f"""<div style="position:absolute;{css_pos};opacity:.72;display:flex;align-items:center;gap:{14*size}px;
      filter:drop-shadow(0 2px 4px rgba(0,0,0,.65)) drop-shadow(0 0 12px rgba(7,18,43,.45))">
      <div style="width:{80*size}px">{MARK}</div>
      <div style="font-family:Deva;font-weight:700;font-size:{25*size}px;color:#fff">सफ़र · पहाड़ · परिवार</div></div>"""
    js = "function setup(){setupMark(); drawMark(99,0);} function render(t){}"
    hp = os.path.join(BUILD, name + ".html"); open(hp, "w", encoding="utf-8").write(page(body, "", js, w, h))
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=2)
        pg.goto("file://" + hp); pg.wait_for_timeout(400); pg.evaluate("setup()")
        pg.screenshot(path=os.path.join(OUT, name + ".png"), omit_background=True); b.close()
    print("watermark", name)
wm(1920, 1080, "right:52px;bottom:40px", "SPP_Watermark_16x9_4K")
wm(1080, 1920, "left:50%;top:150px;transform:translateX(-50%)", "SPP_Watermark_Shorts_9x16", size=1.1)
