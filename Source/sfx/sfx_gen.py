"""
Safar Pahad Parivar - sound-effects library generator.

    python Source/sfx/sfx_gen.py                 # -> <kit>/SFX  (all sounds, ~2-4 min)
    python Source/sfx/sfx_gen.py --only Phone    # just names/categories containing "Phone"
    python Source/sfx/sfx_gen.py --list

Every sound is synthesised from code with fixed seeds, so the library is identical on every PC and does not need
to be stored in git. Files: 48 kHz / 24-bit stereo WAV,  SFX/<NN Category>/SPP_<Name>_v01.wav
Loops are seamless (end joins start) and named *_LOOP_<len>s.  Stems in "01 Title Kits" are timed to the SPP titles.
"""
import argparse, json, math, os, sys, time
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from synth import *  # noqa

KIT = Path(__file__).resolve().parents[2]


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


PENTA = [74, 76, 78, 81, 83, 86, 88, 90, 93, 95]  # D major pentatonic from D5
eo = lambda x: 1 - (1 - np.clip(x, 0, 1)) ** 3


# ================================================================ building blocks
def click(r, bright=4000, dur=0.003):
    x = white(dur, r) * env_exp(dur, dur / 3, 0.0003)
    return hp(x, bright)


def tick(r, kind="metal", gain=1.0, pitch=1.0):
    """One mechanical dial tick."""
    d = 0.06
    c = click(r, 2500 if kind != "wood" else 900)
    body = np.zeros(n_(d))
    body[: len(c)] += c
    if kind == "metal":
        res = [(2800, 0.012, 0.8), (5200, 0.008, 0.5), (1450, 0.02, 0.3)]
    elif kind == "plastic":
        res = [(1650, 0.008, 0.9), (3300, 0.005, 0.4)]
    elif kind == "wood":
        res = [(820, 0.018, 0.9), (1900, 0.009, 0.4)]
    else:  # soft
        res = [(2300, 0.006, 0.5), (4200, 0.004, 0.3)]
    t = tt(d)
    for f, de, a in res:
        body += a * np.sin(2 * np.pi * f * pitch * r.uniform(0.97, 1.03) * t) * np.exp(-t / de) * 0.35
    return fade(body * gain, 0.0002, 0.005)


def pop(r, f0=700, style="soft", d=0.2):
    t = tt(d)
    if style == "bubble":
        f = f0 * (0.7 + 0.6 * np.clip(t / 0.05, 0, 1))
    else:
        f = f0 * (1.55 - 0.55 * np.clip(t / 0.025, 0, 1)) * (1 - 0.12 * np.clip(t / d, 0, 1))
    y = osc(f, d) * env_exp(d, 0.045 if style != "deep" else 0.07, 0.0015)
    y += 0.25 * osc(f * 2.01, d) * env_exp(d, 0.02, 0.001)
    c = click(r, 3000, 0.0015) * 0.5
    y[: len(c)] += c
    return fade(y, 0.0005, 0.02)


def whoosh(r, d=0.7, kind="air", direction="in", pan_move=True):
    """Filtered-noise whoosh. direction: in (builds to a peak late) | out (starts strong, tails away) | pass."""
    n = pink(d, r) if kind != "deep" else (0.6 * brown(d, r) + 0.4 * pink(d, r))
    u = np.linspace(0, 1, len(n))
    if direction == "in":
        shape = u ** 2.2 * np.exp(-((u - 0.82) ** 2) / 0.02) + u ** 3 * 0.4
        fc = 250 + 3200 * u ** 1.6
    elif direction == "out":
        shape = (1 - u) ** 1.8 * (1 - np.exp(-u / 0.04))
        fc = 3400 - 3000 * u ** 0.7
    else:
        shape = np.exp(-((u - 0.5) ** 2) / 0.035)
        fc = 400 + 2600 * np.exp(-((u - 0.5) ** 2) / 0.05)
    if kind == "deep":
        fc = fc * 0.45
    if kind == "bright":
        fc = fc * 1.6
    y = sweep(n, fc, bw_oct=1.1)
    air = sweep(pink(d, r), fc * 1.9, bw_oct=0.35) * 0.35
    y = (y + air) * shape
    p = (np.linspace(-0.7, 0.7, len(y)) if direction != "out" else np.linspace(0, 0.8, len(y))) if pan_move else 0
    y = pan(y / (np.max(np.abs(y)) + 1e-9), p * r.choice([-1, 1]))
    return fade(y, 0.005, 0.03)


def marimba(r, midi, d=0.9, soft=1.0):
    f0 = hz(midi)
    y = partials(f0, [1, 3.93, 9.2], [1, 0.28 * soft, 0.08 * soft], [0.35, 0.09, 0.03], d, r=r)
    return fade(y, 0.0005, 0.05)


def fm_bell(r, f, d=1.4, bright=3.0):
    t = tt(d)
    ie = np.exp(-t / 0.35)
    return fade(fm(f, 3.5, bright, d, idx_env=ie, amp_env=env_exp(d, d / 3.2, 0.001)), 0.0005, 0.05)


def shimmer(r, d=1.2, density=40, lo=3000, hi=9000):
    y = np.zeros(n_(d))
    for _ in range(int(density * d)):
        t0 = r.uniform(0, d * 0.75)
        f = r.uniform(lo, hi)
        g = partials(f, [1], [r.uniform(0.2, 1)], [r.uniform(0.05, 0.25)], 0.5)
        i = n_(t0)
        m = min(len(g), len(y) - i)
        y[i:i + m] += g[:m]
    env = env_curve(d, [(0, 0), (0.15 * d, 1), (d, 0.2)])
    return pan(y * env, smooth_noise(d, r, 3) * 0.6)


def roll(r, d, kind="metal", ticks_per_s=15, settle=True, ease=True):
    """Odometer/dial roll that slows to a stop over d seconds (matches the titles' ease-out count)."""
    tot = d + 0.35
    y = canvas(tot)
    K = max(6, int(ticks_per_s * d))
    ts = []
    for k in range(1, K):
        # time where the eased progress reaches k/K
        p = k / K
        ts.append(d * (1 - (1 - p) ** (1 / 3)) if ease else d * p)
    for i, t0 in enumerate(ts):
        g = 0.55 + 0.45 * r.random()
        put(y, pan(tick(r, kind, g * 0.8), r.uniform(-0.25, 0.25)), t0)
    # rolling whir, louder while fast
    u = tt(tot)
    speed = np.where(u < d, (1 - np.clip(u / d, 0, 1)) ** 2, 0)
    whir = bp(pink(tot, r), 1500, 5000) * speed * 0.18
    y += pan(whir, 0)
    if settle:
        put(y, pan(tick(r, kind, 1.3, 0.85), 0), d)
        put(y, pan(lp(pop(r, 180, "deep", 0.12), 900) * 0.5, 0), d + 0.004)
    return y


def spin_stop(r, d=1.1, kind="plastic"):
    """Slot-machine digit spin that stops (for date/time digits spinning in)."""
    y = canvas(d + 0.3)
    t, rate = 0.0, 32.0
    while t < d:
        put(y, pan(tick(r, kind, 0.45 + 0.2 * r.random(), 1.2), r.uniform(-0.3, 0.3)), t)
        t += 1 / rate
        rate = max(4.0, rate * 0.9)
    put(y, pan(tick(r, kind, 1.1, 0.9), 0), d)
    return y


def loop_ticks(r, L, rate, kind, jitter=0.02, gear_hum=True, X=0.5):
    tot = L + X + 0.2
    y = canvas(tot)
    t, k = 0.0, 0
    while t < tot:
        acc = 1.0 if k % 4 == 0 else 0.7
        put(y, pan(tick(r, kind, acc * (0.8 + 0.2 * r.random())), r.uniform(-0.2, 0.2)), t)
        t += (1 / rate) * (1 + r.uniform(-jitter, jitter))
        k += 1
    if gear_hum:
        u = tt(tot)
        hum = sum(np.sin(2 * np.pi * rate * h * u) / h for h in range(1, 6)) * 0.02
        hum += bp(brown(tot, r), 80, 400) * 0.04
        y += pan(hum, 0)
    return seamless(y, L, X)


def chord_pad(r, midis, d, attack=0.6, release=1.5):
    t = tt(d)
    y = np.zeros_like(t)
    for m in midis:
        for det in (-0.004, 0.004):
            y += osc(hz(m) * (1 + det), d, "tri") * 0.5
    y = lp(y, 2200)
    env = env_curve(d, [(0, 0), (attack, 1), (max(attack, d - release), 0.8), (d, 0)])
    return widen(y * env / len(midis), r, 0.8)


def temple_bell(r, f0=220, d=7.0):
    ratios = [0.5, 1.0, 1.183, 1.506, 2.0, 2.514, 2.662, 3.011, 4.166, 5.433, 6.796]
    amps = [0.6, 1.0, 0.7, 0.45, 0.8, 0.35, 0.3, 0.25, 0.18, 0.1, 0.06]
    decs = [5.5, 4.0, 3.0, 2.4, 2.2, 1.5, 1.3, 1.0, 0.7, 0.5, 0.35]
    y = partials(f0, ratios, amps, decs, d, detune=0.0025, r=r)
    strike = lp(white(0.02, r) * env_exp(0.02, 0.004), 3000)
    y[: len(strike)] += strike * 0.8
    return fade(y, 0.0005, 0.3)


def small_bell(r, f0=1100, d=1.6):
    y = partials(f0, [1, 2.32, 4.25, 6.63], [1, 0.5, 0.25, 0.1], [0.6, 0.35, 0.18, 0.1], d, detune=0.003, r=r)
    return fade(y, 0.0003, 0.1)


def phone_band(x, lo=300, hi=3400):
    return lp(hp(x, lo, 4), hi, 4)


def crinkle(r, d, density=180, lo=1200, hi=9000, env=None):
    y = np.zeros(n_(d))
    for _ in range(int(density * d)):
        t0 = r.uniform(0, d)
        ln = r.uniform(0.001, 0.012)
        b = white(ln, r) * env_exp(ln, ln / 2.5, 0.0003) * r.uniform(0.1, 1) ** 2
        i = n_(t0)
        m = min(len(b), len(y) - i)
        y[i:i + m] += b[:m]
    y = bp(y, lo, hi)
    if env is not None:
        y *= env
    return y


# ================================================================ registry
SOUNDS = []


def sfx(cat, name, variants=3, loop=None, level="peak", db=-3.0, desc=""):
    def deco(fn):
        SOUNDS.append(dict(cat=cat, name=name, variants=variants, loop=loop, level=level, db=db, desc=desc, fn=fn))
        return fn
    return deco


# ---------------------------------------------------------------- 02 UI
@sfx("02 UI", "Pop", 6, desc="Soft pop for items appearing (info-card rows, labels)")
def _(v, r):
    f0 = [520, 640, 760, 900, 1050, 1250][v]
    st = ["soft", "soft", "bubble", "soft", "bubble", "deep"][v]
    return reverb(pan(pop(r, f0, st), 0), r, 0.4, 0.12)


@sfx("02 UI", "Tick_Soft", 5, db=-9, desc="Very quiet tick (caption words, small UI changes)")
def _(v, r):
    return reverb(pan(tick(r, ["soft", "plastic", "soft", "wood", "metal"][v], 0.8, [1, 1.1, 0.9, 1, 1.2][v]), 0), r, 0.3, 0.1)


@sfx("02 UI", "Click_Mouse", 3, desc="Mouse click (subscribe button on the end card)")
def _(v, r):
    y = canvas(0.25)
    put(y, pan(tick(r, "plastic", 1.0, 1.0 + 0.1 * v), 0), 0.0)
    put(y, pan(tick(r, "plastic", 0.5, 1.15 + 0.1 * v), 0), 0.06 + 0.012 * v)
    return y


@sfx("02 UI", "Notification_Bell", 3, desc="Bell 'ding' (subscribe / notification)")
def _(v, r):
    y = canvas(1.6)
    if v == 2:
        put(y, pan(fm_bell(r, hz(88), 1.2), -0.1), 0)
        put(y, pan(fm_bell(r, hz(93), 1.3), 0.1), 0.12)
    else:
        put(y, pan(fm_bell(r, hz([90, 86][v]), 1.5), 0), 0)
    return reverb(y, r, 1.2, 0.22)


@sfx("02 UI", "Chime_Arrival", 5, desc="Two-note marimba chime (a stop / place appears)")
def _(v, r):
    pairs = [(74, 81), (76, 83), (69, 76), (79, 86), (81, 86)]
    y = canvas(1.4)
    a, b = pairs[v]
    put(y, pan(marimba(r, a), -0.15), 0)
    put(y, pan(marimba(r, b), 0.15), 0.11)
    return reverb(y, r, 1.0, 0.2)


@sfx("02 UI", "Shimmer", 4, desc="Sparkle for reveals (snow, logo, weather icon)")
def _(v, r):
    return reverb(shimmer(r, [0.9, 1.2, 1.6, 0.6][v], [35, 45, 30, 50][v]), r, 1.4, 0.35)


@sfx("02 UI", "Swipe", 5, desc="Short UI swipe (text sliding in)")
def _(v, r):
    return whoosh(r, [0.22, 0.28, 0.35, 0.25, 0.3][v], ["air", "bright", "air", "deep", "bright"][v], "pass")


# ---------------------------------------------------------------- 03 Motion
for _L, _dn in (("Short", 0.4), ("Medium", 0.75), ("Long", 1.3)):
    for _dir in ("In", "Out"):
        def _mk(L=_L, dn=_dn, di=_dir):
            @sfx("03 Motion", f"Whoosh_{L}_{di}", 4, desc=f"{L} whoosh, {'builds into' if di == 'In' else 'leaves from'} the moment")
            def _(v, r):
                y = whoosh(r, dn * [1, 0.9, 1.1, 1][v], ["air", "deep", "bright", "air"][v], di.lower())
                return reverb(y, r, 0.8, 0.15)
        _mk()


@sfx("03 Motion", "Swish_Pan", 4, desc="Fast left-right swish (whip pans, quick cuts)")
def _(v, r):
    return whoosh(r, [0.3, 0.35, 0.4, 0.28][v], ["bright", "air", "air", "deep"][v], "pass")


for _d in (2, 4, 6):
    def _mk(d=_d):
        @sfx("03 Motion", f"Riser_{d}s", 3, desc=f"{d}-second riser that peaks at the end (cut on the peak)")
        def _(v, r):
            u = np.linspace(0, 1, n_(d))
            nz = sweep(pink(d, r), 200 * (40 ** u), 1.0) * u ** 2
            base = [50, 45, 52][v]
            f = hz(base) * 2 ** (u * [1, 1.5, 2][v])
            ton = sum(osc(f * (1 + dt), d, "saw") for dt in (-0.006, 0, 0.007)) / 3
            ton = sweep(ton, 300 + 5000 * u ** 2, 1.2) * u ** 2.5 * 0.6
            y = widen(nz + ton, r, 0.9)
            return reverb(fade(y, 0.2, 0.01), r, 1.5, 0.2)
    _mk()


@sfx("03 Motion", "Reverse_Swell", 3, desc="Reverse-cymbal style swell into a title (1.5 s)")
def _(v, r):
    d = 1.6
    t = tt(d)
    x = bp(white(d, r), 2000, 12000) * np.exp(-t / 0.5) + fm_bell(r, hz([74, 69, 78][v]), d) * 0.3
    x = reverb(pan(x, 0), r, 1.2, 0.4)[: n_(d)]
    return x[::-1].copy()


@sfx("03 Motion", "Impact_Soft", 4, desc="Warm soft impact for a title / logo landing")
def _(v, r):
    d = 2.4
    t = tt(d)
    f = [55, 48, 62, 44][v] * (1.4 - 0.4 * np.clip(t / 0.08, 0, 1))
    sub = osc(f, d) * env_exp(d, 0.55, 0.003)
    body = lp(pink(d, r), 900) * env_exp(d, 0.12, 0.001) * 0.6
    y = pan(np.tanh((sub + body) * 1.5), 0)
    put(y, pan(click(r, 1500, 0.004) * 0.6, 0), 0)
    return reverb(y, r, 2.2, 0.3)


@sfx("03 Motion", "Boom_Cinematic", 2, desc="Deep cinematic boom (use sparingly - chapter starts)")
def _(v, r):
    d = 4.0
    t = tt(d)
    sub = osc(40 * (1.6 - 0.6 * np.clip(t / 0.15, 0, 1)), d) * env_exp(d, 1.1, 0.004)
    rum = lp(brown(d, r), 200) * env_exp(d, 0.9, 0.01) * 0.6
    y = pan(np.tanh((sub + rum) * 1.8), 0)
    return reverb(y, r, 3.2, 0.35)


# ---------------------------------------------------------------- 04 Dial & Mechanics
@sfx("04 Dial & Mechanics", "Dial_Tick", 6, desc="Single dial / counter tick")
def _(v, r):
    return pan(tick(r, ["metal", "plastic", "wood", "metal", "plastic", "soft"][v], 1, [1, 1, 1, 0.8, 1.2, 1][v]), 0)


for _d in (1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0):
    def _mk(d=_d):
        @sfx("04 Dial & Mechanics", f"Odometer_Roll_{str(d).replace('.', '_')}s", 3,
             desc=f"Counter rolls and settles over {d} s (matches the titles' count-up)")
        def _(v, r):
            return reverb(roll(r, d, ["metal", "plastic", "wood"][v], 16 + 4 * v), r, 0.5, 0.12)
    _mk()


@sfx("04 Dial & Mechanics", "Digit_Spin_Stop", 4, desc="Slot-machine digit spin landing (date/time digits)")
def _(v, r):
    return reverb(spin_stop(r, [0.9, 1.1, 1.3, 1.0][v], ["plastic", "metal", "wood", "soft"][v]), r, 0.4, 0.1)


@sfx("04 Dial & Mechanics", "Gear_Rotate", 4, loop=10, level="rms", db=-24, desc="Seamless gear / odometer turning loop")
def _(v, r):
    return loop_ticks(r, 10, [8, 12, 16, 6][v], ["metal", "metal", "plastic", "wood"][v])


@sfx("04 Dial & Mechanics", "Clock_Ticking", 3, loop=10, level="rms", db=-27, desc="Clock tick-tock loop (1 Hz, time passing)")
def _(v, r):
    L, X = 10, 0.5
    y = canvas(L + X + 0.3)
    for k in range(int((L + X) * 1) + 1):
        put(y, pan(tick(r, ["metal", "wood", "plastic"][v], 1.0 if k % 2 == 0 else 0.75, 1.0 if k % 2 == 0 else 0.8), 0), k * 1.0)
    return seamless(reverb(y, r, 0.6, 0.18), L, X)


@sfx("04 Dial & Mechanics", "Clock_Timelapse", 3, loop=10, level="rms", db=-26, desc="Fast clock loop for time-lapses / running clock")
def _(v, r):
    return loop_ticks(r, 10, [4, 6, 8][v], ["metal", "wood", "plastic"][v], jitter=0.0, gear_hum=False)


@sfx("04 Dial & Mechanics", "Ratchet", 4, desc="Short ratchet / crank (map pin set, dial lock)")
def _(v, r):
    y = canvas(0.8)
    t, gap = 0.0, [0.05, 0.04, 0.06, 0.035][v]
    for k in range([7, 9, 6, 10][v]):
        put(y, pan(tick(r, "metal", 0.7 + 0.3 * (k == 0)), 0), t)
        t += gap
        gap *= 0.93
    return reverb(y, r, 0.4, 0.12)


# ---------------------------------------------------------------- 05 Map & Travel
@sfx("05 Map & Travel", "Map_Unfold", 4, desc="Paper map unfolding (route map opens)")
def _(v, r):
    d = [1.3, 1.1, 1.6, 1.0][v]
    env = env_curve(d, [(0, 0), (0.1, 1), (0.35, 0.3), (0.55, 1), (0.8 * d, 0.2), (d, 0)])
    c = crinkle(r, d, 220, env=env)
    swish = lp(pink(d, r), 700) * env * 0.5
    return reverb(widen(c + swish, r, 0.7), r, 0.5, 0.12)


@sfx("05 Map & Travel", "Map_Fold", 3, desc="Paper map folding away")
def _(v, r):
    d = [0.8, 0.7, 1.0][v]
    env = env_curve(d, [(0, 0), (0.05, 1), (0.4 * d, 0.5), (0.6 * d, 0.9), (d, 0)])
    return reverb(widen(crinkle(r, d, 200, env=env) + lp(pink(d, r), 500) * env * 0.5, r, 0.6), r, 0.5, 0.1)


@sfx("05 Map & Travel", "Pen_Draw", 3, loop=10, level="rms", db=-28, desc="Pencil drawing on paper loop (route line drawing)")
def _(v, r):
    L, X = 10, 0.5
    d = L + X + 0.2
    strokes = np.zeros(n_(d))
    t = 0.0
    while t < d:
        ln = r.uniform(0.25, 0.8)
        e = env_curve(ln, [(0, 0), (0.05, 1), (ln - 0.06, 0.8), (ln, 0)])
        i = n_(t)
        m = min(len(e), len(strokes) - i)
        strokes[i:i + m] += e[:m] * r.uniform(0.5, 1)
        t += ln + r.uniform(0.02, 0.15)
    scratch = bp(white(d, r), [2500, 1800, 3200][v], 7000) * (1 + 0.4 * smooth_noise(d, r, 40))
    y = scratch * strokes + lp(pink(d, r), 400) * strokes * 0.3
    return seamless(widen(y, r, 0.3), L, X)


@sfx("05 Map & Travel", "Dotted_Trail", 3, loop=10, level="rms", db=-30, desc="Soft dotted-path taps loop (dotted route drawing)")
def _(v, r):
    return loop_ticks(r, 10, [6, 8, 5][v], ["soft", "wood", "plastic"][v], jitter=0.01, gear_hum=False)


@sfx("05 Map & Travel", "Pin_Drop", 5, desc="Map pin drops and bounces (a stop appears)")
def _(v, r):
    y = canvas(0.7)
    put(y, pan(pop(r, [900, 1100, 800, 1300, 1000][v], "bubble"), 0), 0)
    thud = lp(white(0.08, r) * env_exp(0.08, 0.015), 600) + osc(120, 0.08) * env_exp(0.08, 0.03) * 0.8
    put(y, pan(thud * 0.6, 0), 0.03)
    put(y, pan(tick(r, "soft", 0.4, 1.3), 0), 0.13)
    return reverb(y, r, 0.6, 0.15)


@sfx("05 Map & Travel", "Map_Zoom_In", 3, desc="Camera zooms into the map")
def _(v, r):
    d = [0.9, 1.1, 0.8][v]
    u = np.linspace(0, 1, n_(d))
    y = whoosh(r, d, ["air", "deep", "bright"][v], "in")
    ton = osc(hz(62) * 2 ** (u * 1.5), d, "tri") * u ** 2 * 0.15
    return reverb(y + pan(ton, 0), r, 0.8, 0.15)


@sfx("05 Map & Travel", "Map_Zoom_Out", 3, desc="Camera pulls back to the whole route")
def _(v, r):
    d = [1.0, 1.2, 0.9][v]
    u = np.linspace(0, 1, n_(d))
    y = whoosh(r, d, ["air", "deep", "bright"][v], "out")
    ton = osc(hz(74) * 2 ** (-u * 1.5), d, "tri") * (1 - u) ** 2 * 0.15
    return reverb(y + pan(ton, 0), r, 0.8, 0.15)


@sfx("05 Map & Travel", "Travel_Motion", 3, loop=10, level="rms", db=-30, desc="Gentle moving-air bed while the route draws")
def _(v, r):
    L, X = 10, 1.0
    d = L + X + 0.2
    y = lp(pink(d, r), [900, 1400, 700][v]) * (0.75 + 0.25 * smooth_noise(d, r, 0.4))
    return seamless(pan(y, smooth_noise(d, r, 0.2) * 0.5), L, X)


@sfx("05 Map & Travel", "Camera_Shutter", 3, desc="Camera shutter (photo moments, freeze frames)")
def _(v, r):
    y = canvas(0.35)
    put(y, pan(tick(r, "metal", 1.0, 0.7), 0), 0)
    put(y, pan(bp(white(0.05, r), 800, 5000) * env_exp(0.05, 0.012) * 0.6, 0), 0.005)
    put(y, pan(tick(r, "metal", 0.8, 0.6), 0), [0.09, 0.12, 0.07][v])
    return reverb(y, r, 0.3, 0.1)


# ---------------------------------------------------------------- 06 Bells & Brand
@sfx("06 Bells & Brand", "Temple_Bell", 3, desc="Mandir ghanta - long bronze bell (spiritual / arrival moments)")
def _(v, r):
    return reverb(widen(temple_bell(r, [220, 262, 196][v]), r, 0.6), r, 3.5, 0.3)


@sfx("06 Bells & Brand", "Hand_Bell_Ringing", 3, desc="Small ghanti rung a few times (aarti, temple visit)")
def _(v, r):
    d = 2.6
    y = canvas(d)
    t = 0.0
    for k in range([6, 8, 5][v]):
        put(y, pan(small_bell(r, [1100, 1250, 980][v] * r.uniform(0.995, 1.005)) * r.uniform(0.6, 1), r.uniform(-0.2, 0.2)), t)
        t += r.uniform(0.12, 0.2)
    return reverb(y, r, 1.8, 0.3)


@sfx("06 Bells & Brand", "Wind_Chime", 3, desc="Gentle wind chime (calm scenic moments)")
def _(v, r):
    d = 4.0
    y = canvas(d)
    for k in range(10):
        m = r.choice(PENTA[3:])
        put(y, pan(small_bell(r, hz(m) * 2, 1.8) * r.uniform(0.3, 0.8), r.uniform(-0.6, 0.6)), r.uniform(0, 2.5))
    return reverb(y, r, 2.0, 0.35)


def _intro_sting(v, r):
    """Timed to Graphics/SPP_Intro_5s_4K.mov (logo draws 0.3-1.6 s, trail dots 1.6 s, sun 1.9 s, name 2.3 s, out 4.3 s)."""
    d = 5.2
    y = canvas(d)
    sw = whoosh(r, 0.5, "air", "in")
    put(y, sw * 0.5, 0.0)
    # pencil line drawing the ridge
    ln = 1.3
    strokes = env_curve(ln, [(0, 0), (0.05, 1), (ln - 0.1, 0.8), (ln, 0)])
    put(y, widen(bp(white(ln, r), 2500, 7000) * strokes * 0.25, r, 0.3), 0.3)
    put(y, shimmer(r, 0.6, 30) * 0.4, 1.3)
    for i in range(8):  # golden trail dots climbing
        put(y, pan(marimba(r, PENTA[i % len(PENTA)] + 12, 0.5, 0.6) * 0.35, -0.3 + 0.08 * i), 1.6 + i * 0.08)
    sun = [fm_bell(r, hz(86), 2.2), marimba(r, 86, 1.2) * 0.9, small_bell(r, hz(86) * 2, 2.2) * 0.8][v]
    put(y, pan(sun, 0.2), 1.9)
    if v == 2:
        put(y, widen(temple_bell(r, 262, 3.0) * 0.35, r, 0.6), 2.3)
    else:
        put(y, reverb(pan(np.tanh(osc(55, 1.2) * env_exp(1.2, 0.4, 0.003) * 1.3) * 0.5, 0), r, 1.5, 0.2)[: n_(1.2)], 2.3)
    put(y, chord_pad(r, [62, 66, 69, 73, 76] if v != 1 else [62, 69, 74, 78, 81], 2.8, 0.5, 1.0) * 0.45, 2.3)
    put(y, whoosh(r, 0.7, "air", "out") * 0.35, 4.3)
    return reverb(y, r, 1.6, 0.22)


@sfx("06 Bells & Brand", "Intro_Sting", 3, desc="Logo sound timed to the SPP intro (put at the intro's first frame)")
def _(v, r):
    return _intro_sting(v, r)


@sfx("06 Bells & Brand", "EndCard_Sting", 3, desc="End-card sound timed to the SPP end card (first frame)")
def _(v, r):
    d = 3.2
    y = canvas(d)
    put(y, whoosh(r, 0.5, "air", "in") * 0.5, 0)
    put(y, pan(marimba(r, [81, 78, 83][v]) * 0.7, 0), 0.35)
    put(y, pan(pop(r, 700, "soft") * 0.5, -0.4), 0.8)
    put(y, pan(pop(r, 800, "soft") * 0.5, 0.4), 0.95)
    put(y, pan(pop(r, 600, "bubble") * 0.5, 0), 1.2)
    put(y, shimmer(r, 0.9, 30) * 0.5, 1.3)
    put(y, chord_pad(r, [62, 69, 74, 78], 1.9, 0.4, 1.0) * 0.35, 1.3)
    return reverb(y, r, 1.4, 0.22)


# ---------------------------------------------------------------- 07 Nature Beds (seamless 30 s)
@sfx("07 Nature Beds", "Mountain_Wind", 3, loop=30, level="rms", db=-24, desc="Mountain wind: calm / gusty / high-altitude whistle")
def _(v, r):
    L, X = 30, 3.0
    d = L + X + 0.5
    chans = []
    for ch in range(2):
        g = [0.8, 0.62, 0.7][v] + [0.2, 0.38, 0.3][v] * smooth_noise(d, r, [0.1, 0.25, 0.18][v])
        base = lp(brown(d, r), 500) * 0.8 + lp(pink(d, r), 1400) * 0.25
        whistle = sweep(pink(d, r), 450 + 700 * (g ** 2) * [0.6, 1, 1.4][v], 0.25) * (0.3 if v == 2 else 0.12)
        chans.append((base + whistle) * g ** 1.5)
    return seamless(np.stack(chans, 1), L, X)


@sfx("07 Nature Beds", "Prayer_Flags", 2, loop=30, level="rms", db=-25, desc="Wind with prayer flags fluttering")
def _(v, r):
    L, X = 30, 3.0
    d = L + X + 0.5
    chans = []
    for ch in range(2):
        g = 0.5 + 0.5 * smooth_noise(d, r, 0.2)
        rate = 8 + 5 * smooth_noise(d, r, 0.5)
        ph = 2 * np.pi * np.cumsum(rate) / SR
        flap = np.clip(np.sin(ph), 0, 1) ** 3 * g ** 2
        fl = bp(pink(d, r), 400, [3000, 2200][v]) * flap * 0.7
        chans.append(lp(brown(d, r), 450) * 0.6 * g + fl)
    return seamless(np.stack(chans, 1), L, X)


@sfx("07 Nature Beds", "Mountain_Stream", 3, loop=30, level="rms", db=-24, desc="Mountain stream / river")
def _(v, r):
    L, X = 30, 3.0
    d = L + X + 0.5
    chans = []
    for ch in range(2):
        bed = lp(pink(d, r), [1800, 1200, 2600][v], 4) * 0.5 + lp(brown(d, r), 300) * 0.35
        bub = np.zeros(n_(d))
        for _ in range(int(d * [160, 90, 240][v])):
            f0 = r.uniform(250, 1400)
            ln = r.uniform(0.02, 0.07)
            b = osc(f0 * (1 + 0.8 * tt(ln) / ln), ln) * env_exp(ln, ln / 3, 0.002) * r.uniform(0.1, 0.6)  # rising "blup"
            i = n_(r.uniform(0, d - 0.1))
            bub[i:i + len(b)] += b
        chans.append(bed * (0.85 + 0.15 * smooth_noise(d, r, 1)) + lp(bub, 3000) * 0.9)
    return seamless(np.stack(chans, 1), L, X)


@sfx("07 Nature Beds", "Light_Rain", 2, loop=30, level="rms", db=-26, desc="Light rain")
def _(v, r):
    L, X = 30, 3.0
    d = L + X + 0.5
    chans = []
    for ch in range(2):
        bed = hp(pink(d, r), 900) * 0.4
        dr = np.zeros(n_(d))
        for _ in range(int(d * [45, 80][v])):
            b = reson(click(r, 1500, 0.002), r.uniform(2000, 6500), 8) * r.uniform(0.05, 0.4)
            i = n_(r.uniform(0, d - 0.01))
            dr[i:i + len(b)] += b
        chans.append(bed + dr)
    return seamless(np.stack(chans, 1), L, X)


@sfx("07 Nature Beds", "Night_Crickets", 2, loop=30, level="rms", db=-27, desc="Night crickets (camp, village at night)")
def _(v, r):
    L, X = 30, 3.0
    d = L + X + 0.5
    y = canvas(d)
    for c in range([4, 6][v]):
        f = r.uniform(4200, 5200)
        rate, grp = r.uniform(1.5, 3.0), r.integers(2, 5)
        t = r.uniform(0, 1)
        while t < d - 0.3:
            for k in range(grp):
                ln = 0.04
                ch = osc(f, ln) * np.sin(np.pi * tt(ln) / ln) ** 2 * osc(r.uniform(30, 45), ln, "square").clip(0, 1)
                put(y, pan(ch * r.uniform(0.2, 0.6), (c / 3) - 0.8), t + k * 0.055)
            t += 1 / rate
    y += widen(lp(pink(d, r), 600) * 0.03, r)
    return seamless(y, L, X)


# ---------------------------------------------------------------- 08 Phone
def _ind_tone(d, on_off, f=400, am=25):
    t = tt(d)
    tone = np.sin(2 * np.pi * f * t) * (0.6 + 0.4 * np.sin(2 * np.pi * am * t))
    gate = np.zeros_like(t)
    per = sum(on_off)
    ph = t % per
    acc = 0.0
    for k, seg_ in enumerate(on_off):
        if k % 2 == 0:
            gate[(ph >= acc) & (ph < acc + seg_)] = 1
        acc += seg_
    gate = lp(gate, 200)
    return tone * gate


def _line(r, d, level=0.004):
    return bp(white(d, r), 300, 3400) * level + np.sin(2 * np.pi * 50 * tt(d)) * level * 0.3


@sfx("08 Phone", "Ringback_India", 1, loop=12, level="rms", db=-24, desc="Indian ringback tone the caller hears (400 Hz, 0.4-0.2-0.4-2.0 s)")
def _(v, r):
    d = 12.0
    y = phone_band(_ind_tone(d, [0.4, 0.2, 0.4, 2.0]) * 0.5 + _line(r, d))
    return pan(y, 0)


@sfx("08 Phone", "Dial_Tone_India", 1, loop=6, level="rms", db=-24, desc="Indian dial tone (continuous 400 Hz x 25 Hz)")
def _(v, r):
    d = 6.6
    return seamless(pan(phone_band(_ind_tone(d, [d, 0.0]) * 0.5 + _line(r, d)), 0), 6.0, 0.4)


@sfx("08 Phone", "Busy_Tone_India", 1, loop=6, level="rms", db=-24, desc="Indian busy tone (0.75 s on / off)")
def _(v, r):
    return pan(phone_band(_ind_tone(6.0, [0.75, 0.75], 400, 0.0001) * 0.5 + _line(r, 6.0)), 0)


@sfx("08 Phone", "Call_Ended_Beeps", 2, desc="Call disconnected beeps")
def _(v, r):
    d = 1.6
    y = np.zeros(n_(d))
    for k in range(3):
        b = osc([480, 425][v], 0.22) * env_curve(0.22, [(0, 0), (0.01, 1), (0.2, 1), (0.22, 0)]) * 0.5
        i = n_(k * 0.45)
        y[i:i + len(b)] += b
    return pan(phone_band(y + _line(r, d)), 0)


_DTMF = {"1": (697, 1209), "2": (697, 1336), "3": (697, 1477), "4": (770, 1209), "5": (770, 1336), "6": (770, 1477),
         "7": (852, 1209), "8": (852, 1336), "9": (852, 1477), "*": (941, 1209), "0": (941, 1336), "#": (941, 1477)}


@sfx("08 Phone", "Keypad_Dialing", 3, desc="Dialing a 10-digit number on a keypad (DTMF tones)")
def _(v, r):
    digits = "".join(r.choice(list("0123456789")) for _ in range(10))
    y = canvas(4.0)
    t = 0.1
    for dg in digits:
        a, b = _DTMF[dg]
        ln = r.uniform(0.09, 0.14)
        tone = (osc(a, ln) + osc(b, ln)) * 0.25 * env_curve(ln, [(0, 0), (0.005, 1), (ln - 0.01, 1), (ln, 0)])
        put(y, pan(tone, 0), t)
        put(y, pan(tick(r, "plastic", 0.35), 0), t - 0.01)
        t += ln + r.uniform(0.12, 0.35) * [1, 0.7, 1.3][v]
    return trim_silence(y)


@sfx("08 Phone", "Ringtone", 4, loop=6, level="rms", db=-20, desc="Original mobile ringtone melodies (marimba / bell)")
def _(v, r):
    tunes = [[74, 78, 81, 78, 86, 81], [81, 86, 83, 81, 78, 74], [74, 74, 81, 79, 78, 76], [86, 83, 81, 83, 78, 81]]
    L, X = 6.0, 0.2
    y = canvas(L + X + 1.2)
    t = 0.0
    while t < L + X:
        for k, m in enumerate(tunes[v]):
            nt = marimba(r, m, 0.5) if v % 2 == 0 else fm_bell(r, hz(m), 0.6, 2.2) * 0.8
            put(y, pan(nt, 0), t + k * 0.16)
        t += 1.5
    return seamless(reverb(y, r, 0.5, 0.12), L, X)


@sfx("08 Phone", "Vibrate", 3, loop=6, level="rms", db=-22, desc="Phone vibrating on a table (loop)")
def _(v, r):
    L = 6.0
    t = tt(L)
    f = [165, 180, 150][v]
    buzz = np.tanh(3 * osc(f, L)) * 0.5 + bp(white(L, r), 800, 4000) * 0.3 * np.abs(osc(f, L))
    gate = lp(((t % 1.5) < 0.8).astype(float), 60)
    return pan(buzz * gate, 0)


@sfx("08 Phone", "Pickup", 3, desc="Picking up the call (handset click, line opens)")
def _(v, r):
    y = canvas(0.8)
    put(y, pan(tick(r, "plastic", 1.0, 0.8), 0), 0)
    put(y, pan(tick(r, "plastic", 0.6, 1.0), 0), 0.04)
    put(y, pan(phone_band(white(0.6, r)) * env_curve(0.6, [(0, 0), (0.05, 0.02), (0.6, 0.01)]), 0), 0.08)
    return y


@sfx("08 Phone", "Hangup", 3, desc="Hanging up (click, line cuts)")
def _(v, r):
    y = canvas(0.6)
    put(y, pan(phone_band(white(0.2, r)) * 0.015, 0), 0)
    put(y, pan(tick(r, "plastic", 1.2, 0.7), 0), 0.2)
    put(y, pan(lp(pop(r, 150, "deep", 0.12), 700) * 0.4, 0), 0.205)
    return y


@sfx("08 Phone", "Message_Ping", 4, desc="Incoming message ping (original)")
def _(v, r):
    y = canvas(0.9)
    a, b = [(86, 93), (81, 88), (90, 86), (83, 90)][v]
    put(y, pan(fm_bell(r, hz(a), 0.5, 1.5) * 0.7, 0), 0)
    put(y, pan(fm_bell(r, hz(b), 0.6, 1.5) * 0.7, 0), 0.09)
    return reverb(y, r, 0.5, 0.1)


@sfx("08 Phone", "Line_Noise", 2, loop=10, level="rms", db=-40, desc="Phone line hiss / static bed under a phone voice")
def _(v, r):
    L = 10.0
    d = L + 0.6
    y = _line(r, d, 0.05)
    if v:  # crackly line
        y = y + bp(white(d, r), 400, 3000) * (np.abs(smooth_noise(d, r, 8)) > 0.85) * 0.08
    return seamless(pan(y, 0), L, 0.5)


# ---------------------------------------------------------------- 01 Title Kits (timed to the SPP titles)
def _info_in(v, r):
    kind = ["metal", "plastic", "wood", "soft"][v]
    y = canvas(2.7)
    put(y, whoosh(r, 0.5, ["air", "bright", "air", "deep"][v], "in") * 0.7, 0.0)
    put(y, pan(pop(r, 900, "bubble"), 0.2) * 0.5, 0.45)          # weather icon
    for i, m in enumerate([74, 78, 81, 86]):                       # meta rows
        put(y, pan(marimba(r, m + 12, 0.35, 0.5) * 0.28, -0.2 + 0.13 * i), 0.55 + 0.1 * i)
    put(y, roll(r, 1.5, kind, 16) * 0.8, 0.6)                    # odometer altitude 0.6 -> 2.1
    put(y, spin_stop(r, 1.2, kind) * 0.35, 0.8)                   # date/time digits
    if v == 3:
        put(y, shimmer(r, 0.6, 25) * 0.3, 2.1)
    return reverb(y, r, 0.6, 0.12)


@sfx("01 Title Kits", "InfoCard_In", 4, db=-6, desc="SPP Info Card: slide-in, rows, rolling numbers, settle (clip start)")
def _(v, r):
    return _info_in(v, r)


@sfx("01 Title Kits", "Title_Out", 4, db=-8, desc="Any SPP title leaving (0.6 s before its end)")
def _(v, r):
    return reverb(whoosh(r, 0.55, ["air", "bright", "deep", "air"][v], "out") * 0.8, r, 0.6, 0.12)


for _c in (1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0):
    def _mk(c=_c):
        @sfx("01 Title Kits", f"Altitude_In_{str(c).replace('.', '_')}s", 2, db=-6,
             desc=f"SPP Altitude Counter with Count Duration {c} s: box in, counter rolls, lands")
        def _(v, r):
            y = canvas(0.45 + c + 1.4)
            put(y, whoosh(r, 0.45, "air", "in") * 0.6, 0)
            put(y, roll(r, c, ["metal", "wood"][v], 14) * 0.85, 0.45)
            u = np.linspace(0, 1, n_(c))
            rise = sweep(pink(c, r), 300 + 2500 * eo(u), 0.5) * eo(u) * (1 - u) ** 0.3 * 0.12
            put(y, pan(rise, 0), 0.45)
            put(y, pan(marimba(r, [86, 81][v], 0.9) * 0.6, 0), 0.45 + c)
            return reverb(y, r, 0.9, 0.15)
    _mk()


@sfx("01 Title Kits", "PeakCallout_In", 4, db=-6, desc="SPP Peak Callout: marker ping, line draws, label + height")
def _(v, r):
    y = canvas(1.9)
    put(y, pan(fm_bell(r, hz([93, 90, 95, 88][v]), 0.8, 2.0) * 0.5, 0), 0.18)
    ln = 0.55
    u = np.linspace(0, 1, n_(ln))
    zipn = sweep(pink(ln, r), 1500 + 5000 * u, 0.5) * np.sin(np.pi * u) * 0.5
    put(y, pan(zipn, np.linspace(-0.2, 0.3, len(zipn))), 0.25)
    put(y, pan(pop(r, [700, 820, 640, 900][v], "soft") * 0.55, 0.3), 0.72)
    put(y, spin_stop(r, 0.45, "plastic") * 0.35, 1.0)
    return reverb(y, r, 0.8, 0.15)


@sfx("01 Title Kits", "PopupTitle_In", 4, db=-6, desc="SPP Pop-up Title: soft hit, text swipe, sparkle")
def _(v, r):
    y = canvas(2.4)
    if v in (0, 2):
        put(y, pan(np.tanh(osc(55 * (1.3 - 0.3 * np.clip(tt(1.0) / 0.06, 0, 1)), 1.0) * env_exp(1.0, 0.35, 0.003) * 1.4) * 0.45, 0), 0.0)
    put(y, whoosh(r, 0.5, ["air", "bright", "deep", "air"][v], "pass") * 0.6, 0.0)
    put(y, whoosh(r, 0.4, "bright", "pass") * 0.3, 0.25)
    if v == 3:
        put(y, widen(temple_bell(r, 262, 2.0) * 0.25, r, 0.5), 0.05)
    put(y, shimmer(r, 0.8, 30) * 0.35, 0.55)
    return reverb(y, r, 1.2, 0.18)


@sfx("01 Title Kits", "Credits_In", 3, db=-8, desc="SPP Credits: soft swell, heading chime, gentle line ticks")
def _(v, r):
    y = canvas(3.2)
    put(y, chord_pad(r, [62, 69, 74, 78], 3.0, 0.8, 1.5) * 0.35, 0)
    put(y, pan(marimba(r, [81, 86, 78][v], 1.0) * 0.6, 0), 0.25)
    for j in range(5):
        put(y, pan(tick(r, "soft", 0.5), -0.3 + 0.15 * j), 0.55 + 0.16 * j)
    put(y, shimmer(r, 0.8, 25) * 0.3, 1.6)
    return reverb(y, r, 1.4, 0.22)


@sfx("01 Title Kits", "RouteMap_Open", 3, db=-6, desc="SPP Route Map start: map unfolds + title")
def _(v, r):
    y = canvas(1.8)
    d = 1.3
    env = env_curve(d, [(0, 0), (0.1, 1), (0.35, 0.3), (0.55, 1), (1.0, 0.2), (d, 0)])
    put(y, widen(crinkle(r, d, 200, env=env) * 0.8 + lp(pink(d, r), 700) * env * 0.4, r, 0.7), 0)
    put(y, pan(marimba(r, [74, 76, 69][v], 0.9) * 0.5, 0), 0.3)
    return reverb(y, r, 0.6, 0.12)


@sfx("01 Title Kits", "Caption_Word", 4, db=-14, desc="Barely-there tick per caption word (optional)")
def _(v, r):
    return pan(tick(r, ["soft", "wood", "plastic", "soft"][v], 0.6, [1, 1, 1.2, 0.85][v]), 0)


# ================================================================ GRAND (cinematic, bass-heavy, mountain scale)
D1, A1, D2, F2, A2, E2, D3, A3 = 26, 33, 38, 41, 45, 40, 50, 57


def mx(*xs):
    """Mix signals of different lengths / channel counts (pads with silence)."""
    st = any(np.asarray(x).ndim == 2 for x in xs)
    xs = [stereo(np.asarray(x)) if st else np.asarray(x) for x in xs]
    n = max(len(x) for x in xs)
    out = np.zeros((n, 2)) if st else np.zeros(n)
    for x in xs:
        out[: len(x)] += x
    return out


def sub_clean(x):
    """Keep the real sub (35-60 Hz) but drop useless rumble below 28 Hz."""
    return hp(x, 28, 2)


def mountain_echo(x, r, delays=(0.34, 0.78, 1.35, 2.1), gains=(0.42, 0.28, 0.17, 0.09), dark=2600):
    """Valley echo: a few distinct, darker-each-time repeats (sound bouncing off far ridges)."""
    x = stereo(x)
    tail = n_(max(delays) + 0.1)
    y = np.concatenate([x, np.zeros((tail, 2))])
    src = x
    for k, (dl, g) in enumerate(zip(delays, gains)):
        src = lp(src, dark / (1 + 0.5 * k))
        i = n_(dl)
        p = [-0.5, 0.45, -0.3, 0.25][k % 4]
        y[i:i + len(src), 0] += src[:, 0] * g * (1 - p) / 1.3
        y[i:i + len(src), 1] += src[:, 1] * g * (1 + p) / 1.3
    return y


def taiko(r, f0=58, d=2.2, body=1.0):
    t = tt(d)
    f = f0 * (1 + 0.9 * np.exp(-t / 0.025))
    tone = osc(f, d) * env_exp(d, 0.45, 0.002)
    tone2 = osc(f * 1.52, d) * env_exp(d, 0.18, 0.002) * 0.45
    shell = osc(f * 2.3 * (1 + 0.3 * np.exp(-t / 0.02)), d) * env_exp(d, 0.14, 0.001) * 0.55   # the "thud" you hear on small speakers
    skin = bp(white(d, r), 100, 900) * env_exp(d, 0.09, 0.001) * 0.9 * body
    attack = bp(white(d, r), 300, 1600) * env_exp(d, 0.035, 0.0005) * 1.4 * body     # the hit you hear on a phone
    stick = click(r, 1800, 0.004) * 0.5
    y = np.tanh((tone + tone2 + shell + skin) * 2.2) + attack
    y[: len(stick)] += stick
    return sub_clean(fade(y, 0.0005, 0.2))


def tom_low(r, f0=90, d=1.2):
    return taiko(r, f0, d, 0.6)


def braam(r, root=D1, chord=(0, 12, 19, 24), d=4.5, bright=1800):
    t = tt(d)
    y = np.zeros_like(t)
    for iv in chord:
        f = hz(root + iv)
        for det in (-0.006, 0.0, 0.007):
            y += osc(f * (1 + det), d, "saw") / (1 + iv / 24)
    cut = 140 + bright * env_curve(d, [(0, 0), (0.07, 1), (0.6, 0.35), (d, 0.15)])
    y = sweep(y, cut, bw_oct=2.2, fmin=40, fmax=8000)
    y = np.tanh(y * 1.8)
    y = y * env_curve(d, [(0, 0), (0.03, 1), (0.8, 0.75), (d, 0)])
    y += osc(hz(root), d) * env_curve(d, [(0, 0), (0.02, 0.9), (d, 0)]) * 0.9
    return sub_clean(fade(y, 0.001, 0.3))


def gong(r, f0=85, d=10.0, swell=True):
    ratios = sorted(set([1.0, 1.51, 2.02, 2.49, 2.93, 3.46, 4.07, 4.58, 5.21, 5.94, 6.73, 7.6] + list(r.uniform(1.2, 8, 14))))
    t = tt(d)
    y = np.zeros_like(t)
    for k, ra in enumerate(ratios):
        f = f0 * ra
        dec = 7.0 / (1 + 0.25 * ra)
        att = (0.004 if not swell else 0.02 + 0.35 * (ra / 8) ** 1.5)
        a = np.clip(t / att, 0, 1) ** 1.5
        y += np.sin(2 * np.pi * f * t * (1 + 0.0007 * np.sin(2 * np.pi * 0.3 * t + k))) * np.exp(-t / dec) * a / (1 + 0.3 * ra)
    strike = lp(white(0.05, r) * env_exp(0.05, 0.01), 1200) * 1.5
    y[: len(strike)] += strike
    return sub_clean(fade(y, 0.0005, 0.5))


def singing_bowl(r, f0=196, d=9.0):
    y = partials(f0, [1, 2.76, 5.40, 8.93], [1, 0.45, 0.22, 0.1], [5.5, 3.5, 2.0, 1.2], d, detune=0.004, r=r)
    y *= 1 + 0.25 * np.sin(2 * np.pi * 0.9 * tt(d))
    return fade(y, 0.002, 0.5)


def horn(r, notes, d_note=1.4, base=None):
    """Ransingha / narsingha-style copper horn call: brassy, breathy, slightly bending up into each note."""
    parts = []
    for m, dur in notes:
        t = tt(dur)
        f = hz(m) * (1 - 0.035 * np.exp(-t / 0.12)) * (1 + 0.006 * np.sin(2 * np.pi * 5.2 * t) * np.clip((t - 0.3) / 0.4, 0, 1))
        s = osc(f, dur, "saw") * 0.8 + osc(f * 2, dur, "saw") * 0.2
        s = reson(s, 520, 3) * 0.9 + reson(s, 1150, 4) * 0.6 + reson(s, 2400, 5) * 0.25 + lp(s, 900) * 0.4
        br = bp(white(dur, r), 600, 2500) * 0.05
        env = env_curve(dur, [(0, 0), (0.12, 0.8), (0.3, 1), (dur - 0.25, 0.9), (dur, 0)])
        parts.append(np.tanh((s + br) * env * 1.8))
    return np.concatenate(parts)


def drone(r, L, midis, dark=500, move=0.08, X=3.0):
    d = L + X + 0.3
    chans = []
    for ch in range(2):
        y = np.zeros(n_(d))
        for m in midis:
            for det in (-0.004, 0.003):
                y += osc(hz(m) * (1 + det + r.uniform(-0.001, 0.001)), d, "saw") / (1 + (m - midis[0]) / 12)
        lfo = 0.5 + 0.5 * smooth_noise(d, r, move)
        y = sweep(y, dark * (0.6 + 0.9 * lfo), bw_oct=2.5, fmin=40, fmax=6000)
        y += osc(hz(midis[0]) / 2, d) * 0.5
        y += lp(pink(d, r), 300) * 0.15 * lfo
        chans.append(sub_clean(y * (0.8 + 0.2 * lfo)))
    return seamless(np.stack(chans, 1), L, X)


def grand_whoosh(r, d=1.6, direction="in"):
    n = brown(d, r) * 0.6 + pink(d, r) * 0.4
    u = np.linspace(0, 1, len(n))
    if direction == "in":
        shape = u ** 2.5 * (1 - np.clip((u - 0.9) / 0.1, 0, 1))
        fc = 90 + 1400 * u ** 2
    else:
        shape = (1 - u) ** 1.6 * (1 - np.exp(-u / 0.03))
        fc = 1500 - 1400 * u ** 0.6
    y = sweep(n, fc, 1.3, fmin=50) * shape
    sub = osc(hz(D1) * (1 + (0.3 * u if direction == "in" else -0.2 * u)), d) * shape * 0.6
    y = y / (np.max(np.abs(y)) + 1e-9) + sub
    return sub_clean(pan(y, np.linspace(-0.5, 0.5, len(y)) * r.choice([-1, 1])))


def boom(r, f0=42, d=5.0, drop=1.7):
    t = tt(d)
    s_ = osc(f0 * (1 + (drop - 1) * np.exp(-t / 0.09)), d) * env_exp(d, 1.3, 0.003)
    b = lp(brown(d, r), 180) * env_exp(d, 1.0, 0.01) * 0.6
    y = np.tanh((s_ + b) * 2.2) * 0.8
    harm = bp(np.tanh(s_ * 5), 90, 420) * 0.55                                     # audible weight on phones
    thump = osc(120 * (1 - 0.4 * np.clip(t / 0.1, 0, 1)), d) * env_exp(d, 0.14, 0.002) * 0.6
    y = y + harm + thump + bp(white(d, r), 150, 1500) * env_exp(d, 0.08, 0.001) * 0.7
    y[: n_(0.004)] += click(r, 1200, 0.004)[: n_(0.004)] * 0.5
    return sub_clean(y)


def heavy_tick(r, gain=1.0, pitch=1.0):
    t = tick(r, "wood", gain * 0.8, 0.55 * pitch)
    th = osc(95 * pitch, 0.09) * env_exp(0.09, 0.025, 0.001) * 0.6 * gain
    n = max(len(t), len(th))
    y = np.zeros(n)
    y[: len(t)] += t
    y[: len(th)] += th
    return y


def heavy_roll(r, d, rate=10):
    tot = d + 0.4
    y = canvas(tot)
    K = max(5, int(rate * d))
    for k in range(1, K):
        t0 = d * (1 - (1 - k / K) ** (1 / 3))
        put(y, pan(heavy_tick(r, 0.5 + 0.4 * r.random()), r.uniform(-0.2, 0.2)), t0)
    u = tt(tot)
    speed = np.where(u < d, (1 - np.clip(u / d, 0, 1)) ** 2, 0)
    y += pan(bp(brown(tot, r), 120, 900) * speed * 0.35, 0)
    put(y, pan(heavy_tick(r, 1.4, 0.85), 0), d)
    return y


# ---------------------------------------------------------------- 09 Grand Title Kits
def _grand_info(v, r):
    y = canvas(4.2)
    put(y, grand_whoosh(r, 0.55, "in") * 0.55, 0.0)
    put(y, pan(tom_low(r, [92, 80, 100, 86][v]) * 0.6, 0), 0.45)
    for i, m in enumerate([D3, D3 + 4, A2 + 12, D3 + 12] if v % 2 == 0 else [D3, A2 + 12, D3 + 7, D3 + 12]):
        put(y, pan(marimba(r, m, 1.2, 0.4) * 0.3, -0.25 + 0.16 * i), 0.55 + 0.1 * i)
    put(y, heavy_roll(r, 1.5) * 0.7, 0.6)
    put(y, boom(r, 46, 2.2, 1.4) * 0.35, 2.1)
    if v in (1, 3):
        put(y, pan(temple_bell(r, [110, 131, 98, 123][v], 2.0) * 0.3, 0.1), 2.1)
    return reverb(y, r, 2.4, 0.22)


@sfx("09 Grand Title Kits", "Grand_InfoCard_In", 4, db=-6, desc="GRAND Info Card: deep whoosh, low tom, warm rows, heavy counter, soft boom")
def _(v, r):
    return _grand_info(v, r)


@sfx("09 Grand Title Kits", "Grand_Title_Out", 4, db=-8, desc="GRAND title leaving: deep air + sub tail")
def _(v, r):
    return reverb(grand_whoosh(r, [0.8, 1.0, 0.7, 0.9][v], "out") * 0.8, r, 1.8, 0.2)


for _c in (1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0):
    def _mk(c=_c):
        @sfx("09 Grand Title Kits", f"Grand_Altitude_In_{str(c).replace('.', '_')}s", 3, db=-6,
             desc=f"GRAND Altitude Counter ({c} s count): rising drone, heavy counter, landing hit")
        def _(v, r):
            tot = 0.45 + c + 4.0
            y = canvas(tot)
            put(y, grand_whoosh(r, 0.5, "in") * 0.5, 0)
            u = np.linspace(0, 1, n_(c))
            ris = sum(osc(hz(m) * 2 ** (eo(u) * [5, 7, 12][v] / 12), c, "saw") for m in (D2, A2)) / 2
            ris = sweep(ris, 200 + 1600 * eo(u), 2.0, fmin=40) * (0.2 + 0.8 * eo(u)) * 0.35
            put(y, pan(ris, 0), 0.45)
            put(y, heavy_roll(r, c) * 0.6, 0.45)
            land = [mx(taiko(r, 55), boom(r, 44, 3.0) * 0.5), braam(r, D1, (0, 12, 19), 3.5) * 0.8, mx(pan(temple_bell(r, 110, 3.5), 0) * 0.6, boom(r, 44, 3.0) * 0.4)][v]
            put(y, stereo(land), 0.45 + c)
            return reverb(y, r, 2.8, 0.22)
    _mk()


@sfx("09 Grand Title Kits", "Grand_PeakCallout_In", 4, db=-6, desc="GRAND Peak Callout: deep bell, low sweep along the line, soft drum on the label")
def _(v, r):
    y = canvas(5.0)
    b = [gong(r, 80, 4.5), temple_bell(r, 110, 4.5), singing_bowl(r, 147, 4.5), temple_bell(r, 98, 4.5)][v]
    put(y, pan(b * 0.45, 0), 0.15)
    put(y, grand_whoosh(r, 0.6, "in") * 0.35, 0.2)
    put(y, pan(tom_low(r, 96) * 0.45, 0.2), 0.72)
    return mountain_echo(reverb(y, r, 2.5, 0.2), r) if v == 3 else reverb(y, r, 2.5, 0.2)


@sfx("09 Grand Title Kits", "Grand_PopupTitle_In", 5, db=-5, desc="GRAND chapter title: braam / taiko+boom / ransingha horn / gong swell / echo hit")
def _(v, r):
    y = canvas(6.5)
    put(y, grand_whoosh(r, 0.5, "in") * 0.4, 0.0)
    if v == 0:
        put(y, stereo(braam(r, D1, (0, 12, 15, 19, 24), 4.5)) * 0.8, 0.0)
    elif v == 1:
        put(y, stereo(mx(taiko(r, 52) * 0.9, boom(r, 40, 4.0) * 0.6)), 0.0)
    elif v == 2:
        put(y, pan(horn(r, [(A2, 0.9), (D3, 2.0)]) * 0.55, 0), 0.0)
        put(y, stereo(boom(r, 44, 3.0) * 0.4), 0.0)
        return mountain_echo(reverb(y, r, 2.5, 0.2), r)
    elif v == 3:
        put(y, pan(gong(r, 75, 6.0, True) * 0.6, 0), 0.0)
    else:
        put(y, stereo(taiko(r, 60) * 0.9), 0.0)
        return mountain_echo(reverb(y, r, 2.0, 0.2), r)
    return reverb(y, r, 3.0, 0.25)


@sfx("09 Grand Title Kits", "Grand_Credits_In", 3, db=-8, desc="GRAND credits: slow drone swell with a singing bowl")
def _(v, r):
    y = canvas(8.0)
    dr = drone(r, 6.0, [D2, A2, D3] if v != 1 else [D2, A2, E2 + 12], 450, 0.1, 1.0)
    put(y, dr * env_curve(6.0, [(0, 0), (1.2, 1), (4.5, 0.8), (6.0, 0)])[:, None] * 0.6, 0)
    put(y, pan(singing_bowl(r, [196, 147, 220][v], 6.0) * 0.5, 0.1), 0.25)
    return reverb(y, r, 3.0, 0.25)


@sfx("09 Grand Title Kits", "Grand_RouteMap_Open", 3, db=-6, desc="GRAND route map start: deep whoosh, drum, map paper, drone swell")
def _(v, r):
    y = canvas(4.5)
    put(y, grand_whoosh(r, 0.9, "in") * 0.5, 0.0)
    put(y, stereo(taiko(r, [56, 50, 62][v]) * 0.7), 0.35)
    dd = 1.3
    env = env_curve(dd, [(0, 0), (0.1, 1), (0.4, 0.3), (0.6, 0.8), (dd, 0)])
    put(y, widen(crinkle(r, dd, 160, env=env) * 0.35, r, 0.6), 0.4)
    return reverb(y, r, 2.6, 0.22)


@sfx("09 Grand Title Kits", "Grand_Stop_Hit", 5, db=-6, desc="GRAND route stop: low drum + deep bell (instead of pin pop)")
def _(v, r):
    y = canvas(3.5)
    put(y, pan(tom_low(r, [84, 92, 78, 100, 88][v]) * 0.8, 0), 0)
    put(y, pan(marimba(r, [D3, D3 + 7, A2 + 12, D3 + 4, D3 + 12][v], 1.5, 0.5) * 0.4, 0.15), 0.05)
    put(y, pan(temple_bell(r, [220, 196, 247, 262, 175][v], 2.8) * 0.2, -0.1), 0.05)
    return reverb(y, r, 2.4, 0.22)


@sfx("09 Grand Title Kits", "Grand_Journey_Pulse", 3, loop=10, level="rms", db=-26,
     desc="GRAND loop under the route drawing: slow drum pulse on a low drone")
def _(v, r):
    L, X = 10.0, 1.0
    d = L + X + 1.0
    y = canvas(d)
    bpm = [72, 84, 66][v]
    beat = 60 / bpm
    k = 0
    while k * beat < d - 0.5:
        g = 0.9 if k % 4 == 0 else 0.5
        put(y, pan(tom_low(r, 70 if k % 4 == 0 else 95, 0.9) * g, 0), k * beat)
        k += 1
    dr = drone(r, d - X - 0.4, [D2, A2], 380, 0.12, X)
    y[: len(dr)] += dr * 0.35
    return seamless(reverb(y, r, 2.0, 0.2), L, X)


# ---------------------------------------------------------------- 10 Grand Impacts & Swells
@sfx("10 Grand Impacts & Swells", "Grand_Braam", 5, desc="Low brass braam (big reveals, a massive peak on screen)")
def _(v, r):
    ch = [(0, 12, 19, 24), (0, 12, 15, 19), (0, 7, 12, 19), (0, 12, 17, 24), (0, 12, 19, 22)][v]
    return reverb(stereo(braam(r, [D1, D1, E2 - 12, A1, D1][v], ch, 5.0)), r, 3.5, 0.28)


@sfx("10 Grand Impacts & Swells", "Grand_Taiko_Hit", 5, desc="Big taiko-style drum hit")
def _(v, r):
    return reverb(stereo(taiko(r, [52, 58, 48, 64, 55][v], 3.0)), r, 2.8, 0.25)


@sfx("10 Grand Impacts & Swells", "Grand_Sub_Boom", 4, desc="Deep sub boom (cut to a wide mountain shot)")
def _(v, r):
    return reverb(stereo(boom(r, [42, 38, 46, 50][v], 6.0)), r, 3.5, 0.25)


@sfx("10 Grand Impacts & Swells", "Grand_Echo_Boom", 3, desc="Boom that echoes across the valley")
def _(v, r):
    return mountain_echo(reverb(stereo(mx(boom(r, [44, 40, 48][v], 4.0), taiko(r, 56, 4.0) * 0.4)), r, 2.0, 0.2), r)


@sfx("10 Grand Impacts & Swells", "Grand_Whoosh_In", 4, desc="Deep, slow whoosh into a moment (1.5-3 s)")
def _(v, r):
    return reverb(grand_whoosh(r, [1.5, 2.0, 2.5, 3.0][v], "in"), r, 2.5, 0.2)


@sfx("10 Grand Impacts & Swells", "Grand_Whoosh_Out", 4, desc="Deep whoosh leaving")
def _(v, r):
    return reverb(grand_whoosh(r, [1.2, 1.6, 2.0, 2.5][v], "out"), r, 2.5, 0.2)


@sfx("10 Grand Impacts & Swells", "Grand_Riser_Hit", 3, desc="Low riser that lands on a big hit (hit at 4.0 s)")
def _(v, r):
    y = canvas(9.0)
    d = 4.0
    u = np.linspace(0, 1, n_(d))
    ris = sum(osc(hz(m) * 2 ** (u ** 2 * [12, 7, 5][v] / 12), d, "saw") for m in (D2, A2, D3)) / 3
    ris = sweep(ris, 150 + 3000 * u ** 2, 2.0, fmin=40) * u ** 2 * 0.6
    ris += sweep(pink(d, r), 150 + 6000 * u ** 3, 1.0) * u ** 3 * 0.4
    put(y, widen(ris, r, 0.8), 0)
    put(y, stereo([mx(taiko(r, 52, 4.0), boom(r, 42, 4.0) * 0.6), braam(r, D1, (0, 12, 19, 24), 4.5), mx(gong(r, 80, 5.0) * 0.7, boom(r, 44, 4.0) * 0.5)][v]), d)
    return reverb(y, r, 3.2, 0.25)


@sfx("10 Grand Impacts & Swells", "Grand_Reverse_Swell", 3, desc="Deep reverse swell (lands at the end, 2.5 s)")
def _(v, r):
    d = 2.5
    x = stereo([gong(r, 80, d), boom(r, 44, d), temple_bell(r, 110, d)][v])
    x = reverb(x, r, 2.0, 0.5)[: n_(d)]
    return fade(x[::-1].copy(), 0.3, 0.005)


# ---------------------------------------------------------------- 11 Grand Bells & Horns
@sfx("11 Grand Bells & Horns", "Grand_Gong", 3, desc="Big gong / tam-tam swell (10 s)")
def _(v, r):
    return reverb(widen(gong(r, [70, 85, 60][v], 10.0, v != 1), r, 0.7), r, 4.0, 0.25)


@sfx("11 Grand Bells & Horns", "Grand_Temple_Bell_Deep", 3, desc="Very deep mandir bell (10 s tail)")
def _(v, r):
    return reverb(widen(temple_bell(r, [110, 98, 131][v], 10.0), r, 0.6), r, 4.5, 0.3)


@sfx("11 Grand Bells & Horns", "Grand_Singing_Bowl", 3, desc="Singing bowl, long and calm (monastery, sunrise)")
def _(v, r):
    return reverb(widen(singing_bowl(r, [196, 147, 262][v], 10.0), r, 0.5), r, 3.5, 0.25)


@sfx("11 Grand Bells & Horns", "Grand_Ransingha_Call", 4, desc="Himalayan copper horn call with valley echo (Kumaoni ransingha style)")
def _(v, r):
    calls = [[(A2, 0.8), (D3, 2.2)], [(D3, 0.7), (A2, 0.5), (D3, 2.4)], [(A2, 2.6)], [(E2 + 12, 0.6), (A2 + 12, 0.6), (D3, 2.2)]]
    return mountain_echo(reverb(pan(horn(r, calls[v]), 0), r, 2.2, 0.22), r)


# ---------------------------------------------------------------- 12 Grand Drones & Drums (seamless loops)
@sfx("12 Grand Drones & Drums", "Grand_Drone", 4, loop=30, level="rms", db=-24,
     desc="Cinematic low drone bed: warm D / hopeful Dmaj9 / dark / airy fifths")
def _(v, r):
    ch = [[D2, A2, D3], [D2, A2, E2 + 12, F2 + 13], [D1 + 12, A1 + 12, D2 + 3], [D2, A2, A3]][v]
    return drone(r, 30, ch, [520, 700, 330, 900][v], [0.08, 0.1, 0.06, 0.12][v])


@sfx("12 Grand Drones & Drums", "Grand_Dhol_Pulse", 3, loop=16, level="rms", db=-22,
     desc="Slow dhol-damau style drum pattern (journey, festival, procession)")
def _(v, r):
    bpm = [90, 100, 80][v]
    beat = 60 / bpm
    bars = 4
    L = bars * 4 * beat
    X = 0.5
    y = canvas(L + X + 1.5)
    pat = [(0, "low"), (1.5, "high"), (2, "low"), (2.5, "high"), (3, "high"), (3.5, "high")]
    for b in range(bars + 1):
        for pos, kind in pat:
            t = (b * 4 + pos) * beat
            if kind == "low":
                put(y, pan(taiko(r, 68, 1.0) * 0.8, -0.1), t)
            else:
                slap = bp(white(0.12, r), 300, 3000) * env_exp(0.12, 0.03, 0.001) + osc(330, 0.12) * env_exp(0.12, 0.05) * 0.5
                put(y, pan(slap * 0.8, 0.2), t)
    y = reverb(y, r, 1.6, 0.18)
    return seamless(y, L, X)


@sfx("12 Grand Drones & Drums", "Grand_Heavy_Gears", 3, loop=10, level="rms", db=-25,
     desc="Heavy, slow mechanism loop (big dial turning)")
def _(v, r):
    L, X = 10, 0.5
    y = canvas(L + X + 0.5)
    rate = [3, 4, 2.5][v]
    t, k = 0.0, 0
    while t < L + X + 0.3:
        put(y, pan(heavy_tick(r, 1.0 if k % 4 == 0 else 0.7), r.uniform(-0.2, 0.2)), t)
        t += 1 / rate
        k += 1
    y += pan(bp(brown(L + X + 0.5, r), 60, 300) * 0.08, 0)
    return seamless(reverb(y, r, 1.5, 0.2), L, X)


@sfx("12 Grand Drones & Drums", "Grand_Mountain_Air", 3, loop=30, level="rms", db=-24,
     desc="Vast mountain air: deep wind with a low sub presence")
def _(v, r):
    L, X = 30, 3.0
    d = L + X + 0.5
    chans = []
    for ch in range(2):
        g = 0.7 + 0.3 * smooth_noise(d, r, 0.12)
        base = lp(brown(d, r), [320, 420, 260][v]) * 0.9 + lp(pink(d, r), 900) * 0.15
        whistle = sweep(pink(d, r), 350 + 400 * g, 0.3) * 0.08
        sub = osc(hz(D1), d) * 0.12 * g
        chans.append(sub_clean((base + whistle) * g + sub))
    return seamless(np.stack(chans, 1), L, X)


# ---------------------------------------------------------------- brand stings, grand
@sfx("06 Bells & Brand", "Grand_Intro_Sting", 3, desc="GRAND logo sound for the SPP intro (drone rise, dots, bell, braam/horn on the name)")
def _(v, r):
    d = 6.5
    y = canvas(d)
    put(y, grand_whoosh(r, 0.6, "in") * 0.5, 0.0)
    dr = drone(r, 4.3, [D2, A2, D3], 300, 0.2, 0.5)
    put(y, dr * env_curve(4.3, [(0, 0), (1.5, 0.6), (2.3, 1), (4.0, 0.7), (4.3, 0)])[:, None] * 0.45, 0.3)
    for i in range(8):
        put(y, pan(marimba(r, [D3, D3 + 2, D3 + 4, D3 + 7, D3 + 9, D3 + 12, D3 + 14, D3 + 16][i], 0.9, 0.4) * 0.3, -0.3 + 0.08 * i), 1.6 + i * 0.08)
    put(y, pan([temple_bell(r, 220, 3.5), singing_bowl(r, 294, 3.5), gong(r, 110, 3.5)][v] * 0.5, 0.2), 1.9)
    hit = [braam(r, D1, (0, 12, 19, 24), 3.5), mx(taiko(r, 54, 3.5), boom(r, 42, 3.5) * 0.5), mx(horn(r, [(A2, 0.7), (D3, 1.8)]) * 0.6, boom(r, 44, 2.5) * 0.4)][v]
    put(y, stereo(hit) * 0.8, 2.3)
    put(y, grand_whoosh(r, 0.9, "out") * 0.35, 4.3)
    y = reverb(y, r, 3.0, 0.25)
    return mountain_echo(y, r) if v == 2 else y


@sfx("06 Bells & Brand", "Grand_EndCard_Sting", 3, desc="GRAND end-card sound (deep swell, bowl, warm low notes)")
def _(v, r):
    y = canvas(7.0)
    put(y, grand_whoosh(r, 0.6, "in") * 0.45, 0)
    put(y, pan(singing_bowl(r, [196, 147, 220][v], 5.0) * 0.45, 0), 0.3)
    for i, t0 in enumerate((0.8, 0.95, 1.2)):
        put(y, pan(marimba(r, [D3, A2 + 12, D3 + 7][i], 1.2, 0.4) * 0.35, -0.3 + 0.3 * i), t0)
    dr = drone(r, 4.5, [D2, A2], 400, 0.1, 0.5)
    put(y, dr * env_curve(4.5, [(0, 0), (1.0, 1), (3.5, 0.7), (4.5, 0)])[:, None] * 0.4, 1.3)
    return reverb(y, r, 3.0, 0.25)



# ================================================================ run
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(KIT / "SFX"))
    ap.add_argument("--only", default="")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    out = Path(a.out)
    cat = []
    t0 = time.time()
    for s in SOUNDS:
        key = f"{s['cat']} {s['name']}"
        if a.only and a.only.lower() not in key.lower():
            continue
        if a.list:
            print(f"{s['cat']:22s} {s['name']:30s} x{s['variants']}  {'LOOP ' + str(s['loop']) + 's' if s['loop'] else ''}  {s['desc']}")
            continue
        d = out / s["cat"]
        d.mkdir(parents=True, exist_ok=True)
        for v in range(s["variants"]):
            r = rng(s["cat"], s["name"], v)
            x = np.asarray(s["fn"](v, r), float)
            x = stereo(x)
            if not s["loop"]:
                x = fade(trim_silence(x), 0.0005, 0.02)
            if s["level"] == "rms":
                x = rms_norm(x, s["db"])
            else:
                x = peak_norm(x, s["db"])
            fn = f"SPP_{s['name']}" + (f"_LOOP_{round(len(x) / SR)}s" if s["loop"] else "") + f"_v{v + 1:02d}.wav"
            write_wav(d / fn, x)
            m = np.abs(x).max(axis=1)
            w = n_(0.05)
            env = np.convolve(m ** 2, np.ones(w) / w, "same")
            cat.append({"file": f"{s['cat']}/{fn}", "category": s["cat"], "name": s["name"], "variant": v + 1,
                        "seconds": round(len(x) / SR, 3), "peak": round(int(np.argmax(env)) / SR, 3),
                        "loop": bool(s["loop"]), "use": s["desc"]})
        print(f"  {key}  x{s['variants']}", flush=True)
    if not a.list:
        json.dump(cat, open(out / "sfx_catalog.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"{len(cat)} files -> {out}  ({time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main()
