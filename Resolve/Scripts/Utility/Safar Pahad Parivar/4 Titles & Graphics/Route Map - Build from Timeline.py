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
    maps = C.templates_on(tl, "SPP-Route-Map")
    if any((tool.GetInput("DynParamCheck14") or 0) > 0.5 for it, tool, track in maps):   # 'Inside 2.35 cinema bars' ticked
        args.append("--cinema")
        print("Fitting the route inside 2.35 cinema bars")
    print("Making the map... (Resolve will pause)")
    o, err, rc = C.run_gps("route", trip, out, *args)
    print(err[-1500:])
    rj = os.path.join(out, "route.json")
    if rc != 0 or not os.path.exists(rj):
        print("FAILED")
        if os.path.exists(stops):
            print("No GPS in the footage? Open %s in Excel, add one row per place\n"
                  "(Hindi, English, place name, arrive, leave - e.g. धारचूला, Dharchula, Dharchula, 2026-06-24 16:10, 2026-06-25 07:30),\n"
                  "save, and run this again." % stops)
            try:
                os.startfile(os.path.dirname(stops))
            except Exception:
                pass
        return
    maps = C.templates_on(tl, "SPP-Route-Map")
    for it, tool, track in maps:
        tool.SetInput("DynParamText0", rj)
    chapter_ranges(maps, rj, idx)
    print(("Loaded into %d SPP Route Map title(s)." % len(maps)) if maps else
          "Add an SPP Route Map title (Effects > Titles > Safar Pahad Parivar) and choose:\n  " + rj)
    print("Names wrong or a stop missing? Edit %s and run this again." % stops)


def chapter_ranges(maps, rj, idx):
    """A Route Map title inside a chapter shows only that chapter's part of the trip: 'from stop' / 'to stop' are filled
    from the footage between its chapter card and the next one. Titles where you typed them yourself are left alone."""
    chapters = sorted(it.GetStart() for it, tool, track in C.templates_on(tl, "SPP-Chapter"))
    if not chapters and len(maps) < 2:
        return
    R = json.load(open(rj, encoding="utf-8"))
    st = R.get("stops") or []
    if len(st) < 3:
        return
    fps = float(tl.GetSetting("timelineFrameRate") or 30)
    rec = {os.path.basename(r["file"]).lower(): r for r in idx["media"] if r.get("t")}
    clips = []                                  # (timeline start, end, capture start, capture end)
    for t in range(1, tl.GetTrackCount("video") + 1):
        for it in tl.GetItemListInTrack("video", t) or []:
            m = it.GetMediaPoolItem()
            r = rec.get(os.path.basename(m.GetClipProperty("File Path") or "").lower()) if m else None
            if r:
                a = r["t"] + (it.GetLeftOffset() or 0) / fps
                clips.append((it.GetStart(), it.GetEnd(), a, a + it.GetDuration() / fps))
    starts = sorted(set([0] + chapters))
    for it, tool, track in maps:
        if (tool.GetInput("DynParamText15") or "").strip() or (tool.GetInput("DynParamText16") or "").strip():
            continue
        s0 = max([c for c in starts if c <= it.GetStart()] or [0])
        s1 = min([c for c in chapters if c > it.GetStart()] or [tl.GetEndFrame() + 1])
        ts = [(a, b) for c0, c1, a, b in clips if c1 > s0 and c0 < s1]
        if not ts:
            continue
        t0, t1 = min(a for a, b in ts), max(b for a, b in ts)
        i0 = max([i for i, x in enumerate(st) if x["arrive_t"] <= t0 + 600] or [0])
        i1 = min([i for i, x in enumerate(st) if x["arrive_t"] >= t1 - 600 and i > i0] or [len(st) - 1])
        if i0 == 0 and i1 == len(st) - 1:
            continue
        name = lambda x: x.get("hi") or x.get("en") or ""
        tool.SetInput("DynParamText15", name(st[i0]))
        tool.SetInput("DynParamText16", name(st[i1]))
        print("Route Map at %s: %s -> %s" % (it.GetStart(), name(st[i0]), name(st[i1])))


main()
