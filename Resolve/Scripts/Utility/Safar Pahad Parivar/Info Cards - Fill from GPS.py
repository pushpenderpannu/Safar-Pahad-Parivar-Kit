# Safar Pahad Parivar - fill SPP Info Cards from GPS: place (Hindi + English), altitude, date, time, weather, temperature.
# For every SPP Info Card on the timeline whose "Place (Hindi)" is still empty, it looks at the footage clip
# underneath, finds where and when that shot was taken (trip GPS index + Google Timeline) and fills the card.
# To refresh a card later: clear its "Place (Hindi)" field and run again.
import json, os, sys
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

proj = resolve.GetProjectManager().GetCurrentProject()
tl = proj.GetCurrentTimeline() if proj else None
if not tl:
    print("Open a timeline first.")
elif C.engine_ok():
    fps = float(tl.GetSetting("timelineFrameRate"))
    cards = C.templates_on(tl, "SPP-Info-Card")
    if not cards:
        print("No SPP Info Card on this timeline (Effects > Titles > Safar Pahad Parivar > SPP Info Card).")
    done = 0
    for card, tool, track in cards:
        if (tool.GetInput("DynParamText0") or "").strip():
            print("skip card at %d (already filled - clear 'Place (Hindi)' to refresh)" % card.GetStart()); continue
        clip, path = C.media_under(tl, card.GetStart(), track)
        if not clip:
            print("card at %d: no footage under it" % card.GetStart()); continue
        trip = C.trip_of(path)
        if not trip or not C.ensure_index(trip):
            print("card at %d: can't find the trip folder for %s" % (card.GetStart(), path)); continue
        offset = (card.GetStart() - clip.GetStart() + (clip.GetLeftOffset() or 0)) / fps
        out, err, rc = C.run_gps("file", trip, os.path.basename(path), "--offset", "%.2f" % offset)
        try:
            d = json.loads(out)
        except Exception:
            print("card at %d: lookup failed\n%s" % (card.GetStart(), err[-400:])); continue
        if d.get("error"):
            print("card at %d: %s" % (card.GetStart(), d["error"])); continue
        C.set_dyn(tool, 0, d.get("place_hi") or "")
        C.set_dyn(tool, 1, d.get("place_en") or "")
        if d.get("altitude_m") is not None:
            C.set_dyn(tool, 3, float(round(d["altitude_m"])))
        C.set_dyn(tool, 6, d.get("date_hi") or "")
        C.set_dyn(tool, 8, d.get("time_ampm") or "")
        if "card" in d:
            C.set_select(tool, 9, d["card"])
        if d.get("temp_c") is not None:
            C.set_dyn(tool, 10, "%d°C" % d["temp_c"])
        done += 1
        print("card at %d: %s / %s, %s m, %s %s, %s°C" % (card.GetStart(), d.get("place_hi"), d.get("place_en"),
              d.get("altitude_m"), d.get("date_hi"), d.get("time_ampm"), d.get("temp_c")))
    print("Filled %d Info Card(s). Hindi place names come from OpenStreetMap - check the spelling." % done)
