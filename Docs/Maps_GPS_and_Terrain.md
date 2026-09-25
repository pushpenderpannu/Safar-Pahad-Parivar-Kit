# Maps, GPS and terrain — Safar Pahad Parivar kit

## 1. Where the location data comes from
- **Your footage.** Phone photos (EXIF) and most phone videos carry GPS and the time. Files re-downloaded from Google
  Photos often lose GPS in videos (photos usually keep it). File names like `VID20260626111444` give the local time.
- **Google Maps Timeline** fills the gaps (the drive between shots). Export it from the phone:
  Google Maps → your profile picture → **Your Timeline** → ⋮ → **Location and privacy settings** → **Export Timeline data**
  → save `Timeline.json` into the trip folder. (Older Google Takeout `Records.json` / `Semantic Location History` also work.)
  Then re-index: `spp_gps.py index "<trip>" --timeline "<trip>\Timeline.json"` (it remembers it afterwards).

## 2. One-click in Resolve (Workspace → Scripts → Safar Pahad Parivar)
| Script | What it does |
|---|---|
| **Info Cards - Fill from GPS** | Every SPP Info Card whose *Place (Hindi)* is empty gets place (Hindi + English), altitude, date, time, weather icon and temperature for the shot underneath it. Clear *Place (Hindi)* to refresh a card. |
| **Route Map - Build from Timeline** | Makes a relief map + road-following route for the dates of the footage on this timeline, saves it in `<trip>\Route Maps\<timeline>\`, and loads it into any **SPP Route Map** title. |
The first run on a trip builds `_spp_gps_index.json` (≈1 min). Place names come from OpenStreetMap: where there is no
Hindi name you get the English one — type the Hindi yourself.

## 3. Route map
1. Put an **SPP Route Map** title on V3 (Effects → Titles → Safar Pahad Parivar), 10–20 s long.
2. Run **Route Map - Build from Timeline** (Resolve pauses 1–3 min the first time; map tiles are cached).
3. Missing a stop or a wrong name? Open `stops.csv` in that folder in Excel: fix names, add a row for any place GPS missed
   (a place name like `Dharchula` is enough, plus arrive/leave times), delete stops you don't want. Save → run again.
4. Inspector: title, when the drawing starts/ends, pause at each stop, *Follow the journey* camera + zoom,
   arrival/departure times, running date-time clock, keep earlier names, darken map.
- The path follows the **real roads** between your GPS points (OpenStreetMap routing). With a Timeline export the line is your exact track.
- A 9:16 timeline gets a portrait map automatically.
- Credit line (bottom right) is required by the map data licences — leave it on.
- `route.gpx` is saved next to it for the 3D apps below.

## 4. Rolling-dial numbers
Info Card and Altitude Counter numbers now roll like a mechanical counter: altitude counts up odometer-style, date/time/
temperature digits spin in and land. Turn off with **Rolling-dial numbers** in the Inspector.

## 5. Command line / API (optional)
```
$py = ".\Tools\.venv\Scripts\python.exe"
& $py Tools\spp_gps.py at    "<trip>" "2026-06-26 11:14"        # where were we? place, altitude, weather
& $py Tools\spp_gps.py file  "<trip>" VID20260626111444.mp4 --offset 12
& $py Tools\spp_gps.py stops "<trip>" --csv stops.csv
& $py Tools\spp_gps.py route "<trip>" "<out>" --from "2026-06-23" --to "2026-06-27" [--portrait] [--stops-file stops.csv] [--rivers]
& $py Tools\spp_gps.py gpx   "<trip>" trip.gpx
& $py Tools\spp_gps.py serve "<trip>"      # http://127.0.0.1:8777/at?t=2026-06-26T11:14  (JSON)
```

## 6. 3D terrain fly-overs (outside Resolve) — feed them `route.gpx`
| Tool | Good for | Cost / licence (check before use) |
|---|---|---|
| **AvoMap** (web) | 3D terrain fly-over of a GPX, 4K/60, your own logo | Pay per export, no subscription; commercial use allowed; Mapbox credit stays |
| **Travel Animator** (Android/iOS) | 2D/3D route with a vehicle, GPX import | Free HD; paid for 4K without watermark |
| **Mult.dev** (web + app) | Clean 2D route animations | Free 5 videos (low-res, watermark); one-time Pro packs; GPX/real roads need Pro; no 3D |
| **MapAnim** (web/app) | 2D/3D route + photos, GPX | Free tier, 4K export |
| **Blender + BlenderGIS** (PC) | Full-control 3D terrain from real elevation data | Free, steep learning curve |
| **Google Earth Studio** | Beautiful 3D camera moves | Free, but Google does **not** licence it for commercial use — avoid on a monetised channel |
Recommendation: SPP Route Map for the story map inside the edit (on-brand, editable, free); AvoMap for an occasional
hero 3D fly-over of Darma/Panchachuli from `route.gpx`.

Sources (checked Sept 2026, vendor sites — confirm current terms): mult.dev/articles/best-travel-map-animation-tools-in-2026,
travelanimator.com/hub/compare-travel-animator-and-mult-dev, avomap.com, mapanim.com/blog/best-travel-map-animation-apps-and-tools-2026,
google.com/earth/studio/faq.
