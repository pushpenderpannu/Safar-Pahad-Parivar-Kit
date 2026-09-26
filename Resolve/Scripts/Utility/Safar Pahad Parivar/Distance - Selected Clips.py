# Safar Pahad Parivar - make the selected audio clip(s) sound far away (or across the valley).
# Select one or more AUDIO clips on the timeline (a bird, a horn, a temple bell, rain, a car...), run this, pick a distance.
# A processed copy is placed on a free audio track at exactly the same spot and the original clip is switched off
# (not deleted) - select it and press D to switch it back.  Loops (*_LOOP_*) stay seamless.
import os, subprocess, sys
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
import spp_resolve_common as C
import spp_sfx_resolve as S

PRESETS = [("Near (~10 m)", "near"), ("Mid (~50 m)", "mid"), ("Far (~200 m)", "far"), ("Very far (~600 m)", "vfar"),
           ("Across the valley (echoes)", "valley")]


def ask():
    try:
        fu = resolve.Fusion()
        ui = fu.UIManager
        disp = bmd.UIDispatcher(ui)
        win = disp.AddWindow({"ID": "DI", "WindowTitle": "SPP Distance", "Geometry": [500, 300, 360, 160]},
                             ui.VGroup([ui.Label({"Text": "How far away?"}), ui.ComboBox({"ID": "p"}),
                                        ui.CheckBox({"ID": "keep", "Text": "Keep the loudness (change only tone and space)"}),
                                        ui.HGroup([ui.Button({"ID": "ok", "Text": "Make distant"}),
                                                   ui.Button({"ID": "cancel", "Text": "Cancel"})])]))
        it = win.GetItems()
        for label, _ in PRESETS:
            it["p"].AddItem(label)
        it["p"].CurrentIndex = 2
        res = {}

        def done(ev, ok):
            if ok:
                res.update(preset=PRESETS[it["p"].CurrentIndex][1], keep=it["keep"].Checked)
            disp.ExitLoop()
        win.On.ok.Clicked = lambda ev: done(ev, True)
        win.On.cancel.Clicked = lambda ev: done(ev, False)
        win.On.DI.Close = lambda ev: done(ev, False)
        win.Show(); disp.RunLoop(); win.Hide()
        return res or None
    except Exception as e:
        print("(no dialog: %s) using 'far'" % e)
        return {"preset": "far", "keep": False}


def main():
    proj = resolve.GetProjectManager().GetCurrentProject()
    tl = proj.GetCurrentTimeline() if proj else None
    if not tl or not C.engine_ok():
        print("Open a timeline first."); return
    sel = [it for it in (tl.GetSelectedClips() or []) if it.GetTrackTypeAndIndex()[0] == "audio" and it.GetMediaPoolItem()]
    if not sel:
        print("Select one or more audio clips on the timeline first."); return
    opt = ask()
    if not opt:
        return
    fps = float(tl.GetSetting("timelineFrameRate"))
    mp = proj.GetMediaPool()
    root = mp.GetRootFolder()
    bin_ = next((f for f in root.GetSubFolderList() if f.GetName() == "SPP Distance"), None) or mp.AddSubFolder(root, "SPP Distance")
    tool = os.path.join(C.KIT, r"Tools\spp_distance.py")
    audio_tracks = list(range(1, tl.GetTrackCount("audio") + 1))
    for it in sel:
        src = it.GetMediaPoolItem().GetClipProperty("File Path")
        start = (it.GetLeftOffset() or 0) / fps
        dur = (it.GetEnd() - it.GetStart()) / fps
        full = abs(start) < 1e-3 and "_LOOP_" in os.path.basename(src)
        outdir = os.path.join(os.path.dirname(src), "_distance")
        os.makedirs(outdir, exist_ok=True)
        out = os.path.join(outdir, os.path.splitext(os.path.basename(src))[0] + "_%s_%ds.wav" % (opt["preset"], int(start)))
        args = [C.PY, tool, src, "--preset", opt["preset"], "--out", out]
        if not full:
            args += ["--start", "%.3f" % start, "--dur", "%.3f" % dur]
        if opt["keep"]:
            args.append("--keep-level")
        r = subprocess.run(args, capture_output=True, text=True, creationflags=0x08000000)
        if r.returncode != 0:
            print("FAILED", src, r.stderr[-500:]); continue
        prev = mp.GetCurrentFolder(); mp.SetCurrentFolder(bin_)
        m = (mp.ImportMedia([out]) or [None])[0]
        mp.SetCurrentFolder(prev)
        if not m:
            print("import failed", out); continue
        a, b = it.GetStart(), it.GetEnd() + int(2 * fps)          # far sounds ring on a little longer (reverb)
        tr = next((t for t in audio_tracks if t != it.GetTrackTypeAndIndex()[1] and not S.busy(tl, t, a, b)), None)
        if tr is None:
            tl.AddTrack("audio", "stereo"); tr = tl.GetTrackCount("audio"); tl.SetTrackName("audio", tr, "Distance")
            audio_tracks.append(tr)
        if full:
            S.loop_fill(proj, tl, m, tr, a, it.GetEnd(), fps)
        else:
            S.append(proj, tl, m, tr, a, fps=fps)
        it.SetClipEnabled(False)
        print("Distance (%s): %s -> %s" % (opt["preset"], it.GetName(), tl.GetTrackName("audio", tr)))


main()
