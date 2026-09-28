# Safar Pahad Parivar - build the route map for this timeline and load it into the SPP Route Map title.
# Uses only the dates of the footage on this timeline. Resolve pauses while the map is made (1-3 minutes).
# Output: <trip>\Route Maps\<timeline>\  (map.jpg, route.json, stops.csv)
# To fix names or add a stop GPS missed: edit stops.csv in Excel (a place name is enough), save, run again.
import datetime as dt, json, os, re, sys
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


def main():
    if not tl:
        print("Open a timeline first."); return
    if not C.engine_ok():
        return
    files = C.footage_on(tl)
    trips = [C.trip_of(p) for p in files]
    trips = [t for t in trips if t]
    if not trips:
        print("None of the footage is inside a trip folder (…\\<trip>\\Footage)."); return
    trip = max(set(trips), key=trips.count)
    if not C.ensure_index(trip):
        return
    idx = json.load(open(os.path.join(trip, C.INDEX), encoding="utf-8"))
    names = {os.path.basename(p).lower() for p in files}
    ts = [(r["t"], r["t"] + (r.get("dur") or 0)) for r in idx["media"]
          if r.get("t") and os.path.basename(r["file"]).lower() in names]
    tz = dt.timezone(dt.timedelta(hours=idx.get("tz", 5.5)))
    args = []
    if ts:
        t0 = dt.datetime.fromtimestamp(min(a for a, b in ts) - 3600, tz).strftime("%Y-%m-%d %H:%M")
        t1 = dt.datetime.fromtimestamp(max(b for a, b in ts) + 3600, tz).strftime("%Y-%m-%d %H:%M")
        args += ["--from", t0, "--to", t1]
        print("Footage on this timeline: %s → %s" % (t0, t1))
    safe = re.sub(r'[<>:"/\\|?*]', "_", tl.GetName())
    out = os.path.join(trip, "Route Maps", safe)
    stops = os.path.join(out, "stops.csv")
    if os.path.exists(stops):
        args += ["--stops-file", stops]
        print("Using your stops list:", stops)
    if int(tl.GetSetting("timelineResolutionHeight")) > int(tl.GetSetting("timelineResolutionWidth")):
        args.append("--portrait")
    print("Making the map... (Resolve will pause)")
    o, err, rc = C.run_gps("route", trip, out, *args)
    print(err[-1500:])
    rj = os.path.join(out, "route.json")
    if rc != 0 or not os.path.exists(rj):
        print("FAILED"); return
    maps = C.templates_on(tl, "SPP-Route-Map")
    for it, tool, track in maps:
        tool.SetInput("DynParamText0", rj)
    print(("Loaded into %d SPP Route Map title(s)." % len(maps)) if maps else
          "Add an SPP Route Map title (Effects > Titles > Safar Pahad Parivar) and choose:\n  " + rj)
    print("Names wrong or a stop missing? Edit %s and run this again." % stops)


main()
