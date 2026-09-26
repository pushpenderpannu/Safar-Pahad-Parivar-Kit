"""
Safar Pahad Parivar - find the musical key of a piece of music (any file: our music, Epidemic Sound, a phone video...).

    .venv\\Scripts\\python.exe Tools\\spp_key.py "<file>" [--start 60] [--dur 20]
        -> key, confidence and the runners-up, e.g.  "D  (0.84)   also: Bm 0.71, A 0.62"
    .venv\\Scripts\\python.exe Tools\\spp_key.py render bridge D E --out x.wav     (swell: only the new key, tail: only the old)
        -> makes a key-matched transition with the recorded orchestra (used by 'Music - Key Transition' in Resolve)

Method: a pitch-class profile (how much of each of the 12 notes sounds, weighted towards the bass and the long notes)
compared with the classic major / minor key profiles (Krumhansl-Kessler + Albrecht-Shanahan).  Tanpura / drone
music is handled well because the drone is the tonic.  Relative keys (D major / B minor) share their notes, so the
runner-up is shown too - either works for a transition.
"""
import argparse, json, subprocess, sys
import numpy as np

NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
# major / minor profiles (average of Krumhansl-Kessler 1990 and Albrecht-Shanahan 2013, normalised)
KK_MAJ = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
KK_MIN = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
AS_MAJ = np.array([0.238, 0.006, 0.111, 0.006, 0.137, 0.094, 0.016, 0.214, 0.009, 0.080, 0.008, 0.081])
AS_MIN = np.array([0.220, 0.006, 0.104, 0.123, 0.019, 0.103, 0.012, 0.214, 0.062, 0.022, 0.061, 0.052])


def _z(v):
    v = np.asarray(v, float)
    return (v - v.mean()) / (v.std() + 1e-12)


PROF = {"maj": (_z(KK_MAJ) + _z(AS_MAJ)) / 2, "min": (_z(KK_MIN) + _z(AS_MIN)) / 2}
SR = 22050


def key_name(pc, q):
    return NAMES[pc] + ("m" if q == "min" else "")


def parse_key(k):
    """'F#m' -> (6, 'min'); 'Db' -> (1, 'maj')."""
    k = k.strip()
    q = "min" if k.endswith("m") and not k.endswith("maj") else "maj"
    root = k[:-1] if q == "min" else k
    alias = {"Db": "C#", "D#": "Eb", "Gb": "F#", "G#": "Ab", "A#": "Bb", "Cb": "B", "E#": "F", "Fb": "E", "B#": "C"}
    root = alias.get(root, root)
    return NAMES.index(root), q


def load(path, start=None, dur=None):
    cmd = ["ffmpeg", "-nostdin", "-v", "error"]
    if start:
        cmd += ["-ss", f"{max(0.0, start):.3f}"]
    if dur:
        cmd += ["-t", f"{dur:.3f}"]
    cmd += ["-i", path, "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32).astype(float)


def chroma(x):
    """Pitch-class energy from a semitone spectrum (MIDI 28-96) with the overtones of lower notes removed
    (the 3rd / 5th harmonics of a bass note otherwise fake a fifth / major third), bass weighted."""
    n, hop = 8192, 2048
    if len(x) < n:
        x = np.pad(x, (0, n - len(x)))
    win = np.hanning(n)
    f = np.fft.rfftfreq(n, 1 / SR)
    ok = (f >= 38) & (f <= 5000)
    midi = 69 + 12 * np.log2(f[ok] / 440.0)
    mi = np.round(midi).astype(int)
    inb = (mi >= 28) & (mi <= 108) & (np.abs(midi - mi) < 0.35)
    frames = [x[i:i + n] for i in range(0, len(x) - n + 1, hop)]
    if not frames:
        return np.zeros(12)
    M = np.sqrt(np.array([np.abs(np.fft.rfft(fr * win))[ok] for fr in frames]))
    M = np.minimum(M, np.median(M, axis=0, keepdims=True) * 4)   # one loud hit shouldn't decide the key
    spec = M.mean(axis=0)
    S = np.zeros(109)
    np.add.at(S, mi[inb], spec[inb])
    for m in range(28, 97):                                     # greedy overtone removal, low to high
        if S[m] <= 0:
            continue
        for iv, k in ((12, 0.55), (19, 0.45), (24, 0.35), (28, 0.3), (31, 0.25), (34, 0.2), (36, 0.18)):
            if m + iv <= 108:
                S[m + iv] = max(0.0, S[m + iv] - S[m] * k)
    acc = np.zeros(12)
    for m in range(28, 97):
        acc[m % 12] += S[m] * (1.6 if m < 60 else 1.0)
    return acc / (acc.sum() + 1e-12)


def detect(x):
    c = _z(chroma(x))
    scores = []
    for q in ("maj", "min"):
        for pc in range(12):
            scores.append((float(np.corrcoef(c, np.roll(PROF[q], pc))[0, 1]), pc, q))
    scores.sort(reverse=True)
    return scores


def render(argv):
    ap = argparse.ArgumentParser(prog="spp_key.py render")
    ap.add_argument("kind", choices=["bridge", "swell", "tail"])
    ap.add_argument("keys", nargs="+", help="bridge: FROM TO   swell: TO   tail: FROM")
    ap.add_argument("--v", type=int, default=0, help="variation (swell 0-2, tail 0-1, bridge 0-1)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--samples", help="recorded-instrument folder (default <kit>/Source/_vsco)")
    a = ap.parse_args(argv)
    from pathlib import Path
    kit = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(kit / "Source" / "sfx"))
    import sfx_gen as G
    ka = kb = None
    if a.kind == "bridge":
        ka, kb = a.keys[0], a.keys[1]
    elif a.kind == "swell":
        kb = a.keys[0]
    else:
        ka = a.keys[0]
    fix = lambda k: None if k is None else key_name(*parse_key(k))
    x, land = G.render_transition(a.kind, fix(ka), fix(kb), a.v, samples=a.samples)
    G.write_wav(a.out, x)
    print(json.dumps({"file": a.out, "land": land, "seconds": round(len(x) / 48000, 2)}))


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "render":
        return render(sys.argv[2:])
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--start", type=float)
    ap.add_argument("--dur", type=float)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    x = load(a.file, a.start, a.dur)
    if len(x) < SR:
        raise SystemExit("too short / no audio")
    s = detect(x)
    best = s[0]
    out = {"key": key_name(best[1], best[2]), "confidence": round(best[0], 3),
           "also": [[key_name(pc, q), round(v, 3)] for v, pc, q in s[1:4]]}
    if a.json:
        print(json.dumps(out))
    else:
        print(f"{out['key']}  ({out['confidence']:.2f})   also: " + ", ".join(f"{k} {v:.2f}" for k, v in out["also"]))


if __name__ == "__main__":
    main()
