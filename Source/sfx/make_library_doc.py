"""Writes Docs/SFX_Library.md from SFX/sfx_catalog.json.  Usage: python make_library_doc.py <catalog.json> <out.md>"""
import json, sys, collections

HEAD = """# SFX Library — Safar Pahad Parivar

All sounds are built by `Source/sfx/sfx_gen.py` — identical on every PC, so they are **not stored in git**.
Build or rebuild them with `.\\Tools\\make_sfx.ps1` (first run ≈10 min incl. a one-time ~1.1 GB download of recorded instruments) → `<kit>\\SFX\\`.
48 kHz / 24-bit stereo WAV.

Three styles:
- **Strings** (folders 13–15 and `Strings_` stings) — real recorded orchestra: violin / viola / cello sections, solo violin, contrabass,
  harp, timpani, gong, cymbal swells, Nepalese bells. Warm and emotional, built in D major / D pentatonic so the sounds fit together.
  Recordings: *VSCO-2 Community Edition* by Versilian Studios (CC0 public domain — free for YouTube, no credit required).
- **Grand** (folders 09–12 and `Grand_` stings) — deep, cinematic synth: sub-bass, taiko/dhol, braams, gongs, ransingha horn with valley echo, drones.
- **Light** (folders 01–08) — playful UI sounds, ticks, pops, marimba, plus nature beds and phone sounds.

- **vNN** = variations of the same idea, so repeated moments don't sound identical.
- **LOOP_Ns** = seamless loop (the end joins the start) → use **SFX - Loop Fill (In to Out)** for any length.
- Levels: one-shots peak −3 dBFS (title kits −5 to −8 so they sit under the VO); beds ~−24 dB RMS.
- **Title Kits** (01, 09, 13) are timed to the SPP titles — **SFX - Auto Sound for Titles** places them (choose Strings / Grand / Light / Mix).
- Listen: `Docs/SPP_SFX_Strings_Demo.mp3`, `Docs/SPP_SFX_Grand_Demo.mp3`, `Docs/SPP_SFX_Demo_Reel.mp3`.
"""


def main(cat, out):
    c = json.load(open(cat, encoding="utf-8"))
    by = collections.OrderedDict()
    for e in sorted(c, key=lambda e: e["category"]):
        by.setdefault(e["category"], collections.OrderedDict()).setdefault(e["name"], []).append(e)
    L = [HEAD]
    for cat_, names in by.items():
        L += ["", "## " + cat_, "", "| Sound | Variations | Length | Use |", "|---|---|---|---|"]
        for n, es in names.items():
            fn = es[0]["file"].split("/")[-1]
            base = fn.split("_LOOP_")[0] if es[0]["loop"] else fn.rsplit("_v", 1)[0]
            ln = ("loop %.1f s" if es[0]["loop"] else "%.1f s") % es[0]["seconds"]
            L.append("| `%s` | %d | %s | %s |" % (base, len(es), ln, es[0].get("use", "")))
    L += ["", "**%d files, %d sounds.**" % (len(c), sum(len(v) for v in by.values())), ""]
    open(out, "w", encoding="utf-8").write("\n".join(L))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
