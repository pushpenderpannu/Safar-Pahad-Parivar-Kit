import subprocess, time, os, json, sys, urllib.parse, shutil, tempfile
from pathlib import Path as _P
SRC = str(_P(__file__).resolve().parents[1])      # <kit>/Source
KIT = str(_P(__file__).resolve().parents[2])      # <kit>
from playwright.sync_api import sync_playwright
from PIL import Image
S = SRC
D = tempfile.mkdtemp(); OUT = os.path.join(SRC, "_build", "ograf_shots"); os.makedirs(OUT, exist_ok=True)
shutil.copytree(os.path.join(KIT, "Resolve", "Templates", "Edit", "Titles", "Safar Pahad Parivar"), os.path.join(D, "Safar Pahad Parivar"))
shutil.copy(os.path.join(SRC, "templates", "harness.html"), D)
for _b in ("bg_a.jpg", "bg_b.jpg"): shutil.copy(os.path.join(SRC, "assets", _b), D)
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8765", "--bind", "127.0.0.1"], cwd=D,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1.0)
CASES = [  # (template, times ms, resolution, bg, data, tag)
    ("SPP-Info-Card", [300, 700, 1200, 3000, 7700], (1920, 1080), "bg_a.jpg", {}, "169"),
    ("SPP-Info-Card", [3000], (1080, 1920), "bg_b.jpg", {"position": "3", "weather": "5"}, "916"),
    ("SPP-Altitude-Counter", [500, 1800, 4000], (1920, 1080), "bg_b.jpg", {}, "169"),
    ("SPP-Altitude-Counter", [4000], (1920, 1080), "bg_b.jpg", {"position": 4, "scale": 1.4}, "center"),
    ("SPP-Peak-Callout", [200, 600, 1000, 3000], (1920, 1080), "bg_a.jpg", {"targetX": 34, "targetY": 12, "labelDX": 14, "labelDY": 18}, "dot"),
    ("SPP-Peak-Callout", [3000], (1920, 1080), "bg_a.jpg", {"targetX": 92, "targetY": 33, "labelDX": -16, "labelDY": -10, "marker": 1, "peakHi": "पंचाचूली II", "peakEn": "PANCHACHULI II", "heightM": 6904}, "arrow"),
    ("SPP-Popup-Title", [300, 700, 3000], (1920, 1080), "bg_b.jpg", {}, "center"),
    ("SPP-Popup-Title", [3000], (1920, 1080), "bg_a.jpg", {"position": 0}, "bl"),
    ("SPP-Credits", [800, 2000, 5000], (1920, 1080), "bg_b.jpg", {}, "169"),
    ("SPP-Credits", [5000], (1080, 1920), "bg_b.jpg", {}, "916"),
    ("SPP-Captions", [1150, 1900, 3500, 5200, 7000], (1920, 1080), "bg_a.jpg", {"style": "0", "srt": "1\n00:00:01,000 --> 00:00:04,000\n<b>साल की सबसे यादगार ट्रिप</b>\n"}, "pop"),
    ("SPP-Captions", [8300, 9600, 10900], (1920, 1080), "bg_b.jpg", {"style": 1}, "karaoke"),
    ("SPP-Captions", [5500], (1080, 1920), "bg_b.jpg", {"style": "1", "position": "1", "size": 1.15}, "916"),
    ("SPP-Captions", [12500], (1920, 1080), "bg_a.jpg", {"style": 2, "plate": True, "position": 3}, "plate"),
    ("SPP-Captions", [6000], (1920, 1080), "bg_a.jpg", {"clipStart": 3}, "offset"),
]
errors = []
with sync_playwright() as pw:
    b = pw.chromium.launch()
    for tpl, times, (w, h), bg, data, tag in CASES:
        pg = b.new_page(viewport={"width": w, "height": h})
        pg.on("pageerror", lambda e, t=tpl: errors.append(f"{t}: {e}"))
        pg.on("console", lambda m, t=tpl: errors.append(f"{t} console {m.type}: {m.text}") if m.type in ("error", "warning") else None)
        url = f"http://127.0.0.1:8765/harness.html?t={tpl}&w={w}&h={h}&bg={bg}&data={urllib.parse.quote(json.dumps(data))}"
        pg.goto(url); pg.wait_for_function("window.ready===true", timeout=15000)
        tiles = []
        for ms in times:
            pg.evaluate(f"seek({ms})"); pg.wait_for_timeout(60)
            p = os.path.join(OUT, f"{tpl}_{tag}_{ms}.png"); pg.screenshot(path=p); tiles.append(p)
        # determinism check: seek elsewhere, come back, compare
        pg.evaluate(f"seek({times[-1]+900})"); pg.evaluate(f"seek({times[-1]})"); pg.wait_for_timeout(60)
        p2 = os.path.join(OUT, f"_{tpl}_{tag}_re.png"); pg.screenshot(path=p2)
        same = Image.open(tiles[-1]).tobytes() == Image.open(p2).tobytes()
        print(f"{tpl:22s} {tag:7s} ok  deterministic={same}")
        pg.close()
    b.close()
srv.terminate()
print("ERRORS:", errors if errors else "none")
