# Safar Pahad Parivar - number the chapters and make the YouTube chapter list.
# Put an SPP Chapter title (Effects > Titles > Safar Pahad Parivar) at the start of each chapter, type its name, then run:
#  - chapters are numbered 1, 2, 3... in timeline order and each shows "chapter X of N" on its trail
#  - a purple timeline marker is put on each chapter (jump between them with Shift+Up/Down)
#  - the YouTube chapter list (00:00 Intro, 01:12 Chapter 1 ...) is copied to the clipboard and saved as a text file
#    -> paste it into the video description on YouTube.
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

TAG = "spp_chapter"
# property positions in the SPP Chapter template
P_NUMBER, P_TOTAL, P_TITLE_HI, P_TITLE_EN = 0, 1, 2, 3


def stamp(sec):
    sec = int(sec)
    h, m, s = sec // 3600, (sec // 60) % 60, sec % 60
    return "%d:%02d:%02d" % (h, m, s) if h else "%02d:%02d" % (m, s)


def text(tool, i):
    return (tool.GetInput("DynParamText%d" % i) or "").strip()


def main():
    proj = resolve.GetProjectManager().GetCurrentProject()
    tl = proj.GetCurrentTimeline() if proj else None
    if not tl:
        print("Open a timeline first."); return
    found = sorted(C.templates_on(tl, "SPP-Chapter"), key=lambda x: x[0].GetStart())
    if not found:
        print("No SPP Chapter titles on this timeline.\n"
              "Add one at the start of each chapter: Effects > Titles > Safar Pahad Parivar > SPP Chapter, type its name, run again.")
        return
    fps = float(tl.GetSetting("timelineFrameRate"))
    t0 = tl.GetStartFrame()
    n = len(found)
    tl.DeleteMarkerByCustomData(TAG)
    rows = []
    for i, (it, tool, trk) in enumerate(found, 1):
        tool.SetInput("DynParamNum%d" % P_NUMBER, float(i))
        try:
            keep_hidden = float(tool.GetInput("DynParamNum%d" % P_TOTAL) or 0) == 0
        except Exception:
            keep_hidden = False
        if not keep_hidden:
            tool.SetInput("DynParamNum%d" % P_TOTAL, float(n))
        hi, en = text(tool, P_TITLE_HI), text(tool, P_TITLE_EN)
        start = it.GetStart() - t0
        name = hi or en or ("Chapter %d" % i)
        tl.AddMarker(start, "Purple", ("Chapter %d · %s" % (i, name))[:60], (en or "")[:200], 1, TAG)
        rows.append((start / fps, "अध्याय %d · %s%s" % (i, hi or en, (" (%s)" % en.title()) if (hi and en) else "")))
    # YouTube rules: first chapter at 00:00, at least 3 chapters, each at least 10 seconds long
    if rows[0][0] > 0.5:
        rows.insert(0, (0.0, "शुरुआत · Intro"))
    else:
        rows[0] = (0.0, rows[0][1])
    lines = ["%s %s" % (stamp(t), name) for t, name in rows]
    warn = []
    if len(rows) < 3:
        warn.append("YouTube needs at least 3 chapters (you have %d) - it won't show chapters yet." % len(rows))
    end = (tl.GetEndFrame() - t0) / fps
    for (a, na), (b, _) in zip(rows, rows[1:] + [(end, "")]):
        if b - a < 10:
            warn.append("'%s' is only %.0f s long - YouTube needs 10 s or more per chapter." % (na, b - a))
    txt = "\n".join(lines) + "\n"
    # save next to the trip (or in Documents) and copy to the clipboard
    trip = None
    for p in C.footage_on(tl):
        trip = C.trip_of(p)
        if trip:
            break
    folder = os.path.join(trip, "_spp_youtube") if trip else os.path.join(os.path.expanduser("~"), "Documents", "SPP YouTube")
    os.makedirs(folder, exist_ok=True)
    safe = "".join(ch for ch in tl.GetName() if ch not in '\\/:*?"<>|').strip() or "timeline"
    out = os.path.join(folder, "%s - YouTube chapters.txt" % safe)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(txt)
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command",
                        "Get-Content -Raw -Encoding UTF8 -LiteralPath '%s' | Set-Clipboard" % out.replace("'", "''")],
                       creationflags=0x08000000, timeout=20)
        copied = True
    except Exception:
        copied = False
    print("Numbered %d chapter title(s) and added purple markers." % n)
    print("YouTube chapters%s:\n" % (" (copied - paste into the description)" if copied else ""))
    print(txt)
    print("Saved: " + out)
    for w in warn:
        print("Note: " + w)


main()
