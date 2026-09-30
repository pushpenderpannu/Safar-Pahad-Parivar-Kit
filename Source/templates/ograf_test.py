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
shutil.copytree(os.path.join(SRC, "assets", "sample_route"), os.path.join(D, "route"))
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8765", "--bind", "127.0.0.1"], cwd=D,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1.0)
CASES = [  # (template, times ms, resolution, bg, data, tag)
    ("SPP-Info-Card", [300, 700, 1000, 1300, 1600, 3000, 7700], (1920, 1080), "bg_a.jpg", {}, "169"),
    ("SPP-Info-Card", [3000], (1080, 1920), "bg_b.jpg", {"position": "top-right", "weather": "snow"}, "916"),
    ("SPP-Info-Card", [2300, 3000, 3700, 4500], (1920, 1080), "bg_a.jpg", {"fromAltitude": 1650, "fromDate": "24 जून 2026", "fromTime": "04:10 PM", "fromWeather": "cloud"}, "from"),
    ("SPP-Altitude-Counter", [500, 1000, 1400, 1800, 4000], (1920, 1080), "bg_b.jpg", {}, "169"),
    ("SPP-Altitude-Counter", [4000], (1920, 1080), "bg_b.jpg", {"position": 4, "scale": 1.4}, "center"),
    ("SPP-Altitude-Counter", [1000, 1800, 4000], (1920, 1080), "bg_b.jpg", {"startAltitude": 3200, "endAltitude": 915}, "down"),
    ("SPP-Peak-Callout", [300, 700, 1000, 3000], (1920, 1080), "bg_a.jpg", {"p1X": 34, "p1Y": 40}, "one"),
    ("SPP-Peak-Callout", [900, 1600, 2400, 3500], (1920, 1080), "bg_b.jpg", {"peak1": "पंचाचूली II | PANCHACHULI II | 6904", "p1X": 21.4, "p1Y": 59.3, "peak2": "पंचाचूली III | PANCHACHULI III | 6312", "p2X": 36.7, "p2Y": 65.7, "peak3": "पंचाचूली IV | PANCHACHULI IV | 6334", "p3X": 52.1, "p3Y": 70, "peak4": "पंचाचूली V | PANCHACHULI V | 6437", "p4X": 71.1, "p4Y": 63.9}, "four"),
    ("SPP-Peak-Callout", [3500], (1920, 1080), "bg_b.jpg", {**{"peak1": "पंचाचूली II | PANCHACHULI II | 6904", "p1X": 21.4, "p1Y": 59.3, "peak2": "पंचाचूली III | PANCHACHULI III | 6312", "p2X": 36.7, "p2Y": 65.7, "peak3": "पंचाचूली IV | PANCHACHULI IV | 6334", "p3X": 52.1, "p3Y": 70, "peak4": "पंचाचूली V | PANCHACHULI V | 6437", "p4X": 71.1, "p4Y": 63.9}, "marker": 1, "labelBox": False}, "fourarrow"),
    ("SPP-Peak-Callout", [3500], (1920, 1080), "bg_b.jpg", {**{"peak1": "पंचाचूली II | PANCHACHULI II | 6904", "p1X": 21.4, "p1Y": 59.3, "peak2": "पंचाचूली III | PANCHACHULI III | 6312", "p2X": 36.7, "p2Y": 65.7, "peak3": "पंचाचूली IV | PANCHACHULI IV | 6334", "p3X": 52.1, "p3Y": 70, "peak4": "पंचाचूली V | PANCHACHULI V | 6437", "p4X": 71.1, "p4Y": 63.9}, "_rw": 3840}, "4k"),
    ("SPP-Peak-Callout", [3500], (1080, 1920), "bg_b.jpg", {"peak2": "नंदा देवी | NANDA DEVI | 7816", "p1X": 30, "p2X": 85, "p2Y": 42}, "916"),
    ("SPP-Popup-Title", [300, 700, 3000], (1920, 1080), "bg_b.jpg", {}, "center"),
    ("SPP-Popup-Title", [3000], (1920, 1080), "bg_a.jpg", {"position": 0}, "bl"),
    ("SPP-Credits", [800, 2000, 5000], (1920, 1080), "bg_b.jpg", {}, "169"),
    ("SPP-Credits", [5000], (1080, 1920), "bg_b.jpg", {}, "916"),
    ("SPP-Captions", [1150, 1900, 3500, 5200, 7000], (1920, 1080), "bg_a.jpg", {"style": "0", "srt": "1\n00:00:01,000 --> 00:00:04,000\n<b>साल की सबसे यादगार ट्रिप</b>\n"}, "pop"),
    ("SPP-Captions", [8300, 9600, 10900], (1920, 1080), "bg_b.jpg", {"style": 1}, "karaoke"),
    ("SPP-Captions", [5500], (1080, 1920), "bg_b.jpg", {"style": "karaoke", "position": "raised", "size": 1.15}, "916"),
    ("SPP-Captions", [12500], (1920, 1080), "bg_a.jpg", {"style": 2, "plate": True, "position": 3}, "plate"),
    ("SPP-Captions", [6000], (1920, 1080), "bg_a.jpg", {"clipStart": 3}, "offset"),
    ("SPP-Captions", [1500, 2750, 3000, 3800], (1920, 1080), "bg_a.jpg", {"style": "0", "srt": '{"spp": 1, "cues": [{"a": 1.0, "b": 4.2, "text": "ये नज़ारा सच में बेमिसाल था", "w": [[1.0, 1.2, 0], [1.25, 1.8, 0], [1.9, 2.1, 0], [2.1, 2.3, 0], [2.6, 3.5, 1], [3.6, 3.9, 0]]}]}'}, "words"),
    ("SPP-Captions", [2800], (1920, 1080), "bg_b.jpg", {"style": "1", "srt": '{"spp": 1, "cues": [{"a": 1.0, "b": 4.2, "text": "ये नज़ारा सच में बेमिसाल था", "w": [[1.0, 1.2, 0], [1.25, 1.8, 0], [1.9, 2.1, 0], [2.1, 2.3, 0], [2.6, 3.5, 1], [3.6, 3.9, 0]]}]}'}, "wkaraoke"),
    ("SPP-Route-Map", [500, 1600, 3500, 5200, 7600, 9500, 12500, 14000], (1920, 1080), "bg_a.jpg", {"routeFile": "http://127.0.0.1:8765/route/route.json", "camera": "follow"}, "follow"),
    ("SPP-Route-Map", [14000], (1920, 1080), "bg_a.jpg", {"routeFile": "http://127.0.0.1:8765/route/route.json", "camera": "0"}, "whole"),
    ("SPP-Route-Map", [2000], (1920, 1080), "bg_a.jpg", {}, "empty"),
    ("SPP-Route-Map", [3500, 9500, 14000], (1920, 1080), "bg_a.jpg", {"routeFile": "http://127.0.0.1:8765/route/route.json", "cinemaBars": True}, "default235"),
    ("SPP-Film-Title", [300, 800, 1300, 1800, 3000, 6600], (1920, 1080), "bg_a.jpg", {}, "centre"),
    ("SPP-Film-Title", [3000], (1920, 1080), "bg_b.jpg", {"position": "bottom-left"}, "bl"),
    ("SPP-Film-Title", [3000], (1080, 1920), "bg_b.jpg", {}, "916"),
    ("SPP-Chapter", [200, 600, 1000, 1500, 2500, 4700], (1920, 1080), "bg_b.jpg", {}, "centre"),
    ("SPP-Chapter", [2500], (1920, 1080), "bg_a.jpg", {"position": "bottom-left", "number": 4, "total": 6, "hindiDigits": True}, "bl"),
    ("SPP-Chapter", [2500], (1920, 1080), "bg_a.jpg", {"position": "top-left", "total": 0, "meta": ""}, "tl"),
    ("SPP-Chapter", [2500], (1080, 1920), "bg_b.jpg", {"number": 1}, "916"),
    ("SPP-Info-Card", [3000], (1920, 1080), "bg_a.jpg", {"position": "bottom-left 2.35"}, "lb235"),
    ("SPP-Chapter", [2500], (1920, 1080), "bg_a.jpg", {"position": "bottom-left 2.35"}, "lb235"),
    ("SPP-Film-Title", [3000], (1920, 1080), "bg_b.jpg", {"position": "bottom-left 2.35"}, "lb235"),
    ("SPP-Captions", [2000], (1920, 1080), "bg_a.jpg", {"position": "bottom 2.35", "srt": "1\n00:00:01,000 --> 00:00:04,000\nये नज़ारा बेमिसाल था\n"}, "lb235"),
]
errors = []
if os.environ.get("SPP_ONLY"): CASES = [c for c in CASES if c[0] == os.environ["SPP_ONLY"]]
with sync_playwright() as pw:
    b = pw.chromium.launch()
    for tpl, times, (w, h), bg, data, tag in CASES:
        pg = b.new_page(viewport={"width": w, "height": h})
        pg.on("pageerror", lambda e, t=tpl: errors.append(f"{t}: {e}"))
        pg.on("console", lambda m, t=tpl: errors.append(f"{t} console {m.type}: {m.text}") if m.type in ("error", "warning") else None)
        rw = data.pop("_rw", 0) if isinstance(data, dict) else 0
        url = f"http://127.0.0.1:8765/harness.html?t={tpl}&w={w}&h={h}&bg={bg}&data={urllib.parse.quote(json.dumps(data))}"
        if rw: url += f"&rw={rw}&rh={rw * h // w}"   # Resolve on a 4K timeline: reports 3840 wide, page is 1920 CSS px
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
