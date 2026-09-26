"""
Safar Pahad Parivar - make a voice sound like a phone call.

    .venv\\Scripts\\python.exe Tools\\spp_phone_voice.py "<voice file>" [--style mobile|landline|speaker|walkie] [--noise] [--out file.wav]

Styles
  mobile    today's mobile call: narrow band, codec grit, a little compression            (default)
  landline  old PSTN phone: slightly warmer, faint hum and crackle
  speaker   phone on loudspeaker in a room: tinny + small-room echo
  walkie    walkie-talkie / radio: very narrow, driven, squelch at start and end
--noise adds a faint line hiss.   --dropouts adds the odd tiny network glitch (mobile only).
Input can be any audio or video file (ffmpeg decodes it). Output: 48 kHz 24-bit WAV next to the input.
Tip: in Resolve you can also do it live on a track - see Docs\\SPP_Kit_Guide.md ("Phone voice").
"""
import argparse, os, subprocess, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Source" / "sfx"))
from synth import SR, lp, hp, bp, reson, white, rng, reverb, write_wav, stereo, n_, smooth_noise  # noqa


def load(path, start=None, dur=None):
    cmd = ["ffmpeg", "-nostdin", "-v", "error"]
    if start:
        cmd += ["-ss", f"{start:.3f}"]
    if dur:
        cmd += ["-t", f"{dur:.3f}"]
    cmd += ["-i", path, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).astype(float)


def compress(x, thr_db=-24, ratio=4, att=0.005, rel=0.12):
    m = np.abs(x).max(axis=1) if x.ndim == 2 else np.abs(x)
    a, r_ = np.exp(-1 / (att * SR)), np.exp(-1 / (rel * SR))
    # envelope follower (vectorised enough: block-wise)
    env = np.empty_like(m)
    e = 0.0
    for i in range(0, len(m), 64):
        blk = m[i:i + 64].max()
        e = a * e + (1 - a) * blk if blk > e else r_ * e + (1 - r_) * blk
        env[i:i + 64] = e
    db = 20 * np.log10(env + 1e-9)
    gain_db = np.minimum(0, (thr_db - db) * (1 - 1 / ratio))
    g = 10 ** (gain_db / 20)
    return x * (g[:, None] if x.ndim == 2 else g)


def mulaw_grit(x, bits=8, mix=0.35):
    mu = 2 ** bits - 1
    y = np.sign(x) * np.log1p(mu * np.abs(x)) / np.log1p(mu)
    y = np.round(y * (mu / 2)) / (mu / 2)
    y = np.sign(y) * (np.expm1(np.abs(y) * np.log1p(mu)) / mu)
    return x * (1 - mix) + y * mix


def band(x, lo, hi, order=4):
    return lp(hp(x, lo, order), hi, order)


def phone(x, style="mobile", noise=False, dropouts=False, seed=1):
    r = rng("phone", seed)
    m = x.mean(axis=1)                      # phones are mono
    m = m / (np.max(np.abs(m)) + 1e-9) * 0.7
    if style == "mobile":
        y = band(m, 320, 3400, 6)
        y = y + reson(y, 1900, 3) * 0.35     # presence bump
        y = compress(y, -26, 4)
        y = mulaw_grit(y, 7, 0.3)
        if dropouts:
            gate = (smooth_noise(len(y) / SR, r, 3) > 0.93).astype(float)
            y = y * (1 - 0.85 * lp(gate, 80))
    elif style == "landline":
        y = band(m, 300, 3000, 4)
        y = y + reson(y, 1200, 2) * 0.25
        y = np.tanh(y * 2.0) / 2.0
        t = np.arange(len(y)) / SR
        y = y + 0.004 * np.sin(2 * np.pi * 50 * t) + bp(white(len(y) / SR, r), 500, 3000) * 0.003 * (smooth_noise(len(y) / SR, r, 6) > 0.8)
    elif style == "speaker":
        y = band(m, 450, 4200, 4)
        y = y + reson(y, 900, 4) * 0.5 + reson(y, 2600, 5) * 0.3
        y = np.tanh(y * 1.6) / 1.6
        y = reverb(y, r, 0.35, 0.28, damp=5000, pre=0.004)[:len(y), 0]
    elif style == "walkie":
        y = band(m, 550, 2500, 6)
        y = np.tanh(y * 6) / 2.2
        sq = bp(white(0.12, r), 800, 3000) * np.linspace(0.5, 0, n_(0.12))
        y = np.concatenate([sq, y, sq[::-1] * 0.8])
    else:
        raise SystemExit("style must be mobile, landline, speaker or walkie")
    if noise:
        y = y + bp(white(len(y) / SR, r), 300, 3400) * 0.003
    # the phone path itself: nothing survives outside the band (removes hiss/grit the distortion created)
    lo, hi = {"mobile": (300, 3400), "landline": (300, 3000), "speaker": (400, 4200), "walkie": (500, 2600)}[style]
    y = band(y, lo, hi, 8)
    y = y / (np.max(np.abs(y)) + 1e-9) * 0.8
    return stereo(y)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--style", default="mobile")
    ap.add_argument("--noise", action="store_true")
    ap.add_argument("--dropouts", action="store_true")
    ap.add_argument("--start", type=float)
    ap.add_argument("--dur", type=float)
    ap.add_argument("--out")
    a = ap.parse_args()
    x = load(a.input, a.start, a.dur)
    y = phone(x, a.style, a.noise, a.dropouts)
    out = a.out or os.path.splitext(a.input)[0] + f"_phone-{a.style}.wav"
    write_wav(out, y)
    print(out)


if __name__ == "__main__":
    main()
