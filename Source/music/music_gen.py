"""
Safar Pahad Parivar - background-music generator.

    python Source/music/music_gen.py                    # -> <kit>/Music   (all tracks, ~10-15 min)
    python Source/music/music_gen.py --only Bansuri     # just tracks whose name/theme contains "Bansuri"
    python Source/music/music_gen.py --list

Every track is composed in code (melodies written in sargam below) and played with real recorded instruments from
VSCO-2 Community Edition (CC0 public domain: strings, flute, upright piano, harp, glockenspiel, timpani, gong, bells)
plus synthesised tanpura, temple bells, manjira and mountain wind.  Fixed seeds -> identical on every PC, so the music
is not stored in git.  Output: 48 kHz / 24-bit stereo WAV,  Music/<NN Theme>/SPP_Music_<Name>.wav  (+ music_catalog.json)
"""
import argparse, json, os, sys, time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "sfx"))
from synth import *          # noqa
import samples as _smp
from sfx_gen import temple_bell, small_bell, singing_bowl, mx, hz  # noqa

KIT = HERE.parents[1]
L = [None]


def lib():
    return L[0]


# ================================================================ notation: sargam
SW = {"S": 0, "r": 1, "R": 2, "g": 3, "G": 4, "m": 5, "M": 6, "P": 7, "d": 8, "D": 9, "n": 10, "N": 11}


def sargam(text, sa):
    """Parse sargam into events [(midi, start_beat, beats, flags)].
    One space-separated token = one beat.  Inside a token several swaras share the beat ("SR" = two 1/2 beats,
    "S-R" = S 2/3 + R 1/3).  Octave: "." lower, "'" upper (S. = mandra Sa, S' = taar Sa).
    "-" holds the previous note, "_" is a rest, "|" is ignored.
    Ornaments before a swara: "~" = meend (glide from the previous note), "^" = kan (grace from the note above)."""
    ev, b = [], 0.0
    for tok in text.split():
        if tok == "|":
            continue
        units, i = [], 0
        while i < len(tok):
            c = tok[i]
            fl = ""
            while c in "~^":
                fl += c
                i += 1
                c = tok[i]
            if c in "-_":
                units.append((c, None, fl))
                i += 1
                continue
            if c not in SW:
                raise ValueError("bad swara %r in %r" % (c, tok))
            m = sa + SW[c]
            i += 1
            while i < len(tok) and tok[i] in ".'":
                m += -12 if tok[i] == "." else 12
                i += 1
            units.append(("n", m, fl))
        step = 1.0 / len(units)
        for kind, m, fl in units:
            if kind == "-":
                if ev:
                    ev[-1][2] += step
            elif kind == "_":
                pass
            else:
                ev.append([m, b, step, fl])
            b += step
    return [tuple(e) for e in ev], b


# ================================================================ mix bus
STATS = []


class Mix:
    def __init__(self, d, bpm=72, r=None):
        self.d, self.bpm = d, bpm
        self.beat = 60.0 / bpm
        self.dry = canvas(d + 12)
        self.wet = canvas(d + 12)
        self.r = r
        self.energy = {}            # per-instrument energy (for balancing; see --stats)

    def at(self, bar, beat=0, per_bar=4):
        return (bar * per_bar + beat) * self.beat

    def add(self, x, t, gain=1.0, pan_=0.0, send=0.25):
        x = stereo(np.asarray(x, float)) * gain
        tag = sys._getframe(1).f_code.co_name
        if tag == "_":
            tag = "track"
        self.energy[tag] = self.energy.get(tag, 0.0) + float(np.sum(x ** 2))
        if pan_:
            a = (pan_ + 1) * np.pi / 4
            x = x * np.array([np.cos(a), np.sin(a)]) * np.sqrt(2)
        put(self.dry, x, t)
        if send:
            put(self.wet, x, t, send)

    def render(self, t60=2.8, fade_out=4.0, target=-19.0):
        STATS.append(self.energy)
        r = self.r
        w = reverb(self.wet, r, t60, 1.0, damp=6500, pre=0.025)[: len(self.dry)]
        y = self.dry + w
        y = hp(y, 30, 2)
        # gentle glue: slow RMS compressor (-3..-4 dB on the loud parts)
        e = np.sqrt(lp(np.mean(y ** 2, axis=1), 2.0, 1) + 1e-12)
        db = 20 * np.log10(e + 1e-9)
        thr = np.percentile(db[db > -80], 85) - 2
        g = 10 ** (np.minimum(0, (thr - db) * (1 - 1 / 2.0)) / 20)
        y = y * g[:, None]
        y = trim_silence(y, -66, 0.3)
        y = y[: n_(self.d + 8)]
        if fade_out:
            y = fade(y, 0.01, min(fade_out, len(y) / SR / 3))
        return rms_norm(y, target, -1.0)


# ================================================================ instruments
def lev(x, target=0.1, a=0.0, b=0.6):
    """Scale a note so its RMS over [a, b] seconds is 'target' -> instrument gains become comparable."""
    seg = x[n_(a): max(n_(b), n_(a) + 64)]
    return x * (target / (np.sqrt(np.mean(np.asarray(seg) ** 2)) + 1e-7))


def smooth(t, a, b):
    u = np.clip((t - a) / max(b - a, 1e-6), 0, 1)
    return u * u * (3 - 2 * u)


def bansuri(M, text, sa, t0, beat, gain=1.0, key="fl_nv", pan_=0.05, send=0.35, glide_p=0.35, vib=0.2, breath=0.05,
            octave=0, seed=0):
    """Flute played like a bansuri: slurred phrases, meend glides, kan grace notes, delayed vibrato, breath."""
    r = rng("bansuri", text[:40], seed)
    ev, nb = sargam(text, sa + 12 * octave)
    prev_m, prev_end = None, -9
    for m, b, dur, fl in ev:
        t = t0 + b * beat
        ds = dur * beat
        joined = prev_m is not None and abs(t - prev_end) < 0.02
        glide = joined and ("~" in fl or (abs(m - prev_m) <= 4 and r.random() < glide_p))
        g0 = (prev_m - m) if glide else 0.0
        gt = min(0.28, 0.35 * ds) if "~" in fl else min(0.12, 0.3 * ds)
        kan = "^" in fl
        vr = 5.0 + r.uniform(-0.4, 0.4)
        vd = vib * (0.7 + 0.6 * r.random())

        def bend(tt_, g0=g0, gt=gt, kan=kan, ds=ds, vr=vr, vd=vd):
            y = g0 * (1 - smooth(tt_, 0, gt))
            if kan:
                y = y + 2.0 * (1 - smooth(tt_, 0.03, 0.075))
            onset = min(0.45, ds * 0.5)
            depth = vd * smooth(tt_, onset, onset + 0.6)
            return y + depth * np.sin(2 * np.pi * vr * tt_) * (tt_ > onset)

        x = lib().note(key, m, r, dur=ds + 0.08, vel=2, release=min(0.35, 0.25 + ds * 0.1), attack=None, bend=bend)
        # even out the recorded dynamics (low flute notes are much softer): same loudness for every note,
        # then a natural lift for higher notes
        core = x[n_(0.05): n_(0.05 + max(0.15, min(ds, 1.0)))]
        x = x * (0.12 / (np.sqrt(np.mean(core ** 2)) + 1e-6)) * (1 + 0.012 * (m - sa))
        if joined:                      # slur: no new tonguing, crossfade into the new pitch
            x = x[n_(0.10):]
            k = n_(0.05)
            x[:k] *= np.linspace(0, 1, k)[:, None]
        # breath: noise following the note's own envelope
        env = lp(np.abs(x).max(axis=1), 12, 1)
        br = bp(white(len(x) / SR, r), 1800, 7000) * env * breath * 4
        if not joined:
            puff = bp(white(0.12, r), 700, 3500) * np.linspace(1, 0, n_(0.12)) ** 2 * 0.03
            br[: len(puff)] += puff[: len(br)]
        # phrase shape: a little swell through long notes
        sh = 0.85 + 0.15 * smooth(np.arange(len(x)) / SR, 0, max(0.3, ds * 0.6))
        x = (x + stereo(br)) * sh[:, None]
        M.add(x, t - (0.03 if joined else 0.0), gain, pan_, send)
        prev_m, prev_end = m, t + ds
    return nb


def tanpura_pluck(r, f0, d=7.0, bright=1.0):
    """One tanpura string: harmonic pluck with the 'jawari' shimmer (a resonance sweeping up the harmonics)."""
    t = tt(d)
    y = np.zeros_like(t)
    c = 4 + 22 * (1 - np.exp(-t / 1.6))             # moving formant (harmonic number)
    for n in range(1, 34):
        f = f0 * n * (1 + 0.0004 * n)
        if f > 9000:
            break
        a = n ** -0.9 * np.exp(-t / (5.5 / (1 + 0.06 * n)))
        a = a * (0.35 + bright * 1.6 * np.exp(-((n - c) / 3.5) ** 2))
        ph = r.uniform(0, 2 * np.pi)
        y += a * np.sin(2 * np.pi * f * t + ph)
        y += 0.35 * a * np.sin(2 * np.pi * f * (1.0015) * t + ph)   # second string of the course -> slow beating
    att = np.clip(t / 0.004, 0, 1)
    return fade(y * att, 0.0005, 0.6)


def tanpura(M, sa, t0, t1, cycle=4.6, first="P", gain=0.35, send=0.3):
    """Classic 4-string pattern (Pa/Ma - Sa - Sa - Sa-mandra), looping from t0 to t1."""
    r = rng("tanpura", sa, first)
    f_sa = hz(sa)
    fr = {"P": hz(sa - 5), "m": hz(sa - 7), "N": hz(sa - 1)}[first]
    strings = [fr, f_sa, f_sa, f_sa / 2]
    cache = {i: [lev(tanpura_pluck(rng("tp", sa, i, v), f, 7.5, [0.9, 1.1, 1.0, 0.8][i]), 0.1, 0, 1.0) for v in range(3)]
             for i, f in enumerate(strings)}
    t, k = t0, 0
    while t < t1:
        for i in range(4):
            tp = t + i * cycle / 4 + r.uniform(-0.03, 0.03)
            if tp >= t1:
                break
            x = cache[i][k % 3] * (0.9 + 0.2 * r.random())
            M.add(x, tp, gain * (0.8 if i == 3 else 1.0), [-0.35, 0.1, -0.1, 0.3][i], send)
        t += cycle
        k += 1


def manjira(r, gain=1.0, open_=True):
    """Small temple cymbals (manjira / jhanj): bright inharmonic clink; open rings, closed is choked."""
    d = 1.6 if open_ else 0.25
    f0 = r.uniform(2350, 2550)
    y = partials(f0, [1, 1.47, 2.09, 2.56, 3.32, 4.1], [1, 0.7, 0.55, 0.4, 0.3, 0.2],
                 [0.9, 0.7, 0.5, 0.4, 0.3, 0.2] if open_ else [0.08] * 6, d, detune=0.006, r=r)
    hit = hp(white(d, r), 5000) * env_exp(d, 0.02 if open_ else 0.01) * 0.25
    return lev(fade((y + hit) * gain, 0.0003, 0.05), 0.1, 0, 0.3)


def wind_bed(r, d, kind=0, level=1.0):
    chans = []
    for ch in range(2):
        g = [0.8, 0.62, 0.7][kind] + [0.2, 0.38, 0.3][kind] * smooth_noise(d, r, [0.1, 0.25, 0.18][kind])
        base = lp(brown(d, r), 500) * 0.8 + lp(pink(d, r), 1400) * 0.25
        whistle = sweep(pink(d, r), 450 + 700 * (g ** 2) * [0.6, 1, 1.4][kind], 0.25) * (0.3 if kind == 2 else 0.12)
        chans.append((base + whistle) * g ** 1.5)
    y = np.stack(chans, 1)
    return y / (np.sqrt(np.mean(y ** 2)) + 1e-9) * 0.05 * level


def pad(M, chord_by_key, t, d, gain=0.5, attack=1.2, release=2.0, send=0.35, vel=1, seed=0):
    r = rng("pad", t, seed)
    n = sum(len(v) for v in chord_by_key.values())
    for key, ms in chord_by_key.items():
        for m in ms:
            x = lev(lib().note(key, m, r, dur=d, vel=vel, attack=None, release=release), 0.1, 0.4, 1.4)
            k = min(len(x), n_(attack))
            x[:k] *= np.linspace(0, 1, k)[:, None] ** 1.5
            M.add(x, t + r.uniform(0, 0.08), gain / np.sqrt(n), {"vln_sus": -0.3, "vla_sus": 0.25, "vc_sus": 0.1,
                                                                  "cb_sus": 0.0, "svln_sus": -0.1}.get(key, 0), send)


def piano(M, m, t, d=2.0, vel=1, gain=0.5, pan_=0.0, send=0.3, r=None):
    x = lev(lib().note("piano", m, r or rng("pno", m, t), dur=d, vel=vel, release=0.9), 0.1, 0, 0.4)
    M.add(x, t, gain, pan_ + (m - 60) / 80, send)


def pluck(M, key, m, t, gain=0.5, pan_=0.0, send=0.3, vel=None, r=None):
    M.add(lev(lib().note(key, m, r or rng(key, m, t), vel=vel), 0.1, 0, 0.3), t, gain, pan_, send)


def chord_tones(root, kind="maj"):
    return [root + i for i in {"maj": (0, 4, 7), "min": (0, 3, 7), "sus2": (0, 2, 7), "sus4": (0, 5, 7),
                                "add9": (0, 4, 7, 14), "m7": (0, 3, 7, 10), "maj7": (0, 4, 7, 11), "5": (0, 7)}[kind]]


def near(ms, lo, hi):
    """Fold notes into [lo, hi)."""
    out = []
    for m in ms:
        while m < lo:
            m += 12
        while m >= hi:
            m -= 12
        out.append(m)
    return sorted(out)


def strings_chord(root, kind, lo=50, hi=74):
    ct = chord_tones(root, kind)
    return {"cb_sus": [root % 12 + 28],
            "vc_sus": near([ct[0], ct[-1]], 38, 57), "vla_sus": near(ct[1:3], 50, 67), "vln_sus": near(ct, 62, 79)}


def temple(M, t, f0, gain=0.4, pan_=0.0, send=0.5, seed=0, d=7.0):
    M.add(lev(temple_bell(rng("tb", t, seed), f0, d), 0.1, 0, 1.0), t, gain, pan_, send)


def nep_bell(M, t, gain=0.3, pan_=0.0, send=0.4, seed=0):
    M.add(lev(lib().raw("nepal_bells", rng("nb", t, seed)), 0.1, 0, 0.5), t, gain, pan_, send)


def gong_hit(M, t, gain=0.4, send=0.4, seed=0):
    M.add(lev(lib().raw("gong", rng("gong", t, seed)), 0.1, 0, 2.0), t, gain, 0, send)


def bowed(M, key, text, sa, t0, beat, gain=0.5, pan_=0.0, send=0.35, vel=2, attack=0.12, legato=0.18, release=0.7, seed=0):
    """A legato string (or other sustained) line written in sargam."""
    r = rng("bowed", key, text[:30], seed)
    ev, nb = sargam(text, sa)
    for m, b, dur, fl in ev:
        ds = dur * beat
        x = lev(lib().note(key, m, r, dur=ds + legato, vel=vel, release=release), 0.1, 0.1, max(0.4, min(ds, 1.2)))
        k = min(len(x), n_(attack))
        x[:k] *= np.linspace(0, 1, k)[:, None]
        M.add(x, t0 + b * beat, gain, pan_, send)
    return nb


def arp(M, key, notes, t, step, gain=0.3, pan_=0.0, send=0.3, vel=None, accent=1.25, seed=0):
    r = rng("arp", key, t, seed)
    for i, m in enumerate(notes):
        if m is None:
            continue
        g = gain * (accent if i == 0 else 1.0) * (0.9 + 0.2 * r.random())
        pluck(M, key, m, t + i * step + r.uniform(-0.006, 0.006), g, pan_ + 0.25 * np.sin(i), send, vel, r)


def bdrum(M, t, gain=0.3, send=0.15, seed=0):
    M.add(lev(lib().raw("bdrum", rng("bd", t, seed), 3), 0.1, 0, 0.25), t, gain, 0, send)


def timpani(M, t, gain=0.4, vel=4, send=0.3, seed=0):
    M.add(lev(lib().raw("timp_hit", rng("tim", t, seed), vel), 0.1, 0, 0.3), t, gain, 0.1, send)


def timp_roll_to(M, land, d=4.0, gain=0.35, seed=0):
    """Timpani roll crescendo that arrives at 'land' seconds."""
    x = lib().raw("timp_roll", rng("tr", land, seed))[: n_(d)]
    x = lev(x, 0.1, 0, d) * np.linspace(0.15, 1, len(x))[:, None] ** 2
    M.add(fade(x, 0.3, 0.05), land - d, gain, 0.1, 0.3)


def cymbal_swell(M, land, gain=0.3):
    import sfx_gen
    x, st = sfx_gen.cymbal_to(rng("cy", land), land)
    M.add(lev(x, 0.1, 0, len(x) / SR), st, gain, 0, 0.35)


def ghanti(M, t, d, gain=0.12, seed=0):
    """Hand bell rung continuously during aarti."""
    r = rng("ghanti", t, seed)
    f0 = r.uniform(1450, 1650)
    tt_ = 0.0
    while tt_ < d:
        x = lev(small_bell(r, f0 * (1 + r.uniform(-0.004, 0.004)), 1.2), 0.1, 0, 0.3)
        M.add(x, t + tt_, gain * (0.5 + 0.5 * r.random()) * min(1, (tt_ + 0.3) / 1.0) * min(1, (d - tt_) / 1.0 + 0.05),
              0.35, 0.4)
        tt_ += 1 / 7.0 + r.uniform(-0.02, 0.02)


def bowl(M, t, f0, gain=0.25, pan_=0.0, send=0.4, seed=0):
    M.add(lev(singing_bowl(rng("bowl", t, seed), f0, 10.0), 0.1, 0, 2.0), t, gain, pan_, send)


def drone(M, notes, t, d, gain=0.3, keys=("vc_sus", "cb_sus"), send=0.3, seed=0):
    """Long bowed drone built from overlapping sustained notes (never a hard restart)."""
    r = rng("drone", t, seed)
    seg = 9.0
    tt_ = t
    while tt_ < t + d:
        for key, m in zip(keys, notes):
            x = lev(lib().note(key, m, r, dur=seg, vel=1, release=3.0), 0.1, 1.0, 4.0)
            x *= env_curve(len(x) / SR, [(0, 0), (2.5, 1), (len(x) / SR - 3, 1), (len(x) / SR, 0)])[: len(x), None]
            M.add(x, tt_, gain / np.sqrt(len(notes)), 0.1 if "vc" in key else -0.1, send)
        tt_ += seg - 3.0


# ================================================================ tracks
TRACKS = []


def track(theme, name, desc, bpm, mood=""):
    def w(fn):
        TRACKS.append(dict(theme=theme, name=name, desc=desc, bpm=bpm, mood=mood, fn=fn))
        return fn
    return w


# ---------------------------------------------------------------- 04 Flute (bansuri-style)
@track("04 Flute", "Bansuri_Valley", "Bansuri alaap over tanpura, then a gentle Bhupali tune with harp and strings - valleys, villages, slow drives",
       84, "calm, warm")
def _(r):
    sa = 64                                  # Sa = E4 (flute), tanpura an octave lower
    M = Mix(150, 84, r)
    b = M.beat
    tanpura(M, sa - 12, 0.0, 146, 4.8, "P", 0.24)
    M.add(wind_bed(r, 40, 0, 0.6) * env_curve(40, [(0, 0), (4, 1), (30, 0.6), (40, 0)])[:, None], 0, 1.0, 0, 0.1)
    # alaap - free and slow (a beat of 0.95 s)
    al = ("_ S D. - ~S - - - R G - ~R - S - - - _ _ "
          "G - P - ~G - R - G - - - ~R - S - D. - ~S - - - _ _ "
          "P - D - S' - - - ~D - P - G - ~P - - - G R S - - - - _")
    t = 2.5 + bansuri(M, al, sa, 2.5, 0.95, 0.9, send=0.45) * 0.95
    # gat - 16-beat lines at 84 bpm
    lines = {"A": "G G P - D P G - R G P - G R S -",
             "B": "S R G P D S' D P G - R G ~P - - -",
             "C": "D S' R' - S' D P - D S' D P G - R -",
             "D": "G R S D. S - R - G - P G R - S -"}
    prog = [(52, "5"), (49, "m7"), (45, "add9"), (47, "sus4")]      # E5  C#m7  Aadd9  Bsus4 (one chord per 4 beats)
    order = ["intro", "intro", "A", "B", "A", "B", "C", "D", "C", "D", "solo", "A", "B", "end"]
    t0 = t + 0.5
    for li, name in enumerate(order):
        ts = t0 + li * 16 * b
        full = name in ("C", "D") or li >= 11
        for ci, (root, kind) in enumerate(prog):
            tc = ts + ci * 4 * b
            if name == "end" and ci > 1:
                break
            ct = chord_tones(root, kind)
            # harp: rising 8th-note arpeggio
            arp = near(ct + [ct[0] + 12], 57, 81)
            for k in range(8):
                pluck(M, "harp", arp[k % len(arp)] + (12 if k >= 4 and k % 2 else 0), tc + k * b / 2,
                      0.28 if k % 2 else 0.36, -0.25 + 0.07 * k, 0.35, vel=3)
            pluck(M, "vc_pizz", root - 12 if root > 47 else root, tc, 0.4, 0.1, 0.2, vel=2)
            pluck(M, "vc_pizz", root - 5 if root > 44 else root + 7, tc + 2 * b, 0.28, 0.1, 0.2, vel=1)
            if li >= 2:
                pad(M, strings_chord(root, kind), tc, 4 * b, 0.5 if full else 0.32, 1.0, 1.6, seed=li)
        if name in lines:
            bansuri(M, lines[name], sa, ts, b, 1.0, send=0.3, seed=li)
        elif name == "solo":
            bansuri(M, "S' - - R' G' - R' S' D - S' - ~D - P - G - P D S' - D P G - - - ~R - - -", sa, ts, b, 0.95, send=0.4)
    te = t0 + (len(order) - 1) * 16 * b + 8 * b
    bansuri(M, "G R S - - - - - - -", sa, te - 8 * b, b, 0.9, send=0.45, seed=99)
    pad(M, strings_chord(52, "add9"), te - 2 * b, 8, 0.45, 1.5, 3.0, seed=77)
    temple(M, te + 0.3, 330, 0.3, 0.2)
    M.d = te + 9
    return M.render(3.0)


# ---------------------------------------------------------------- 01 Slow Build
@track("01 Slow Build", "First_Light", "Piano arpeggios at dawn, strings join one by one and rise to a warm full climax - openings, sunrise, first views",
       72, "hopeful, rising")
def _(r):
    M = Mix(160, 72, r)
    b = M.beat
    bar = 4 * b
    prog = [(50, "maj"), (47, "min"), (43, "maj"), (45, "maj")]          # D  Bm  G  A
    A1 = "P - G R | G - - - | D - P m | R - - - | P - S' N | D - - P | m - G R | R - - -"
    A2 = "P - G R | G - - - | D - P m | R - - - | P - S' R' | S' - D P | m G R G | R - S -"
    B = "S' - - N | D - - P | D S' D P | G - - - | P - S' R' | G' - R' S' | D - P m | G - R -"
    sec = ["intro"] * 4 + ["A"] * 8 + ["A2"] * 8 + ["B"] * 8 + ["C"] * 8 + ["out"] * 4
    for i, name in enumerate(sec):
        t = 1.0 + i * bar
        root, kind = prog[i % 4]
        ct = chord_tones(root, kind)
        third = ct[1] - root
        pat = [root, root + 7, root + 12, root + 12 + third, root + 19, root + 12 + third, root + 12, root + 7]
        vel = 1 if name in ("intro", "A", "out") else 2
        for k, m in enumerate(pat):
            piano(M, m, t + k * b / 2, 1.2 * b, vel, 0.33 if k else 0.4, -0.1, 0.3, r)
        if name != "intro":
            piano(M, root - 12, t, bar, vel, 0.3, 0, 0.25, r)
        if name in ("A2", "B", "C"):
            pad(M, {"vc_sus": near([root], 38, 50), "vla_sus": near(ct[1:], 55, 67)}, t, bar, 0.34, 1.2, 1.6, seed=i)
        if name in ("B", "C"):
            pad(M, {"vln_sus": near(ct, 66, 81), "cb_sus": [root % 12 + 28]}, t, bar, 0.36 if name == "B" else 0.48,
                1.0, 1.6, seed=i + 50)
        if name == "C" and i % 4 == 0:
            timpani(M, t, 0.45, 4)
        if name == "C":
            bdrum(M, t, 0.25) if i % 2 == 0 else None
    t0 = 1.0 + 4 * bar
    bowed(M, "svln_sus", A1, 62 + 12, t0, b, 0.55, -0.05, 0.4)
    bowed(M, "svln_sus", A2, 62 + 12, t0 + 8 * bar, b, 0.55, -0.05, 0.4, seed=1)
    bowed(M, "vln_sus", B, 62 + 12, t0 + 16 * bar, b, 0.6, -0.1, 0.35)
    bowed(M, "vc_sus", A2, 62 - 12, t0 + 16 * bar, b, 0.35, 0.2, 0.3)
    tc = t0 + 24 * bar
    timp_roll_to(M, tc, 4.0, 0.4)
    cymbal_swell(M, tc, 0.3)
    bowed(M, "vln_sus", A2, 62 + 12, tc, b, 0.65, -0.15, 0.35, seed=2)
    bansuri(M, A2, 62 + 12, tc, b, 0.3, key="fl_sus", pan_=-0.3, send=0.45, glide_p=0.1, vib=0.0, breath=0.02, seed=3)
    bowed(M, "vla_sus", A2, 62, tc, b, 0.35, 0.25, 0.35, seed=4)
    te = 1.0 + len(sec) * bar
    piano(M, 50, te, 6, 1, 0.4, 0, 0.4, r); piano(M, 62, te, 6, 1, 0.3, 0, 0.4, r); piano(M, 66, te + 0.1, 6, 1, 0.25, 0, 0.4, r)
    pad(M, {"vln_sus": [66, 69, 74], "vla_sus": [62], "vc_sus": [50]}, te, 6, 0.35, 1.0, 3.0, seed=9)
    M.d = te + 8
    return M.render(2.6)


@track("01 Slow Build", "Long_Road_Up", "Driving string ostinato and pizzicato pulse that keeps adding layers - long drives, climbs, road montages",
       92, "determined, forward")
def _(r):
    M = Mix(150, 92, r)
    b = M.beat
    bar = 4 * b
    prog = [(47, "min"), (43, "maj"), (50, "maj"), (45, "maj")]          # Bm  G  D  A
    mel = "D. - S R | G - - R | S - - P. | N. - - - | D. - S R | G - P - | D - P G | R - - -"
    mel2 = "D - S' R' | G' - - R' | S' - - P | N - - - | D - S' R' | G' - P' - | D' - P' G' | R' - - -"
    sec = ["o"] * 8 + ["p"] * 8 + ["m"] * 8 + ["h"] * 8 + ["br"] * 4 + ["f"] * 8 + ["end"] * 2
    for i, nm in enumerate(sec):
        t = 1.0 + i * bar
        root, kind = prog[i % 4]
        ct = chord_tones(root, kind)
        if nm == "end":
            if i == len(sec) - 2:
                pad(M, strings_chord(47, "min"), t, 2 * bar, 0.6, 0.05, 3.0, seed=i)
                timpani(M, t, 0.5, 5)
                bdrum(M, t, 0.4)
            continue
        if nm != "br":
            hi = near([root + 12, root + 19, root + 24, root + 19], 66, 86)
            arp(M, "vln_spic", hi * 2, t, b / 2, 0.16 if nm in ("o", "p") else 0.22, -0.3, 0.25, vel=1, seed=i)
            for q in range(4):
                pluck(M, "vc_pizz", near([root], 38, 50)[0] + (7 if q == 2 else 0), t + q * b, 0.34 if q % 2 == 0 else 0.24,
                      0.15, 0.15, 2 if q == 0 else 1, r)
        if nm in ("p", "m", "h", "br", "f"):
            pad(M, {"cb_sus": [root % 12 + 28], "vla_sus": near(ct, 55, 67)}, t, bar, 0.3 if nm != "f" else 0.45, 0.8, 1.2, seed=i)
        if nm in ("h", "f"):
            bdrum(M, t, 0.3); bdrum(M, t + 2.5 * b, 0.18, seed=1)
        if nm == "f" and i % 2 == 0:
            timpani(M, t, 0.4, 4)
        if nm in ("br",):
            arp(M, "harp", near(ct + [ct[0] + 12], 62, 86), t, b / 2, 0.25, -0.2, 0.4, 3, seed=i)
    t = 1.0 + 16 * bar
    bowed(M, "vc_sus", mel, 62 - 12, t, b, 0.55, 0.2, 0.3)
    bowed(M, "vc_sus", mel, 62 - 12, t + 8 * bar, b, 0.45, 0.2, 0.3, seed=1)
    bowed(M, "vln_sus", mel2, 62, t + 8 * bar, b, 0.5, -0.2, 0.35)
    tb = 1.0 + 32 * bar
    bansuri(M, "S' - - - | D - P - | G - - - | R - - -", 74, tb, b, 0.55, send=0.45)
    tf = 1.0 + 36 * bar
    timp_roll_to(M, tf, 3.5, 0.4)
    cymbal_swell(M, tf, 0.3)
    bowed(M, "vln_sus", mel2, 62, tf, b, 0.6, -0.2, 0.35, seed=2)
    bowed(M, "vc_sus", mel, 62 - 12, tf, b, 0.45, 0.2, 0.3, seed=2)
    bowed(M, "vla_sus", mel, 62, tf, b, 0.35, 0.3, 0.35, seed=3)
    M.d = 1.0 + len(sec) * bar + 5
    return M.render(2.4)


@track("01 Slow Build", "Summit_Rise", "Very slow orchestral rise from a low drone to a big final chord with timpani and gong - summits, peaks, the big reveal",
       60, "epic, emotional")
def _(r):
    M = Mix(160, 60, r)
    b = M.beat
    bar = 4 * b
    prog = [(52, "maj"), (49, "min"), (45, "maj"), (47, "sus4")]          # E  C#m  A  Bsus4
    mel = "G - - - | S - R G | P - - G | R - - - | G - P D | S' - D P | G - R G | R - - -"
    drone(M, [40, 28], 0.5, 36, 0.4)
    for i in range(32):
        t = 4.0 + i * bar
        root, kind = prog[i % 4]
        if i % 4 == 3 and i >= 8:
            kind = "maj" if i % 8 == 7 else "sus4"
        ct = chord_tones(root, kind)
        lay = {"vla_sus": near(ct, 55, 67)}
        if i >= 4:
            lay["vc_sus"] = near([root], 38, 50)
        if i >= 12:
            lay["vln_sus"] = near(ct, 64, 79)
        if i >= 20:
            lay["cb_sus"] = [root % 12 + 28]
        pad(M, lay, t, bar, 0.26 + 0.24 * min(1, i / 24), 1.5 if i < 8 else 0.9, 1.6, seed=i)
        if i >= 8:
            arp(M, "harp", near(ct + [ct[0] + 12, ct[1] + 12], 64, 88), t, b / 2, 0.2, -0.2, 0.4, 3, seed=i)
        if i >= 24 and i % 2 == 0:
            timpani(M, t, 0.35, 4)
    bowed(M, "svln_sus", mel, 64 + 12, 4.0 + 8 * bar, b, 0.55, -0.05, 0.45)
    bowed(M, "vln_sus", mel, 64 + 12, 4.0 + 16 * bar, b, 0.55, -0.15, 0.35, seed=1)
    bowed(M, "vc_sus", mel, 64 - 12, 4.0 + 16 * bar, b, 0.35, 0.2, 0.3, seed=1)
    tc = 4.0 + 24 * bar
    timp_roll_to(M, tc, 4.0, 0.45)
    cymbal_swell(M, tc, 0.35)
    bowed(M, "vln_sus", mel, 64 + 12, tc, b, 0.6, -0.15, 0.35, seed=2)
    bansuri(M, mel, 64 + 12, tc, b, 0.3, key="fl_sus", pan_=-0.3, send=0.45, glide_p=0.1, vib=0.0, breath=0.02, seed=3)
    bowed(M, "vla_sus", mel, 64, tc, b, 0.35, 0.3, 0.35, seed=4)
    te = 4.0 + 32 * bar
    timp_roll_to(M, te, 3.0, 0.4, seed=1)
    pad(M, {"vln_sus": [68, 71, 76, 80], "vla_sus": [64, 59], "vc_sus": [52, 40], "cb_sus": [28]}, te, 7, 0.75, 0.05, 4.0, seed=99)
    timpani(M, te, 0.55, 5)
    gong_hit(M, te, 0.35)
    M.d = te + 11
    return M.render(3.2, fade_out=5.0)


# ---------------------------------------------------------------- 02 Temple Bells
@track("02 Temple Bells", "Mandir_Dawn", "Tanpura, distant temple bells, singing bowl and a low bansuri at first light - temples, ghats, quiet mornings",
       60, "serene, devotional")
def _(r):
    M = Mix(160, 60, r)
    b = 1.1
    tanpura(M, 50, 0.0, 150, 5.0, "P", 0.22)
    drone(M, [38, 26], 6.0, 140, 0.3)
    bells = [(2.0, 293, -0.4), (14, 220, 0.5), (29, 330, -0.2), (47, 293, 0.3), (66, 196, -0.5), (83, 330, 0.4),
             (101, 293, -0.3), (118, 220, 0.2), (136, 196, 0.0)]
    for t, f, p in bells:
        temple(M, t, f, 0.33, p, 0.6, d=9.0)
    for t, f in [(8, 147), (58, 196), (108, 147)]:
        bowl(M, t, f, 0.28, 0.2)
    for t in (22, 75, 128):
        nep_bell(M, t, 0.14, 0.5); nep_bell(M, t + 1.3, 0.1, -0.4, seed=1)
    al = ("_ S - - - D. - ~S - - - R - G - - ~R - - S - - - _ _ "
          "G - P - - - ~G - R - G - - - ~R - S - - - _ _ _ "
          "P - D - S' - - - ~D - P - - - G - ~P - - - G - R - S - - - - - _ _")
    t = 18.0 + bansuri(M, al, 62, 18.0, b, 0.8, send=0.5, glide_p=0.5) * b
    for i, (root, kind) in enumerate([(50, "add9"), (43, "add9"), (50, "add9"), (45, "sus4"), (50, "add9")]):
        pad(M, strings_chord(root, kind), 80 + i * 11, 12, 0.32, 3.0, 3.0, seed=i)
    mel = "G - P - D - P - G - R - S - - - R - G - P - G R S - - - - - - -"
    bansuri(M, mel, 62, 86, b, 0.8, send=0.5, glide_p=0.5, seed=1)
    bansuri(M, "S' - - - D - P - G - - - R - - - S - - - - - - -", 62, 122, b, 0.75, send=0.55, glide_p=0.6, seed=2)
    temple(M, 146, 147, 0.4, 0, 0.6, seed=9, d=10.0)
    M.d = 156
    return M.render(3.5, fade_out=6.0)


@track("02 Temple Bells", "Aarti_Glow", "Joyful aarti feel: manjira, hand bells and a devotional tune on flute and strings - temple visits, festivals, evening aarti",
       84, "devotional, joyful")
def _(r):
    M = Mix(150, 84, r)
    b = M.beat
    bar = 4 * b
    A = "S S R G | G - G - | G m P m | G - - - | G G m P | P - D P | m G R G | S - - -"
    B = "P P D P | S' - S' - | D S' R' S' | D - P - | m m P D | P - m G | R G m G | S - - -"
    chA = [(50, "maj"), (50, "maj"), (43, "maj"), (50, "maj"), (43, "maj"), (43, "maj"), (45, "maj"), (50, "maj")]
    chB = [(50, "maj"), (43, "maj"), (43, "maj"), (50, "maj"), (43, "maj"), (50, "maj"), (45, "maj"), (50, "maj")]
    plan = [("intro", None)] * 2 + [("A", "fl"), ("A", "vl"), ("B", "fl"), ("A", "both"), ("B", "both"), ("A", "all")]
    temple(M, 0.3, 293, 0.4, -0.3, 0.6)
    t = 1.0
    for sec, who in plan:
        chords = chA if sec in ("A", "intro") else chB
        nbars = 1 if sec == "intro" else 8
        for k in range(nbars):
            root, kind = chords[k]
            ct = chord_tones(root, kind)
            tb = t + k * bar
            for q in range(4):
                M.add(manjira(rng("mj", tb, q), 1.0, q % 2 == 0), tb + q * b, 0.12 if q % 2 == 0 else 0.07, 0.3, 0.3)
            pluck(M, "vc_pizz", near([root], 38, 50)[0], tb, 0.4, 0.1, 0.2, 2, r)
            pluck(M, "vc_pizz", near([root + 7], 38, 52)[0], tb + 2 * b, 0.3, 0.1, 0.2, 1, r)
            arp(M, "harp", near(ct, 62, 76) + near(ct, 74, 88)[::-1] + [None, None], tb, b / 2, 0.22, -0.2, 0.35, 3, seed=int(tb))
            if sec != "intro":
                pad(M, strings_chord(root, kind), tb, bar, 0.28 if who == "fl" else 0.4, 0.5, 1.2, seed=int(tb * 7))
            if who in ("both", "all") and k % 2 == 0:
                bdrum(M, tb, 0.22)
        if sec == "intro":
            t += bar
            continue
        mel = A if sec == "A" else B
        if who in ("fl", "both", "all"):
            bansuri(M, mel, 74, t, b, 0.75, send=0.35, glide_p=0.15, vib=0.12, seed=int(t))
        if who in ("vl", "both", "all"):
            bowed(M, "vln_sus", mel, 62 + (12 if who == "vl" else 0), t, b, 0.5, -0.15, 0.35, seed=int(t))
        if who == "all":
            arp(M, "glock", [n for n, _, _, _ in sargam(mel, 86)[0]][:16], t, b, 0.12, 0.3, 0.45)
            ghanti(M, t, 8 * bar, 0.08)
        t += 8 * bar
    temple(M, t, 293, 0.45, 0, 0.6, seed=3, d=9.0)
    pad(M, strings_chord(50, "maj"), t, 6, 0.4, 0.3, 3.0, seed=77)
    M.add(manjira(rng("mj", t), 1.0, True), t, 0.15, 0.3, 0.4)
    M.d = t + 9
    return M.render(2.4)


@track("02 Temple Bells", "Himalayan_Gongs", "No rhythm: gongs, singing bowls, Nepalese bells over a deep bowed drone - monasteries, meditation, time-lapses",
       0, "meditative, vast")
def _(r):
    M = Mix(160, 60, r)
    drone(M, [38, 26], 0.0, 150, 0.22)
    drone(M, [45, 33], 30.0, 90, 0.12, seed=1)
    tanpura(M, 50, 10.0, 150, 6.0, "P", 0.1)
    M.add(wind_bed(r, 150, 0, 0.18), 0, 1.0, 0, 0.05)
    for i, t in enumerate([1.0, 36, 72, 108, 140]):
        gong_hit(M, t, 0.35 if i else 0.3, seed=i)
    for i, (t, f) in enumerate([(12, 147), (24, 220), (48, 196), (60, 147), (84, 220), (96, 294), (120, 147), (130, 196)]):
        bowl(M, t, f, 0.25, [-0.5, 0.4, -0.2, 0.3][i % 4], seed=i)
    for i, t in enumerate(np.arange(18, 150, 13.0)):
        for k in range(3):
            nep_bell(M, t + k * r.uniform(0.6, 1.8), 0.1, r.uniform(-0.7, 0.7), 0.5, seed=i * 3 + k)
    M.d = 155
    return M.render(4.0, fade_out=8.0, target=-21)


# ---------------------------------------------------------------- 03 Wind
@track("03 Wind", "High_Pass", "Mountain wind with airy high strings, sparse harp and a slow flute - high passes, snow, drone shots, silence",
       66, "airy, open")
def _(r):
    M = Mix(150, 66, r)
    b = M.beat
    bar = 4 * b
    M.add(wind_bed(r, 145, 2, 0.8), 0, 1.0, 0, 0.05)
    prog = [((62, 64, 69), 50), ((62, 66, 69, 71), 47), ((62, 66, 71), 43), ((62, 64, 69), 45)]   # Dsus2 Bm7 Gmaj7 Asus4
    fl = "P - - - | - - G - | R - - - | - - - - | S' - - - | D - P - | G - - - | - - - -"
    for i in range(36):
        t = 2.0 + i * bar
        ch, root = prog[(i // 2) % 4]
        if i % 2 == 0:
            lay = {"vln_sus": near([c + 12 for c in ch], 74, 90)}
            if i >= 8:
                lay["vla_sus"] = near(list(ch), 60, 72)
            if i >= 16:
                lay["vc_sus"] = near([root], 38, 50)
            pad(M, lay, t, 2 * bar, 0.28 + 0.12 * (i >= 16), 2.5, 2.5, seed=i)
        for k in range(3):
            if r.random() < 0.55:
                pluck(M, "harp", PENT_D[r.integers(3, 10)], t + r.integers(0, 8) * b / 2, 0.3, r.uniform(-0.6, 0.6), 0.5, 3, r)
        if i % 4 == 2 and r.random() < 0.7:
            pluck(M, "glock", PENT_D[r.integers(5, 10)] + 12, t + 2 * b, 0.08, 0.4, 0.6, None, r)
    bansuri(M, fl, 74, 2.0 + 8 * bar, b, 0.6, send=0.55, glide_p=0.6, vib=0.15, breath=0.08)
    bansuri(M, fl, 74, 2.0 + 20 * bar, b, 0.6, send=0.55, glide_p=0.6, vib=0.15, breath=0.08, seed=1)
    M.d = 2.0 + 36 * bar + 6
    return M.render(3.5, fade_out=7.0)


PENT_D = [50, 52, 54, 57, 59, 62, 64, 66, 69, 71, 74, 76, 78, 81, 83]


@track("03 Wind", "Prayer_Flags", "Light fluttering harp and glockenspiel with a bright flute over the wind - prayer flags, ridge walks, sunny days",
       104, "bright, light")
def _(r):
    M = Mix(130, 104, r)
    b = M.beat
    bar = 4 * b
    M.add(wind_bed(r, 125, 1, 0.6), 0, 1.0, 0, 0.05)
    mel = "P D S' D | P - G - | R G P G | R - S - | P D S' R' | G' - R' S' | D S' D P | G - - -"
    prog = [(50, "sus2"), (47, "min"), (43, "add9"), (45, "sus4"), (50, "sus2"), (47, "min"), (43, "add9"), (45, "maj")]
    sec = ["i"] * 4 + ["A"] * 8 + ["A2"] * 8 + ["br"] * 4 + ["A"] * 8 + ["A3"] * 8 + ["e"] * 2
    for i, nm in enumerate(sec):
        t = 1.0 + i * bar
        root, kind = prog[i % 8] if nm != "e" else (50, "sus2")
        ct = chord_tones(root, kind)
        up = near(ct, 74, 88)
        flutter = [up[0], up[1], up[2], up[1]] * 4
        arp(M, "harp", flutter, t, b / 4, 0.14 if nm != "br" else 0.1, -0.35, 0.35, 3, accent=1.5, seed=i)
        if nm in ("A2", "A3", "br"):
            arp(M, "glock", [up[2] + 12, None, up[1] + 12, None, up[0] + 12, None, None, None], t, b / 2, 0.07, 0.4, 0.5, seed=i)
        if nm != "br":
            pluck(M, "vc_pizz", near([root], 38, 50)[0], t, 0.35, 0.1, 0.2, 2, r)
            pluck(M, "vc_pizz", near([root + 7], 40, 52)[0], t + 2 * b, 0.25, 0.1, 0.2, 1, r)
        if nm in ("A2", "A3", "br", "e"):
            pad(M, strings_chord(root, kind), t, bar, 0.3, 0.6, 1.4, seed=i)
        if nm == "e":
            break
    for st, nm_ in [(4, "A"), (12, "A2"), (24, "A"), (32, "A3")]:
        bansuri(M, mel, 74, 1.0 + st * bar, b, 0.7, send=0.35, glide_p=0.2, vib=0.12, seed=st)
    bowed(M, "vln_sus", mel, 74, 1.0 + 32 * bar, b, 0.35, -0.2, 0.35)
    M.d = 1.0 + (len(sec) - 1) * bar + 6
    return M.render(2.6)


@track("03 Wind", "Snowline", "Cold wind, deep cello drone, sparse piano and a lonely viola in a minor mode - snow, hardship, dusk, remote villages",
       56, "lonely, cold")
def _(r):
    M = Mix(160, 56, r)
    b = M.beat
    bar = 4 * b
    M.add(wind_bed(r, 150, 1, 0.8), 0, 1.0, 0, 0.05)
    drone(M, [38, 26], 3.0, 145, 0.35)
    prog = [(50, "min"), (46, "maj"), (43, "min"), (45, "sus4")]          # Dm  Bb  Gm  Asus4
    mel = "P - g - | m - R - | g - - R | S - - - | d - P - | m - g R | g - m - | R - - -"
    for i in range(32):
        t = 4.0 + i * bar
        root, kind = prog[i % 4]
        if i % 8 == 7:
            kind = "maj"
        ct = chord_tones(root, kind)
        if i >= 4:
            for k, m in enumerate(near(ct, 57, 72)):
                piano(M, m, t + k * b * 1.5 + r.uniform(0, 0.05), 2.5 * b, 1, 0.34, -0.2, 0.45, r)
            piano(M, near([root], 38, 50)[0], t, bar, 1, 0.34, 0, 0.35, r)
        if i >= 24:
            pad(M, {"vln_sus": near(ct, 62, 77), "vla_sus": near(ct, 55, 67)}, t, bar, 0.3, 1.5, 1.8, seed=i)
    bowed(M, "vla_sus", mel, 62, 4.0 + 8 * bar, b, 0.5, 0.1, 0.4)
    bowed(M, "vla_sus", mel, 62, 4.0 + 16 * bar, b, 0.45, 0.1, 0.4, seed=1)
    bowed(M, "vc_sus", "S - - - | R - - - | g - - - | m - - - | P - - - | d - - - | P - - - | N - - -", 50, 4.0 + 16 * bar, b, 0.3, 0.25, 0.3)
    bowed(M, "svln_sus", mel, 74, 4.0 + 24 * bar, b, 0.4, -0.1, 0.45)
    M.d = 4.0 + 32 * bar + 8
    return M.render(3.2, fade_out=7.0)


# ---------------------------------------------------------------- 04 Flute (more)
@track("04 Flute", "Pahadi_Dhun", "Cheerful Pahadi folk tune on flute in a lilting 6/8 with harp, pizzicato and manjira - village walks, markets, happy travel",
       72, "cheerful, folk")
def _(r):
    M = Mix(130, 72, r)
    e8 = 60.0 / 72 / 3                       # one 8th note (6/8, dotted-quarter = 72)
    bar = 6 * e8
    A = ("S - R G - P | G - R S - - | R - G P - D | P - - - - - | "
         "P - D S' - D | P - G R - S | R - G R - S | S - - - - - ")
    B = ("D - S' R' - S' | D - P G - - | P - D S' - D | P - G R - - | "
         "G - P D - P | G - R S - D. | S - R G - R | S - - - - - ")
    chA = [(50, "maj"), (50, "maj"), (43, "maj"), (50, "maj"), (50, "maj"), (45, "maj"), (45, "maj"), (50, "maj")]
    chB = [(43, "maj"), (50, "maj"), (43, "maj"), (50, "maj"), (50, "maj"), (45, "maj"), (45, "maj"), (50, "maj")]
    plan = ["i", "A", "A2", "B", "A", "alaap", "B2", "A3"]
    t = 1.0
    for sec in plan:
        if sec == "alaap":
            tanpura(M, 62, t - 0.5, t + 14, 3.6, "P", 0.2)
            pad(M, strings_chord(50, "add9"), t, 14, 0.25, 2.0, 2.5)
            bansuri(M, "S' - - D P - G - - - R - ~G - - R S - - -", 74, t, 0.7, 0.75, send=0.5, glide_p=0.6)
            t += 15.0
            continue
        chords = chB if sec.startswith("B") else chA
        nb = 2 if sec == "i" else 8
        for k in range(nb):
            root, kind = chords[k]
            ct = chord_tones(root, kind)
            tb = t + k * bar
            pluck(M, "vc_pizz", near([root], 38, 50)[0], tb, 0.4, 0.1, 0.15, 2, r)
            pluck(M, "vc_pizz", near([root + 7], 40, 52)[0], tb + 3 * e8, 0.3, 0.1, 0.15, 1, r)
            hc = near(ct, 62, 76)
            for q in (1, 2, 4, 5):
                arp(M, "harp", [hc[0]], tb + q * e8, 0, 0.12, -0.3, 0.3, 3, seed=int(tb * 10) + q)
                arp(M, "harp", [hc[1]], tb + q * e8 + 0.01, 0, 0.1, 0.1, 0.3, 3, seed=int(tb * 10) + q + 7)
            M.add(manjira(rng("mj", tb), 1.0, True), tb, 0.07, 0.3, 0.3)
            M.add(manjira(rng("mj", tb, 1), 1.0, False), tb + 3 * e8, 0.05, 0.3, 0.3)
            if sec in ("A2", "B2", "A3"):
                bdrum(M, tb, 0.2)
                pad(M, strings_chord(root, kind), tb, bar, 0.28, 0.3, 0.8, seed=int(tb * 3))
        if sec != "i":
            mel = B if sec.startswith("B") else A
            bansuri(M, mel, 74, t, e8, 0.8, send=0.3, glide_p=0.12, vib=0.1, seed=int(t))
            if sec in ("A2", "B2", "A3"):
                bowed(M, "vln_sus", mel, 62, t, e8, 0.3, -0.2, 0.3, attack=0.05, legato=0.08, release=0.3, seed=int(t))
        t += nb * bar
    pluck(M, "vc_pizz", 38, t, 0.45, 0.1, 0.3, 3, r)
    arp(M, "harp", [62, 66, 69, 74, 78, 81, 86], t, 0.06, 0.2, 0, 0.45, 3)
    M.add(manjira(rng("mj", t, 9), 1.0, True), t, 0.12, 0.3, 0.4)
    M.d = t + 5
    return M.render(2.2)


@track("04 Flute", "Evening_Raag", "Slow, emotional bansuri in Raag Yaman over tanpura, warm strings and soft piano - sunsets, reflection, endings",
       58, "emotional, reflective")
def _(r):
    M = Mix(200, 58, r)
    b = M.beat
    bar = 4 * b
    sa = 62
    tanpura(M, 50, 0.0, 160, 5.2, "P", 0.22)
    al = ("_ N. R G - - ~R - S - - - _ N. D. N. R - S - - - _ _ "
          "G M D - ~M - G - - - R G ~R - S - - - _ _")
    t = 3.0 + bansuri(M, al, sa, 3.0, 1.0, 0.8, send=0.5, glide_p=0.5) * 1.0
    lines = ["N. R G - | M - G - | R G ~R S | N. - S - ",
             "G M D - | N - D M | G M ~G R | S - - - ",
             "M D N S' | R' - S' - | N D M D | ~N - D - ",
             "M G R G | M - G R | N. R ~G R | S - - - "]
    prog = [(50, {"vc_sus": [50], "vla_sus": [57, 61], "vln_sus": [66, 69]}),            # Dmaj7
            (52, {"vc_sus": [50], "vla_sus": [56, 59], "vln_sus": [64, 71]}),            # E/D
            (47, {"vc_sus": [47], "vla_sus": [57, 62], "vln_sus": [66, 69]}),            # Bm7
            (45, {"vc_sus": [45], "vla_sus": [57, 61], "vln_sus": [64, 69]})]            # A
    t0 = t + 1.0
    order = [0, 1, 2, 3, 0, 1, 2, 3]
    for j, li in enumerate(order):
        tl = t0 + j * 4 * bar
        for k in range(4):
            root, ch = prog[k]
            tb = tl + k * bar
            pad(M, ch, tb, bar, 0.3 if j < 4 else 0.42, 1.2, 1.8, seed=j * 4 + k)
            piano(M, near([root], 38, 50)[0], tb, bar, 1, 0.32, 0, 0.35, r)
            piano(M, ch["vln_sus"][-1] + 12, tb + 2 * b, 2 * b, 1, 0.2, 0.2, 0.45, r)
        bansuri(M, lines[li], sa + (12 if j in (4, 5) else 0), tl, b, 0.8, send=0.45, glide_p=0.35, vib=0.22, seed=j)
        if j >= 6:
            bowed(M, "vc_sus", lines[li], sa - 12, tl, b, 0.3, 0.25, 0.3, seed=j)
    te = t0 + len(order) * 4 * bar
    bansuri(M, "N. R G - ~R - S - - - - -", sa, te, 1.0, 0.75, send=0.55, glide_p=0.6, seed=77)
    pad(M, prog[0][1], te, 10, 0.3, 2.0, 3.5, seed=88)
    bowl(M, te + 7, 147, 0.2)
    M.d = te + 16
    return M.render(3.4, fade_out=6.0)


# ================================================================ docs
def write_doc(catp, out):
    cat = json.load(open(catp, encoding="utf-8"))
    L_ = ["# Music Library — Safar Pahad Parivar", "",
          "Original background music, composed in code (`Source/music/music_gen.py`) and played with recorded instruments from",
          "*VSCO-2 Community Edition* (CC0 public domain) plus synthesised tanpura, temple bells, manjira and wind.",
          "Build with `.\\Tools\\make_music.ps1` → `<kit>\\Music\\` (not in git); import with **Music - Import Library**.",
          "Free for monetised YouTube, no credit needed. Preview: `Docs/SPP_Music_Preview.mp3`.", ""]
    for th in sorted({c["theme"] for c in cat}):
        L_ += ["## " + th, "", "| Track | Length | Tempo | Mood | Use |", "|---|---|---|---|---|"]
        for c in [c for c in cat if c["theme"] == th]:
            L_.append("| `%s` | %d:%02d | %s | %s | %s |" % (c["file"].split("/")[-1], c["seconds"] // 60, c["seconds"] % 60,
                                                          "%d bpm" % c["bpm"] if c["bpm"] else "free", c["mood"], c["use"]))
        L_.append("")
    open(out, "w", encoding="utf-8").write("\n".join(L_))
    print("wrote", out)


# ================================================================ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(KIT / "Music"))
    ap.add_argument("--samples", default=str(KIT / "Source" / "_vsco"))
    ap.add_argument("--only", default="")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--stats", action="store_true", help="print the instrument balance of each track")
    ap.add_argument("--doc", help="write Docs/Music_Library.md from an existing music_catalog.json and exit")
    a = ap.parse_args()
    if a.doc:
        return write_doc(Path(a.out) / "music_catalog.json", a.doc)
    if a.list:
        for t in TRACKS:
            print(f"{t['theme']:16s} {t['name']:22s} {t['bpm']:4d} bpm  {t['desc']}")
        return
    if not os.path.exists(os.path.join(a.samples, "LICENSE")):
        raise SystemExit("Recorded instruments missing - run .\\Tools\\make_music.ps1 (downloads them once).")
    L[0] = _smp.Lib(a.samples)
    import sfx_gen
    sfx_gen.LIB[0] = L[0]
    out = Path(a.out)
    catp = out / "music_catalog.json"
    cat = json.load(open(catp, encoding="utf-8")) if catp.exists() and a.only else []
    t0 = time.time()
    for t in TRACKS:
        if a.only and a.only.lower() not in (t["theme"] + " " + t["name"]).lower():
            continue
        ts = time.time()
        x = t["fn"](rng("music", t["name"]))
        if a.stats and STATS:
            e = STATS[-1]
            tot = sum(e.values())
            print("    balance: " + ", ".join("%s %+.0f dB" % (k, 10 * np.log10(v / tot)) for k, v in sorted(e.items(), key=lambda kv: -kv[1])))
        d = out / t["theme"]
        d.mkdir(parents=True, exist_ok=True)
        fn = f"SPP_Music_{t['name']}.wav"
        write_wav(d / fn, x)
        cat = [c for c in cat if c["name"] != t["name"]]
        cat.append({"file": f"{t['theme']}/{fn}", "theme": t["theme"], "name": t["name"], "seconds": round(len(x) / SR, 1),
                    "bpm": t["bpm"], "mood": t["mood"], "use": t["desc"]})
        print(f"  {t['theme']} {t['name']}  {len(x) / SR:.0f}s  ({time.time() - ts:.0f}s)", flush=True)
        del x
        STATS.clear()
        L[0].cache.clear(); L[0].shift.clear()
        import gc; gc.collect()
    out.mkdir(parents=True, exist_ok=True)
    cat.sort(key=lambda c: c["file"])
    json.dump(cat, open(catp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(cat)} tracks -> {out}  ({time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main()
