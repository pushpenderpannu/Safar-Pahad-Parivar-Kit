"""
Safar Pahad Parivar - word timing + stress for captions (runs in Tools\\.venv).

Listens to the VO clips, finds when every word is actually spoken, and which words are stressed,
then writes a caption file that the SPP Captions title animates word-by-word.

Called by the Resolve menu script "Captions - Sync Words to VO" (normally you never run this by hand):
    .venv\\Scripts\\python.exe spp_word_timing.py job.json out.json

job.json:
  {"cues":  [{"a": sec, "b": sec, "text": "..."}],        # subtitle track (timeline seconds); may be empty
   "clips": [{"file": path, "tl": sec, "src": sec, "dur": sec}],   # VO clips on the timeline
   "model": "large-v3", "lang": "hi"}
out.json:  {"spp": 1, "cues": [{"a","b","text","w": [[start, end, stress], ...]}]}   (one w per word)

Words wrapped in *stars* in a subtitle are always treated as stressed.
"""
import json, os, re, subprocess, sys, unicodedata, difflib, glob

SR = 16000


def log(*a):
    print(*a, flush=True)


# ------------------------------------------------------------------ audio
def load_clip(c):
    """Clip audio (mono 16 kHz float32) exactly as used on the timeline."""
    import numpy as np
    cmd = ["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{c['src']:.3f}", "-t", f"{c['dur']:.3f}",
           "-i", c["file"], "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


# ------------------------------------------------------------------ text
_DROP = dict.fromkeys(map(ord, "़‌‍।॥"), None)   # nukta, ZWNJ/ZWJ, danda


def norm(s):
    s = unicodedata.normalize("NFC", s).translate(_DROP)
    s = s.replace("ँ", "ं")                        # chandrabindu -> anusvara
    s = re.sub(r"[^\w]", "", s.lower())
    return s


def tokens(text):
    """Same word split as the SPP Captions template (whitespace, line by line)."""
    return [w for ln in text.split("\n") for w in ln.split()]


# ------------------------------------------------------------------ recognition
def cuda_dll_dirs():
    if os.name != "nt":
        return
    for d in glob.glob(os.path.join(sys.prefix, "Lib", "site-packages", "nvidia", "*", "bin")):
        try:
            os.add_dll_directory(d)
        except Exception:
            pass
        os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")


def load_model(name):
    cuda_dll_dirs()
    from faster_whisper import WhisperModel
    try:
        m = WhisperModel(name, device="cuda", compute_type="float16")
        log(f"model {name} on GPU")
        return m
    except Exception as e:
        log(f"GPU not available ({str(e)[:120]}), using CPU - slower")
        return WhisperModel(name, device="cpu", compute_type="int8")


def recognise(model, audio, tl0, lang, prompt):
    segs, _ = model.transcribe(audio, language=lang, word_timestamps=True, beam_size=5,
                               vad_filter=False, condition_on_previous_text=False,
                               initial_prompt=(prompt[-800:] or None))
    words, segments = [], []
    for s in segs:
        segments.append({"a": tl0 + s.start, "b": tl0 + s.end, "text": s.text.strip()})
        for w in (s.words or []):
            t = w.word.strip()
            if t:
                words.append({"w": t, "a": tl0 + w.start, "b": tl0 + w.end})
    return words, segments


# ------------------------------------------------------------------ alignment (known text <-> heard words)
def align(known, heard):
    """known: list of words; heard: [{"w","a","b"}]. Returns [(a,b) or None] per known word."""
    kc, ki, hc, hi = [], [], [], []
    for i, w in enumerate(known):
        for ch in norm(w):
            kc.append(ch); ki.append(i)
    for j, h in enumerate(heard):
        for ch in norm(h["w"]):
            hc.append(ch); hi.append(j)
    hits = [set() for _ in known]
    nmatch = [0] * len(known)
    sm = difflib.SequenceMatcher(None, kc, hc, autojunk=False)
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            hits[ki[blk.a + k]].add(hi[blk.b + k]); nmatch[ki[blk.a + k]] += 1
    out = []
    for i, w in enumerate(known):
        n = max(1, len(norm(w)))
        # at least half of the word's letters must line up, within at most 3 heard words
        if hits[i] and nmatch[i] * 2 >= n and len(hits[i]) <= 3:
            js = sorted(hits[i])
            out.append((heard[js[0]]["a"], heard[js[-1]]["b"]))
        else:
            out.append(None)
    return out


def fill_gaps(times, words, a, b):
    """Interpolate words that could not be matched, by letter count, between known neighbours."""
    n = len(times)
    res = list(times)
    i = 0
    while i < n:
        if res[i] is not None:
            i += 1; continue
        j = i
        while j < n and res[j] is None:
            j += 1
        left = res[i - 1][1] if i > 0 else a
        right = res[j][0] if j < n else b
        if right <= left:
            right = left + 0.25 * (j - i)
        L = [max(1, len(norm(words[k]))) for k in range(i, j)]
        tot, acc = sum(L), 0
        for k, l in zip(range(i, j), L):
            s = left + (right - left) * acc / tot; acc += l
            res[k] = (s, left + (right - left) * acc / tot)
        i = j
    # monotonic, no overlaps, minimum length
    for k in range(n):
        s, e = res[k]
        if k and s < res[k - 1][1]:
            s = res[k - 1][1]
        e = max(e, s + 0.08)
        res[k] = (s, e)
    return res


# ------------------------------------------------------------------ voice trimming
def voiced_floor(audios):
    """Loudness threshold (dB) that separates voice from room noise, from all VO audio."""
    import numpy as np
    db = []
    for _, a in audios:
        n = len(a) // 160
        if n:
            f = a[: n * 160].reshape(n, 160)
            db.append(20 * np.log10(np.sqrt((f * f).mean(1)) + 1e-7))
    db = np.concatenate(db) if db else np.array([-60.0])
    noise, peak = np.percentile(db, 10), np.percentile(db, 99)
    return max(noise + 0.35 * (peak - noise), peak - 38)


def trim_to_voice(spans, audio_at, thr):
    """Move each word's start/end onto where the voice actually is (whisper often folds pauses into words)."""
    import numpy as np
    out = []
    for s, e in spans:
        x = audio_at(s, e)
        n = len(x) // 160
        if n >= 3:
            f = x[: n * 160].reshape(n, 160)
            v = np.nonzero(20 * np.log10(np.sqrt((f * f).mean(1)) + 1e-7) > thr)[0]
            if v.size:
                s2 = s + max(0, v[0] - 2) * 0.01
                e2 = s + min(n, v[-1] + 3) * 0.01
                if e2 - s2 >= 0.08:
                    s, e = s2, e2
        out.append((s, e))
    return out


# ------------------------------------------------------------------ stress
def stress_flags(words, spans, audio_at):
    """Loudness + stretch per word, compared with the rest of its line. Returns 0/1 per word."""
    import numpy as np
    forced = [w.startswith("*") and w.endswith("*") and len(w) > 2 for w in words]
    if any(forced):
        return [1 if f else 0 for f in forced]
    if len(words) < 3:
        return [0] * len(words)
    loud, stretch = [], []
    for w, (s, e) in zip(words, spans):
        x = audio_at(s, e)
        rms = float(np.sqrt(np.mean(x * x))) if x.size else 0.0
        loud.append(20 * np.log10(rms + 1e-6))
        stretch.append((e - s) / max(1, len(norm(w))))
    loud, stretch = np.array(loud), np.array(stretch)

    def z(v):
        sd = v.std()
        return (v - np.median(v)) / sd if sd > 1e-6 else v * 0
    score = z(loud) + 0.6 * z(stretch)
    flags = [0] * len(words)
    for k in np.argsort(-score)[: (2 if len(words) >= 9 else 1)]:
        if score[k] >= 1.3 and len(norm(words[k])) >= 2:
            flags[int(k)] = 1
    return flags


# ------------------------------------------------------------------ main
def main(job_path, out_path):
    import numpy as np
    job = json.load(open(job_path, encoding="utf-8"))
    clips = sorted(job["clips"], key=lambda c: c["tl"])
    cues = sorted(job.get("cues") or [], key=lambda c: c["a"])
    model = load_model(job.get("model", "large-v3"))

    heard, segments, audios = [], [], []
    for n, c in enumerate(clips, 1):
        audio = load_clip(c)
        audios.append((c["tl"], audio))
        prompt = " ".join(q["text"].replace("*", "") for q in cues
                          if q["b"] > c["tl"] and q["a"] < c["tl"] + c["dur"])
        w, s = recognise(model, audio, c["tl"], job.get("lang", "hi"), prompt)
        heard += w; segments += s
        log(f"VO clip {n}/{len(clips)}: {len(w)} words heard")

    def audio_at(s, e):
        for tl0, a in audios:
            if tl0 <= s < tl0 + len(a) / SR:
                return a[int((s - tl0) * SR): int((e - tl0) * SR)]
        return np.zeros(0, dtype=np.float32)

    if not cues:  # no subtitles yet -> use what was heard
        cues = [{"a": s["a"], "b": s["b"], "text": s["text"]} for s in segments if s["text"]]
        log(f"No subtitle track: made {len(cues)} captions from the VO (check the spelling!)")

    known, owner = [], []
    for ci, q in enumerate(cues):
        for w in tokens(q["text"]):
            known.append(w.strip("*") or w); owner.append(ci)
    spans = align(known, heard)
    thr = voiced_floor(audios)

    out, k0, matched = [], 0, 0
    for ci, q in enumerate(cues):
        idx = [k for k in range(len(known)) if owner[k] == ci]
        raw_words = tokens(q["text"])
        words = [known[k] for k in idx]
        ts = []
        for k in idx:
            t = spans[k]
            # a heard word far outside its subtitle is a wrong match
            if t and (t[0] < q["a"] - 1.5 or t[1] > q["b"] + 1.5):
                t = None
            ts.append(t); matched += t is not None
        ts = trim_to_voice(fill_gaps(ts, words, q["a"], q["b"]), audio_at, thr)
        st = stress_flags(raw_words, ts, audio_at)
        a = min(q["a"], ts[0][0]) if ts else q["a"]
        b = max(q["b"], ts[-1][1]) if ts else q["b"]
        text = "\n".join(" ".join(w.strip("*") or w for w in ln.split()) for ln in q["text"].split("\n"))
        out.append({"a": round(a, 2), "b": round(b, 2), "text": text,
                    "w": [[round(s, 2), round(e, 2), f] for (s, e), f in zip(ts, st)]})
    json.dump({"spp": 1, "cues": out}, open(out_path, "w", encoding="utf-8"), ensure_ascii=False,
              separators=(",", ":"))
    log(f"Done: {len(out)} captions, {matched}/{len(known)} words matched to the VO, "
        f"{sum(f for c in out for *_, f in c['w'])} stressed")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
