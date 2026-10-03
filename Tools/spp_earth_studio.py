"""Google Earth Studio fly-over from an SPP route (route.json made by 'Route Map - Build from Timeline').

Writes, for the whole trip or one chapter (from stop -> to stop):
    <name>.esp   a Google Earth Studio project: a camera that flies along your road, behind and above the car,
                 looking ahead and down, high enough to clear the ridges on the way (terrain-aware)
    <name>.kml   the route line (SPP gold) + stop pins, to add in Earth Studio (Add > KML) so the road shows on the map

Earth Studio (earth.google.com/studio, free, Google account, Chrome) then renders it as an image sequence you drop
into Resolve. Google requires the on-screen credit "Google Earth" while its imagery is shown.

    python spp_earth_studio.py route.json out_folder [--from Dharchula] [--to Dugtu] [--seconds 30] [--fps 30]
                               [--height 1500] [--behind 3000] [--size 3840x2160]
"""
import argparse, io, json, math, os, re, sys, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
EARTH_M = 2 * math.pi * 6.371e6
ACCENT_KML = "ff3eb0f4"                       # #f4b03e as KML aabbggrr


# ------------------------------------------------------------------ geometry
def dxdy(a, b):
    """metres east / north from a to b (lat, lon)"""
    return (EARTH_M * (b[1] - a[1]) / 360 * math.cos(math.radians(a[0])), EARTH_M * (b[0] - a[0]) / 360)


def dist(a, b):
    return math.hypot(*dxdy(a, b))


def offset(p, east, north):
    return (p[0] + north / EARTH_M * 360, p[1] + east / (EARTH_M * math.cos(math.radians(p[0]))) * 360)


def resample(pts, n):
    """n points evenly spaced along the polyline pts [(lat, lon)]"""
    L = [0.0]
    for a, b in zip(pts, pts[1:]):
        L.append(L[-1] + dist(a, b))
    tot = L[-1] or 1.0
    out, j = [], 0
    for i in range(n):
        s = tot * i / (n - 1)
        while j < len(L) - 2 and L[j + 1] < s:
            j += 1
        q = (s - L[j]) / max(L[j + 1] - L[j], 1e-9)
        a, b = pts[j], pts[min(j + 1, len(pts) - 1)]
        out.append((a[0] + (b[0] - a[0]) * q, a[1] + (b[1] - a[1]) * q))
    return out, tot


def smooth(vals, w):
    """moving average (window w, edges shrink) for lists of numbers or tuples"""
    if w <= 1:
        return list(vals)
    h = w // 2
    out = []
    for i in range(len(vals)):
        seg = vals[max(0, i - h):i + h + 1]
        if isinstance(vals[0], tuple):
            out.append(tuple(sum(x[k] for x in seg) / len(seg) for k in range(len(vals[0]))))
        else:
            out.append(sum(seg) / len(seg))
    return out


# ------------------------------------------------------------------ terrain (same free tiles as the route map)
_tiles = {}


def terrain(lat, lon, z=11):
    """ground height (m) from Terrarium elevation tiles, cached on disk by spp_gps"""
    try:
        import spp_gps
        from PIL import Image
    except Exception:
        return 0.0
    s = 256 * 2 ** z
    x = (lon + 180) / 360 * s
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * s
    tx, ty = int(x // 256), int(y // 256)
    k = (z, tx, ty)
    if k not in _tiles:
        try:
            _tiles[k] = Image.open(spp_gps.fetch_tile(z, tx, ty)).convert("RGB")
        except Exception:
            _tiles[k] = None
    im = _tiles[k]
    if im is None:
        return 0.0
    r, g, b = im.getpixel((min(255, int(x % 256)), min(255, int(y % 256))))
    return r * 256 + g + b / 256 - 32768


# ------------------------------------------------------------------ route.json -> segment
def norm(s):
    return re.sub(r"[^a-z0-9ऀ-ॿ]", "", str(s or "").lower())


def stop_index(stops, q, default):
    q = str(q or "").strip()
    if not q:
        return default
    if q.isdigit():
        return max(0, min(len(stops) - 1, int(q) - 1))
    k = norm(q)
    for test in (lambda a: a == k, lambda a: a.startswith(k), lambda a: k in a):
        for i, s in enumerate(stops):
            if test(norm(s.get("hi"))) or test(norm(s.get("en"))):
                return i
    raise SystemExit("No stop called '%s'. Stops: %s" % (q, ", ".join(s.get("en") or s.get("hi") for s in stops)))


def segment(R, frm=None, to=None):
    """(track points [(lat, lon)], stops in the segment [(name, lat, lon)])"""
    st, tr = R["stops"], R["track"]
    i0, i1 = stop_index(st, frm, 0), stop_index(st, to, len(st) - 1)
    if i1 < i0:
        i0, i1 = i1, i0
    if i1 == i0:
        i1 = min(i1 + 1, len(st) - 1)
    t0, t1 = st[i0]["leave_t"], st[i1]["arrive_t"]
    timed = [k for k, p in enumerate(tr) if p[2]]
    k0 = next((k for k in timed if tr[k][2] >= t0 - 1), 0)
    k1 = max([k for k in timed if tr[k][2] <= t1 + 1] or [len(tr) - 1])
    pts = [(p[0], p[1]) for p in tr[k0:k1 + 1]]
    pins = []
    for i in range(i0, i1 + 1):                     # stop positions = the track point at its arrive / leave time
        s = st[i]
        want = s["leave_t"] if i == i0 else s["arrive_t"]
        k = min(timed, key=lambda k: abs(tr[k][2] - want)) if timed else 0
        name = " · ".join(x for x in (s.get("hi"), s.get("en")) if x)
        pins.append((name, tr[k][0], tr[k][1]))
    return pts, pins, (st[i0], st[i1])


# ------------------------------------------------------------------ camera path
def camera(pts, n=240, height=1500.0, behind=3000.0):
    path, total = resample(pts, max(n * 3, 50))
    w = max(3, int(len(path) * min(0.06, 4000.0 / max(total, 1))))      # smooth over ~4 km (bends -> sweeps)
    sm = smooth(path, w)
    tgt, _ = resample(sm, n)
    out = []
    for i, p in enumerate(tgt):                     # heading from a point well ahead -> calm, cinematic turns
        a, b = tgt[max(0, i - 3)], tgt[min(n - 1, i + 3)]
        e, no = dxdy(a, b)
        hd = math.atan2(e, no) if (e or no) else (out[-1]["hd"] if out else 0.0)
        cam = offset(p, -behind * math.sin(hd), -behind * math.cos(hd))
        out.append({"tgt": p, "cam": cam, "hd": hd})
    # altitude: clear the highest ground around camera + target, then smooth so the camera floats
    for o in out:
        g = [terrain(*o["cam"]), terrain(*o["tgt"])]
        for f in (0.33, 0.66):
            g.append(terrain(o["cam"][0] + (o["tgt"][0] - o["cam"][0]) * f, o["cam"][1] + (o["tgt"][1] - o["cam"][1]) * f))
        o["ground"], o["tg"] = max(g), g[1]
    alts = smooth([o["ground"] + height for o in out], 9)
    alts = [max(a, o["ground"] + 0.6 * height) for a, o in zip(alts, out)]
    for o, a in zip(out, alts):
        o["alt"] = a
        o["tilt"] = math.degrees(math.atan2(behind, max(50.0, a - o["tg"])))   # 0 = straight down, 90 = horizon
    tilts = smooth([o["tilt"] for o in out], 9)
    pans, prev = [], None
    for o in out:
        b = (math.degrees(o["hd"]) + 360) % 360
        if prev is not None:
            while b - prev > 180:
                b -= 360
            while b - prev < -180:
                b += 360
        pans.append(b)
        prev = b
    pans = smooth(pans, 7)
    for o, t, p in zip(out, tilts, pans):
        o["tilt"], o["pan"] = t, p
    return out, total


# ------------------------------------------------------------------ Earth Studio project (.esp, JSON)
# Values are stored as a 0..1 position between minValueRange and maxValueRange (format worked out by
# github.com/mkatzef/google-studio-utils): longitude min..180, latitude min..90, altitude metres * 1.53567e-8
# (linear), pan between its own min / max, tilt degrees / 180.
def _block(kind, vals, lo=None, hi=None, alt=False):
    n = len(vals)
    b = {"type": kind, "value": {"relative": 0}, "keyframes": [{"time": i / (n - 1), "value": v} for i, v in enumerate(vals)],
         "inTimeline": True}
    if lo is not None:
        b["value"]["minValueRange"] = lo
    if hi is not None:
        b["value"]["maxValueRange"] = hi
    if alt:
        b["value"]["logarithmic"] = False
    return b


def esp(cam, name, frames, fps, w, h):
    lons = [c["cam"][1] for c in cam]
    lats = [c["cam"][0] for c in cam]
    lo_lon, lo_lat = min(lons), min(lats)
    pans = [c["pan"] for c in cam]
    p0, p1 = min(pans), max(pans)
    if p1 - p0 < 1e-6:
        p1 = p0 + 1
    pos = [_block("longitude", [(x - lo_lon) / (180 - lo_lon) for x in lons], lo_lon, 180),
           _block("latitude", [(y - lo_lat) / (90 - lo_lat) for y in lats], lo_lat, 90),
           _block("altitude", [c["alt"] * 1.5356706349899208e-08 for c in cam], alt=True)]
    rot = [_block("rotationX", [(p - p0) / (p1 - p0) for p in pans], p0, p1),
           _block("rotationY", [c["tilt"] / 180 for c in cam]),
           {"type": "rotationZ", "value": {}}]
    v = lambda **k: k
    return {
        "modelVersion": 17,
        "settings": {"name": name, "frameRate": fps, "dimensions": {"width": w, "height": h}, "duration": frames,
                     "timeFormat": "frames"},
        "scenes": [{
            "animationModel": {"roving": False, "logarithmic": False, "groupedPosition": True},
            "duration": frames,
            "attributes": [
                {"type": "cameraGroup", "inTimeline": True, "attributes": [
                    {"type": "cameraPositionGroup", "inTimeline": True, "attributes": pos},
                    {"type": "cameraTargetEffect", "attributes": [
                        {"type": "enabled", "value": {}},
                        {"type": "poi", "attributes": [{"type": "longitudePOI", "value": {}}, {"type": "latitudePOI", "value": {}},
                                                       {"type": "altitudePOI", "value": {"logarithmic": False}}]},
                        {"type": "influence", "value": {}}]},
                    {"type": "cameraRotationGroup", "inTimeline": True, "attributes": rot},
                    {"type": "cameraLensGroup", "attributes": [{"type": t, "value": {}} for t in ("fov", "exposure", "aperture", "minFocusLength")]}]},
                {"type": "environmentGroup", "attributes": [
                    {"type": "sunGroup", "attributes": [{"type": "sunVisibility", "value": {}}, {"type": "worldTime", "value": {"relative": 0.5}}]},
                    {"type": "cloudGroup", "attributes": [{"type": "cloudVisibility", "value": {}}, {"type": "cloudopacity", "value": {}},
                                                          {"type": "cloudheight", "value": {}}, {"type": "clouddate", "value": {"relative": 0.95}}]},
                    {"type": "starsPlanetsGroup", "attributes": [{"type": "starsEnabled", "value": {}}]},
                    {"type": "seawaterGroup", "attributes": [{"type": "seawater", "value": {}}, {"type": "influence", "value": {"relative": 1}}]},
                    {"type": "buildingsEnabled", "value": {}}]}],
            "cameraExport": {"logarithmic": False, "modelVersion": 2}}],
        "playbackManager": {"range": {"start": 0, "end": frames}},
    }


def kml(pts, pins, name):
    esc = lambda s: s.replace("&", "&amp;").replace("<", "&lt;")
    coords = " ".join("%.6f,%.6f,0" % (lo, la) for la, lo in pts)
    marks = "".join('<Placemark><name>%s</name><styleUrl>#stop</styleUrl><Point><coordinates>%.6f,%.6f,0</coordinates></Point></Placemark>'
                    % (esc(n), lo, la) for n, la, lo in pins)
    return ('<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>%s</name>'
            '<Style id="road"><LineStyle><color>%s</color><width>6</width></LineStyle></Style>'
            '<Style id="stop"><IconStyle><color>%s</color><scale>1.2</scale></IconStyle><LabelStyle><scale>1.1</scale></LabelStyle></Style>'
            '<Placemark><name>Route</name><styleUrl>#road</styleUrl><LineString><tessellate>1</tessellate>'
            '<altitudeMode>clampToGround</altitudeMode><coordinates>%s</coordinates></LineString></Placemark>%s</Document></kml>'
            % (esc(name), ACCENT_KML, ACCENT_KML, coords, marks))


def make(route_json, out_dir, frm=None, to=None, seconds=30.0, fps=30, height=1500.0, behind=3000.0, size="3840x2160",
         name=None):
    R = json.load(open(route_json, encoding="utf-8"))
    pts, pins, (a, b) = segment(R, frm, to)
    if len(pts) < 2:
        raise SystemExit("Not enough route points between those stops.")
    w, h = (int(x) for x in size.lower().split("x"))
    cam, km = camera(pts, n=max(40, min(400, int(seconds * 6))), height=height, behind=behind)
    nm = name or "SPP Flyover - %s to %s" % (a.get("en") or a.get("hi"), b.get("en") or b.get("hi"))
    nm = re.sub(r'[<>:"/\\|?*]', "_", nm)
    os.makedirs(out_dir, exist_ok=True)
    frames = int(round(seconds * fps))
    pe = os.path.join(out_dir, nm + ".esp")
    json.dump(esp(cam, nm, frames, fps, w, h), open(pe, "w", encoding="utf-8"), indent=1)
    pk = os.path.join(out_dir, nm + ".kml")
    open(pk, "w", encoding="utf-8").write(kml(pts, pins, nm))
    print("%s: %.0f km, %d keyframes, %ds at %d fps -> %s (+ .kml)" % (nm, km / 1000, len(cam), seconds, fps, pe))
    return pe, pk


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("route_json"); ap.add_argument("out_dir")
    ap.add_argument("--from", dest="frm"); ap.add_argument("--to")
    ap.add_argument("--seconds", type=float, default=30); ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--height", type=float, default=1500, help="camera height above the ridges (m)")
    ap.add_argument("--behind", type=float, default=3000, help="camera distance behind the car (m)")
    ap.add_argument("--size", default="3840x2160")
    ap.add_argument("--name")
    a = ap.parse_args()
    make(a.route_json, a.out_dir, a.frm, a.to, a.seconds, a.fps, a.height, a.behind, a.size, a.name)
