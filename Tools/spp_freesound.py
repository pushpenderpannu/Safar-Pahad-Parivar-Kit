"""
Safar Pahad Parivar - fetch public-domain (CC0) field recordings from Freesound for the SFX / music kit.

    .venv\\Scripts\\python.exe Tools\\spp_freesound.py            # fetch everything on the wish list (skips what's there)
    .venv\\Scripts\\python.exe Tools\\spp_freesound.py --only Birds
    .venv\\Scripts\\python.exe Tools\\spp_freesound.py --list     # show the wish list

Needs a free Freesound API key in Tools\\freesound_key.txt (freesound.org/apiv2/apply - never commit it; it's git-ignored).
Only sounds licensed **Creative Commons 0** (public domain) are taken, so they are free for monetised YouTube with no credit.
Files go to Source\\_cc0\\<group>\\<wish>\\<id>_<name>.ogg (high-quality previews) with manifest.json recording the
author / link / licence of every file.  The folder is not in git; the generator turns them into library sounds.
"""
import argparse, json, os, re, sys, time, urllib.parse, urllib.request
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
OUT = KIT / "Source" / "_cc0"
API = "https://freesound.org/apiv2/search/text/"

# group, wish name, search query, duration range (s), how many to keep
WISHES = [
    # ---------------------------------------------------------------- Rain
    ("Rain", "Rain_Light", "light rain", (30, 900), 4),
    ("Rain", "Rain_Heavy", "heavy rain downpour", (30, 900), 4),
    ("Rain", "Rain_On_Roof", ["rain on roof", "rain roof", "rain window", "rain gutter"], (20, 900), 3),
    ("Rain", "Rain_On_Tin_Roof", ["rain tin roof", "rain metal roof", "rain corrugated", "rain tent"], (20, 900), 3),
    ("Rain", "Rain_In_Car", "rain car interior", (20, 900), 3),
    ("Rain", "Rain_Forest", "rain forest leaves", (30, 900), 3),
    ("Rain", "Thunder", "thunder rumble", (4, 60), 5),
    # ---------------------------------------------------------------- Car & road
    ("Car", "Car_Door_Open", "car door open", (0.5, 6), 5),
    ("Car", "Car_Door_Close", "car door close", (0.5, 6), 6),
    ("Car", "Car_Trunk", "car trunk boot close", (0.5, 6), 3),
    ("Car", "Car_Engine_Start", "car engine start", (2, 20), 4),
    ("Car", "Car_Horn", "car horn", (0.3, 5), 4),
    ("Car", "Tyres_Tarmac", "car driving asphalt road interior", (20, 600), 4),
    ("Car", "Tyres_Gravel", "tires gravel road driving", (5, 600), 4),
    ("Car", "Tyres_Wet_Road", "car wet road driving", (10, 600), 3),
    ("Car", "Car_Pass_By", "car pass by", (3, 30), 5),
    ("Car", "Footsteps_Gravel", "footsteps gravel", (3, 120), 3),
    # ---------------------------------------------------------------- Birds (Himalaya / India)
    ("Birds", "Whistling_Thrush", ["whistling thrush", "thrush song", "blackbird song", "song thrush"], (2, 300), 4),
    ("Birds", "Himalayan_Monal", ["monal", "pheasant call", "pheasant"], (1, 300), 3),
    ("Birds", "Cuckoo", "cuckoo call", (2, 300), 4),
    ("Birds", "Barbet", "barbet", (2, 300), 3),
    ("Birds", "Laughing_Thrush", "laughingthrush", (2, 300), 3),
    ("Birds", "Raven_Crow", "raven croak", (1, 120), 3),
    ("Birds", "Crows_India", "house crow india", (2, 300), 3),
    ("Birds", "Dawn_Chorus", "dawn chorus forest birds", (30, 900), 4),
    ("Birds", "Forest_Birds_India", "india forest birds ambience", (30, 900), 4),
    ("Birds", "Eagle_Kite", ["black kite call", "kite bird", "buzzard call", "eagle call", "hawk call"], (1, 120), 3),
    # ---------------------------------------------------------------- Water
    ("Water", "Stream_Close", "mountain stream close", (30, 900), 4),
    ("Water", "River_Rapids", "river rapids", (30, 900), 4),
    ("Water", "River_Distant", "river distant", (30, 900), 3),
    ("Water", "Waterfall_Close", "waterfall close", (30, 900), 4),
    ("Water", "Waterfall_Distant", "waterfall distant", (30, 900), 3),
    ("Water", "Water_Drips", "water drips cave", (10, 600), 3),
    ("Water", "Splash", "water splash", (0.5, 10), 4),
    # ---------------------------------------------------------------- Temple
    ("Temple", "Conch_Shankh", "conch shell blow", (2, 30), 3),
    ("Temple", "Temple_Bell_Real", "temple bell india", (2, 60), 4),
    ("Temple", "Temple_Crowd", "temple india ambience", (30, 900), 3),
    # ---------------------------------------------------------------- South Indian instruments (music pack)
    ("SouthIndian", "Mridangam", "mridangam", (1, 600), 6),
    ("SouthIndian", "Thavil", ["thavil", "tavil", "dhol", "indian drum"], (1, 600), 4),
    ("SouthIndian", "Ghatam", "ghatam", (1, 600), 4),
    ("SouthIndian", "Kanjira", ["kanjira", "frame drum", "tambourine india", "daf"], (1, 600), 3),
    ("SouthIndian", "Veena", "veena", (1, 600), 5),
    ("SouthIndian", "Nadaswaram", ["nadaswaram", "nagaswaram", "shehnai", "shenai"], (1, 600), 4),
    ("SouthIndian", "Konnakol", ["konnakol", "indian rhythm syllables", "bol tabla"], (1, 600), 3),
]


# a download only counts if its name / tags really mention the thing (search ranking alone pulls in misfits)
MUST = {
    "Rain_Light": [["rain"]], "Rain_Heavy": [["rain", "downpour", "storm"]], "Rain_On_Roof": [["rain"], ["roof", "window", "gutter"]],
    "Rain_On_Tin_Roof": [["rain"], ["tin", "metal", "roof", "tent", "corrugated"]], "Rain_In_Car": [["rain"], ["car", "vehicle"]],
    "Rain_Forest": [["rain"]], "Thunder": [["thunder"]],
    "Car_Door_Open": [["door"], ["car", "vehicle", "truck", "van"]], "Car_Door_Close": [["door"], ["car", "vehicle", "truck", "van"]],
    "Car_Trunk": [["trunk", "boot", "tailgate"]], "Car_Engine_Start": [["engine", "ignition", "start"]], "Car_Horn": [["horn", "honk"]],
    "Tyres_Tarmac": [["road", "asphalt", "tarmac", "driving", "interior", "highway"]], "Tyres_Gravel": [["gravel"]],
    "Tyres_Wet_Road": [["wet", "rain"]], "Car_Pass_By": [["pass", "passing", "passby", "drive", "drives"]],
    "Footsteps_Gravel": [["footstep", "footsteps", "walk", "walking", "steps"]],
    "Whistling_Thrush": [["thrush", "blackbird"]], "Himalayan_Monal": [["monal", "pheasant"]], "Cuckoo": [["cuckoo", "coucou"]],
    "Barbet": [["barbet"]], "Laughing_Thrush": [["laughingthrush", "laughing"]], "Raven_Crow": [["raven", "crow", "caw", "croak"]],
    "Crows_India": [["crow", "kaak", "caw"]], "Dawn_Chorus": [["dawn", "chorus", "birdsong", "birds"]],
    "Forest_Birds_India": [["bird", "birds", "jungle", "forest"]], "Eagle_Kite": [["kite", "buzzard", "eagle", "hawk", "raptor"]],
    "Stream_Close": [["stream", "brook", "creek", "river"]], "River_Rapids": [["river", "rapids"]],
    "River_Distant": [["river", "stream"]], "Waterfall_Close": [["waterfall", "falls", "cascade"]],
    "Waterfall_Distant": [["waterfall", "falls"]], "Water_Drips": [["drip", "drips", "dripping", "drop", "drops"]],
    "Splash": [["splash"]], "Conch_Shankh": [["conch", "shankh", "shell"]], "Temple_Bell_Real": [["bell", "bells"]],
    "Temple_Crowd": [["temple", "india", "indian", "crowd", "prayer"]],
    "Mridangam": [["mridangam", "mrdangam", "mridanga"]], "Thavil": [["thavil", "tavil", "dhol", "drum"]], "Ghatam": [["ghatam"]],
    "Kanjira": [["kanjira", "frame", "daf", "tambourine"]], "Veena": [["veena", "vina"]],
    "Nadaswaram": [["nadaswaram", "nagaswaram", "shehnai", "shenai"]], "Konnakol": [["konnakol", "solkattu", "bol"]],
}


def relevant(wish, name, tags):
    words = set(re.findall(r"[a-z]+", (name + " " + " ".join(tags or [])).lower().replace("_", " ")))
    return all(any(w in words or any(x.startswith(w) for x in words) for w in grp) for grp in MUST.get(wish, []))


def key():
    p = KIT / "Tools" / "freesound_key.txt"
    if not p.exists():
        raise SystemExit("Put your Freesound API key in Tools\\freesound_key.txt (freesound.org/apiv2/apply).")
    return p.read_text(encoding="utf-8-sig").strip()


def get(url, params=None, tries=3):
    if params:
        url += "?" + urllib.parse.urlencode(params)
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "SPP-kit/1.0"}), timeout=60) as r:
                return r.read()
        except Exception as e:
            if k == tries - 1:
                raise
            time.sleep(2 + 3 * k)


def search(tok, q, dur, n):
    params = {"query": q, "token": tok, "page_size": 80, "sort": "rating_desc",
              "filter": 'license:"Creative Commons 0" duration:[%g TO %g]' % dur,
              "fields": "id,name,username,license,duration,previews,avg_rating,num_ratings,num_downloads,tags,url,samplerate,channels"}
    res = json.loads(get(API, params))["results"]
    # prefer well-rated, much-downloaded, >= 44.1 kHz recordings
    def score(s):
        return (s.get("avg_rating") or 0) * min(1, (s.get("num_ratings") or 0) / 3) + min(2.0, (s.get("num_downloads") or 0) / 500) + \
            (0.5 if (s.get("samplerate") or 0) >= 44100 else 0)
    return sorted(res, key=score, reverse=True)[: n * 2]


def slug(s):
    return re.sub(r"[^A-Za-z0-9]+", "_", s)[:40].strip("_")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        for g, w, q, d, n in WISHES:
            print(f"{g:12s} {w:22s} x{n}  {q}  {d[0]}-{d[1]} s")
        return
    tok = key()
    manp = OUT / "manifest.json"
    man = json.load(open(manp, encoding="utf-8")) if manp.exists() else {}
    for g, w, q, d, n in WISHES:
        if a.only and a.only.lower() not in (g + " " + w).lower():
            continue
        folder = OUT / g / w
        folder.mkdir(parents=True, exist_ok=True)
        have = [k for k, v in man.items() if v["wish"] == w and relevant(w, v["name"], v.get("tags"))]
        if len(have) >= n:
            print(f"  {g}/{w}: already {len(have)}")
            continue
        hits = []
        for qq in (q if isinstance(q, list) else [q]):
            try:
                hits += [h for h in search(tok, qq, d, n) if h["id"] not in {x["id"] for x in hits}]
            except Exception as e:
                print(f"  {g}/{w}: search '{qq}' failed ({e})")
            if len(hits) >= n * 2:
                break
        got = len(have)
        for s in hits:
            if got >= n:
                break
            if str(s["id"]) in man or s.get("license", "").find("publicdomain/zero") < 0 and "Creative Commons 0" not in s.get("license", ""):
                continue
            if not relevant(w, s["name"], s.get("tags")):
                continue
            url = s["previews"].get("preview-hq-ogg") or s["previews"].get("preview-hq-mp3")
            ext = ".ogg" if url.endswith(".ogg") else ".mp3"
            fn = folder / f"{s['id']}_{slug(s['name'])}{ext}"
            try:
                fn.write_bytes(get(url))
            except Exception as e:
                print(f"    download failed {s['id']}: {e}")
                continue
            man[str(s["id"])] = {"wish": w, "group": g, "file": str(fn.relative_to(OUT)).replace("\\", "/"), "name": s["name"],
                                 "author": s["username"], "url": s["url"], "license": s["license"], "duration": s["duration"],
                                 "rating": s.get("avg_rating"), "downloads": s.get("num_downloads"), "tags": s.get("tags", [])[:12]}
            got += 1
            time.sleep(0.3)
        print(f"  {g}/{w}: {got} files  ({q})", flush=True)
        json.dump(man, open(manp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ok = sum(1 for v in man.values() if relevant(v["wish"], v["name"], v.get("tags")))
    print(f"{len(man)} CC0 recordings in {OUT} ({ok} relevant, the rest are ignored)")


if __name__ == "__main__":
    main()
