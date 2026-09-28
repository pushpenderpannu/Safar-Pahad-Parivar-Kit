# Safar Pahad Parivar - remove windshield / window reflections (dashboard, phone, hands, clothes on the glass).
# Select the clips on the timeline (or park the playhead on one) and run.
#  - First run: the used part of each clip is cleaned in a background window (about 1-2 minutes per minute of 4K).
#  - Run again when that window says "All done": the cleaned copy goes onto the SAME timeline clip as a second take
#    (clip turns teal).  Switch back any time with 'Reflection - Show Original or Cleaned'.
#  - 'Preview pictures only' makes a before / after / removed picture per clip in a few seconds - check it first.
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
import spp_reflection_resolve as R


def ask(n_ready, n_todo, default_strength=0.85):
    try:
        ui = resolve.Fusion().UIManager
        disp = bmd.UIDispatcher(ui)
        msg = "%d clip(s) selected.  %s%s" % (n_ready + n_todo, ("%d already cleaned - will go on the timeline.  " % n_ready) if n_ready else "",
                                              ("%d to clean." % n_todo) if n_todo else "")
        win = disp.AddWindow({"ID": "RW", "WindowTitle": "SPP Reflection Remover", "Geometry": [480, 300, 560, 170]}, ui.VGroup([
            ui.Label({"Text": msg, "WordWrap": True}),
            ui.HGroup([ui.Label({"Text": "Strength", "Weight": 0.2}), ui.ComboBox({"ID": "st"})]),
            ui.HGroup([ui.Button({"ID": "go", "Text": "Clean"}), ui.Button({"ID": "pv", "Text": "Preview pictures only"}),
                       ui.Button({"ID": "cancel", "Text": "Cancel"})])]))
        it = win.GetItems()
        for name, _ in R.STRENGTHS:
            it["st"].AddItem(name)
        it["st"].CurrentIndex = min(range(len(R.STRENGTHS)), key=lambda i: abs(R.STRENGTHS[i][1] - default_strength))
        res = {}

        def done(mode):
            if mode:
                res.update(mode=mode, strength=R.STRENGTHS[it["st"].CurrentIndex][1])
            disp.ExitLoop()
        win.On.go.Clicked = lambda ev: done("clean")
        win.On.pv.Clicked = lambda ev: done("preview")
        win.On.cancel.Clicked = lambda ev: done(None)
        win.On.RW.Close = lambda ev: done(None)
        win.Show(); disp.RunLoop(); win.Hide()
        return res or None
    except Exception as e:
        print("(no dialog: %s) - cleaning at Normal strength" % e)
        return {"mode": "clean", "strength": 0.85}


proj = resolve.GetProjectManager().GetCurrentProject()
tl = proj.GetCurrentTimeline() if proj else None
if not tl:
    print("Open a timeline first.")
elif C.engine_ok():
    mp = proj.GetMediaPool()
    items = R.selected_video_items(tl)
    work = []
    for it in items:
        o = R.original_take(it)
        if o and o != it.GetSelectedTakeIndex():
            it.SelectTakeByIndex(o)                      # look at the original, not an older cleaned take
        src = R.src_of(it)
        if not src or R.is_cleaned(src):
            continue
        a, b = R.used_range(it)
        work.append((it, src, a, b))
    if not work:
        print("Select one or more video clips on the timeline (or park the playhead on one) and run again.")
    else:
        # cleaned files that already exist (any strength) -> offer that strength so they're used as they are
        found = [R.find_cleaned(s, a, b)[0] for _, s, a, b in work]
        pre_ready = sum(1 for f in found if f)
        default = R.cleaned_strength(next(f for f in found if f)) if pre_ready else 0.85
        opt = ask(pre_ready, len(work) - pre_ready, default)
        if opt and opt["mode"] == "preview":
            outs = []
            for it, src, a, b in work:
                fps = float(it.GetMediaPoolItem().GetClipProperty("FPS") or 30)
                at = (a + b) / 2 / fps
                out = os.path.join(R.clean_dir(src), "%s__preview_%ds.jpg" % (os.path.splitext(os.path.basename(src))[0], at))
                os.makedirs(os.path.dirname(out), exist_ok=True)
                print("Preview:", os.path.basename(src), "...")
                r = subprocess.run([C.PY, R.ENGINE, "preview", src, "--at", "%.2f" % at, "--strength", str(opt["strength"]),
                                    "--out", out, "--fast"], capture_output=True, text=True, encoding="utf-8", errors="replace",
                                   creationflags=0x08000000)
                if os.path.exists(out):
                    outs.append(out)
                    print("   " + (r.stdout.strip().splitlines() or [""])[-1])
                else:
                    print("   failed:", r.stderr[-300:])
            for o in outs[:6]:
                os.startfile(o)
            print("Left: original, middle: cleaned, right: what was removed (x3 brighter).  If it looks good, run again and press Clean.")
        elif opt:
            placed, jobs = 0, []
            for it, src, a, b in work:
                f, first = R.find_cleaned(src, a, b, opt["strength"])
                if f:
                    ok, msg = R.add_clean_take(mp, it, f, first)
                    print(("Cleaned take added: " if ok else "Problem: ") + msg)
                    placed += ok
                else:
                    fps = float(it.GetMediaPoolItem().GetClipProperty("FPS") or 29.97)
                    jobs.append({"file": src, "in": a, "out": b, "strength": opt["strength"], "fps": fps})
            if jobs:
                logp = R.start_jobs(jobs)
                print("Cleaning %d clip(s) in the background window 'SPP Reflection cleaning' (about %d min)." % (len(jobs), R.estimate_minutes(jobs)))
                print("Keep editing.  When the window says 'All done', select the same clips and run this script again.")
                print("Log: " + logp)
            if placed:
                print("%d clip(s) now show the cleaned take (teal).  'Reflection - Show Original or Cleaned' switches back." % placed)
