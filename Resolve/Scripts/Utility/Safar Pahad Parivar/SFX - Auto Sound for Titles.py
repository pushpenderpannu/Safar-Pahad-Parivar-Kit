# Safar Pahad Parivar - add matching sound effects to every SPP title on this timeline.
#   Info Card, Altitude Counter, Peak Callout, Pop-up Title, Credits, Route Map (+ SPP intro / end card clips).
# Sounds go on the audio tracks named "SFX 1/2/3" (a new SFX track is added if they are busy), coloured Lime.
# Running it again first removes the previous Lime auto-sounds, so it always matches the current edit.
# Want to keep a sound you tweaked? Change its clip colour - then it is left alone.
# Variations rotate so the same title never sounds identical twice in a row.
import json, os, sys, zlib
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
proj = resolve.GetProjectManager().GetCurrentProject()
tl = proj.GetCurrentTimeline() if proj else None

import math

DUR = {"SPP-Info-Card": 8, "SPP-Altitude-Counter": 8, "SPP-Peak-Callout": 6, "SPP-Popup-Title": 5, "SPP-Credits": 10, "SPP-Route-Map": 40}
OUTAT = {"SPP-Info-Card": 13, "SPP-Altitude-Counter": 9, "SPP-Peak-Callout": 10, "SPP-Popup-Title": 6, "SPP-Credits": 11, "SPP-Route-Map": 12}
IN = {"SPP-Info-Card": ("01 Title Kits", "InfoCard_In", 4), "SPP-Peak-Callout": ("01 Title Kits", "PeakCallout_In", 4),
      "SPP-Popup-Title": ("01 Title Kits", "PopupTitle_In", 4), "SPP-Credits": ("01 Title Kits", "Credits_In", 3)}
ALT = [1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0]


def num(tool, i, default):
    try:
        v = float(tool.GetInput("DynParamNum%d" % i) or 0)
    except Exception:
        v = 0
    return v if v > 0 else default


def f(sec):
    return int(round(sec * fps))


def main():
    global fps
    if not tl:
        print("Open a timeline first."); return
    if S.catalog() is None:
        return
    fps = float(tl.GetSetting("timelineFrameRate"))
    pool = S.Pool(proj)
    # 1) remove previous auto sounds
    old = []
    for i in range(1, tl.GetTrackCount("audio") + 1):
        old += [it for it in (tl.GetItemListInTrack("audio", i) or [])
                if it.GetClipColor() == S.AUTO_COLOR and (it.GetName() or "").startswith("SPP_")]
    if old:
        tl.DeleteClips(old)
    tracks = S.sfx_tracks(tl)
    if not tracks:
        for k in range(3):
            tl.AddTrack("audio", "stereo")
            tl.SetTrackName("audio", tl.GetTrackCount("audio"), "SFX %d" % (k + 1))
        tracks = S.sfx_tracks(tl)
    rot = zlib.crc32(tl.GetName().encode()) % 7
    counter = {}

    def var(name, n):
        counter[name] = counter.get(name, rot) + 1
        return (counter[name] % n) + 1

    placed = []

    def put(cat, name, n, at, loop_to=None, loop=None):
        fn = "%s/SPP_%s%s_v%02d.wav" % (cat, name, ("_LOOP_%ds" % loop) if loop else "", var(name, n))
        m = pool.get(fn)
        if not m:
            print("  missing", fn); return
        if loop_to is not None:
            tr = S.free_track(tl, tracks, at, loop_to)
            its = S.loop_fill(proj, tl, m, tr, at, loop_to, fps)
        else:
            ln = S.clip_frames(m, fps)
            tr = S.free_track(tl, tracks, at, at + ln)
            its = S.append(proj, tl, m, tr, at, fps=fps)
        for it in its:
            it.SetClipColor(S.AUTO_COLOR)
        placed.extend(its)

    # 2) titles
    for tpl in DUR:
        for it, tool, trk in C.templates_on(tl, tpl):
            s0, e0 = it.GetStart(), it.GetEnd()
            if tpl in IN:
                put(*IN[tpl], s0)
            elif tpl == "SPP-Altitude-Counter":
                c = num(tool, 2, 3.0)
                best = min(ALT, key=lambda a: abs(a - c))
                put("01 Title Kits", "Altitude_In_%s" % str(best).replace(".", "_") + "s", 2, s0)
            elif tpl == "SPP-Route-Map":
                route_sounds(tool, s0, e0, put)
            outat = num(tool, OUTAT[tpl], 0)
            t_out = s0 + f(outat if outat > 0 else DUR[tpl] - 0.6)
            if t_out < e0 - f(0.2):
                put("01 Title Kits", "Title_Out", 4, t_out)
    # 3) SPP intro / end card clips
    for t in range(1, tl.GetTrackCount("video") + 1):
        for it in tl.GetItemListInTrack("video", t) or []:
            nm = (it.GetName() or "")
            if nm.startswith("SPP_Intro"):
                put("06 Bells & Brand", "Intro_Sting", 3, it.GetStart())
            elif nm.startswith("SPP_EndCard"):
                put("06 Bells & Brand", "EndCard_Sting", 3, it.GetStart())
    print("Placed %d sounds (Lime clips on the SFX tracks). Run again after changing titles." % len(placed))


def route_sounds(tool, s0, e0, put):
    rf = tool.GetInput("DynParamText0") or ""
    try:
        R = json.load(open(rf, encoding="utf-8"))
        st = R["stops"]
    except Exception:
        print("  route map without a route file - skipped"); return
    n = len(st)
    a0, a1, P = num(tool, 3, 1.2), num(tool, 4, 12.0), num(tool, 5, 1.0)
    a1 = max(a0 + 1, a1)
    move = max(0.5, (a1 - a0) - P * (n - 1))
    cam = (tool.GetInput("DynParamText6") or "follow").strip().lower()

    def arrive(i):
        tc = a0 + P
        for j in range(1, i + 1):
            tc += move * max(0, st[j]["f"] - st[j - 1]["f"])
            if j < i:
                tc += P
        return tc

    put("01 Title Kits", "RouteMap_Open", 3, s0)
    if not cam.startswith("w") and cam != "0":
        put("05 Map & Travel", "Map_Zoom_In", 3, s0 + f(max(0, a0 - 0.7)))
        put("05 Map & Travel", "Map_Zoom_Out", 3, s0 + f(a1 + 0.2))
    put("05 Map & Travel", "Dotted_Trail", 3, s0 + f(a0 + P), loop_to=min(e0, s0 + f(a1)), loop=10)
    put("05 Map & Travel", "Pin_Drop", 5, s0 + f(a0))
    for i in range(1, n):
        t = arrive(i)
        put("05 Map & Travel", "Pin_Drop", 5, s0 + f(t))
        put("02 UI", "Chime_Arrival", 5, s0 + f(t + 0.12))


fps = 30.0
main()
