"""
Safar Pahad Parivar - make a sound come from far away (or across the valley).

    .venv\\Scripts\\python.exe Tools\\spp_distance.py "<audio or video file>" [--preset far] [--meters 300] [--out file.wav]

Presets (what they do)
  near     ~10 m   : a touch of air and space, full tone                      (a car door beside the camera)
  mid      ~50 m   : softer top, less bass punch, some reverb, narrower        (a bird in the next tree line)
  far      ~200 m  : dull top, thin, mostly reverb, almost a point in space   (a bus on the road below)
  vfar     ~600 m  : very dull and quiet, reverb-heavy                        (a temple bell from the next village)
  valley   ~400 m  : like 'far' plus distinct echoes off the mountain walls   (a horn / shout across the valley)
--meters N overrides the distance of the preset (1-2000).  --loop keeps a _LOOP_ file seamless (auto for *_LOOP_* names).
Physics used: air absorbs treble with distance, the direct sound drops ~6 dB per doubling while the room/valley
reverb stays, the proximity bass disappears, and the source shrinks to a point (narrow stereo).
Output: 48 kHz 24-bit WAV (by default next to the input in a _distance folder).
"""
import argparse, os, subprocess, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Source" / "sfx"))
from synth import SR, lp, hp, reverb, write_wav, stereo, n_, rng  # noqa

PRESETS = {"near": (10, False), "mid": (50, False), "far": (200, False), "vfar": (600, False), "valley": (400, True)}


def load(path, start=None, dur=None):
    cmd = ["ffmpeg", "-nostdin", "-v", "error"]
    if start:
        cmd += ["-ss", f"{start:.3f}"]
    if dur:
        cmd += ["-t", f"{dur:.3f}"]
    cmd += ["-i", path, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).astype(float)


def echoes(x, r, dist):
    """Discrete reflections off far mountain walls (each later one darker and quieter)."""
    base = 0.25 + dist / 900.0
    delays = [base, base * 2.1 + 0.15, base * 3.3 + 0.3, base * 4.8 + 0.4]
    gains = [0.38, 0.24, 0.14, 0.08]
    tail = n_(delays[-1] + 0.1)
    y = np.concatenate([x, np.zeros((tail, 2))])
    src = x
    for k, (dl, g) in enumerate(zip(delays, gains)):
        src = lp(src, 2600 / (1 + 0.6 * k))
        i = n_(dl)
        p = [-0.6, 0.5, -0.35, 0.3][k]
        y[i:i + len(src), 0] += src[:, 0] * g * (1 - p) / 1.3
        y[i:i + len(src), 1] += src[:, 1] * g * (1 + p) / 1.3
    return y


def distance(x, meters=200, valley=False, seed=1):
    r = rng("distance", meters, valley, seed)
    d = float(np.clip(meters, 1, 2000))
    x = stereo(x)
    # 1. point source: narrow the stereo image the further it is
    w = 1.0 / (1.0 + d / 40.0)
    mid, side = (x[:, 0] + x[:, 1]) / 2, (x[:, 0] - x[:, 1]) / 2
    x = np.stack([mid + w * side, mid - w * side], 1)
    # 2. air absorption (treble) + no proximity bass
    fc = 16000 * (30.0 / (30.0 + d)) ** 0.7
    direct = lp(x, fc, 2)
    direct = hp(direct, 40 + 160 * d / (d + 150), 2)
    # 3. level: ~ -4.5 dB per doubling of distance (relative to 10 m; real life is -6, but the ear/mix expects less),
    #    capped so it stays usable
    g = 10 ** (-min(26.0, 4.5 * np.log2(max(d, 10) / 10.0)) / 20)
    # 4. more of the space than of the source
    wet_share = d / (d + 60.0)
    t60 = 1.2 + 1.8 * d / (d + 300.0)
    wet = reverb(direct, r, t60, 1.0, damp=max(1500, fc * 0.8), pre=0.01 + min(0.08, d / 4000.0), width=0.55)
    y = np.zeros_like(wet)
    y[: len(direct)] += direct * g * (1 - 0.6 * wet_share)
    y += wet * g * (0.35 + 0.9 * wet_share)
    if valley:
        y = echoes(y, r, d)
    return y


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--preset", default="far", choices=list(PRESETS))
    ap.add_argument("--meters", type=float)
    ap.add_argument("--start", type=float)
    ap.add_argument("--dur", type=float)
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--keep-level", action="store_true", help="don't make it quieter (only the tone/space changes)")
    ap.add_argument("--out")
    a = ap.parse_args()
    meters, valley = PRESETS[a.preset]
    meters = a.meters or meters
    x = load(a.input, a.start, a.dur)
    loop = a.loop or "_LOOP_" in os.path.basename(a.input)
    if loop:
        # process the loop twice back to back and keep the second pass: it already contains the reverb/echo tail of
        # the previous pass, exactly as when the loop repeats on the timeline -> still seamless
        yy = distance(np.concatenate([x, x]), meters, valley)
        y = yy[len(x): 2 * len(x)].copy()
    else:
        y = distance(x, meters, valley)
        a_ = np.max(np.abs(y), axis=1)
        idx = np.nonzero(a_ > 10 ** (-70 / 20))[0]
        y = y[: (idx[-1] + n_(0.05)) if len(idx) else len(y)]
    if a.keep_level:
        y = y * (np.sqrt(np.mean(x ** 2)) / (np.sqrt(np.mean(y ** 2)) + 1e-9))
    y = np.clip(y, -1, 1)
    if a.out:
        out = a.out
    else:
        d = os.path.join(os.path.dirname(os.path.abspath(a.input)), "_distance")
        os.makedirs(d, exist_ok=True)
        out = os.path.join(d, os.path.splitext(os.path.basename(a.input))[0] + f"_{a.preset}{int(meters)}m.wav")
    write_wav(out, y)
    print(out)


if __name__ == "__main__":
    main()
