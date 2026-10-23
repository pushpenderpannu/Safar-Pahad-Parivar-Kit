# Safar Pahad Parivar - tag every video clip in the Media Pool as 8-bit or 10-bit (and HDR type), so you can sort,
# search and filter them. Adds a Keyword to each clip:
#   "10-bit HDR HLG"   (OnePlus H.265 Main 10, iPhone HDR ...)
#   "10-bit HDR PQ"    (HDR10)
#   "10-bit SDR"       (10-bit but normal Rec.709, e.g. log/pro modes)
#   "8-bit SDR"        (H.264 / H.265 Main - normal phone video)
# Optional: also move the clips into bins "SPP 10-bit HDR" / "SPP 8-bit SDR" etc.
# Sort / filter afterwards: Media Pool list view -> Keywords column, or the search box (type 10-bit), or a Smart Bin
# (Media Pool > right-click > Add Smart Bin > Keywords contains "10-bit").
# Re-running is safe: old SPP tags are replaced, your own keywords are kept. Clip colours are not touched.
import os, shutil, subprocess
try:
    resolve
except NameError:
    try:
        resolve = app.GetResolve()
    except Exception:
        resolve = bmd.scriptapp("Resolve")

TAGS = ("10-bit HDR HLG", "10-bit HDR PQ", "10-bit SDR", "8-bit SDR")
FFPROBE = shutil.which("ffprobe")


def probe(path):
    """(bit depth, transfer) from the file itself - used when Resolve doesn't report them."""
    if not FFPROBE or not path or not os.path.exists(path):
        return None, ""
    try:
        r = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries",
                            "stream=pix_fmt,color_transfer,bits_per_raw_sample", "-of", "default=nw=1", path],
                           capture_output=True, text=True, timeout=20, creationflags=0x08000000)
        d = dict(l.split("=", 1) for l in r.stdout.splitlines() if "=" in l)
        pf = d.get("pix_fmt", "")
        bits = 10 if ("10" in pf or "12" in pf or d.get("bits_per_raw_sample") in ("10", "12")) else 8
        return bits, d.get("color_transfer", "")
    except Exception:
        return None, ""


def classify(mpi):
    p = mpi.GetClipProperty() or {}
    try:
        bits = int(str(p.get("Bit Depth") or "0").split()[0])
    except ValueError:
        bits = 0
    codec = p.get("Video Codec") or ""
    ics = (p.get("Input Color Space") or "") + " " + (p.get("Gamma Notes") or "")
    trc = ""
    if not bits or ("HLG" not in ics and "ST2084" not in ics and bits >= 10):
        b2, trc = probe(p.get("File Path"))
        bits = bits or b2 or (10 if "Main 10" in codec else 8)
    if bits >= 10 or "Main 10" in codec:
        if "HLG" in ics or "b67" in trc:
            return "10-bit HDR HLG"
        if "ST2084" in ics or "2084" in trc:
            return "10-bit HDR PQ"
        return "10-bit SDR"
    return "8-bit SDR"


def all_clips(folder, out):
    for c in folder.GetClipList() or []:
        out.append(c)
    for f in folder.GetSubFolderList() or []:
        all_clips(f, out)
    return out


proj = resolve.GetProjectManager().GetCurrentProject()
mp = proj.GetMediaPool() if proj else None


def ask(n_sel):
    ui = resolve.Fusion().UIManager
    disp = bmd.UIDispatcher(ui)
    win = disp.AddWindow({"ID": "TB", "WindowTitle": "SPP - Tag 8-bit / 10-bit", "Geometry": [520, 320, 440, 170]}, ui.VGroup([
        ui.Label({"Text": "Adds a keyword (10-bit HDR HLG / 10-bit HDR PQ / 10-bit SDR / 8-bit SDR) to video clips.", "WordWrap": True}),
        ui.ComboBox({"ID": "scope"}),
        ui.CheckBox({"ID": "bins", "Text": "Also move the clips into bins by type", "Checked": False}),
        ui.HGroup([ui.Button({"ID": "go", "Text": "Tag"}), ui.Button({"ID": "no", "Text": "Cancel"})])]))
    it = win.GetItems()
    it["scope"].AddItem("All clips in the Media Pool")
    if n_sel:
        it["scope"].AddItem("Only the %d selected clips" % n_sel)
    res = {}

    def done(ok):
        res.update(ok=ok, sel=it["scope"].CurrentIndex == 1, bins=bool(it["bins"].Checked))
        disp.ExitLoop()
    win.On.go.Clicked = lambda ev: done(True)
    win.On.no.Clicked = lambda ev: done(False)
    win.On.TB.Close = lambda ev: done(False)
    win.Show(); disp.RunLoop(); win.Hide()
    return res


def main():
    if not mp:
        print("Open a project first."); return
    sel = mp.GetSelectedClips() or []
    sel = list(sel.values()) if isinstance(sel, dict) else list(sel)
    a = ask(len(sel))
    if not a.get("ok"):
        print("Cancelled."); return
    clips = sel if a["sel"] else all_clips(mp.GetRootFolder(), [])
    groups = {t: [] for t in TAGS}
    for c in clips:
        if "Video" not in str(c.GetClipProperty("Type") or ""):
            continue
        tag = classify(c)
        kw = [k.strip() for k in (c.GetMetadata("Keywords") or "").split(",") if k.strip() and k.strip() not in TAGS]
        c.SetMetadata("Keywords", ",".join(kw + [tag]))
        groups[tag].append(c)
    for t in TAGS:
        if groups[t]:
            print("%-15s %d clip(s)" % (t, len(groups[t])))
    if a["bins"]:
        root = mp.GetRootFolder()
        existing = {f.GetName(): f for f in root.GetSubFolderList() or []}
        for t, cl in groups.items():
            if cl:
                name = "SPP " + t
                fol = existing.get(name) or mp.AddSubFolder(root, name)
                mp.MoveClips(cl, fol)
        print("Moved into bins 'SPP <type>' at the top of the Media Pool.")
    if not any(groups.values()):
        print("No video clips found.")
    else:
        print("Sort: Media Pool list view -> Keywords column. Filter: type 10-bit in the Media Pool search box.")


main()
