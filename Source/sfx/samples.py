"""
Real-instrument sample engine for the Safar Pahad Parivar SFX generator.

Uses the Versilian Studios Chamber Orchestra 2 Community Edition (VSCO-2 CE, CC0 / public domain):
strings (violin section, solo violin, viola, cello, contrabass, harp), timpani, gong, bass drum, cymbal swells,
triangle and Nepalese bells.  Tools/make_sfx.ps1 downloads just those folders (~850 MB, once) into Source/_vsco.

Every sample's real pitch is measured once (file names use different octave conventions per instrument),
and cached in <root>/_spp_index.json.
"""
import json, os, re, glob
import numpy as np
from scipy.io import wavfile
from scipy import signal
from synth import SR, stereo, fade, n_

REPO = "https://github.com/sgossner/VSCO-2-CE.git"
SPARSE = ["/Strings/Violin Section/", "/Strings/Solo Violin/", "/Strings/Viola Section/", "/Strings/Cello Section/",
          "/Strings/Solo Contrabass/", "/Strings/Harp/", "/Percussion/Timpani/", "/Percussion/gongHit_*",
          "/Percussion/susCymb1-cresc-*", "/Percussion/susCymb1-bow-*", "/Percussion/BDrumNewhit_*",
          "/Percussion/Triangle3-Hit_*", "/Miscellania Raw/Misc 2/NepaleseBells/", "/LICENSE"]

# instrument key -> folder (relative), pitched?
INSTR = {
    "vln_sus": ("Strings/Violin Section/susVib", True), "vln_trem": ("Strings/Violin Section/Trem", True),
    "vln_spic": ("Strings/Violin Section/Spic", True), "vln_pizz": ("Strings/Violin Section/Pizz", True),
    "svln_sus": ("Strings/Solo Violin/Arco Vib", True), "svln_pizz": ("Strings/Solo Violin/Pizz", True),
    "svln_trem": ("Strings/Solo Violin/Trem", True), "svln_spic": ("Strings/Solo Violin/spic", True),
    "vla_sus": ("Strings/Viola Section/susvib", True), "vla_trem": ("Strings/Viola Section/trem", True),
    "vla_spic": ("Strings/Viola Section/spic", True), "vla_pizz": ("Strings/Viola Section/pizz", True),
    "vc_sus": ("Strings/Cello Section/susvib", True), "vc_trem": ("Strings/Cello Section/trem", True),
    "vc_spic": ("Strings/Cello Section/spic", True), "vc_pizz": ("Strings/Cello Section/pizzT", True),
    "cb_sus": ("Strings/Solo Contrabass/SusVib", True), "cb_pizz": ("Strings/Solo Contrabass/Pizz", True),
    "cb_trem": ("Strings/Solo Contrabass/Trem", True),
    "harp": ("Strings/Harp", True),
    "timp_hit": ("Percussion/Timpani", False), "timp_roll": ("Percussion/Timpani/Rolls", False),
    "gong": ("Percussion", False), "cymb_cresc": ("Percussion", False), "cymb_bow": ("Percussion", False),
    "bdrum": ("Percussion", False), "triangle": ("Percussion", False),
    "nepal_bells": ("Miscellania Raw/Misc 2/NepaleseBells", False),
}
UNPITCHED_PAT = {"gong": "gongHit_", "cymb_cresc": "susCymb1-cresc-", "cymb_bow": "susCymb1-bow-", "bdrum": "BDrumNewhit_",
                 "triangle": "Triangle3-Hit_", "timp_hit": "Timpani", "timp_roll": "Timpani", "nepal_bells": ""}
NOTE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
DYN = {"ppp": 0, "pp": 1, "p": 2, "mp": 3, "mf": 4, "f": 5, "ff": 6, "fff": 7}


def _read(path):
    sr, x = wavfile.read(path)
    if x.dtype.kind == "i":
        x = x / float(np.iinfo(x.dtype).max)
    elif x.dtype.kind == "u":
        x = (x - 128) / 128.0
    x = x.astype(float)
    x = stereo(x) if x.ndim == 1 else x[:, :2]
    if sr != SR:
        g = np.gcd(SR, sr)
        x = signal.resample_poly(x, SR // g, sr // g, axis=0)
    return x


def _f0(x):
    m = x.mean(axis=1)
    a, b = n_(0.25), n_(1.25)
    m = m[a:b] if len(m) > b else m[len(m) // 4:]
    m = m - m.mean()
    if len(m) < 2048 or np.max(np.abs(m)) < 1e-4:
        return None
    F = np.fft.rfft(m, 2 * len(m))
    ac = np.fft.irfft(F * np.conj(F))[: len(m)]
    lo, hi = int(SR / 2200), int(SR / 35)
    lag = np.argmax(ac[lo:hi]) + lo
    return SR / lag


def _name_midi(fn):
    m = re.search(r"_([A-G])(#|b)?(-?\d)(?=[_.])", fn)
    if not m:
        return None
    n = NOTE[m.group(1)] + (1 if m.group(2) == "#" else -1 if m.group(2) == "b" else 0)
    return 12 * (int(m.group(3)) + 1) + n


def _vel(fn):
    m = re.search(r"_v(\d)", fn)
    if m:
        return int(m.group(1))
    for k in sorted(DYN, key=len, reverse=True):
        if re.search(r"[_-]%s[_.]" % k, fn):
            return DYN[k]
    return 3


def build_index(root):
    idx = {}
    for key, (folder, pitched) in INSTR.items():
        d = os.path.join(root, folder)
        files = sorted(glob.glob(os.path.join(d, "*.wav")))
        pat = UNPITCHED_PAT.get(key)
        if pat is not None and not pitched:
            files = [f for f in files if os.path.basename(f).startswith(pat)]
            if key == "timp_hit":
                files = [f for f in files if "_Hit_" in os.path.basename(f)]
        items = []
        for f in files:
            e = {"file": os.path.relpath(f, root), "vel": _vel(os.path.basename(f))}
            if pitched:
                nm = _name_midi(os.path.basename(f))
                if nm is None:
                    continue
                try:
                    fr = _f0(_read(f))
                except Exception:
                    fr = None
                if fr:
                    meas = 69 + 12 * np.log2(fr / 440)
                    cands = [nm + k for k in (-12, 0, 12, 24)]
                    e["midi"] = min(cands, key=lambda c: abs(c - meas))
                else:
                    e["midi"] = nm
            items.append(e)
        idx[key] = items
    json.dump(idx, open(os.path.join(root, "_spp_index.json"), "w"), indent=0)
    return idx


class Lib:
    def __init__(self, root):
        self.root = root
        p = os.path.join(root, "_spp_index.json")
        self.idx = json.load(open(p)) if os.path.exists(p) else build_index(root)
        self.cache = {}

    def ok(self):
        return any(self.idx.get(k) for k in self.idx)

    def _load(self, rel):
        if rel not in self.cache:
            self.cache[rel] = _read(os.path.join(self.root, rel))
        return self.cache[rel]

    def raw(self, key, r, vel=None):
        items = self.idx[key]
        if vel is not None:
            best = min(abs(i["vel"] - vel) for i in items)
            items = [i for i in items if abs(i["vel"] - vel) == best]
        return self._load(items[r.integers(len(items))]["file"]).copy()

    def note(self, key, midi, r, dur=None, vel=None, release=0.35, attack=None, gain=1.0):
        """One note: nearest sample, pitch-shifted by resampling; optional length with a natural release."""
        items = self.idx[key]
        near = min(abs(i["midi"] - midi) for i in items)
        c = [i for i in items if abs(i["midi"] - midi) == near]
        if vel is not None:
            bv = min(abs(i["vel"] - vel) for i in c)
            c = [i for i in c if abs(i["vel"] - vel) == bv]
        e = c[r.integers(len(c))]
        x = self._load(e["file"])
        semis = midi - e["midi"]
        if abs(semis) > 0.01:
            ratio = 2 ** (semis / 12)
            n = int(len(x) / ratio)
            x = signal.resample(x, n, axis=0) if n < 400000 else np.stack(
                [np.interp(np.arange(n) * ratio, np.arange(len(x)), x[:, ch]) for ch in range(2)], axis=1)
        else:
            x = x.copy()
        # skip leading silence
        a = np.nonzero(np.max(np.abs(x), axis=1) > 0.003)[0]
        if len(a):
            x = x[max(0, a[0] - n_(0.005)):]
        if attack:
            k = min(len(x), n_(attack))
            x[:k] *= np.linspace(0, 1, k)[:, None] ** 1.5
        if dur is not None:
            L = min(len(x), n_(dur + release))
            x = x[:L]
            rl = min(L, n_(release))
            x[-rl:] *= np.linspace(1, 0, rl)[:, None] ** 2
        return x * gain

    def chord(self, key, midis, r, **kw):
        parts = [self.note(key, m, r, **kw) for m in midis]
        n = max(len(p) for p in parts)
        y = np.zeros((n, 2))
        for p in parts:
            y[: len(p)] += p / np.sqrt(len(midis))
        return y
