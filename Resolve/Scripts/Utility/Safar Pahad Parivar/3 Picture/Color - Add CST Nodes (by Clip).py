# Safar Pahad Parivar - give every clip on the timeline a ready colour-grading node tree in one go:
#   01 CST IN  ->  02 EXPOSURE + WB  ->  03 CONTRAST  ->  04 COLOUR + SAT  ->  05 WINDOW / SKY  ->  06 CST OUT
# CST IN is picked per clip from what the phone recorded:
#   10-bit HDR (HLG, e.g. OnePlus "H.265 Main 10")  -> Rec.2020 / Rec.2100 HLG  -> DaVinci Wide Gamut / Intermediate
#   HDR10 (PQ)                                       -> Rec.2020 / Rec.2100 ST2084 -> DWG / Intermediate
#   normal 8-bit video (H.265 Main / H.264)         -> Rec.709 / Gamma 2.4       -> DWG / Intermediate
# CST OUT is always DWG / Intermediate -> Rec.709 Gamma 2.4 (DaVinci tone mapping + saturation compression).
# Grade in nodes 02-05; leave 01 and 06 alone. Clips that already have a grade are skipped unless you tick 'Replace'.
# The node trees are in <kit>\Resolve\Grades\*.drx.
import os, sys, shutil, subprocess
try:
    resolve
except NameError:
    try:
        resolve = app.GetResolve()
    except Exception:
        resolve = bmd.scriptapp("Resolve")
_h = os.path.join(os.environ["APPDATA"], r"Blackmagic Design\DaVinci Resolve\Support\Fusion\Scripts\Utility\Safar Pahad Parivar")
try:
    _k = open(os.path.join(_h, "kit_path.txt"), encoding="utf-8-sig").read().strip()
except Exception:
    _k = r"F:\Video Editing\_Safar Pahad Parivar Kit"
GR = os.path.join(_k, "Resolve", "Grades")
DRX = {"HLG": os.path.join(GR, "SPP CST - HLG (phone 10-bit HDR).drx"),
       "PQ": os.path.join(GR, "SPP CST - PQ (HDR10).drx"),
       "709": os.path.join(GR, "SPP CST - Rec709 (phone 8-bit).drx")}
NAME = {"HLG": "HDR HLG", "PQ": "HDR10 PQ", "709": "Rec.709"}
FFPROBE = shutil.which("ffprobe")
_probe_cache = {}


def probe_transfer(path):
    if not FFPROBE or not path or not os.path.exists(path):
        return ""
    if path not in _probe_cache:
        try:
            r = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=color_transfer",
                                "-of", "default=nw=1:nk=1", path], capture_output=True, text=True, timeout=20,
                               creationflags=0x08000000)
            _probe_cache[path] = r.stdout.strip().lower()
        except Exception:
            _probe_cache[path] = ""
    return _probe_cache[path]


def kind_of(mpi):
    p = mpi.GetClipProperty() or {}
    ics = (p.get("Input Color Space") or "") + " " + (p.get("Gamma Notes") or "")
    if "HLG" in ics:
        return "HLG"
    if "ST2084" in ics or " PQ" in ics:
        return "PQ"
    tr = probe_transfer(p.get("File Path"))          # Resolve didn't say - ask the file itself
    if "b67" in tr:
        return "HLG"
    if "2084" in tr:
        return "PQ"
    return "709"


def has_grade(g):
    try:
        n = g.GetNumNodes()
        return n > 1 or bool(g.GetToolsInNode(1))
    except Exception:
        return False


proj = resolve.GetProjectManager().GetCurrentProject()
tl = proj.GetCurrentTimeline() if proj else None


def ask():
    ui = resolve.Fusion().UIManager
    disp = bmd.UIDispatcher(ui)
    win = disp.AddWindow({"ID": "CST", "WindowTitle": "SPP - Add CST Nodes", "Geometry": [500, 300, 470, 170]}, ui.VGroup([
        ui.Label({"Text": "Adds CST IN / grading nodes / CST OUT to every video clip on this timeline,\n"
                          "choosing HLG, PQ or Rec.709 for each clip automatically.", "WordWrap": True}),
        ui.CheckBox({"ID": "rep", "Text": "Replace clips that already have a grade (their grade is lost)", "Checked": False}),
        ui.HGroup([ui.Button({"ID": "go", "Text": "Add Nodes"}), ui.Button({"ID": "no", "Text": "Cancel"})])]))
    it = win.GetItems()
    res = {}

    def done(ok):
        res["ok"] = ok
        res["rep"] = bool(it["rep"].Checked)
        disp.ExitLoop()
    win.On.go.Clicked = lambda ev: done(True)
    win.On.no.Clicked = lambda ev: done(False)
    win.On.CST.Close = lambda ev: done(False)
    win.Show(); disp.RunLoop(); win.Hide()
    return res


def main():
    if not tl:
        print("Open a timeline first."); return
    missing = [p for p in DRX.values() if not os.path.exists(p)]
    if missing:
        print("Missing node-tree files:\n  " + "\n  ".join(missing)); return
    if proj.GetSetting("colorScienceMode") != "davinciYRGB" or proj.GetSetting("isAutoColorManage") == "1":
        print("This project uses Resolve Color Management, which already converts the clips.\n"
              "CST nodes would convert twice. Set Project Settings > Color Management > Color science\n"
              "to 'DaVinci YRGB' first (or don't use this script in this project).")
        return
    a = ask()
    if not a.get("ok"):
        print("Cancelled."); return
    counts, skipped, failed = {}, 0, []
    for t in range(1, tl.GetTrackCount("video") + 1):
        for it in tl.GetItemListInTrack("video", t) or []:
            mpi = it.GetMediaPoolItem()
            if not mpi or "Video" not in str((mpi.GetClipProperty() or {}).get("Type", "Video")):
                continue
            g = it.GetNodeGraph()
            if not g:
                continue
            if has_grade(g) and not a["rep"]:
                skipped += 1
                continue
            k = kind_of(mpi)
            if g.ApplyGradeFromDRX(DRX[k], 0):
                counts[k] = counts.get(k, 0) + 1
            else:
                failed.append(it.GetName())
    for k, n in counts.items():
        print("%-9s %d clip(s)" % (NAME[k], n))
    if skipped:
        print("Skipped %d clip(s) that already had a grade (tick 'Replace' to redo them)." % skipped)
    if failed:
        print("Could not apply to: " + ", ".join(failed[:10]))
    if not counts and not skipped and not failed:
        print("No video clips on this timeline.")
    print("Grade in nodes 02-05. Leave 01 CST IN and 06 CST OUT as they are.")


main()
