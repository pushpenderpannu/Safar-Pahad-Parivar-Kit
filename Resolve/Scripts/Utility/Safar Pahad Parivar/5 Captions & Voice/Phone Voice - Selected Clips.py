# Safar Pahad Parivar - turn the selected audio clip(s) into a phone-call voice.
# Select one or more AUDIO clips on the timeline (e.g. a VO line, or a family member's dialogue), run this, pick a style.
# A processed copy is placed on a free audio track at exactly the same spot and the original clip is switched off
# (not deleted) - re-enable it any time (select it, press D).  Styles: mobile, landline, speaker, walkie.
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

STYLES = ["mobile", "landline", "speaker", "walkie"]


def ask():
    """Small window: style + options. Falls back to 'mobile' if the UI isn't available."""
    try:
        fu = resolve.Fusion()
        ui = fu.UIManager
        disp = bmd.UIDispatcher(ui)
        win = disp.AddWindow({"ID": "PV", "WindowTitle": "SPP Phone Voice", "Geometry": [500, 300, 340, 170]},
                             ui.VGroup([ui.Label({"Text": "Style"}), ui.ComboBox({"ID": "style"}),
                                        ui.CheckBox({"ID": "noise", "Text": "Faint line hiss", "Checked": True}),
                                        ui.CheckBox({"ID": "drop", "Text": "Tiny network glitches (mobile)"}),
                                        ui.HGroup([ui.Button({"ID": "ok", "Text": "Make phone voice"}),
                                                   ui.Button({"ID": "cancel", "Text": "Cancel"})])]))
        it = win.GetItems()
        for s_ in STYLES:
            it["style"].AddItem(s_)
        res = {}

        def done(ev, ok):
            if ok:
                res.update(style=STYLES[it["style"].CurrentIndex], noise=it["noise"].Checked, drop=it["drop"].Checked)
            disp.ExitLoop()
        win.On.ok.Clicked = lambda ev: done(ev, True)
        win.On.cancel.Clicked = lambda ev: done(ev, False)
        win.On.PV.Close = lambda ev: done(ev, False)
        win.Show(); disp.RunLoop(); win.Hide()
        return res or None
    except Exception as e:
        print("(no dialog: %s) using style 'mobile'" % e)
        return {"style": "mobile", "noise": True, "drop": False}


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
    bin_ = next((f for f in root.GetSubFolderList() if f.GetName() == "SPP Phone Voice"), None) or mp.AddSubFolder(root, "SPP Phone Voice")
    tool = os.path.join(C.KIT, r"Tools\spp_phone_voice.py")
    audio_tracks = list(range(1, tl.GetTrackCount("audio") + 1))
    for it in sel:
        src = it.GetMediaPoolItem().GetClipProperty("File Path")
        start = (it.GetLeftOffset() or 0) / fps
        dur = (it.GetEnd() - it.GetStart()) / fps
        out = os.path.splitext(src)[0] + "_phone-%s_%ds.wav" % (opt["style"], int(start))
        args = [C.PY, tool, src, "--style", opt["style"], "--start", "%.3f" % start, "--dur", "%.3f" % dur, "--out", out]
        if opt["noise"]:
            args.append("--noise")
        if opt["drop"]:
            args.append("--dropouts")
        r = subprocess.run(args, capture_output=True, text=True, creationflags=0x08000000)
        if r.returncode != 0:
            print("FAILED", src, r.stderr[-500:]); continue
        prev = mp.GetCurrentFolder(); mp.SetCurrentFolder(bin_)
        m = (mp.ImportMedia([out]) or [None])[0]
        mp.SetCurrentFolder(prev)
        if not m:
            print("import failed", out); continue
        pad = 0.12 if opt["style"] == "walkie" else 0.0     # walkie adds squelch before/after
        a = it.GetStart() - int(round(pad * fps))
        tr = next((t for t in audio_tracks if t != it.GetTrackTypeAndIndex()[1] and not S.busy(tl, t, a, it.GetEnd() + int(pad * fps))), None)
        if tr is None:
            tl.AddTrack("audio", "stereo"); tr = tl.GetTrackCount("audio"); tl.SetTrackName("audio", tr, "Phone Voice")
            audio_tracks.append(tr)
        S.append(proj, tl, m, tr, a, fps=fps)
        it.SetClipEnabled(False)
        print("Phone voice (%s): %s -> %s" % (opt["style"], it.GetName(), tl.GetTrackName("audio", tr)))


main()
