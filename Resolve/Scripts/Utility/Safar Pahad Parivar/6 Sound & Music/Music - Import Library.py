# Safar Pahad Parivar - import the background-music library into an 'SPP Music' bin (one sub-bin per theme).
import json, os, sys
try:
    resolve
except NameError:
    try:
        resolve = app.GetResolve()
    except Exception:
        resolve = bmd.scriptapp("Resolve")
_h = os.path.join(os.environ["APPDATA"], r"Blackmagic Design\DaVinci Resolve\Support\Fusion\Scripts\Utility\Safar Pahad Parivar")
_k = open(os.path.join(_h, "kit_path.txt"), encoding="utf-8-sig").read().strip()
sys.path.insert(0, os.path.join(_k, "Tools"))
import spp_sfx_resolve as S

MUSIC = os.path.join(_k, "Music")
catp = os.path.join(MUSIC, "music_catalog.json")
proj = resolve.GetProjectManager().GetCurrentProject()
if not os.path.exists(catp):
    print("The music library isn't built yet. In PowerShell (kit folder) run:  .\\Tools\\make_music.ps1")
elif proj:
    cat = json.load(open(catp, encoding="utf-8"))
    mp = proj.GetMediaPool()
    root = S._sub(mp, mp.GetRootFolder(), "SPP Music")
    have = set()
    for f in root.GetSubFolderList():
        for c in f.GetClipList() or []:
            have.add(os.path.normcase(c.GetClipProperty("File Path") or ""))
    prev, n = mp.GetCurrentFolder(), 0
    for theme in sorted({c["theme"] for c in cat}):
        files = [os.path.join(MUSIC, c["file"]) for c in cat if c["theme"] == theme]
        files = [f for f in files if os.path.exists(f) and os.path.normcase(f) not in have]
        if files:
            mp.SetCurrentFolder(S._sub(mp, root, theme))
            items = mp.ImportMedia(files) or []
            for it in items:
                it.SetClipColor("Purple")
            n += len(items)
    mp.SetCurrentFolder(prev)
    print("Imported %d new tracks into the 'SPP Music' bin (%d in the library)." % (n, len(cat)))
    for c in cat:
        print("  %-16s %-18s %4ss  %s" % (c["theme"], c["name"], int(c["seconds"]), c["mood"]))
