"""
Safar Pahad Parivar - GPS lookup for a trip (runs in Tools\\.venv).

Builds a location index for a trip from
  * the footage itself (photo EXIF GPS, phone-video GPS tags, file-name / EXIF times), and
  * Google Maps Timeline exports (phone: Maps > Settings > Location & privacy > Export Timeline data
    -> Timeline.json;  or Google Takeout: Records.json / Semantic Location History *.json),
and answers "where were we at <date time>?" with place names (Hindi + English), altitude and weather.
It also finds the stops of the trip and makes a route map for the SPP Route Map title.

Usage (PowerShell, kit folder):
  $py = ".\\Tools\\.venv\\Scripts\\python.exe"
  & $py Tools\\spp_gps.py index  "<trip folder>" [--timeline Timeline.json ...]
  & $py Tools\\spp_gps.py at     "<trip folder>" "2026-06-26 11:14"
  & $py Tools\\spp_gps.py file   "<trip folder>" VID20260626111444.mp4 [--offset 12.5]
  & $py Tools\\spp_gps.py stops  "<trip folder>" [--min-stay 40]
  & $py Tools\\spp_gps.py route  "<trip folder>" "<out folder>" [--from "2026-06-23" --to "2026-06-27"] [--portrait]
        -> writes <out>\\stops.csv too. Fix names, add missing stops (a place name is enough), then:
  & $py Tools\\spp_gps.py route  "<trip folder>" "<out folder>" --stops-file "<out folder>\\stops.csv"
  & $py Tools\\spp_gps.py gpx    "<trip folder>" out.gpx [--from ... --to ...]   # for AvoMap / Travel Animator etc.
  & $py Tools\\spp_gps.py serve  "<trip folder>"          # http://127.0.0.1:8777/at?t=2026-06-26T11:14
Times are local (IST by default, --tz +05:30).
"""
import argparse, bisect, datetime as dt, glob, io, json, math, os, re, subprocess, sys, time, urllib.parse, urllib.request

UA = {"User-Agent": "SafarPahadParivarKit/1.0 (personal travel-video tool)"}
MEDIA_V = (".mp4", ".mov", ".m4v", ".mts", ".3gp")
MEDIA_P = (".jpg", ".jpeg", ".heic", ".heif", ".dng", ".png")
INDEX = "_spp_gps_index.json"
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "spp_gps")
os.makedirs(CACHE_DIR, exist_ok=True)


def log(*a):
    print(*a, file=sys.stderr, flush=True)


# ------------------------------------------------------------------ time helpers
def parse_tz(s):
    m = re.match(r"([+-])(\d{1,2}):?(\d{2})", s)
    sign = -1 if m.group(1) == "-" else 1
    return dt.timezone(sign * dt.timedelta(hours=int(m.group(2)), minutes=int(m.group(3))))


def iso_to_epoch(s):
    s = s.strip().replace("Z", "+00:00")
    if re.fullmatch(r"\d{12,14}", s):          # timestampMs
        return int(s) / 1000.0
    return dt.datetime.fromisoformat(s).timestamp()


def local_to_epoch(s, tz):
    s = s.strip().replace("T", " ")
    for f in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%d-%m-%Y %H:%M", "%d/%m/%Y %H:%M"):
        try:
            return dt.datetime.strptime(s, f).replace(tzinfo=tz).timestamp()
        except ValueError:
            pass
    raise SystemExit(f"Can't read the time '{s}'. Use e.g. 2026-06-26 11:14")


def fmt_local(ep, tz, f="%Y-%m-%d %H:%M"):
    return dt.datetime.fromtimestamp(ep, tz).strftime(f)


HI_MONTHS = ["जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर"]


def hi_date(ep, tz, year=True):
    d = dt.datetime.fromtimestamp(ep, tz)
    return f"{d.day} {HI_MONTHS[d.month - 1]}" + (f" {d.year}" if year else "")


def ampm(ep, tz):
    return dt.datetime.fromtimestamp(ep, tz).strftime("%I:%M %p").lstrip("0")


# ------------------------------------------------------------------ geometry
def hav_km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(h))


def parse_latlng(v):
    """'29.61°, 80.19°' | 'geo:29.61,80.19' | {'latitudeE7':..} -> (lat, lon)"""
    if isinstance(v, dict):
        if "latitudeE7" in v:
            return v["latitudeE7"] / 1e7, v["longitudeE7"] / 1e7
        if "latE7" in v:
            return v["latE7"] / 1e7, v["lngE7"] / 1e7
        for k in ("latLng", "LatLng", "point", "placeLocation"):
            if k in v:
                return parse_latlng(v[k])
        return None
    if isinstance(v, str):
        nums = re.findall(r"-?\d+(?:\.\d+)?", v)
        if len(nums) >= 2:
            return float(nums[0]), float(nums[1])
    return None


# ------------------------------------------------------------------ media
def name_time(fn, tz):
    m = re.search(r"(20\d{2})(\d{2})(\d{2})[_-]?(\d{2})(\d{2})(\d{2})", os.path.basename(fn))
    if m:
        y, mo, d, h, mi, s = map(int, m.groups())
        try:
            return dt.datetime(y, mo, d, h, mi, s, tzinfo=tz).timestamp()
        except ValueError:
            return None
    return None


def video_meta(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:format_tags", "-of", "json", path],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        fmt = json.loads(r.stdout)["format"]
    except Exception:
        return {}
    tags = {k.lower(): v for k, v in (fmt.get("tags") or {}).items()}
    out = {"dur": float(fmt.get("duration") or 0)}
    loc = tags.get("location") or tags.get("com.apple.quicktime.location.iso6709")
    if loc:
        m = re.match(r"([+-]\d+(?:\.\d+)?)([+-]\d+(?:\.\d+)?)([+-]\d+(?:\.\d+)?)?", loc)
        if m:
            la, lo = float(m.group(1)), float(m.group(2))
            if abs(la) > 0.01 or abs(lo) > 0.01:
                out["lat"], out["lon"] = la, lo
            if "lat" in out and m.group(3):
                out["alt"] = float(m.group(3))
    ct = tags.get("creation_time")
    if ct and not ct.startswith("1970"):
        try:
            out["t"] = iso_to_epoch(ct)
        except Exception:
            pass
    return out


def photo_meta(path, tz):
    try:
        from PIL import Image
        try:
            import pillow_heif
            pillow_heif.register_heif_opener()
        except Exception:
            pass
        im = Image.open(path)
        ex = im.getexif()
    except Exception:
        return {}
    out = {}
    sub = ex.get_ifd(0x8769) if ex else {}
    dto = sub.get(0x9003) or ex.get(0x0132)
    if dto:
        try:
            off = sub.get(0x9011)  # OffsetTimeOriginal
            t = dt.datetime.strptime(str(dto).strip()[:19], "%Y:%m:%d %H:%M:%S")
            out["t"] = t.replace(tzinfo=parse_tz(off) if off else tz).timestamp()
        except Exception:
            pass
    g = ex.get_ifd(0x8825) if ex else {}
    try:
        def dms(v):
            return float(v[0]) + float(v[1]) / 60 + float(v[2]) / 3600
        if g.get(2) and g.get(4):
            lat, lon = dms(g[2]), dms(g[4])
            if g.get(1) == "S":
                lat = -lat
            if g.get(3) == "W":
                lon = -lon
            if abs(lat) > 0.01 or abs(lon) > 0.01:
                out["lat"], out["lon"] = lat, lon
        if g.get(6) is not None:
            out["alt"] = float(g[6]) * (-1 if g.get(5) == 1 else 1)
    except Exception:
        pass
    return out


# ------------------------------------------------------------------ Google Timeline exports
def timeline_points(path):
    """Every (epoch, lat, lon, alt) found in a Google Timeline / Takeout export."""
    data = json.load(open(path, encoding="utf-8"))
    pts = []

    def add(t, ll, alt=None):
        if t is None or not ll:
            return
        try:
            pts.append((iso_to_epoch(t) if isinstance(t, str) else float(t), ll[0], ll[1], alt))
        except Exception:
            pass

    if isinstance(data, dict) and "locations" in data:                       # Takeout Records.json
        for p in data["locations"]:
            add(p.get("timestamp") or p.get("timestampMs"), parse_latlng(p), p.get("altitude"))
    if isinstance(data, dict) and "semanticSegments" in data or isinstance(data, list):   # on-device export
        segs = data["semanticSegments"] if isinstance(data, dict) else data
        for s in segs:
            st, en = s.get("startTime"), s.get("endTime")
            for p in s.get("timelinePath") or []:
                if "time" in p:
                    add(p["time"], parse_latlng(p.get("point")))
                elif "durationMinutesOffsetFromStartTime" in p and st:
                    add(iso_to_epoch(st) + 60 * float(p["durationMinutesOffsetFromStartTime"]), parse_latlng(p.get("point")))
            v = s.get("visit")
            if v:
                ll = parse_latlng((v.get("topCandidate") or {}).get("placeLocation"))
                add(st, ll); add(en, ll)
            a = s.get("activity")
            if a:
                add(st, parse_latlng(a.get("start"))); add(en, parse_latlng(a.get("end")))
        if isinstance(data, dict):
            for r in data.get("rawSignals") or []:
                p = r.get("position")
                if p:
                    add(p.get("timestamp"), parse_latlng(p.get("LatLng") or p.get("latLng")), p.get("altitudeMeters"))
    if isinstance(data, dict) and "timelineObjects" in data:                 # Takeout Semantic Location History
        for o in data["timelineObjects"]:
            pv = o.get("placeVisit")
            if pv:
                ll = parse_latlng(pv.get("location") or {})
                d = pv.get("duration") or {}
                add(d.get("startTimestamp") or d.get("startTimestampMs"), ll)
                add(d.get("endTimestamp") or d.get("endTimestampMs"), ll)
            ac = o.get("activitySegment")
            if ac:
                d = ac.get("duration") or {}
                add(d.get("startTimestamp"), parse_latlng(ac.get("startLocation") or {}))
                add(d.get("endTimestamp"), parse_latlng(ac.get("endLocation") or {}))
                for p in (ac.get("simplifiedRawPath") or {}).get("points") or []:
                    add(p.get("timestamp") or p.get("timestampMs"), parse_latlng(p))
                for p in (ac.get("waypointPath") or {}).get("waypoints") or []:
                    pass  # no times on waypoints
    return pts


# ------------------------------------------------------------------ index
def build_index(trip, timelines, tz):
    foot = os.path.join(trip, "Footage") if os.path.isdir(os.path.join(trip, "Footage")) else trip
    files = []
    for dp, dn, fn in os.walk(foot):
        dn[:] = [d for d in dn if not d.startswith((".", "_"))]
        for f in fn:
            if f.lower().endswith(MEDIA_V + MEDIA_P) and not f.startswith("."):
                files.append(os.path.join(dp, f))
    media = []
    for n, p in enumerate(sorted(files), 1):
        is_v = p.lower().endswith(MEDIA_V)
        m = video_meta(p) if is_v else photo_meta(p, tz)
        t_name = name_time(p, tz)
        # phone file names carry the local start time; trust them over re-exported metadata
        t = t_name if t_name else m.get("t")
        rec = {"file": os.path.relpath(p, trip), "kind": "video" if is_v else "photo", "t": t}
        for k in ("lat", "lon", "alt", "dur"):
            if k in m:
                rec[k] = round(m[k], 6) if k in ("lat", "lon") else round(m[k], 2)
        media.append(rec)
        if n % 100 == 0:
            log(f"  {n}/{len(files)} files")
    pts = [(r["t"], r["lat"], r["lon"], r.get("alt"), "media") for r in media
           if r.get("t") and "lat" in r and (abs(r["lat"]) > 0.01 or abs(r["lon"]) > 0.01)]
    for tl in timelines:
        tp = timeline_points(tl)
        log(f"  {os.path.basename(tl)}: {len(tp)} points")
        pts += [(t, la, lo, al, "timeline") for t, la, lo, al in tp if abs(la) > 0.01 or abs(lo) > 0.01]
    pts.sort()
    idx = {"tz": tz.utcoffset(None).total_seconds() / 3600, "made": time.time(), "timelines": timelines,
           "media": media, "points": [[round(t, 1), round(la, 6), round(lo, 6), al, s] for t, la, lo, al, s in pts]}
    json.dump(idx, open(os.path.join(trip, INDEX), "w", encoding="utf-8"), ensure_ascii=False)
    got = sum(1 for r in media if "lat" in r)
    log(f"Indexed {len(media)} files ({got} with GPS) + {len(pts) - got} timeline points -> {INDEX}")
    return idx


def load_index(trip):
    p = os.path.join(trip, INDEX)
    if not os.path.exists(p):
        raise SystemExit(f"No index yet. Run:  spp_gps.py index \"{trip}\"")
    return json.load(open(p, encoding="utf-8"))


def position_at(idx, ep, max_gap=45 * 60):
    """Interpolated position at epoch; None if no fix within max_gap."""
    P = idx["points"]
    if not P:
        return None
    ts = [p[0] for p in P]
    i = bisect.bisect_left(ts, ep)
    before = P[i - 1] if i > 0 else None
    after = P[i] if i < len(P) else None
    if before and after and after[0] - before[0] <= 2 * max_gap and after[0] > before[0]:
        f = (ep - before[0]) / (after[0] - before[0])
        la = before[1] + f * (after[1] - before[1]); lo = before[2] + f * (after[2] - before[2])
        gap = min(ep - before[0], after[0] - ep)
        return {"lat": la, "lon": lo, "gap_min": round(gap / 60, 1), "source": before[4]}
    best = min([p for p in (before, after) if p], key=lambda p: abs(p[0] - ep))
    if abs(best[0] - ep) <= max_gap:
        return {"lat": best[1], "lon": best[2], "gap_min": round(abs(best[0] - ep) / 60, 1), "source": best[4]}
    return None


# ------------------------------------------------------------------ web lookups (cached)
def _cache(name):
    p = os.path.join(CACHE_DIR, name + ".json")
    try:
        return p, json.load(open(p, encoding="utf-8"))
    except Exception:
        return p, {}


def get_json(url, cache_name=None, key=None, pause=0.0, timeout=25):
    if cache_name:
        p, c = _cache(cache_name)
        if key in c:
            return c[key]
    time.sleep(pause)
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        v = json.loads(r.read().decode("utf-8"))
    if cache_name:
        c[key] = v
        json.dump(c, open(p, "w", encoding="utf-8"), ensure_ascii=False)
    return v


def place_names(lat, lon):
    """(hindi, english, state) from OpenStreetMap."""
    out = {}
    for lang in ("hi", "en"):
        key = f"{lat:.3f},{lon:.3f},{lang}"
        try:
            d = get_json(f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&zoom=14"
                         f"&accept-language={lang}", "places", key, pause=1.1)
        except Exception:
            d = {}
        a = d.get("address", {})
        name = next((a[k] for k in ("village", "hamlet", "town", "city", "suburb", "municipality", "county",
                                     "state_district") if a.get(k)), d.get("name") or "")
        out[lang] = (name, a.get("state", ""))
    hi, en = out.get("hi", ("", "")), out.get("en", ("", ""))
    return hi[0] or en[0], en[0], en[1]


def elevation(lat, lon):
    try:
        return get_json(f"https://api.open-meteo.com/v1/elevation?latitude={lat:.5f}&longitude={lon:.5f}",
                        "elevation", f"{lat:.4f},{lon:.4f}")["elevation"][0]
    except Exception:
        return None


# WMO weather code -> SPP Info Card weather dropdown (0 none 1 sun 2 part-cloud 3 cloud 4 rain 5 snow 6 fog 7 night)
def wmo_to_card(code, is_day):
    if code is None:
        return 0
    if code in (45, 48):
        return 6
    if 71 <= code <= 77 or code in (85, 86):
        return 5
    if 51 <= code <= 67 or 80 <= code <= 82 or code >= 95:
        return 4
    if code == 3:
        return 3
    if code == 2:
        return 2 if is_day else 7
    return 1 if is_day else 7


def weather(lat, lon, ep, tz):
    day = fmt_local(ep, tz, "%Y-%m-%d")
    hour = int(fmt_local(ep, tz, "%H"))
    tzname = "Asia%2FKolkata" if abs(tz.utcoffset(None).total_seconds() - 19800) < 1 else "auto"
    q = (f"latitude={lat:.3f}&longitude={lon:.3f}&start_date={day}&end_date={day}"
         f"&hourly=temperature_2m,weather_code,is_day&timezone={tzname}")
    for base in ("https://archive-api.open-meteo.com/v1/archive?", "https://api.open-meteo.com/v1/forecast?"):
        try:
            d = get_json(base + q, "weather", f"{base[8:20]}{lat:.2f},{lon:.2f},{day}")
            h = d["hourly"]
            if h["temperature_2m"][hour] is None:
                continue
            code = h["weather_code"][hour]
            return {"temp_c": round(h["temperature_2m"][hour]), "wmo": code,
                    "card": wmo_to_card(code, h["is_day"][hour])}
        except Exception:
            continue
    return None


def describe(idx, ep, tz, web=True, pos=None):
    pos = pos or position_at(idx, ep)
    out = {"time_local": fmt_local(ep, tz), "date_hi": hi_date(ep, tz), "time_ampm": ampm(ep, tz)}
    if not pos:
        out["error"] = "no GPS near this time - add a Google Timeline export (index --timeline ...)"
        return out
    out.update({k: (round(v, 5) if isinstance(v, float) else v) for k, v in pos.items()})
    if web:
        hi, en, state = place_names(pos["lat"], pos["lon"])
        out["place_hi"], out["place_en"] = hi, (f"{en} · {state}" if state else en).upper()
        out["altitude_m"] = elevation(pos["lat"], pos["lon"])
        w = weather(pos["lat"], pos["lon"], ep, tz)
        if w:
            out.update(w)
    return out


def file_time(idx, name):
    """Start time of a media file from the index (by file name)."""
    name = os.path.basename(name).lower()
    for r in idx["media"]:
        if os.path.basename(r["file"]).lower() == name:
            return r.get("t"), r
    return None, None


# ------------------------------------------------------------------ stops
def find_stops(idx, tz, min_stay_min=40, radius_km=1.5, t_from=None, t_to=None):
    P = [p for p in idx["points"] if (t_from is None or p[0] >= t_from) and (t_to is None or p[0] <= t_to)]
    stops, i = [], 0
    while i < len(P):
        j, la, lo = i, P[i][1], P[i][2]
        n = 1
        while j + 1 < len(P) and hav_km((la, lo), (P[j + 1][1], P[j + 1][2])) <= radius_km:
            j += 1; n += 1
            la += (P[j][1] - la) / n; lo += (P[j][2] - lo) / n
        if P[j][0] - P[i][0] >= min_stay_min * 60:
            stops.append({"lat": la, "lon": lo, "arrive": P[i][0], "leave": P[j][0], "n": n})
        i = j + 1
    # merge stops at the same place (e.g. two nights in one town with a gap)
    merged = []
    for s in stops:
        if merged and hav_km((merged[-1]["lat"], merged[-1]["lon"]), (s["lat"], s["lon"])) <= radius_km:
            merged[-1]["leave"] = s["leave"]
        else:
            merged.append(s)
    return merged


def stop_labels(stops, tz, web=True):
    for s in stops:
        if web and not (s.get("hi") and s.get("en")):
            hi, en, state = place_names(s["lat"], s["lon"])
            s["hi"], s["en"] = s.get("hi") or hi, s.get("en") or en.upper()
        if web:
            s["alt"] = elevation(s["lat"], s["lon"])
        s["arrive_local"], s["leave_local"] = fmt_local(s["arrive"], tz), fmt_local(s["leave"], tz)
        s["arrive_hi"] = f"{hi_date(s['arrive'], tz, False)} · {ampm(s['arrive'], tz)}"
        s["leave_hi"] = f"{hi_date(s['leave'], tz, False)} · {ampm(s['leave'], tz)}"
    return stops


def geocode(q):
    d = get_json("https://nominatim.openstreetmap.org/search?format=json&limit=1&countrycodes=in,np&q="
                 + urllib.parse.quote(q), "geocode", q.lower(), pause=1.1)
    if not d:
        raise SystemExit(f"Can't find the place '{q}' - use 'lat, lon' instead")
    return float(d[0]["lat"]), float(d[0]["lon"])


STOP_COLS = ["hindi", "english", "place (name or lat, lon)", "arrive (YYYY-MM-DD HH:MM)", "leave (YYYY-MM-DD HH:MM)"]


def write_stops_csv(stops, tz, path):
    import csv
    with open(path, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh); w.writerow(STOP_COLS)
        for s in stops:
            w.writerow([s.get("hi", ""), s.get("en", "").title(), f"{s['lat']:.5f}, {s['lon']:.5f}",
                        fmt_local(s["arrive"], tz), fmt_local(s["leave"], tz)])
    log(f"Stops written to {path} - edit names / add or delete rows in Excel, then use  route ... --stops-file")


def read_stops_csv(path, tz):
    import csv
    out = []
    with open(path, encoding="utf-8-sig") as fh:
        rows = list(csv.reader(fh))
    for r in rows[1:]:
        if len(r) < 5 or not r[2].strip():
            continue
        hi, en, place, arr, lev = [x.strip() for x in r[:5]]
        ll = parse_latlng(place) if re.fullmatch(r"\s*-?\d+(\.\d+)?\s*,\s*-?\d+(\.\d+)?\s*", place) else geocode(place)
        a = local_to_epoch(arr, tz); b = local_to_epoch(lev, tz) if lev else a
        out.append({"lat": ll[0], "lon": ll[1], "arrive": a, "leave": max(a, b), "hi": hi, "en": en.upper(), "manual": True})
    return sorted(out, key=lambda s: s["arrive"])


# ------------------------------------------------------------------ roads between stops (OSRM)
def road_path(a, b):
    """Driving geometry between two (lat, lon) points, or None."""
    url = (f"https://router.project-osrm.org/route/v1/driving/{a[1]:.5f},{a[0]:.5f};{b[1]:.5f},{b[0]:.5f}"
           f"?overview=full&geometries=geojson")
    try:
        d = get_json(url, "roads", f"{a[0]:.4f},{a[1]:.4f};{b[0]:.4f},{b[1]:.4f}", pause=1.0)
        coords = d["routes"][0]["geometry"]["coordinates"]
        road_path.last_duration = d["routes"][0].get("duration")
        return [(la, lo) for lo, la in coords]
    except Exception:
        return None


# ------------------------------------------------------------------ route map
def mercator(lat, lon, z):
    s = 256 * 2 ** z
    x = (lon + 180) / 360 * s
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * s
    return x, y


def fetch_tile(z, x, y):
    p = os.path.join(CACHE_DIR, "terrain", f"{z}_{x}_{y}.png")
    if not os.path.exists(p):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        url = f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
            open(p, "wb").write(r.read())
    return p


def render_relief(bbox_px, z, W, H):
    """Brand-coloured shaded relief for the Mercator pixel box (x0,y0,x1,y1) at zoom z, resized to W x H.
    Returns (PIL image RGB, elevation array at output size)."""
    import numpy as np
    from PIL import Image
    x0, y0, x1, y1 = bbox_px
    tx0, ty0, tx1, ty1 = int(x0 // 256), int(y0 // 256), int(x1 // 256), int(y1 // 256)
    from concurrent.futures import ThreadPoolExecutor
    jobs = [(z, tx, ty) for ty in range(ty0, ty1 + 1) for tx in range(tx0, tx1 + 1)]
    log(f"  terrain tiles: {len(jobs)}")
    with ThreadPoolExecutor(8) as ex:
        list(ex.map(lambda j: fetch_tile(*j), jobs))
    mos = np.zeros(((ty1 - ty0 + 1) * 256, (tx1 - tx0 + 1) * 256), np.float32)
    for ty in range(ty0, ty1 + 1):
        for tx in range(tx0, tx1 + 1):
            a = np.asarray(Image.open(fetch_tile(z, tx, ty)).convert("RGB"), np.float32)
            mos[(ty - ty0) * 256:(ty - ty0 + 1) * 256, (tx - tx0) * 256:(tx - tx0 + 1) * 256] = \
                a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
    cx0, cy0 = int(x0 - tx0 * 256), int(y0 - ty0 * 256)
    el = mos[cy0:cy0 + int(y1 - y0), cx0:cx0 + int(x1 - x0)]
    el = np.asarray(Image.fromarray(el).resize((W, H), Image.BICUBIC), np.float32)
    k = 2 if W > 2000 else 1                   # light smoothing: down and up again (removes tile grain)
    if k > 1:
        el = np.asarray(Image.fromarray(el).resize((W // k, H // k), Image.BILINEAR).resize((W, H), Image.BICUBIC), np.float32)
    # hillshade (sun from north-west), metres per output pixel
    lat_c = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * ((y0 + y1) / 2) / (256 * 2 ** z)))))
    mpp = 156543.03 * math.cos(math.radians(lat_c)) / 2 ** z * (x1 - x0) / W
    gy, gx = np.gradient(el, mpp)
    exag = float(np.interp(z, [6, 9, 12, 13], [3.0, 1.8, 1.0, 0.8]))   # flatter at close zoom
    slope = np.arctan(exag * np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    az, alt = math.radians(315), math.radians(45)
    shade = np.clip(np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect), 0, 1)
    # brand colour ramp by height: night navy valleys -> glacier blue ridges -> snow only on the high peaks
    stops = [(-100, (12, 24, 46)), (1000, (20, 38, 66)), (2200, (28, 52, 88)), (3400, (40, 70, 108)),
             (4600, (74, 102, 138)), (5400, (150, 170, 196)), (6200, (226, 234, 243)), (8000, (245, 248, 252))]
    hs = np.array([q[0] for q in stops], np.float32)
    cols = np.array([q[1] for q in stops], np.float32)
    rgb = np.stack([np.interp(el, hs, cols[:, k]) for k in range(3)], -1)
    lit = (0.45 + 0.75 * shade ** 1.3)[..., None]
    rgb = rgb * lit
    # soft vignette so labels read well
    yy, xx = np.mgrid[0:H, 0:W]
    v = 1 - 0.32 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) ** 1.2
    rgb = np.clip(rgb * np.clip(v, 0.6, 1)[..., None], 0, 255).astype(np.uint8)
    return Image.fromarray(rgb, "RGB"), el


def rivers(bbox_ll):
    """Main rivers in the box from OpenStreetMap (list of [(lat,lon),...])."""
    s, w, n, e = bbox_ll
    q = f'[out:json][timeout:120];way["waterway"="river"]["name"]({s:.4f},{w:.4f},{n:.4f},{e:.4f});out geom;'
    for server in ("https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"):
        try:
            d = get_json(server + "?data=" + urllib.parse.quote(q), "rivers", f"{s:.2f},{w:.2f},{n:.2f},{e:.2f}", timeout=130)
            return [[(g["lat"], g["lon"]) for g in el.get("geometry", [])] for el in d.get("elements", [])]
        except Exception as ex:
            log("  rivers:", server.split('/')[2], ex)
    return []


def make_route(idx, tz, out_dir, t_from=None, t_to=None, portrait=False, min_stay=40, roads=True, stops_file=None,
               with_rivers=False):
    from PIL import Image, ImageDraw
    if stops_file:
        stops = read_stops_csv(stops_file, tz)          # your list replaces the automatic one
    else:
        stops = find_stops(idx, tz, min_stay, t_from=t_from, t_to=t_to)
        os.makedirs(out_dir, exist_ok=True)
        write_stops_csv(stop_labels([dict(x) for x in stops], tz), tz, os.path.join(out_dir, "stops.csv"))
    stops = stop_labels(stops, tz)
    if len(stops) < 2:
        raise SystemExit("Fewer than 2 stops found - add a Google Timeline export or lower --min-stay.")
    P = [p for p in idx["points"] if (t_from is None or p[0] >= t_from) and (t_to is None or p[0] <= t_to)]
    # travel path: GPS points between stops, or the road between them when points are sparse
    path = []  # (lat, lon, t or None)
    for a, b in zip(stops, stops[1:]):
        anchors = [(a["lat"], a["lon"], a["leave"])]
        for p in P:
            if a["leave"] < p[0] < b["arrive"] and hav_km(anchors[-1][:2], (p[1], p[2])) >= 1.0:
                anchors.append((p[1], p[2], p[0]))
        anchors.append((b["lat"], b["lon"], b["arrive"]))
        for u, w in zip(anchors, anchors[1:]):
            path.append(u)
            d = hav_km(u[:2], w[:2])
            if roads and d > 2.0:
                road_path.last_duration = None
                rp = road_path(u[:2], w[:2])
                if rp:
                    rl = sum(hav_km(p, q) for p, q in zip(rp, rp[1:]))
                    elapsed = (w[2] - u[2]) if (u[2] and w[2]) else None
                    drive = road_path.last_duration
                    # take the road if it is direct, or if we had enough time between the two GPS fixes to drive it
                    if rl <= 2.5 * d + 3 or (elapsed and drive and drive <= 1.5 * elapsed + 1800):
                        path += [(la, lo, None) for la, lo in rp[1:-1]]
        path.append(anchors[-1])
    W, H = (1080, 1920) if portrait else (3840, 2160)
    lats = [p[0] for p in path]; lons = [p[1] for p in path]
    # zoom: the largest one where the route fits ~72% of the frame, then one more level (rendered big, scaled down = sharp)
    def span(z):
        xa, ya = mercator(max(lats), min(lons), z); xb, yb = mercator(min(lats), max(lons), z)
        return xa, ya, xb, yb
    zf = 4
    for z in range(4, 14):
        xa, ya, xb, yb = span(z)
        if (xb - xa) <= 0.72 * W and (yb - ya) <= 0.72 * H:
            zf = z
    z = min(zf + 1, 13)
    xa, ya, xb, yb = span(z)
    cx, cy = (xa + xb) / 2, (ya + yb) / 2
    scale = min(0.72 * W / max(xb - xa, 1), 0.72 * H / max(yb - ya, 1))
    scale = max(0.35, min(scale, 2.5))
    bw, bh = W / scale, H / scale
    box = (cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2)
    log(f"  map: zoom {z}, {W}x{H}")
    img, el = render_relief(box, z, W, H)

    def to_px(la, lo):
        x, y = mercator(la, lo, z)
        return (x - box[0]) / bw * W, (y - box[1]) / bh * H

    # rivers in glacier blue
    inv = lambda x, y: (math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / (256 * 2 ** z))))), x / (256 * 2 ** z) * 360 - 180)
    n_, w_ = inv(box[0], box[1]); s_, e_ = inv(box[2], box[3])
    dr = ImageDraw.Draw(img, "RGBA")
    for rv in (rivers((s_, w_, n_, e_)) if with_rivers else []):
        pts = [to_px(la, lo) for la, lo in rv]
        if len(pts) > 1:
            dr.line(pts, fill=(62, 124, 177, 170), width=max(2, W // 900), joint="curve")
    os.makedirs(out_dir, exist_ok=True)
    img.save(os.path.join(out_dir, "map.jpg"), quality=92)

    # simplify path to <= 600 points
    pxs = [(*to_px(la, lo), t) for la, lo, t in path]
    step = max(1, len(pxs) // 600)
    pxs = [p for i, p in enumerate(pxs) if i % step == 0 or p[2] or i == len(pxs) - 1]   # keep every timed point
    L = [0.0]
    for (x1, y1, _), (x2, y2, _) in zip(pxs, pxs[1:]):
        L.append(L[-1] + math.hypot(x2 - x1, y2 - y1))
    tot = L[-1] or 1

    def frac_of(s):
        sx, sy = to_px(s["lat"], s["lon"])
        k = min(range(len(pxs)), key=lambda i: (pxs[i][0] - sx) ** 2 + (pxs[i][1] - sy) ** 2)
        return L[k] / tot

    route = {
        "spp": "route", "map": "map.jpg", "w": W, "h": H,
        "path": [[round(x / W, 5), round(y / H, 5), round(l / tot, 5), (int(t) if t else None)]
                 for (x, y, t), l in zip(pxs, L)],
        "stops": [{"x": round(to_px(s["lat"], s["lon"])[0] / W, 5), "y": round(to_px(s["lat"], s["lon"])[1] / H, 5),
                   "f": round(frac_of(s), 5), "hi": s["hi"], "en": s["en"], "alt": s["alt"],
                   "arrive": s["arrive_hi"], "leave": s["leave_hi"], "arrive_t": int(s["arrive"]), "leave_t": int(s["leave"])}
                  for s in stops],
        "tz": idx.get("tz", 5.5),
        "track": [[round(la, 6), round(lo, 6), (int(t) if t else None)] for la, lo, t in path],
        "credit": "Terrain: Mapzen / AWS Terrain Tiles · Places & rivers © OpenStreetMap contributors",
    }
    # first stop starts the route, last one ends it
    route["stops"][0]["f"], route["stops"][-1]["f"] = 0.0, 1.0
    json.dump(route, open(os.path.join(out_dir, "route.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    write_gpx(idx, os.path.join(out_dir, "route.gpx"), tz, route_json=os.path.join(out_dir, "route.json"))
    log(f"Route: {len(stops)} stops, {len(route['path'])} path points -> {out_dir}")
    for s in stops:
        log(f"  {s['arrive_local']} → {s['leave_local']}  {s['hi']} / {s['en']}  {s['alt']} m")
    return route


# ------------------------------------------------------------------ GPX export (for 3D flyover apps)
def write_gpx(idx, path, tz, t_from=None, t_to=None, route_json=None):
    """Track as GPX: the road-following route from route.json if given, else the raw GPS points."""
    pts = []
    if route_json:
        R = json.load(open(route_json, encoding="utf-8"))
        pts = [(la, lo, t) for la, lo, t in R.get("track", [])]
    if not pts:
        pts = [(p[1], p[2], p[0]) for p in idx["points"]
               if (t_from is None or p[0] >= t_from) and (t_to is None or p[0] <= t_to)]
    iso = lambda t: dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8"?>\n<gpx version="1.1" creator="Safar Pahad Parivar" '
                 'xmlns="http://www.topografix.com/GPX/1/1"><trk><name>Safar Pahad Parivar</name><trkseg>\n')
        for la, lo, t in pts:
            fh.write(f'<trkpt lat="{la:.6f}" lon="{lo:.6f}">' + (f"<time>{iso(t)}</time>" if t else "") + "</trkpt>\n")
        fh.write("</trkseg></trk></gpx>\n")
    log(f"GPX: {len(pts)} points -> {path}")


# ------------------------------------------------------------------ local API
def serve(trip, tz, port=8777):
    from http.server import BaseHTTPRequestHandler, HTTPServer
    idx = load_index(trip)

    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            u = urllib.parse.urlparse(self.path); q = dict(urllib.parse.parse_qsl(u.query))
            try:
                if u.path == "/at":
                    body = describe(idx, local_to_epoch(q["t"], tz), tz, web=q.get("web", "1") != "0")
                elif u.path == "/file":
                    t0, r = file_time(idx, q["name"])
                    own = {"lat": r["lat"], "lon": r["lon"], "gap_min": 0, "source": "file"} if r and "lat" in r else None
                    body = describe(idx, t0 + float(q.get("offset", 0)), tz, pos=own) if t0 else {"error": "file not in index"}
                elif u.path == "/stops":
                    body = stop_labels(find_stops(idx, tz, float(q.get("min_stay", 40))), tz, web=q.get("web", "1") != "0")
                else:
                    body = {"use": ["/at?t=2026-06-26T11:14", "/file?name=VID20260626111444.mp4&offset=10", "/stops"]}
                code = 200
            except Exception as e:
                body, code = {"error": str(e)}, 400
            b = json.dumps(body, ensure_ascii=False, indent=1).encode("utf-8")
            self.send_response(code); self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    log(f"SPP GPS API on http://127.0.0.1:{port}/at?t=2026-06-26T11:14   (Ctrl+C to stop)")
    HTTPServer(("127.0.0.1", port), H).serve_forever()


# ------------------------------------------------------------------ CLI
def main():
    ap = argparse.ArgumentParser(description="Safar Pahad Parivar GPS lookup")
    ap.add_argument("cmd", choices=["index", "at", "file", "stops", "route", "gpx", "serve"])
    ap.add_argument("trip")
    ap.add_argument("arg", nargs="?")
    ap.add_argument("--timeline", action="append", default=[])
    ap.add_argument("--tz", default="+05:30")
    ap.add_argument("--offset", type=float, default=0.0, help="seconds into the file (for 'file')")
    ap.add_argument("--min-stay", type=float, default=40)
    ap.add_argument("--from", dest="t_from"); ap.add_argument("--to", dest="t_to")
    ap.add_argument("--portrait", action="store_true")
    ap.add_argument("--no-roads", action="store_true")
    ap.add_argument("--rivers", action="store_true", help="draw rivers (slow; OpenStreetMap servers often time out)")
    ap.add_argument("--stops-file", help="your own stops (CSV made by 'stops --csv' or 'route')")
    ap.add_argument("--csv", help="also write the stops to this CSV (for 'stops')")
    ap.add_argument("--offline", action="store_true", help="no place names / altitude / weather lookups")
    a = ap.parse_args()
    tz = parse_tz(a.tz)
    trip = os.path.abspath(a.trip)
    if a.cmd == "index":
        tls = []
        for t in a.timeline:
            tls += glob.glob(t)
        old = os.path.join(trip, INDEX)
        if not tls and os.path.exists(old):       # keep timelines added earlier
            tls = [t for t in json.load(open(old, encoding="utf-8")).get("timelines", []) if os.path.exists(t)]
        build_index(trip, [os.path.abspath(t) for t in tls], tz)
        return
    idx = load_index(trip)
    tf = local_to_epoch(a.t_from, tz) if a.t_from else None
    tt = local_to_epoch(a.t_to, tz) + (86400 if a.t_to and len(a.t_to) <= 10 else 0) if a.t_to else None
    if a.cmd == "at":
        res = describe(idx, local_to_epoch(a.arg, tz), tz, web=not a.offline)
    elif a.cmd == "file":
        t0, r = file_time(idx, a.arg)
        if not t0:
            raise SystemExit("File not in the index (run 'index' again?)")
        own = {"lat": r["lat"], "lon": r["lon"], "gap_min": 0, "source": "file"} if "lat" in r else None
        res = describe(idx, t0 + a.offset, tz, web=not a.offline, pos=own)  # the file's own GPS beats interpolation
        res["file"] = r["file"]
    elif a.cmd == "stops":
        res = stop_labels(find_stops(idx, tz, a.min_stay, t_from=tf, t_to=tt), tz, web=not a.offline)
        for s in res:
            s["lat"], s["lon"] = round(s["lat"], 5), round(s["lon"], 5)
        if a.csv:
            write_stops_csv(res, tz, a.csv)
    elif a.cmd == "route":
        if not a.arg:
            raise SystemExit("Give an output folder, e.g. \"<video>\\Graphics\\Route\"")
        make_route(idx, tz, os.path.abspath(a.arg), tf, tt, a.portrait, a.min_stay, not a.no_roads, a.stops_file, a.rivers)
        return
    elif a.cmd == "gpx":
        write_gpx(idx, os.path.abspath(a.arg or os.path.join(trip, "trip.gpx")), tz, tf, tt)
        return
    elif a.cmd == "serve":
        serve(trip, tz)
        return
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
