# Safar Pahad Parivar — Kit User Guide

Everything in the kit, in the order you use it when making a video.
Menu scripts live in **Workspace → Scripts → Safar Pahad Parivar**; titles live in **Effects → Titles → Safar Pahad Parivar**.

![Menu scripts](guide_img/tag_menu.jpg)

**Contents**
1. [One-time setup](#1-one-time-setup)
2. [Start a new trip / video](#2-start-a-new-trip--video)
3. [New timeline](#3-new-timeline)
4. [Tag shot types (colours)](#4-tag-shot-types-colours)
5. [Brand graphics: intro, end card, watermark](#5-brand-graphics-intro-end-card-watermark)
6. [Titles — how they work](#6-titles--how-they-work)
7. [Info Card (+ fill from GPS)](#7-info-card--fill-from-gps)
8. [Altitude Counter](#8-altitude-counter)
9. [Peak Callout](#9-peak-callout)
10. [Pop-up Title](#10-pop-up-title)
11. [Credits](#11-credits)
12. [Hindi captions (+ sync to VO)](#12-hindi-captions--sync-to-vo)
13. [Route Map](#13-route-map)
14. [GPS lookup tool](#14-gps-lookup-tool)
15. [VO sound recipe](#15-vo-sound-recipe)
15a. [Sound effects](#15a-sound-effects)
15b. [Phone-call voice](#15b-phone-call-voice)
16. [Render (Deliver)](#16-render-deliver)
17. [Backup with git](#17-backup-with-git)
18. [Troubleshooting](#18-troubleshooting)

---

## 1. One-time setup
Do this on a new or rebuilt PC (or after pulling kit changes).

| Step | What to do |
|---|---|
| 1 | Install DaVinci Resolve Studio, **Git + Git LFS**, **Python 3.13 from python.org** (not the Microsoft Store one), ffmpeg (`choco install ffmpeg`). |
| 2 | `git clone https://github.com/pushpenderpannu/Safar-Pahad-Parivar-Kit.git "F:\Video Editing\_Safar Pahad Parivar Kit"` then `git lfs pull` |
| 3 | PowerShell in the kit folder: `.\install.ps1` — copies menu scripts + titles into Resolve. |
| 4 | `.\Tools\setup_word_timing.ps1` — installs the Python tools (caption timing, GPS, route maps, sound). First caption sync downloads a 3 GB speech model. |
| 4b | `.\Tools\make_sfx.ps1` — builds the sound-effects library (≈1 min). |
| 5 | Restart Resolve, then once: **Setup Render Presets** (menu script). |

> After any kit update: `git pull` → `.\install.ps1` → restart Resolve.

## 2. Start a new trip / video
One folder per **trip** (footage stored once), one sub-folder + one Resolve project per **video**.
```
.\Tools\new_video.ps1 -Trip "2026-10 Chopta Tungnath" -Video "01 Main Film"
```
Copy the camera/phone files into `<trip>\Footage`, then sort them by real orientation:
```
python Tools\spp_sort_media.py "<trip>\Footage"           # dry run - shows the plan
python Tools\spp_sort_media.py "<trip>\Footage" --apply   # -> Horizontal / Vertical / Square / Photos
python Tools\spp_sort_media.py --undo "<trip>\Footage\_spp_sort_log_<date>.csv"
```
In Resolve: new project → *Project Settings → Master Settings → Working Folders → Project media location* = `<video>\Resolve Media`.

## 3. New timeline
**New Timeline - YouTube 16x9** (3840×2160, scale-to-fit) or **New Timeline - Shorts 9x16** (1080×1920, scale-to-crop).
Every timeline gets the same named tracks:

| Track | Name | Use |
|---|---|---|
| V1 | Main (A-Roll) | main story clips |
| V2 | B-Roll / Overlay | cutaways |
| V3 | GFX / Info Cards | SPP titles, map, watermark |
| A1 | Nat Sound / Dialogue | clips' own sound, family talk |
| A2 | **VO** | your voice-over (the caption sync looks for this name) |
| A3–A5 | Music 1–3 | music beds / cross-fades |
| A6–A8 | SFX 1–3 | whooshes, ambience |
| ST1 | Subtitles | Hindi subtitles (source for captions + YouTube CC) |

## 4. Tag shot types (colours)
Select clips (timeline or media pool) → **Tag Shot Type → 1…9**. Sets the clip colour **and** a keyword, so you can make
Smart Bins like *Keywords contains "Hero Shot"*. **0 Clear Tag** removes it.

![Shot colours](guide_img/shot_colours.png)

## 5. Brand graphics: intro, end card, watermark
**Import Brand Graphics** puts them in an **SPP Graphics** bin:

![SPP Graphics bin](guide_img/media_pool_graphics.jpg)

| Intro (5 s, transparent) | End card (15 s) — drop the next-video / suggested-video end screens on the two boxes in YouTube Studio |
|---|---|
| ![Intro](guide_img/intro.jpg) | ![End card](guide_img/endcard.jpg) |

Watermark: `SPP_Watermark_16x9_4K.png` (or `_Shorts_9x16`) on the top video track for the whole film, opacity ~70 %.
Brand board (colours, fonts, logo): [`Brand/brand_board.png`](../Brand/brand_board.png).

## 6. Titles — how they work
![Titles panel](guide_img/titles_panel.jpg)

- Drag a title onto **V3**, stretch it as long as you want it on screen. Select it → **Inspector → Video → Title** shows its settings.
- Text fields accept Hindi directly. Numbers are sliders/boxes; tick-boxes switch parts on/off.
- **Choice fields are typed words** (Resolve 21 shows them as text boxes). The field name lists the choices, e.g.
  *Position: bottom-left / bottom-right / top-left / top-right* → type `top-right` (just `top-r` or the number `3` also works).
- **Animate Out At (s, 0 = end)** — when the title leaves; 0 = at its end.
- **Accent Colour** — defaults to brand gold `#F4B03E`.
- Works in 16:9 and 9:16 timelines (layouts adapt automatically).

![Inspector](guide_img/inspector.png)

## 7. Info Card (+ fill from GPS)
Place · date · time · altitude · weather · temperature. Each item can be hidden.

![Info Card](guide_img/info_card.jpg)

| Setting | Notes |
|---|---|
| Place (Hindi) / Place (English) | English line looks best in CAPS with ` · STATE` |
| Show Altitude, Altitude (m), Count Altitude Up | counts up from 0 like an odometer |
| Show Date / Date, Show Time / Time | type as you want it shown: `26 जून 2026`, `09:58 AM` |
| Weather | `none / sun / part-cloud / cloud / rain / snow / fog / night` |
| Temperature | e.g. `14°C` (blank = hidden) |
| Position, Size | corner + scale |
| Rolling-dial numbers | digits spin like a dial (see below); untick for plain numbers |

**Automatic fill:** put Info Cards over your shots, then run **Info Cards - Fill from GPS**. Every card whose
*Place (Hindi)* is **empty** is filled from the shot underneath: place (Hindi + English), altitude, date, time, weather, temperature.
To refill a card, clear its *Place (Hindi)* and run again. Check Hindi spellings — where OpenStreetMap has no Hindi name you get the English one.

**Rolling-dial numbers** (Info Card + Altitude Counter):

![Rolling numbers](guide_img/rolling_numbers.jpg)

## 8. Altitude Counter
Big counter from *Start* to *End* altitude over *Count Duration*, with a small mountain profile.

![Altitude Counter](guide_img/altitude_counter.jpg)

Tip: use it when the drive climbs (e.g. Dharchula 915 m → Dugtu 3,200 m). Position `centre` + Size 1.4 for a full-screen moment.

## 9. Peak Callout
Names a mountain in the shot with a dot-and-line or an arrow.

![Peak Callout](guide_img/peak_callout.jpg)

- **Peak X / Peak Y** — where the summit is, in % of the frame (0,0 = top-left). Scrub to a still frame, estimate, adjust.
- **Label Offset X / Y** — where the label sits relative to the peak (negative = left / up).
- **Marker** — `dot` or `arrow`. **Show Height / Height (m)** — e.g. 6,904 m for Panchachuli II.
- If the camera moves, keyframe nothing — just keep the callout short (3–4 s) on a steady shot.

## 10. Pop-up Title
Chapter / place title: small kicker, big Hindi headline, English line.

![Pop-up Title](guide_img/popup_title.jpg)

*Darken Background* adds a soft vignette so the text reads over bright snow.

## 11. Credits
Heading + up to 7 lines written `Role | Name` (blank lines are hidden), logo and handle.

![Credits](guide_img/credits.jpg)

## 12. Hindi captions (+ sync to VO)
Resolve's own *animated* subtitles break Hindi (matras/conjuncts come apart). **SPP Captions** animates whole words, so Hindi always shapes correctly.

| Word pop + gold highlight (`pop`) | Karaoke sweep (`karaoke`) | Shorts (`raised`) |
|---|---|---|
| ![pop](guide_img/captions_pop.jpg) | ![karaoke](guide_img/captions_karaoke.jpg) | ![shorts](guide_img/captions_shorts.jpg) |

**Recommended — synced to your voice (one click):**
1. Subtitles on the subtitle track (type them, or *Timeline → Create Subtitles from Audio* and correct the text).
   Put `*stars*` around a word to force a stress: `ये नज़ारा *बेमिसाल* था` (stars never show).
2. VO clips on the audio track named **VO**.
3. One **SPP Captions** title on V3 over the VO section.
4. Run **Captions - Sync Words to VO**. Resolve pauses (~1 min per 10 min of VO). It finds when every word is spoken,
   trims silences, marks stressed words (louder/stretched → bigger, gold) and fills the caption clip (text + start time).
5. **Turn the subtitle track off** (its eye/enable button) so captions aren't shown twice. Keep it — export it as SRT for YouTube CC
   (*File → Export → Subtitle*).

Changed the subtitles or re-cut the VO? Run the sync again.

**Manual (no sync):** *File → Export → Subtitle → SRT*, open it in Notepad, copy all, paste into **SRT text**, and set
**This clip starts at timeline time (s)** (clip at 00:02:15 → `135`). Words then spread evenly across each line.

Settings: **Animation** `pop / karaoke / fade`, **Position** `bottom / raised / centre / top`, Size, Dark plate, Text + Highlight colour.

## 13. Route Map
Relief map in brand colours, dotted path along the **real roads**, stops pop up with arrival/departure times, a running date-time clock, camera following the journey.

![Route map in Resolve](guide_img/route_in_resolve.jpg)

| Follow camera (mid-journey) | Whole route (end) |
|---|---|
| ![follow](guide_img/route_follow.jpg) | ![whole](guide_img/route_whole.jpg) |

1. Put an **SPP Route Map** title on V3, 12–20 s.
2. Run **Route Map - Build from Timeline**. It uses only the dates of the footage on this timeline, builds the map
   (1–3 min first time) into `<trip>\Route Maps\<timeline name>\` and loads it into the title.
3. **Fix / add stops:** open `stops.csv` in that folder (Excel). Columns: *hindi, english, place, arrive, leave*.
   Fix names, delete rows, or add a stop GPS missed — the place can be a name (`Dharchula`) or `lat, lon`; times as `2026-06-23 18:00`. Save → run the script again.
4. Inspector: *Title*, *Route starts drawing at / finished at*, *Pause at each stop*, *Camera* `whole / follow`, *Follow zoom*,
   times on/off, running clock on/off, keep earlier names, darken map.
- A Shorts (9:16) timeline gets a portrait map automatically.
- Keep the credit line (bottom-right) — the map data licences require it.
- `route.gpx` in the same folder can be loaded into 3D fly-over apps (see `Docs\Maps_GPS_and_Terrain.md`).

**Better paths:** export your Google Maps Timeline (phone: Maps → profile → Your Timeline → ⋮ → Location & privacy settings →
Export Timeline data) and save `Timeline.json` in the trip folder, then:
`.\Tools\.venv\Scripts\python.exe Tools\spp_gps.py index "<trip>" --timeline "<trip>\Timeline.json"`.

## 14. GPS lookup tool
The menu scripts above use it; you can also ask it directly (PowerShell in the kit folder):
```
$py = ".\Tools\.venv\Scripts\python.exe"
& $py Tools\spp_gps.py at    "<trip>" "2026-06-26 11:14"          # where were we? place, altitude, weather
& $py Tools\spp_gps.py file  "<trip>" VID20260626111444.mp4 --offset 12
& $py Tools\spp_gps.py stops "<trip>" --csv stops.csv
& $py Tools\spp_gps.py gpx   "<trip>" trip.gpx
& $py Tools\spp_gps.py serve "<trip>"     # http://127.0.0.1:8777/at?t=2026-06-26T11:14  (JSON)
```
Example answer: `Sela · 2,378 m · 22°C · drizzle`. Full details: [`Maps_GPS_and_Terrain.md`](Maps_GPS_and_Terrain.md).

## 15. VO sound recipe
On the **VO** track (Fairlight): Voice Isolation 60–70 → EQ (high-pass 80 Hz, small cut 250–350 Hz, lift 3–5 kHz) →
De-esser → Dialogue Leveler / compressor 3:1 → final mix **−14 LUFS**, music 15–20 dB under the voice.

## 15a. Sound effects
A brand sound library made for the SPP titles — **111 sounds, 364 files** in two styles, several variations each, seamless loops for any length.
**Grand** (default): deep and cinematic like the mountains — sub-bass hits, taiko/dhol, low brass braams, gongs, deep mandir bell,
singing bowl, a ransingha-style horn with valley echo, drone beds. **Light**: playful UI ticks, pops and marimba.
Full list: [`SFX_Library.md`](SFX_Library.md). Listen first: `SPP_SFX_Grand_Demo.mp3` and `SPP_SFX_Demo_Reel.mp3`.

**Build it once per PC:** `.\Tools\make_sfx.ps1` (≈1 min) → `<kit>\SFX\`. Then **SFX - Import Library** puts it in an **SPP SFX** bin.
The sounds are generated from code, so they are identical on every PC and don't need backing up.

| Folder | What's in it |
|---|---|
| 01 Title Kits | sounds timed to each SPP title (Info Card, Altitude 1.5–6 s, Peak, Pop-up, Credits, Route Map, title-out, caption tick) |
| 02 UI | pops, soft ticks, mouse click, notification bell, arrival chimes, shimmer, swipes |
| 03 Motion | whooshes (short/medium/long, in/out), swish pans, risers 2/4/6 s, reverse swell, soft impact, cinematic boom |
| 04 Dial & Mechanics | dial ticks, **odometer rolls 1–6 s** (slow down and settle like the rolling numbers), digit spin-stop, **gear loop**, clock tick-tock loop, time-lapse clock loop, ratchet |
| 05 Map & Travel | map unfold/fold, pencil-drawing loop, dotted-trail loop, pin drop, map zoom in/out, travel-motion loop, camera shutter |
| 06 Bells & Brand | mandir bell, hand ghanti, wind chime, **intro sting** and **end-card sting** timed to the SPP intro / end card |
| 07 Nature Beds | 30 s seamless: mountain wind (calm/gusty/high whistle), prayer flags, mountain stream, light rain, night crickets |
| 08 Phone | Indian ringback / dial / busy tones, ringtones, vibrate, keypad dialing, pickup, hang-up, call-ended beeps, message ping, line noise |
| 09 Grand Title Kits | grand versions of every title kit (Info Card, Altitude 1.5–6 s with 3 landings, Peak, 5 chapter-title hits, Credits, Route open, stop hits, journey pulse loop, title-out) |
| 10 Grand Impacts & Swells | braams, taiko hits, sub booms, valley-echo boom, deep whooshes, riser-into-hit, deep reverse swells |
| 11 Grand Bells & Horns | gong / tam-tam, deep mandir bell, singing bowl, ransingha horn calls with valley echo |
| 12 Grand Drones & Drums | 30 s drone beds (warm, hopeful, dark, airy), dhol-damau pulse loops, heavy gears, vast mountain air |

**One click for all titles — SFX - Auto Sound for Titles.** Pick a style — **Grand** (default), **Light** or **Mix**
(grand for chapter titles, altitude, route map, intro/end; light for small cards). It finds every SPP title (and the SPP intro / end-card clips) on the timeline and
lays the matching sounds on the **SFX 1–3** tracks, exactly on the animation beats: card whoosh, row pops, odometer roll that slows with
the numbers, pin drop + chime at each route stop (times read from the route file), dotted-trail loop while the path draws, out-whoosh.
Variations rotate so repeats never sound the same. Auto clips are **Lime**; run again after editing — it replaces the old Lime clips.
Keep a tweaked sound by changing its clip colour. **SFX - Remove Auto Sounds** clears them.

**Any length — SFX - Loop Fill (In to Out).** Select one `_LOOP_` sound in the media pool, set In/Out on the timeline (I / O), run it:
the loop is laid end-to-end with seamless joins (last copy trimmed). Great for wind, stream, gear, clock, dotted trail.

Mixing tips: title sounds sit around −6 dB under the VO already; ride the SFX tracks down (−6 to −12 dB) when the voice is on.
Beds (wind, stream) at −18 to −24 dB under dialogue.

## 15b. Phone-call voice
Select one or more **audio** clips (a VO line, or someone's dialogue) → **Phone Voice - Selected Clips** → choose a style
(`mobile`, `landline`, `speaker`, `walkie`, optional line hiss / tiny network glitches). A processed copy is placed at exactly the same spot on a free
audio track and the original clip is switched off (select it and press **D** to switch it back on).
Add the phone sounds around it: `SPP_Ringtone` / `SPP_Vibrate` → `SPP_Pickup` → *(phone voice)* → `SPP_Hangup` + `SPP_Call_Ended_Beeps`;
for the caller's side, `SPP_Keypad_Dialing` → `SPP_Ringback_India`.

Command line (any audio/video file): `& $py Tools\spp_phone_voice.py "<file>" --style mobile --noise`

**Live alternative inside Resolve (Fairlight, adjustable):** on a track holding only the phone lines add
**EQ**: high-pass 300 Hz (steep), low-pass 3.4 kHz (steep), bell +4 dB at 1.8 kHz → **Dynamics**: compressor 4:1, threshold ≈ −25 dB →
optional **Distortion** (small amount) for a cheap handset. Speakerphone: add a short small-room **Reverb**.

## 16. Render (Deliver)
Pick a preset: **SPP YouTube 4K**, **SPP YouTube 1080p**, **SPP Shorts 9x16**.

![Render presets](guide_img/render_presets.jpg)

Save the final file into `<video>\Exports`. Then *File → Export Project* (.drp) into `<video>\Resolve`.

## 17. Backup with git
- The kit is in git (GitHub, private). After changes: `git add -A`, `git commit -m "…"`, `git push`.
- Footage is **not** in git — back up `F:\Video Editing\Projects` to an external drive / cloud.
- Keep music/SFX used in a video inside its `Audio` folder.

## 18. Troubleshooting
| Problem | Fix |
|---|---|
| New titles/scripts don't appear | Run `.\install.ps1`, restart Resolve. |
| Title shows old settings after a kit update | Delete the clip and drag a fresh one from Effects. |
| Captions show twice | Turn off the subtitle track. |
| Hindi letters broken in captions | You used Resolve's animated subtitles — use SPP Captions. |
| "Word-timing engine not installed" | `.\Tools\setup_word_timing.ps1` |
| Route map shows "Choose route.json" | Run **Route Map - Build from Timeline**, or pick `route.json` in the Inspector. |
| Route has few stops / straight lines | Add stops in `stops.csv`; add a Google Timeline export. |
| Info Card not filled | Its *Place (Hindi)* wasn't empty, or the shot has no GPS near that time (add Timeline export). |
| "The SFX library isn't built yet" | `.\Tools\make_sfx.ps1`, then **SFX - Import Library**. |
| Auto sounds in the wrong place | Titles moved after running it — just run **SFX - Auto Sound for Titles** again. |
| Resolve froze while a script ran | Normal for caption sync / route map — wait; the Console (Workspace → Console) shows progress. |
