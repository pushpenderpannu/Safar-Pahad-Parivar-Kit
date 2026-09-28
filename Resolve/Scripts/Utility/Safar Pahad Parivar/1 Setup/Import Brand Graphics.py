# Safar Pahad Parivar - import brand graphics (intro, end card, watermarks) into an "SPP Graphics" bin
import os
try:
    resolve
except NameError:
    try:
        resolve = app.GetResolve()
    except Exception:
        resolve = bmd.scriptapp("Resolve")

HERE = os.path.join(os.environ["APPDATA"], r"Blackmagic Design\DaVinci Resolve\Support\Fusion\Scripts\Utility\Safar Pahad Parivar")
KIT = r"F:\Video Editing\_Safar Pahad Parivar Kit"
try:
    with open(os.path.join(HERE, "kit_path.txt"), encoding="utf-8-sig") as fh:
        KIT = fh.read().strip() or KIT
except Exception:
    pass
GFX = os.path.join(KIT, "Graphics")

proj = resolve.GetProjectManager().GetCurrentProject()
mp = proj.GetMediaPool(); root = mp.GetRootFolder()
bins = [f for f in root.GetSubFolderList() if f.GetName() == "SPP Graphics"]
b = bins[0] if bins else mp.AddSubFolder(root, "SPP Graphics")
have = {c.GetName() for c in b.GetClipList()}
files = [os.path.join(GFX, f) for f in sorted(os.listdir(GFX))
         if f.lower().endswith((".mov", ".png")) and f not in have]
prev = mp.GetCurrentFolder(); mp.SetCurrentFolder(b)
items = mp.ImportMedia(files) if files else []
mp.SetCurrentFolder(prev)
print("Imported %d new graphics from %s into 'SPP Graphics'" % (len(items or []), GFX))
