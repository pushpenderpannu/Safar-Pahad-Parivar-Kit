"""
Safar Pahad Parivar - small sound-synthesis toolkit (numpy + scipy) used by sfx_gen.py.
Everything is deterministic (seeded), so the whole library can be regenerated bit-identically.
Signals are float arrays: mono shape (n,), stereo shape (n, 2). Sample rate 48 kHz.
"""
import math, struct, zlib
import numpy as np
from scipy import signal

SR = 48000


def rng(*key):
    return np.random.default_rng(zlib.crc32("|".join(map(str, key)).encode()))


def n_(d):
    return max(1, int(round(d * SR)))


def tt(d):
    return np.arange(n_(d)) / SR


# ---------------------------------------------------------------- noise
def white(d, r):
    return r.standard_normal(n_(d))


def pink(d, r):
    n = n_(d)
    X = np.fft.rfft(r.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    f[0] = f[1]
    y = np.fft.irfft(X / np.sqrt(f), n)
    return y / (np.std(y) + 1e-12)


def brown(d, r):
    n = n_(d)
    X = np.fft.rfft(r.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    f[0] = f[1]
    X = X / f
    X[f < 15] = 0
    y = np.fft.irfft(X, n)
    return y / (np.std(y) + 1e-12)


def smooth_noise(d, r, rate):
    """Slow random control signal in [-1, 1] changing about `rate` times per second."""
    n = n_(d)
    k = max(4, int(d * rate) + 4)
    pts = r.uniform(-1, 1, k)
    x = np.linspace(0, k - 3, n)
    i = np.floor(x).astype(int)
    f = x - i
    # cosine interpolation
    w = (1 - np.cos(np.pi * f)) / 2
    return pts[i] * (1 - w) + pts[i + 1] * w


# ---------------------------------------------------------------- filters
def _sos(kind, f, order=2):
    nyq = SR / 2
    if kind == "bp":
        lo, hi = max(10, f[0]), min(nyq * 0.98, f[1])
        return signal.butter(order, [lo / nyq, hi / nyq], btype="band", output="sos")
    f = min(max(f, 10), nyq * 0.98)
    return signal.butter(order, f / nyq, btype=kind, output="sos")


def lp(x, f, order=2):
    return signal.sosfilt(_sos("low", f, order), x, axis=0)


def hp(x, f, order=2):
    return signal.sosfilt(_sos("high", f, order), x, axis=0)


def bp(x, lo, hi, order=2):
    return signal.sosfilt(_sos("bp", (lo, hi), order), x, axis=0)


def reson(x, f, q=20):
    b, a = signal.iirpeak(min(f, SR / 2 * 0.95) / (SR / 2), q)
    return signal.lfilter(b, a, x, axis=0)


def sweep(x, fc, bw_oct=0.8, bands=28, fmin=80, fmax=16000):
    """Time-varying band-pass: crossfades a bank of fixed band-passes following the curve fc (Hz, per sample)."""
    fc = np.broadcast_to(np.asarray(fc, float), (len(x),))
    centers = np.geomspace(fmin, fmax, bands)
    half = 2 ** (bw_oct / 2)
    outs = [bp(x, c / half, c * half, 2) for c in centers]
    pos = np.interp(np.log(np.clip(fc, fmin, fmax)), np.log(centers), np.arange(bands))
    i0 = np.floor(pos).astype(int)
    i1 = np.minimum(i0 + 1, bands - 1)
    fr = pos - i0
    stack = np.stack(outs)
    idx = np.arange(len(x))
    return stack[i0, idx] * (1 - fr) + stack[i1, idx] * fr


# ---------------------------------------------------------------- envelopes & oscillators
def env_exp(d, tau, attack=0.002):
    t = tt(d)
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    return a * np.exp(-np.maximum(t - attack, 0) / tau)


def env_curve(d, pts):
    """Piecewise-linear envelope from [(time, value), ...]."""
    t = tt(d)
    xs, ys = zip(*pts)
    return np.interp(t, xs, ys)


def osc(freq, d, kind="sine", phase=0.0):
    f = np.broadcast_to(np.asarray(freq, float), (n_(d),))
    ph = 2 * np.pi * np.cumsum(f) / SR + phase
    if kind == "sine":
        return np.sin(ph)
    if kind == "tri":
        return 2 / np.pi * np.arcsin(np.sin(ph))
    if kind == "saw":
        return 2 * ((ph / (2 * np.pi)) % 1) - 1
    if kind == "square":
        return np.sign(np.sin(ph))
    raise ValueError(kind)


def fm(fc, ratio, index, d, idx_env=None, amp_env=None):
    fm_ = osc(fc * ratio, d)
    ie = index * (idx_env if idx_env is not None else 1.0)
    f = fc + ie * fc * ratio * fm_
    y = osc(f, d)
    return y * (amp_env if amp_env is not None else 1.0)


def partials(f0, ratios, amps, decays, d, detune=0.0, r=None):
    """Additive bell/marimba: sum of decaying sine partials (optionally with slow beating)."""
    t = tt(d)
    y = np.zeros_like(t)
    for k, (ra, am, de) in enumerate(zip(ratios, amps, decays)):
        f = f0 * ra
        if f > SR / 2 * 0.9:
            continue
        ph = r.uniform(0, 2 * np.pi) if r is not None else 0
        y += am * np.sin(2 * np.pi * f * t + ph) * np.exp(-t / de)
        if detune:
            y += am * 0.5 * np.sin(2 * np.pi * f * (1 + detune / (k + 1)) * t + ph) * np.exp(-t / de)
    a = np.clip(t / 0.0015, 0, 1)
    return y * a


# ---------------------------------------------------------------- space
def pan(x, p):
    """Mono -> stereo, p in [-1, 1] (scalar or per-sample), equal-power."""
    p = np.broadcast_to(np.asarray(p, float), x.shape)
    a = (p + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], axis=1)


def widen(x, r, amount=0.5, max_ms=12):
    """Mono -> stereo with gentle decorrelation (short random delays)."""
    dl = int(r.uniform(3, max_ms) * SR / 1000)
    y = np.concatenate([np.zeros(dl), x])[: len(x)]
    L = x * (1 - amount / 2) + y * amount / 2
    R = x * (1 - amount / 2) - y * amount / 2 * 0.6 + np.roll(y, dl // 2) * amount / 3
    return np.stack([L, R], axis=1)


def stereo(x):
    return x if x.ndim == 2 else np.stack([x, x], axis=1)


def reverb(x, r, t60=1.2, mix=0.25, damp=7000, pre=0.012, width=1.0):
    """Convolution reverb with a synthetic decaying-noise impulse response."""
    x = stereo(x)
    L = n_(t60 * 1.2)
    t = np.arange(L) / SR
    envr = np.exp(-6.9 * t / t60)
    irs = []
    for ch in range(2):
        nz = r.standard_normal(L) * envr
        # progressively darker tail
        nz = lp(nz, damp) * 0.6 + lp(nz, damp / 3) * 0.4
        irs.append(nz)
    irL, irR = irs
    irR = irL * (1 - width) + irR * width
    pd = n_(pre)
    irL = np.concatenate([np.zeros(pd), irL])
    irR = np.concatenate([np.zeros(pd), irR])
    n = len(x) + len(irL) - 1
    wet = np.stack([signal.fftconvolve(x[:, 0], irL)[:n], signal.fftconvolve(x[:, 1], irR)[:n]], axis=1)
    wet /= (np.sqrt(np.sum(irL ** 2)) + 1e-9)
    dry = np.zeros_like(wet)
    dry[: len(x)] = x
    return dry * (1 - mix) + wet * mix


# ---------------------------------------------------------------- assembly
def canvas(d):
    return np.zeros((n_(d), 2))


def put(buf, x, t, gain=1.0):
    """Mix x into buf at time t (seconds); grows nothing - clipped at the end."""
    x = stereo(x) * gain
    i = n_(t) if t > 0 else 0
    if i >= len(buf):
        return buf
    m = min(len(x), len(buf) - i)
    buf[i:i + m] += x[:m]
    return buf


def fade(x, fin=0.003, fout=0.01):
    x = x.copy()
    a, b = n_(fin), n_(fout)
    if a > 1:
        x[:a] *= np.linspace(0, 1, a)[:, None] if x.ndim == 2 else np.linspace(0, 1, a)
    if b > 1:
        x[-b:] *= np.linspace(1, 0, b)[:, None] if x.ndim == 2 else np.linspace(1, 0, b)
    return x


def trim_silence(x, thr_db=-70, keep=0.02):
    a = np.max(np.abs(stereo(x)), axis=1)
    idx = np.nonzero(a > 10 ** (thr_db / 20))[0]
    if not len(idx):
        return x
    end = min(len(x), idx[-1] + n_(keep))
    return x[:end]


def peak_norm(x, db=-3.0):
    p = np.max(np.abs(x)) + 1e-12
    return x * (10 ** (db / 20) / p)


def rms_norm(x, db=-24.0, ceiling=-3.0):
    r = np.sqrt(np.mean(x ** 2)) + 1e-12
    y = x * (10 ** (db / 20) / r)
    p = np.max(np.abs(y))
    c = 10 ** (ceiling / 20)
    if p > c:  # soft-limit the rare peaks instead of lowering the whole bed
        y = np.tanh(y / c) * c
    return y


def seamless(x, L, X=0.4):
    """Make a perfect loop of length L seconds from a longer signal (needs len >= L+X)."""
    Ls, Xs = n_(L), n_(X)
    x = stereo(x)
    assert len(x) >= Ls + Xs, "source too short for seamless loop"
    y = x[:Ls].copy()
    ramp = np.linspace(0, np.pi / 2, Xs)[:, None]
    y[:Xs] = x[:Xs] * np.sin(ramp) + x[Ls:Ls + Xs] * np.cos(ramp)
    return y


def write_wav(path, x, bits=24):
    x = np.clip(stereo(x), -1, 1)
    if bits == 24:
        i = np.round(x * 8388607).astype("<i4").reshape(-1)
        b = i.view(np.uint8).reshape(-1, 4)[:, :3].tobytes()
    else:
        b = np.round(x * 32767).astype("<i2").reshape(-1).tobytes()
    ch, bps = 2, bits // 8
    hdr = b"RIFF" + struct.pack("<I", 36 + len(b)) + b"WAVE"
    hdr += b"fmt " + struct.pack("<IHHIIHH", 16, 1, ch, SR, SR * ch * bps, ch * bps, bits)
    hdr += b"data" + struct.pack("<I", len(b))
    with open(path, "wb") as fh:
        fh.write(hdr + b)
