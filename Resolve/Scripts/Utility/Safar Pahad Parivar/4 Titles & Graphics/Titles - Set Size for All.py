# Safar Pahad Parivar - one Size per title type, for the whole timeline.
# Shows every SPP title type (Info Card, Film Title, Chapter ...) with how many are on the current timeline and their
# size. Change a number -> every title of that type on the timeline gets it, and (ticked by default) it becomes the
# size of new titles you drag in from Effects (after restarting Resolve). Types you don't change are left alone.
import os, sys
from collections import Counter
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
import spp_title_sizes as S

proj = resolve.GetProjectManager().GetCurrentProject()
tl = proj.GetCurrentTimeline() if proj else None
if not tl:
    print("Open a timeline first.")
else:
    found = S.scan(tl)
    saved = S.load_saved()
    rows = []
    for f, label in S.NAMES.items():
        info = S.size_info(f)
        if not info:
            continue
        vals = [round(v, 3) for _, _, v in found.get(f, [])]
        common = Counter(vals).most_common(1)[0][0] if vals else saved.get(f, info[2])
        mixed = len(set(vals)) > 1
        note = ("%d on this timeline" % len(vals) + (", sizes differ" if mixed else "")) if vals else "none on this timeline"
        rows.append((f, label, note, common, info))
    ui = resolve.Fusion().UIManager
    disp = bmd.UIDispatcher(ui)
    lines = [ui.Label({"Text": "Size for every title of a type (0.3 - 2). Only the types you change are updated.", "WordWrap": True})]
    for f, label, note, v, info in rows:
        lines.append(ui.HGroup([
            ui.Label({"Text": "<b>%s</b>  <span style='color:#999'>%s</span>" % (label, note), "Weight": 0.75}),
            ui.DoubleSpinBox({"ID": "sz_" + f.replace("-", "_"), "Minimum": info[3], "Maximum": info[4], "SingleStep": 0.05,
                              "Decimals": 2, "Value": v, "Weight": 0.25})]))
    lines.append(ui.CheckBox({"ID": "dflt", "Text": "Also use these sizes for new titles I drag in (after restarting Resolve)", "Checked": True}))
    lines.append(ui.HGroup([ui.Button({"ID": "go", "Text": "Apply"}), ui.Button({"ID": "cancel", "Text": "Cancel"})]))
    win = disp.AddWindow({"ID": "TS", "WindowTitle": "SPP Title Sizes", "Geometry": [460, 260, 560, 90 + 34 * len(rows)]}, ui.VGroup(lines))
    it = win.GetItems()
    res = {}

    def done(ok):
        if ok:
            for f, label, note, v, info in rows:
                nv = round(float(it["sz_" + f.replace("-", "_")].Value), 3)
                if abs(nv - v) > 1e-6:
                    res[f] = nv
            res["_dflt"] = bool(it["dflt"].Checked)
        disp.ExitLoop()
    win.On.go.Clicked = lambda ev: done(True)
    win.On.cancel.Clicked = lambda ev: done(False)
    win.On.TS.Close = lambda ev: done(False)
    win.Show(); disp.RunLoop(); win.Hide()

    dflt = res.pop("_dflt", False)
    if not res:
        print("Nothing changed.")
    else:
        for f, v in res.items():
            n = S.set_timeline(found, f, v)
            print("%-16s -> %.2f  (%d on the timeline updated)" % (S.NAMES[f], v, n))
        if dflt:
            S.save(res)
            ch = S.apply_defaults()
            print("New %s will start at these sizes after you restart Resolve." % ", ".join(S.NAMES[f] + "s" for f in res))
