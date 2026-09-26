"""
Safar Pahad Parivar - Moment finder.  Listens to every clip of a trip and finds the family moments:
laughter, kids shouting / cheering, singing, "wow / papa dekho" reactions - plus a searchable Hindi transcript
of everything anyone said.

    .venv\\Scripts\\python.exe Tools\\spp_moments.py "<trip folder>"            # analyse (incremental, cached)
    .venv\\Scripts\\python.exe Tools\\spp_moments.py "<trip folder>" --report   # only rewrite the reports
    .venv\\Scripts\\python.exe Tools\\spp_moments.py "<trip folder>" --search "बर्फ"

Output in <trip>\\_spp_moments\\
    Moments.md      top moments (ranked), 3 opening candidates, per-day list          <- read this
    Transcript.md   everything that was said, clip by clip, with times                <- Ctrl+F in any editor
    moments.json    the same for the Resolve scripts (markers, best-moments timeline, transcript search)
    clips\\*.json    per-clip cache (speech + sound events); delete one to re-analyse that clip
Engines: faster-whisper large-v3 (speech, GPU) + PANNs CNN14 (AudioSet sound events, CPU).
"""
import argparse, json, os, re, subprocess, sys, time, unicodedata, glob
from pathlib import Path
import numpy as np

VIDEO = (".mp4", ".mov", ".m4v", ".mts", ".3gp")
FAMILY = {  # names as they may be heard / written (Devanagari + roman) -> display name
    "Pihu": ["पिहू", "पीहू", "पिहु", "पीहु", "पीवू", "पिउ", "पीउ", "pihu"],
    "Oju": ["ओजू", "ओजु", "ओझू", "ओजस", "oju", "ojas"],
    "Meenakshi": ["मीनाक्षी", "मीनू", "meenakshi"],
    "Brijesh": ["बृजेश", "ब्रजेश", "ब्रिजेश", "brijesh"],
    "Alka": ["अलका", "alka"],
    "Pushpender": ["पुष्पेंद्र", "पुष्पेन्द्र", "pushpender"],
    "Papa/Mummy": ["पापा", "मम्मी", "मामा", "मामी", "बुआ", "फूफा", "चाचा", "चाची", "papa", "mummy", "mama", "mami"],
}
EXCLAIM = ["वाह", "वॉव", "वाओ", "wow", "अरे", "देखो", "देख", "ओह", "याय", "yay", "हाय", "उफ़", "उफ", "अद्भुत", "कमाल",
           "सुंदर", "खूबसूरत", "मज़ा", "मजा", "जल्दी", "आओ", "चलो", "बर्फ", "झरना", "पानी", "ठंड", "ठंडा", "पहाड़", "नदी",
           "बादल", "बारिश", "जय", "भोले", "महादेव", "हर हर", "पहुँच", "पहुंच", "ऊपर", "नीचे", "beautiful", "amazing", "look",
           "snow", "waterfall"]
HALLUCINATIONS = ["सब्सक्राइब", "subscribe", "धन्यवाद", "thank you for watching", "like और share", "लाइक", "चैनल को"]

# AudioSet classes we care about (PANNs label names) -> our kinds
EVENTS = {
    "laugh": ["Laughter", "Baby laughter", "Giggle", "Snicker", "Belly laugh", "Chuckle, chortle"],
    "kids": ["Child speech, kid speaking", "Children shouting", "Children playing", "Babbling"],
    "shout": ["Shout", "Yell", "Screaming", "Whoop", "Battle cry"],
    "cheer": ["Cheering", "Applause", "Clapping", "Crowd"],
    "sing": ["Singing", "Child singing", "Choir", "Chant", "Humming"],
    "wind": ["Wind noise (microphone)"],
}
SCENE = ["Stream", "Waterfall", "Rain", "Thunderstorm", "Wind", "Bird", "Bird vocalization, bird call, bird song", "Crow",
         "Rooster", "Dog", "Cattle, bovinae", "Goat", "Sheep", "Horse", "Bell", "Church bell", "Chime", "Gong",
         "Vehicle", "Car", "Truck", "Bus", "Motorcycle", "Engine", "Vehicle horn, car horn, honking", "Traffic noise, roadway noise",
         "Music", "Speech", "Crowd", "Fire", "Water", "Ocean", "Footsteps", "Train"]
KIND_LABEL = {"laugh": "Laughter", "kids": "Kids talking", "shout": "Shout / excitement", "cheer": "Cheering",
              "sing": "Singing", "word": "Reaction", "talk": "Talk"}


def log(*a):
    print(*a, flush=True)


def norm(s):
    s = unicodedata.normalize("NFC", s.lower())
    return s.replace("ँ", "ं").replace("़", "")


# ------------------------------------------------------------------ audio
def audio(path, sr):
    cmd = ["ffmpeg", "-nostdin", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


def _yin(w, sr=16000, fmin=70, fmax=700, thr=0.15):
    n = len(w)
    F = np.fft.rfft(w, 2 * n)
    ac = np.fft.irfft(F * np.conj(F))[:n]
    e = np.cumsum(w ** 2)
    tau_max = min(n - 1, sr // fmin)
    taus = np.arange(1, tau_max)
    d = e[-1] + (e[-1] - e[taus - 1]) - 2 * ac[taus]            # difference function (approx.)
    cm = d * taus / (np.cumsum(d) + 1e-12)                        # cumulative mean normalised
    lo = sr // fmax
    idx = np.where(cm[lo:] < thr)[0]
    if not len(idx):
        return None
    k = idx[0] + lo
    while k + 1 < len(cm) and cm[k + 1] < cm[k]:
        k += 1
    return sr / taus[k]


def child_voice(x16, t0, t1):
    """Child / adult guess from the voice pitch (YIN): kids' voices sit mostly above ~270 Hz."""
    seg = x16[int(t0 * 16000): int(t1 * 16000)]
    if len(seg) < 4800:
        return None
    f0s = []
    for i in range(0, len(seg) - 1024, 480):
        w = seg[i:i + 1024].astype(float)
        if np.sqrt(np.mean(w ** 2)) < 0.01:
            continue
        f = _yin(w - w.mean())
        if f:
            f0s.append(f)
    if len(f0s) < 6:
        return None
    m = float(np.median(f0s))
    return "child" if m > 270 else "adult"


# ------------------------------------------------------------------ engines
_DLL = []


def whisper_model():
    if os.name == "nt":
        for d in glob.glob(os.path.join(sys.prefix, "Lib", "site-packages", "nvidia", "*", "bin")):
            try:
                _DLL.append(os.add_dll_directory(d))            # keep the handle, or Windows forgets the folder
                os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")
            except Exception:
                pass
    from faster_whisper import WhisperModel
    try:
        m = WhisperModel("large-v3", device="cuda", compute_type="float16")
        log("speech: large-v3 on GPU")
    except Exception as e:
        log("speech: GPU not available (%s) - CPU, slower" % e)
        m = WhisperModel("large-v3", device="cpu", compute_type="int8")
    return m


def tagger():
    try:
        from panns_inference import AudioTagging, labels
    except Exception as e:
        log("sound events: PANNs not installed (%s) - speech only" % e)
        return None, None
    ck = os.path.join(os.path.expanduser("~"), "panns_data", "Cnn14_mAP=0.431.pth")
    return AudioTagging(checkpoint_path=ck, device="cpu"), labels


def speech(model, x16):
    segs, info = model.transcribe(x16, language="hi", beam_size=5, vad_filter=True, word_timestamps=False,
                                  condition_on_previous_text=False, vad_parameters={"min_silence_duration_ms": 400})
    out = []
    for s in segs:
        t = s.text.strip()
        if not t or s.no_speech_prob > 0.6 or s.avg_logprob < -1.2 or s.compression_ratio > 2.4:
            continue
        if any(h in t.lower() for h in HALLUCINATIONS) and (s.avg_logprob < -0.5 or len(t.split()) <= 3):
            continue
        out.append({"a": round(s.start, 2), "b": round(s.end, 2), "text": t, "conf": round(float(np.exp(s.avg_logprob)), 2),
                    "voice": child_voice(x16, s.start, s.end)})
    return out


def events(at, labels, x32):
    """Per-second probabilities of the event groups (2 s windows, 1 s hop) + clip-level scene tags."""
    if at is None or len(x32) < 32000:
        return {}, []
    win, hop = 64000, 32000
    starts = list(range(0, max(1, len(x32) - win + 1), hop)) or [0]
    frames = np.stack([np.pad(x32[s:s + win], (0, max(0, win - len(x32[s:s + win])))) for s in starts])
    probs = []
    for i in range(0, len(frames), 32):
        p, _ = at.inference(frames[i:i + 32])
        probs.append(p)
    P = np.concatenate(probs)                       # (windows, 527)
    idx = {l: i for i, l in enumerate(labels)}
    ev = {k: [round(float(v), 3) for v in P[:, [idx[n] for n in names if n in idx]].max(axis=1)] for k, names in EVENTS.items()}
    mean = P.mean(axis=0)
    scene = [(labels[i], round(float(mean[i]), 3)) for i in np.argsort(mean)[::-1] if labels[i] in SCENE][:5]
    return ev, [s for s in scene if s[1] > 0.05]


# ------------------------------------------------------------------ moments
def keyword_hits(text):
    t = norm(text)
    names = [n for n, alts in FAMILY.items() if any(norm(a) in t for a in alts)]
    ex = [w for w in EXCLAIM if norm(w) in t]
    return names, ex


def find_moments(clip):
    dur = clip["dur"]
    n = max(1, int(np.ceil(dur)))
    score = np.zeros(n)
    kind = [""] * n
    ev = clip.get("events") or {}
    wind = np.zeros(n)
    for k, w in (("laugh", 1.0), ("shout", 0.8), ("cheer", 0.7), ("sing", 0.7), ("kids", 0.45)):
        v = np.array(ev.get(k, []), float)
        for i, p in enumerate(v):          # window i covers [i, i+2) s
            for j in (i, i + 1):
                if j < n and p * w > score[j]:
                    score[j], kind[j] = p * w, k
    if "wind" in ev:
        for i, p in enumerate(ev["wind"]):
            for j in (i, i + 1):
                if j < n:
                    wind[j] = max(wind[j], p)
    for s in clip["speech"]:
        names, ex = keyword_hits(s["text"])
        bonus = 0.35 * min(2, len(ex)) + 0.25 * min(2, len(names)) + (0.15 if s.get("voice") == "child" else 0)
        for j in range(int(s["a"]), min(n, int(np.ceil(s["b"])))):
            if bonus > 0 and score[j] + bonus * 0.6 > score[j]:
                if bonus * 0.6 > score[j]:
                    kind[j] = "word"
                score[j] += bonus * 0.6
    score *= (1 - 0.5 * np.clip(wind - 0.3, 0, 1))
    out = []
    thr = 0.3
    j = 0
    while j < n:
        if score[j] < thr:
            j += 1
            continue
        k = j
        while k + 1 < n and score[k + 1] >= thr * 0.7:
            k += 1
        seg = score[j:k + 1]
        pk = j + int(np.argmax(seg))
        ks = [kind[i] for i in range(j, k + 1) if kind[i]]
        main = max(set(ks), key=ks.count) if ks else "talk"
        a, b = max(0.0, j - 1.5), min(dur, k + 2.5)
        said = [s for s in clip["speech"] if s["b"] > a and s["a"] < b]
        if said:
            a, b = max(0.0, min(a, said[0]["a"] - 0.3)), min(dur, max(b, said[-1]["b"] + 0.4))
        text = " ".join(s["text"] for s in said)
        names, ex = keyword_hits(text)
        voices = [s.get("voice") for s in said if s.get("voice")]
        out.append({"file": clip["file"], "t": clip.get("t"), "a": round(a, 2), "b": round(b, 2), "peak": pk,
                    "score": round(float(seg.max()) + 0.1 * min(3, len(seg) / 3), 3), "kind": main,
                    "label": KIND_LABEL.get(main, main), "text": text, "names": names, "words": ex,
                    "child": voices.count("child") > 0, "wind": bool(wind[j:k + 1].max() > 0.5)})
        j = k + 1
    return out


# ------------------------------------------------------------------ reports
def hhmm(t, tz):
    return time.strftime("%d %b %H:%M", time.gmtime(t + tz * 3600)) if t else "?"


def mmss(s):
    return "%d:%02d" % (int(s) // 60, int(s) % 60)


def write_reports(trip, clips, moments, tz):
    out = Path(trip) / "_spp_moments"
    moments.sort(key=lambda m: -m["score"])
    top = moments[:40]
    opens = []
    for m in moments:                     # 3 opening candidates: short, strong, kids involved, different kinds
        if len(opens) == 3:
            break
        if m["b"] - m["a"] <= 12 and (m["child"] or m["kind"] in ("laugh", "shout", "cheer")) and not m["wind"] \
                and all(o["kind"] != m["kind"] or o["file"] != m["file"] for o in opens):
            opens.append(m)
    L = ["# Moments — " + os.path.basename(trip), "",
         f"{len(clips)} clips analysed, {len(moments)} moments found. Markers in Resolve: **Moments - Add Markers**; "
         "a timeline of the best ones: **Moments - Best Moments Timeline**; search what was said: **Moments - Search Transcript**.", "",
         "## Opening candidates (cold open, first 15 s)", ""]
    for i, m in enumerate(opens, 1):
        L.append(f"{i}. **{m['label']}** — `{os.path.basename(m['file'])}` {mmss(m['a'])}–{mmss(m['b'])} "
                 f"({hhmm(m['t'], tz)})" + (f" — “{m['text']}”" if m["text"] else ""))
    L += ["", "## Top moments", "", "| # | Score | Kind | Clip | In–Out | When | Who / words | What was said |", "|---|---|---|---|---|---|---|---|"]
    for i, m in enumerate(top, 1):
        who = ", ".join(m["names"] + (["child voice"] if m["child"] else []) + m["words"][:3])
        L.append(f"| {i} | {m['score']:.2f} | {m['label']}{' (wind)' if m['wind'] else ''} | `{os.path.basename(m['file'])}` | "
                 f"{mmss(m['a'])}–{mmss(m['b'])} | {hhmm(m['t'], tz)} | {who} | {m['text'][:120]} |")
    L += ["", "## By day", ""]
    days = {}
    for m in sorted(moments, key=lambda m: ((m["t"] or 0) + m["a"])):
        days.setdefault(hhmm(m["t"], tz)[:6], []).append(m)
    for d, ms in days.items():
        L.append(f"**{d}** — " + ", ".join(f"{m['label']} `{os.path.basename(m['file'])}` {mmss(m['a'])}" for m in ms[:25]))
        L.append("")
    (out / "Moments.md").write_text("\n".join(L), encoding="utf-8")
    T = ["# Transcript — " + os.path.basename(trip), "",
         "Everything the microphones heard, clip by clip (Hindi, automatic - expect some mistakes). "
         "`[child]` = a child's voice by pitch.", ""]
    for c in sorted(clips, key=lambda c: c.get("t") or 0):
        if not c["speech"]:
            continue
        tags = ", ".join(s for s, _ in c.get("scene", [])[:3])
        T.append(f"### `{os.path.basename(c['file'])}` — {hhmm(c.get('t'), tz)} — {mmss(c['dur'])}" + (f" — _{tags}_" if tags else ""))
        for s in c["speech"]:
            T.append(f"- {mmss(s['a'])} {'[child] ' if s.get('voice') == 'child' else ''}{s['text']}")
        T.append("")
    (out / "Transcript.md").write_text("\n".join(T), encoding="utf-8")
    json.dump({"trip": trip, "tz": tz, "moments": moments, "opens": opens,
               "clips": [{k: c[k] for k in ("file", "t", "dur", "speech", "scene") if k in c} for c in clips]},
              open(out / "moments.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    return out


# ------------------------------------------------------------------ main
def clip_list(trip):
    idx = Path(trip) / "_spp_gps_index.json"
    tz, times = 5.5, {}
    if idx.exists():
        j = json.load(open(idx, encoding="utf-8"))
        tz = j.get("tz", 5.5)
        times = {os.path.normcase(os.path.join(trip, m["file"])): (m.get("t"), m.get("dur")) for m in j.get("media", [])}
    files = []
    for r, d, f in os.walk(trip):
        if "_spp_moments" in r or os.sep + "Exports" in r:
            continue
        for x in f:
            if x.lower().endswith(VIDEO):
                p = os.path.join(r, x)
                t, du = times.get(os.path.normcase(p), (None, None))
                files.append((p, t or os.path.getmtime(p), du))
    return sorted(files, key=lambda f: f[1]), tz


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trip")
    ap.add_argument("--report", action="store_true", help="only rebuild the reports from the cache")
    ap.add_argument("--search")
    a = ap.parse_args()
    trip = os.path.abspath(a.trip)
    cache = Path(trip) / "_spp_moments" / "clips"
    cache.mkdir(parents=True, exist_ok=True)
    files, tz = clip_list(trip)
    if a.search:
        q = norm(a.search)
        mj = json.load(open(Path(trip) / "_spp_moments" / "moments.json", encoding="utf-8"))
        for c in mj["clips"]:
            for s in c["speech"]:
                if q in norm(s["text"]):
                    print(f"{os.path.basename(c['file'])}  {mmss(s['a'])}  {s['text']}")
        return
    model = None
    at = labels = None
    ck = os.path.join(os.path.expanduser("~"), "panns_data", "Cnn14_mAP=0.431.pth")
    if not a.report and os.path.exists(ck):
        at, labels = tagger()
    elif not a.report:
        log("sound events: model not downloaded yet - speech only for now (re-run later to add laughter / cheering)")
    clips = []
    t0 = time.time()
    for i, (p, t, du) in enumerate(files):
        st = os.stat(p)
        cf = cache / (re.sub(r"[^\w.-]", "_", os.path.relpath(p, trip)) + ".json")
        if cf.exists():
            c = json.load(open(cf, encoding="utf-8"))
            if c.get("size") == st.st_size:
                if c.get("vv") != 2 and not a.report and c["speech"]:          # voice guess from an older version
                    x16 = audio(p, 16000)
                    for sp in c["speech"]:
                        sp["voice"] = child_voice(x16, sp["a"], sp["b"])
                    c["speech"] = [sp for sp in c["speech"] if not (any(h in sp["text"].lower() for h in HALLUCINATIONS)
                                                                    and len(sp["text"].split()) <= 3)]
                    c["vv"] = 2
                    json.dump(c, open(cf, "w", encoding="utf-8"), ensure_ascii=False)
                if at is not None and not c.get("events") and not a.report:      # speech done earlier, add sound events now
                    c["events"], c["scene"] = events(at, labels, audio(p, 32000))
                    json.dump(c, open(cf, "w", encoding="utf-8"), ensure_ascii=False)
                    log(f"[{i + 1}/{len(files)}] +events {os.path.basename(p)}")
                clips.append(c)
                continue
        if a.report:
            continue
        if model is None:
            model = whisper_model()
        x16 = audio(p, 16000)
        if len(x16) < 8000:
            continue
        c = {"file": p, "t": t, "dur": round(len(x16) / 16000, 2), "size": st.st_size, "vv": 2}
        c["speech"] = speech(model, x16)
        x32 = audio(p, 32000) if at is not None else np.zeros(0)
        c["events"], c["scene"] = events(at, labels, x32)
        json.dump(c, open(cf, "w", encoding="utf-8"), ensure_ascii=False)
        clips.append(c)
        log(f"[{i + 1}/{len(files)}] {os.path.basename(p)}  {c['dur']:.0f}s  speech {len(c['speech'])}  "
            f"{', '.join(s for s, _ in c['scene'][:2])}  ({time.time() - t0:.0f}s)")
    moments = [m for c in clips for m in find_moments(c)]
    out = write_reports(trip, clips, moments, tz)
    log(f"{len(moments)} moments -> {out}")


if __name__ == "__main__":
    main()
