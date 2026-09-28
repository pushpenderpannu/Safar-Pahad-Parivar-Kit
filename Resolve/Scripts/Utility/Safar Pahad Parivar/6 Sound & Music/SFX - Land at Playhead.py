# Safar Pahad Parivar - drop a sound so that its big moment lands exactly on the playhead.
# 1) Put the playhead on the cut / reveal / first beat of the next track.  2) Select one sound in the Media Pool
# (SPP SFX bin) - a riser, a Swell_Into_*, a Bridge_*, a drum fill, a whoosh...  3) Run this.
# It starts the sound early by its landing time (e.g. Riser_Epic_8s starts 8 s before the playhead) on a free SFX track.
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



def frames_of(tc, fps):
    h, m, s, f = [int(v) for v in tc.replace(";", ":").split(":")]
    return int(round(((h * 60 + m) * 60 + s) * fps)) + f


def main():
    proj = resolve.GetProjectManager().GetCurrentProject()
    tl = proj.GetCurrentTimeline() if proj else None
    if not tl:
        print("Open a timeline first."); return
    mp = proj.GetMediaPool()
    sel = mp.GetSelectedClips() or []
    sel = list(sel.values()) if isinstance(sel, dict) else list(sel)
    if not sel:
        print("Select a sound in the Media Pool first (e.g. SPP SFX > 16 Cinematic Risers)."); return
    fps = float(tl.GetSetting("timelineFrameRate"))
    at = frames_of(tl.GetCurrentTimecode(), fps)
    cat = {os.path.basename(e["file"]).lower(): e for e in (S.catalog() or [])}
    tracks = S.sfx_tracks(tl)
    if not tracks:
        tl.AddTrack("audio", "stereo"); tracks = [tl.GetTrackCount("audio")]; tl.SetTrackName("audio", tracks[0], "SFX 1")
    for m in sel:
        e = cat.get(os.path.basename(m.GetClipProperty("File Path") or "").lower())
        land = float(e.get("peak") or 0) if e else 0.0
        a = max(tl.GetStartFrame(), at - int(round(land * fps)))
        n = S.clip_frames(m, fps)
        tr = S.free_track(tl, tracks, a, a + n)
        S.append(proj, tl, m, tr, a, fps=fps)
        print("%s: lands at the playhead (starts %.2f s before) on %s" % (m.GetName(), land, tl.GetTrackName("audio", tr)))


main()
