"""
Safar Pahad Parivar - turn the CC0 field recordings (Source/_cc0, fetched by Tools/spp_freesound.py) into library sounds.

    python Source/sfx/field_gen.py [--out SFX] [--cc0 Source/_cc0]

Beds become seamless 30 s loops (the steadiest part of the recording, mono-safe stereo, -24 dB RMS);
one-shots are trimmed and peak-normalised; files with several events (door slams, bird calls, splashes) are cut into
separate sounds.  Every file is chosen by hand below (CURATION) - search results alone pull in misfits.
The entries are added to SFX/sfx_catalog.json (run after sfx_gen.py) and the sources are listed in
Docs/Field_Recordings_Credits.md (CC0: no credit needed, kept for the record).
"""
import argparse, json, os, subprocess, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from synth import SR, lp, hp, bp, write_wav, stereo, n_, fade, seamless, rms_norm, peak_norm  # noqa

KIT = Path(__file__).resolve().parents[2]

# freesound id -> (category, name, mode, note)      mode: bed | oneshot | events | calls | excerpt
CURATION = {
    # ---------------------------------------------------------------- 20 Rain & Weather
    "405630": ("20 Rain & Weather", "Rain_Light", "bed", "light rain, end of a storm"),
    "664162": ("20 Rain & Weather", "Rain_Light", "bed", "soft rain drops"),
    "26220": ("20 Rain & Weather", "Rain_Heavy", "bed", "heavy rain"),
    "164206": ("20 Rain & Weather", "Rain_Heavy", "bed", "very heavy rain with thunder"),
    "344994": ("20 Rain & Weather", "Rain_Heavy", "bed", "heavy rain, lightning storm"),
    "431656": ("20 Rain & Weather", "Rain_On_Roof", "bed", "raindrops on an open roof window"),
    "450360": ("20 Rain & Weather", "Rain_On_Roof", "bed", "medium rain on a terrace roof"),
    "595072": ("20 Rain & Weather", "Rain_On_Roof", "bed", "rain heard from inside"),
    "451152": ("20 Rain & Weather", "Rain_On_Tin_Roof", "bed", "light rain on a tin roof"),
    "521772": ("20 Rain & Weather", "Rain_On_Tin_Roof", "bed", "rain on a tin shed roof, indoors"),
    "149244": ("20 Rain & Weather", "Rain_On_Tin_Roof", "bed", "rain on a car / metal roof, inside"),
    "123021": ("20 Rain & Weather", "Rain_In_Car", "bed", "rain on the car, heard inside"),
    "46525": ("20 Rain & Weather", "Rain_In_Car", "bed", "rain on the car, heard inside"),
    "398844": ("20 Rain & Weather", "Rain_In_Car", "bed", "rain on the car, heard inside"),
    "383064": ("20 Rain & Weather", "Rain_Forest", "bed", "rain shower in a forest"),
    "536843": ("20 Rain & Weather", "Rain_Forest", "bed", "rain in the forest"),
    "414050": ("20 Rain & Weather", "Thunder", "oneshot", "big thunder"),
    "477839": ("20 Rain & Weather", "Thunder", "oneshot", "thunder"),
    "469612": ("20 Rain & Weather", "Thunder", "oneshot", "thunder clap and rumble"),
    "505294": ("20 Rain & Weather", "Thunder", "oneshot", "thunder, rain begins"),
    "581124": ("20 Rain & Weather", "Thunder", "oneshot", "distant thunder"),
    "717876": ("20 Rain & Weather", "Thunder", "oneshot", "distant rolling thunder"),
    "459981": ("20 Rain & Weather", "Wind_Strong", "bed", "strong wind gusts (real)"),
    # ---------------------------------------------------------------- 21 Car & Road
    "173009": ("21 Car & Road", "Car_Door_Close", "oneshot", "car door closing"),
    "538947": ("21 Car & Road", "Car_Door_Close", "oneshot", "heavy door (jeep / truck) closing"),
    "242815": ("21 Car & Road", "Car_Door_Close", "events", "car door open / close"),
    "556690": ("21 Car & Road", "Car_Door_Close", "events", "car door open / close"),
    "118245": ("21 Car & Road", "Car_Door_Open", "oneshot", "driver's door opening"),
    "123020": ("21 Car & Road", "Car_Door_Open", "oneshot", "car door opening"),
    "629320": ("21 Car & Road", "Car_Door_Open", "oneshot", "car door opened from outside"),
    "629322": ("21 Car & Road", "Car_Door_Open", "oneshot", "car door opened from inside, with the door chime"),
    "335102": ("21 Car & Road", "Car_Door_Open", "oneshot", "car door opening"),
    "154753": ("21 Car & Road", "Car_Door_Handle", "events", "door handle clicks"),
    "396448": ("21 Car & Road", "Car_Lock", "oneshot", "central locking"),
    "136535": ("21 Car & Road", "Car_Trunk_Close", "oneshot", "boot / dickey closing"),
    "401554": ("21 Car & Road", "Car_Engine_Start", "oneshot", "engine start, heard inside"),
    "629313": ("21 Car & Road", "Car_Engine_Start", "oneshot", "ignition and start"),
    "413311": ("21 Car & Road", "Car_Engine_Start", "oneshot", "engine"),
    "461679": ("21 Car & Road", "Car_Horn", "events", "horn"),
    "254678": ("21 Car & Road", "Car_Horn", "events", "horn beeps"),
    "176215": ("21 Car & Road", "Car_Pass_By", "oneshot", "car passing by"),
    "237337": ("21 Car & Road", "Car_Pass_By", "oneshot", "car passing slowly"),
    "237338": ("21 Car & Road", "Car_Pass_By", "oneshot", "two cars passing slowly"),
    "465397": ("21 Car & Road", "Car_Pass_By", "oneshot", "one car passing"),
    "258002": ("21 Car & Road", "Car_Pass_By", "oneshot", "car drives by"),
    "462862": ("21 Car & Road", "Car_Pass_By_Wet", "oneshot", "car passing on a wet road"),
    "613963": ("21 Car & Road", "Car_Pass_By_Wet", "oneshot", "car on a wet country road"),
    "648786": ("21 Car & Road", "Traffic_Wet_Road", "bed", "cars and trucks on a wet road"),
    "399822": ("21 Car & Road", "Traffic_Wet_Road", "bed", "cars passing in a rainy street"),
    "251661": ("21 Car & Road", "Tyres_Gravel", "bed", "tyres on a gravel road"),
    "251662": ("21 Car & Road", "Tyres_Gravel", "bed", "tyres on a gravel road"),
    "577504": ("21 Car & Road", "Tyres_Gravel", "bed", "tyre on gravel, close"),
    "584320": ("21 Car & Road", "Footsteps_Gravel", "bed", "walking on a gravel forest road"),
    "614053": ("21 Car & Road", "Footsteps_Gravel", "bed", "footsteps on earth"),
    "556002": ("21 Car & Road", "Footsteps_Gravel_Steps", "events", "mountain boots on gravel, single steps"),
    # ---------------------------------------------------------------- 22 Birds
    "855951": ("22 Birds", "Cuckoo_Call", "calls", "cuckoo"),
    "59261": ("22 Birds", "Cuckoo_Morning", "bed", "cuckoo at dawn from a balcony"),
    "274771": ("22 Birds", "Cuckoo_Morning", "bed", "cuckoo in the woods"),
    "573080": ("22 Birds", "Dawn_Chorus", "bed", "dawn chorus"),
    "341675": ("22 Birds", "Dawn_Chorus", "bed", "blackbirds at dawn"),
    "269244": ("22 Birds", "Dawn_Chorus", "bed", "dawn chorus"),
    "578523": ("22 Birds", "Dawn_Chorus", "bed", "birds singing, dawn"),
    "644886": ("22 Birds", "Forest_Birds_India", "bed", "Nagarhole forest, India"),
    "644989": ("22 Birds", "Forest_Birds_India", "bed", "jungle / forest birds"),
    "566207": ("22 Birds", "Forest_Birds_India", "bed", "morning birds"),
    "535813": ("22 Birds", "Laughing_Thrush_Call", "calls", "laughingthrush calls"),
    "136259": ("22 Birds", "Crow_Caw", "calls", "crow 'kaa kaa'"),
    "528871": ("22 Birds", "Crow_Caw", "calls", "crows in a tree"),
    "716962": ("22 Birds", "Raven_Croak", "calls", "raven croak"),
    "249567": ("22 Birds", "Crows_Town", "bed", "crows in an Indian city"),
    "519105": ("22 Birds", "Thrush_Song", "calls", "songbird whistle"),
    "519109": ("22 Birds", "Thrush_Song", "calls", "songbird whistle"),
    "519110": ("22 Birds", "Thrush_Song", "calls", "songbird whistle"),
    "519120": ("22 Birds", "Thrush_Song", "calls", "songbirds"),
    "169185": ("22 Birds", "Pheasant_Call", "calls", "pheasant call (stand-in for monal)"),
    "194678": ("22 Birds", "Raptor_Call", "calls", "buzzard / kite mewing call"),
    "830292": ("22 Birds", "Raptor_Call", "calls", "red kite call"),
    # ---------------------------------------------------------------- 23 Water
    "414906": ("23 Water", "Stream_Close", "bed", "rapid mountain stream, close"),
    "822937": ("23 Water", "Stream_Close", "bed", "mountain stream"),
    "618914": ("23 Water", "Stream_Close", "bed", "forest stream, close"),
    "643546": ("23 Water", "Stream_Close", "bed", "stream in Nepal"),
    "394097": ("23 Water", "River", "bed", "river with small rapids"),
    "588177": ("23 Water", "River", "bed", "mountain river"),
    "588178": ("23 Water", "River", "bed", "mountain river"),
    "459407": ("23 Water", "River", "bed", "small fast river"),
    "642775": ("23 Water", "River", "bed", "river gurgling in a forest"),
    "332419": ("23 Water", "River_India_Birds", "bed", "riverside in India, water and birds"),
    "184818": ("23 Water", "River_India_Birds", "bed", "river with birds"),
    "555458": ("23 Water", "Waterfall_Close", "bed", "waterfall, close"),
    "698306": ("23 Water", "Waterfall_Close", "bed", "small waterfall, close"),
    "348822": ("23 Water", "Waterfall_Distant", "bed", "waterfall in the distance"),
    "507710": ("23 Water", "Waterfall_Distant", "bed", "waterfall in the distance"),
    "466955": ("23 Water", "Night_River_Crickets", "bed", "night by a river: crickets and frogs"),
    "162116": ("23 Water", "Water_Drips", "bed", "water dripping in a large echoey space"),
    "398039": ("23 Water", "Splash", "oneshot", "splash"),
    "829676": ("23 Water", "Splash", "oneshot", "splash"),
    "560886": ("23 Water", "Splash", "oneshot", "big piece of ice dropped in water"),
    # ---------------------------------------------------------------- 24 Temple & Town
    "78974": ("24 Temple & Town", "Conch_Shankh", "oneshot", "conch (shankh) blown"),
    "507468": ("24 Temple & Town", "Mountain_Horn", "oneshot", "alphorn - long mountain horn call"),
    "34870": ("24 Temple & Town", "Temple_Bells_Real", "oneshot", "Shiva temple bells"),
    "466652": ("24 Temple & Town", "Temple_Bells_Real", "oneshot", "Indian temple bell"),
    "462735": ("24 Temple & Town", "Monastery_Chant","excerpt", "monks chanting / monastery music"),
    "423510": ("24 Temple & Town", "Crowd_India", "bed", "outdoor crowd, India"),
    "462737": ("24 Temple & Town", "Town_India", "bed", "busy Indian town"),
    "418780": ("24 Temple & Town", "Dhol_Wedding","excerpt", "wedding dhols"),
    "728135": ("24 Temple & Town", "Dhol_Street","excerpt", "dhol in the street with singing"),
}
LOOP, X = 30.0, 3.0


def load(path):
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(path), "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(float)
    if len(x) and np.abs(x[:, 0] - x[:, 1]).max() > 1e-4:
        if x[:, 0].std() > 0 and x[:, 1].std() > 0 and np.corrcoef(x[:, 0], x[:, 1])[0, 1] < -0.3:
            x[:, 1] *= -1                                    # one channel recorded with inverted polarity
        mid, side = (x[:, 0] + x[:, 1]) / 2, (x[:, 0] - x[:, 1]) / 2
        c = np.corrcoef(x[:, 0], x[:, 1])[0, 1] if x[:, 0].std() > 0 and x[:, 1].std() > 0 else 1.0
        w = 0.8 if c > 0.4 else 0.5                          # spaced-mic recordings -> narrower, mono-safe
        x = np.stack([mid + w * side, mid - w * side], 1)
    return hp(x, 25, 2)


def env_db(x, win=0.05):
    m = np.abs(x).max(axis=1) if x.ndim == 2 else np.abs(x)
    k = n_(win)
    e = np.sqrt(np.convolve(m ** 2, np.ones(k) / k, "same")) + 1e-9
    return 20 * np.log10(e)


def best_window(x, L, avoid_spikes=True):
    """Start (samples) of the steadiest L-second window (low loudness variation, no clipping, no big spikes)."""
    n = n_(L)
    if len(x) <= n + n_(X):
        return 0
    hop = n_(1.0)
    m = x.mean(axis=1)
    sec = np.array([np.sqrt(np.mean(m[i:i + hop] ** 2)) + 1e-9 for i in range(0, len(m) - hop, hop)])
    db = 20 * np.log10(sec)
    pk = np.array([np.abs(x[i:i + hop]).max() for i in range(0, len(m) - hop, hop)])
    nsec = int((L + X) // 1) + 1
    best, bi = 1e9, 0
    for s in range(0, len(db) - nsec):
        seg = db[s:s + nsec]
        cost = np.std(seg) + (3.0 if pk[s:s + nsec].max() > 0.98 else 0) + max(0, np.median(db) - np.median(seg) - 6) * 0.3
        if avoid_spikes:
            cost += 0.3 * max(0, seg.max() - np.median(seg) - 10)
        if cost < best:
            best, bi = cost, s
    return bi * hop


def make_bed(x, which=0):
    L = LOOP if len(x) / SR >= LOOP + X + 1 else max(8.0, len(x) / SR - X - 0.5)
    if which and len(x) / SR > 3 * (L + X):                  # 2nd variant from another part of a long recording
        half = len(x) // 2
        s = half + best_window(x[half:], L)
    else:
        s = best_window(x, L)
    seg = x[s: s + n_(L + X + 0.2)]
    if len(seg) < n_(L + X):
        return None
    y = seamless(seg, L, X)
    return rms_norm(y, -24.0, -3.0), L


def trim(x, thr_rel=-50, pre=0.02, max_len=None):
    e = env_db(x, 0.01)
    top = e.max()
    idx = np.nonzero(e > top + thr_rel)[0]
    if not len(idx):
        return x
    a, b = max(0, idx[0] - n_(pre)), min(len(x), idx[-1] + n_(0.15))
    y = x[a:b]
    if max_len and len(y) > n_(max_len):
        y = y[: n_(max_len)]
    return fade(y, 0.003, min(0.3, len(y) / SR / 4))


def events(x, band=None, max_n=6, max_len=3.0, min_len=0.06, gap=0.25):
    """Cut a recording into separate events (door slams, calls, splashes), strongest first."""
    y = bp(x, band[0], band[1], 2) if band else x
    e = env_db(y, 0.02)
    floor = np.percentile(e, 20)
    thr = max(floor + 12, e.max() - 35)
    on = e > thr
    segs, i, n = [], 0, len(on)
    while i < n:
        if not on[i]:
            i += 1
            continue
        j = i
        quiet = 0
        while j < n and quiet < n_(gap):
            quiet = quiet + 1 if not on[j] else 0
            j += 1
        a, b = max(0, i - n_(0.03)), min(n, j - quiet + n_(0.12))
        if (b - a) / SR >= min_len:
            segs.append((a, min(b, a + n_(max_len)), float(e[i:j].max())))
        i = j
    segs.sort(key=lambda s: -s[2])
    out = []
    for a, b, _ in segs[:max_n]:
        out.append(fade(x[a:b], 0.002, min(0.08, (b - a) / SR / 4)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(KIT / "SFX"))
    ap.add_argument("--cc0", default=str(KIT / "Source" / "_cc0"))
    ap.add_argument("--docs", default=str(KIT / "Docs"))
    a = ap.parse_args()
    out, cc0 = Path(a.out), Path(a.cc0)
    manp = cc0 / "manifest.json"
    if not manp.exists():
        print("No field recordings yet - run Tools\\spp_freesound.py first.")
        return
    man = json.load(open(manp, encoding="utf-8"))
    catp = out / "sfx_catalog.json"
    cat = json.load(open(catp, encoding="utf-8")) if catp.exists() else []
    cat = [c for c in cat if not c.get("field")]                 # replace our own earlier entries
    count = {}
    credits = []
    for fid, (category, name, mode, note) in CURATION.items():
        m = man.get(fid)
        if not m or not (cc0 / m["file"]).exists():
            continue
        x = load(cc0 / m["file"])
        if len(x) < n_(0.05):
            continue
        outs = []
        if mode == "bed":
            for w in (0, 1):
                r = make_bed(x, w)
                if r is None or (w and len(x) / SR < 3 * (LOOP + X)):
                    break
                outs.append(("bed", r[0], r[1]))
        elif mode == "excerpt":                               # rhythmic / musical: a clean 30 s piece, not a loop
            st = best_window(x, LOOP, avoid_spikes=False)
            seg = x[st: st + n_(LOOP)]
            outs.append(("one", rms_norm(fade(seg, 1.0, 2.0), -22.0, -3.0), None))
        elif mode == "oneshot":
            outs.append(("one", peak_norm(trim(x, max_len=30.0), -3.0), None))
        elif mode == "events":
            outs += [("one", peak_norm(e, -3.0), None) for e in events(x, max_n=4, max_len=4.0)]
        elif mode == "calls":
            outs += [("one", peak_norm(e, -3.0), None) for e in events(x, band=(900, 9000), max_n=5, max_len=3.5, gap=0.35)]
        d = out / category
        d.mkdir(parents=True, exist_ok=True)
        for kind, y, L in outs:
            count[name] = count.get(name, 0) + 1
            v = count[name]
            fn = f"SPP_{name}" + (f"_LOOP_{round(L)}s" if kind == "bed" else "") + f"_v{v:02d}.wav"
            write_wav(d / fn, y)
            env = env_db(y, 0.05)
            cat.append({"file": f"{category}/{fn}", "category": category, "name": name, "variant": v,
                        "seconds": round(len(y) / SR, 3), "peak": round(float(np.argmax(env)) / SR, 3) if kind == "one" else 0.0,
                        "loop": kind == "bed", "use": f"REAL recording: {note}", "field": True,
                        "source": m["url"], "author": m["author"]})
        credits.append(f"| `{name}` | {note} | [{m['name']}]({m['url']}) | {m['author']} | CC0 |")
        print(f"  {category} {name}: +{len(outs)}  ({m['name'][:40]})", flush=True)
    json.dump(cat, open(catp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    Path(a.docs).mkdir(parents=True, exist_ok=True)
    (Path(a.docs) / "Field_Recordings_Credits.md").write_text(
        "# Field recordings — sources\n\nReal recordings used for the SFX folders 20–24, all **CC0 (public domain)** from freesound.org: "
        "free for any use, no credit required. Listed so we always know where every sound came from.\n\n"
        "| Library sound | What | Original | Recorded by | Licence |\n|---|---|---|---|---|\n" + "\n".join(sorted(credits)) + "\n",
        encoding="utf-8")
    print(f"{sum(count.values())} field sounds added -> {out}")


if __name__ == "__main__":
    main()
