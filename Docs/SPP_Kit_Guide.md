# Safar Pahad Parivar — Kit User Guide

Everything in the kit, in the order you use it when making a video.
Menu scripts live in **Workspace → Scripts → Safar Pahad Parivar**; titles live in **Effects → Titles → Safar Pahad Parivar**.

![Menu scripts](guide_img/tag_menu.jpg)

**Contents**
0. [Where each tool runs — inside Resolve or outside](#0-where-each-tool-runs--inside-resolve-or-outside)
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
15c. [Background music](#15c-background-music)
15d. [Moment finder](#15d-moment-finder)
16. [Render (Deliver)](#16-render-deliver)
17. [Backup with git](#17-backup-with-git)
18. [Troubleshooting](#18-troubleshooting)

---

## 0. Where each tool runs — inside Resolve or outside
**Almost everything is used inside DaVinci Resolve.** Outside Resolve you only run a few PowerShell commands —
once per PC to install/build things, and at the start of each trip to make folders and sort footage — and you read
two text reports the moment finder writes.

### Inside Resolve — menu scripts (Workspace → Scripts → Safar Pahad Parivar → …)
| When | Menu script | What you select first | What it does |
|---|---|---|---|
| Once per PC | **Setup Render Presets** | — | adds the SPP YouTube 4K / 1080p / Shorts render presets |
| New video | **New Timeline - YouTube 16x9** / **Shorts 9x16** | — | named tracks (Main, B-Roll, GFX, Nat Sound, VO, Music, SFX, Subtitles) |
| New video | **Import Brand Graphics** | — | intro, end card, watermarks into a bin |
| New trip | **Moments - Analyse Trip** | trip footage in the project | finds laughter / kids / reactions + Hindi transcript (runs in the background) |
| Finding shots | **Moments - Add Markers** · **Best Moments Timeline** · **Search Transcript** | — | markers on clips · a selects timeline · a timeline of every clip where a word was said |
| Logging | **Tag Shot Type → 0–9** | timeline or media-pool clips | colour + keyword (Hero, Family talk, Scenery, Road, Drone, Timelapse, Kids, Stay/Food, Reject) |
| Titles | **Info Cards - Fill from GPS** | — (works on all empty SPP Info Cards) | place, altitude, date, time, weather from the GPS of the shot underneath |
| Titles | **Route Map - Build from Timeline** | an SPP Route Map clip on the timeline | real-road route, stops, times for the trip |
| Captions | **Captions - Sync Words to VO** | subtitles + a track named **VO** | word-by-word timing + stress into SPP Captions |
| Sound | **SFX - Import Library** · **Music - Import Library** | — | puts the libraries into the *SPP SFX* / *SPP Music* bins |
| Sound | **SFX - Auto Sound for Titles** | — | beat-timed sounds for every SPP title (Strings / Grand / Light / Mix) |
| Sound | **SFX - Land at Playhead** | one sound in the Media Pool | its hit / swell lands exactly on the playhead |
| Sound | **SFX - Loop Fill (In to Out)** | one `_LOOP_` sound in the Media Pool + In/Out | repeats it seamlessly for any length |
| Sound | **SFX - Remove Auto Sounds** | — | clears the Lime auto-sound clips |
| Music | **Music - Key Transition** | 1 or 2 music clips on the timeline | detects the keys, places a bridge / swell / tail on the cut |
| Voices | **Phone Voice - Selected Clips** | audio clips | phone / walkie-talkie voice |
| Voices / SFX | **Distance - Selected Clips** | audio clips | near / mid / far / very far / across the valley |
Titles (Info Card, Altitude Counter, Peak Callout, Pop-up Title, Credits, Captions, Route Map) are in **Effects → Titles → Safar Pahad Parivar**.
Script output and progress show in **Workspace → Console**.

### Outside Resolve — PowerShell in the kit folder (`F:\Video Editing\_Safar Pahad Parivar Kit`)
| When | Command | Time |
|---|---|---|
| New PC / after `git pull` of kit changes | `.\install.ps1` then restart Resolve | seconds |
| New PC (once) | `.\Tools\setup_word_timing.ps1` — installs all Python engines (speech, sound events, GPU) | 10–20 min |
| New PC (once) or when the guide says the library changed | `.\Tools\make_sfx.ps1` — builds `SFX\` (downloads the instruments + real recordings the first time) | 15–25 min first time, ~10 min later |
| New PC (once) or when the music changed | `.\Tools\make_music.ps1` (one track: `.\Tools\make_music.ps1 Pahadi`) | ~10 min |
| New trip / video | `.\Tools\new_video.ps1 -Trip "2026-10 Chopta Tungnath" -Video "01 Main Film"` | seconds |
| New trip | `python Tools\spp_sort_media.py "<trip>\Footage" --apply` (sort by orientation) | a minute |
| Only to fetch more real recordings | `Tools\.venv\Scripts\python.exe Tools\spp_freesound.py` (needs `Tools\freesound_key.txt`) | minutes |

### Outside Resolve — files you read
| File | What |
|---|---|
| `<trip>\_spp_moments\Moments.md` | 3 opening candidates, top 40 moments, day-by-day list (after *Moments - Analyse Trip*) |
| `<trip>\_spp_moments\Transcript.md` | everything said on the trip, clip by clip (Ctrl+F) |
| `<trip>\stops.csv` | route-map stops — edit names/times, then run *Route Map - Build from Timeline* again |
| `Docs\SFX_Library.md` · `Docs\Music_Library.md` | every sound / track, what it's for, length, key |
| `Docs\*.mp3` | demo reels: listen before choosing |

### Optional command-line tools (the menu scripts call these for you)
`spp_gps.py` (GPS lookup, stops, route, GPX, local API) · `spp_key.py` (find a song's key / make a transition) ·
`spp_distance.py` · `spp_phone_voice.py` · `spp_moments.py --search "बर्फ"` — all run with `Tools\.venv\Scripts\python.exe`.

### A video, start to finish
1. **PowerShell:** `new_video.ps1` → copy footage into `<trip>\Footage` → `spp_sort_media.py --apply`.
2. **Resolve:** new project → import footage → **New Timeline** → **Import Brand Graphics** → **Moments - Analyse Trip**.
3. Read `Moments.md`; **Moments - Add Markers** / **Best Moments Timeline**; **Tag Shot Type** while you watch.
4. Edit. Add SPP titles → **Info Cards - Fill from GPS**, **Route Map - Build from Timeline**.
5. Record the VO onto the **VO** track → subtitles → **Captions - Sync Words to VO**.
6. Music from *SPP Music* → **Music - Key Transition** where tracks change. **SFX - Auto Sound for Titles**, real sounds from
   folders 20–24 (use **Loop Fill** for beds, **Distance** for far-away sounds, **Land at Playhead** for risers).
7. Mix (VO recipe, §15) → render with an SPP preset → save to `<video>\Exports`.

## 1. One-time setup
Do this on a new or rebuilt PC (or after pulling kit changes).

| Step | What to do |
|---|---|
| 1 | Install DaVinci Resolve Studio, **Git + Git LFS**, **Python 3.13 from python.org** (not the Microsoft Store one), ffmpeg (`choco install ffmpeg`). An NVIDIA GPU is used for speech (captions, moments). |
| 2 | `git clone https://github.com/pushpenderpannu/Safar-Pahad-Parivar-Kit.git "F:\Video Editing\_Safar Pahad Parivar Kit"` then `git lfs pull` |
| 3 | PowerShell in the kit folder: `.\install.ps1` — copies menu scripts + titles into Resolve. |
| 4 | `.\Tools\setup_word_timing.ps1` — installs **all** Python engines: caption timing, GPS, route maps, sound, music, key finder, moment finder (incl. its 312 MB sound-event model; the 3 GB speech model downloads on first use). |
| 5 | Optional, for the real-world sounds: create a free key at freesound.org/apiv2/apply and save it as `Tools\freesound_key.txt` (git ignores it). Without it the SFX library is built without folders 20–24. |
| 6 | `.\Tools\make_sfx.ps1` — builds the sound-effects library (first time 15–25 min: downloads ~1.1 GB of CC0 instrument recordings and the real-world recordings). |
| 7 | `.\Tools\make_music.ps1` — builds the 12 background-music tracks (~10 min). |
| 8 | Restart Resolve, then once: **Setup Render Presets**, **SFX - Import Library**, **Music - Import Library** (menu scripts). |
Disk space: ~5 GB for the generated libraries and the instrument recordings (`SFX` 2 GB, `Music` 0.5 GB, `Source\_vsco` 2 GB, `Source\_cc0` 0.3 GB) — none of it is in git.

> After any kit update: `git pull` → `.\install.ps1` → restart Resolve. Re-run `make_sfx.ps1` / `make_music.ps1` only when the update changed the sounds or music (the commit message says so).

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
Import the footage, then run **Moments - Analyse Trip** once per trip (it works in the background — see §15d).

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
A brand sound library made for the SPP titles — **269 sounds, 846 files** (incl. real field recordings) in three styles plus cinematic risers, impacts and music transitions, several variations each, seamless loops for any length.
**Strings** (default): real recorded orchestra — violin, viola and cello sections, solo violin, harp, timpani, gong, Nepalese bells; warm
and emotional, all in D major so the sounds fit together. **Grand**: deep cinematic synth — sub-bass hits, taiko/dhol, braams, gongs,
ransingha-style horn with valley echo, drone beds. **Light**: playful UI ticks, pops and marimba.
Full list: [`SFX_Library.md`](SFX_Library.md). Listen first: `SPP_SFX_RealWorld_Demo.mp3`, `SPP_SFX_Strings_Demo.mp3`, `SPP_SFX_Cinematic_Demo.mp3`, `SPP_SFX_Grand_Demo.mp3`, `SPP_SFX_Demo_Reel.mp3`.

**Build it once per PC:** `.\Tools\make_sfx.ps1` → `<kit>\SFX\`. The first run downloads the recorded strings
(*VSCO-2 Community Edition*, public domain / CC0 — free for YouTube, no credit needed; ~1.1 GB into `Source\_vsco` incl. the music instruments, not in git) and takes ≈10 min;
later runs ≈3 min. Then **SFX - Import Library** puts it in an **SPP SFX** bin.
The sounds are built from code + those recordings, so they are identical on every PC and don't need backing up.

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
| 13 Strings Title Kits | strings versions of every title kit: harp + pizzicato Info Card, tremolo that climbs with the altitude count and lands on timpani + chord, harp-to-violin peak, 5 chapter-title hits, credits swell, route open, pizz + bell stop hits, spiccato journey loop, title-out |
| 14 Strings Hits & Swells | section swells, tremolo risers, string stabs, timpani hits and rolls, gong, bass drum, cymbal swells, solo-violin phrases (pahadi-style pentatonic) |
| 15 Strings Beds & Bells | 30 s string pads and cello drone loops, harp glissandos, Nepalese bells, pizzicato pops |
| 16 Cinematic Risers | **Riser_Epic** 3/5/8/12 s (tremolo strings, timpani + snare roll, cymbal → BIG HIT exactly at 3/5/8/12 s) · **Riser_Awe** 3/5/8/12 s (for waterfalls and big mountains: strings bloom, harp sweep, opens into a warm chord) · **Riser_Tension** 3/5/8 s (suspense, cuts to silence) |
| 17 Downers & Sub Drops | sub drops, boom + sub drop (with valley echo), downers (strings slide down, energy drains), power-down / tape-stop |
| 18 Impact Drums | big hits (taiko + timpani + bass drum + strings/crash/gong/boom), drum fills that run into a hit, soft hits, valley-echo hits |
| 19 Music Transitions | for **all 24 keys**: `Swell_Into_<key>` ×3 (strings+cymbal / +harp / soft — lands on the new music), `Tail_<key>` ×2 (covers an early music cut); `Bridge_<a>_to_<b>` between the SPP music keys (D, E, Bm, Dm) — any other pair is made on demand by **Music - Key Transition** |
| 20 Rain & Weather | REAL recordings: light / heavy rain, rain on roof / tin roof / the car (inside), forest rain, thunder, strong wind |
| 21 Car & Road | REAL: car doors open / close / handle / lock / boot, engine start, horn, pass-bys (dry and wet), wet-road traffic, tyres on gravel, footsteps on gravel |
| 22 Birds | REAL: cuckoo calls + morning beds, songbird whistles, crows, raven, pheasant, kite / buzzard, dawn chorus, Indian forest birds |
| 23 Water | REAL: close streams (one from Nepal), rivers, riverside with birds, waterfall close / distant, night river with crickets, drips, splashes |
| 24 Temple & Town | REAL: conch (shankh), temple bells, mountain horn, monastery chant, Indian crowd / town, wedding and street dhol |

**One click for all titles — SFX - Auto Sound for Titles.** Pick a style — **Strings** (default), **Grand**, **Light** or **Mix**
(grand for chapter titles, altitude, route map, intro/end; light for small cards). It finds every SPP title (and the SPP intro / end-card clips) on the timeline and
lays the matching sounds on the **SFX 1–3** tracks, exactly on the animation beats: card whoosh, row pops, odometer roll that slows with
the numbers, pin drop + chime at each route stop (times read from the route file), dotted-trail loop while the path draws, out-whoosh.
Variations rotate so repeats never sound the same. Auto clips are **Lime**; run again after editing — it replaces the old Lime clips.
Keep a tweaked sound by changing its clip colour. **SFX - Remove Auto Sounds** clears them.

**Land it on the cut — SFX - Land at Playhead.** Put the playhead on the reveal / title / first beat of the next track, select a sound
in the Media Pool (a riser, `Swell_Into_*`, `Bridge_*`, drum fill…) and run it: the sound is placed so its big moment lands exactly
on the playhead (a `Riser_Epic_8s` starts 8 s earlier). Every sound's landing time is stored in the library.

**Changing music — Music - Key Transition.** Select the two music clips on the timeline (the one ending and the one starting)
and run it. It listens to the end of the first and the start of the second, shows their keys (e.g. *D → E*, with the runner-up —
relative keys like D / Bm share their notes, either works), lets you change them, then places a **Bridge** (old key → new key),
a **Swell into** the new key, or **Tail + Swell** on a free SFX track so its big moment lands exactly on the first frame of the new music.
One clip selected: swell into it, or tail at its end. Works on any music (Epidemic Sound too). Command line:
`Tools\spp_key.py <file> --start 60 --dur 20` (find a key) · `Tools\spp_key.py render bridge Ab Em --out x.wav` (make a transition).

**Near or far — Distance - Selected Clips.** You don't need separate near/far files. Select audio clip(s) on the timeline, run it, pick
*Near (~10 m) · Mid (~50 m) · Far (~200 m) · Very far (~600 m) · Across the valley (echoes)*. It makes a processed copy on a free track and
switches the original off (D to switch back). What it does — and what you'd do by hand in Fairlight: cut the treble (air absorbs it:
high-cut ~8 kHz at 50 m, ~4 kHz at 200 m), cut the low bass (no proximity), lower the level, add more reverb than direct sound (reverb
send, longer decay), narrow the stereo (a far sound is a point), and for valleys add 2–4 darker echoes 0.4–2 s apart. Tick *Keep the
loudness* if you'd rather set the level with the fader. Loops stay seamless. Command line: `Tools\spp_distance.py <file> --preset far`.

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

## 15c. Background music
Twelve original background tracks (2–3 min each) composed in code and played with recorded instruments — real strings, flute,
upright piano, harp, glockenspiel, timpani, gong and Nepalese bells (VSCO-2 Community Edition, CC0) — plus a synthesised
tanpura, temple bells, manjira and mountain wind. Listen first: `Docs\SPP_Music_Preview.mp3` (32 s of each). Full list: [`Music_Library.md`](Music_Library.md).

| Theme | Tracks |
|---|---|
| 01 Slow Build | **First Light** (piano → full strings, sunrise/openings) · **Long Road Up** (driving ostinato, drives/climbs) · **Summit Rise** (slow epic rise, peaks/reveals) |
| 02 Temple Bells | **Mandir Dawn** (tanpura, bells, low bansuri) · **Aarti Glow** (manjira, hand bells, devotional tune) · **Himalayan Gongs** (no rhythm: gongs, bowls, drone) |
| 03 Wind | **High Pass** (wind + airy strings) · **Prayer Flags** (fluttering harp/glock + bright flute) · **Snowline** (cold wind, lonely viola) |
| 04 Flute | **Bansuri Valley** (alaap then Bhupali tune) · **Pahadi Dhun** (6/8 folk tune) · **Evening Raag** (Raag Yaman, sunsets) |

**Build it once per PC:** `.\Tools\make_music.ps1` (≈10–15 min; uses the same instrument download as the sound effects) → `<kit>\Music\`.
Then **Music - Import Library** puts the tracks in an **SPP Music** bin (Purple clips). Rebuild one track: `.\Tools\make_music.ps1 Pahadi`.

**Using it:** put music on the *Music* track, duck it under the VO (−18 to −24 dB while the voice talks, −10 to −12 dB alone).
Tracks start soft and end on a proper final chord / bell, so you can cut from the middle and let the ending ring out.

**Rights:** everything is original (our code) or public domain (CC0 recordings), so it is free to use on monetised YouTube with no
credit needed. Don't register these tracks with a Content-ID service — that could cause claims on your own videos.
(The upright-piano recordings are by Simon Dalzell / Ivy Audio via Versilian Studios; credit is welcome, not required.)

## 15d. Moment finder
Finds the family moments in a whole trip's footage — laughter, kids shouting or cheering, singing, "wow / papa dekho" reactions,
names being called (Pihu, Oju, Meenakshi, Brijesh, Alka, Pushpender) — and writes a Hindi transcript of everything that was said.
1. **Moments - Analyse Trip** (runs in the background; a 2-hour trip takes ~20–40 min the first time, later only new clips).
2. Read `<trip>\_spp_moments\Moments.md`: **3 opening candidates** for the cold open, the top 40 moments, and a day-by-day list.
   `Transcript.md` has every sentence with clip name and time (Ctrl+F for पानी, बर्फ, पिहू…).
3. **Moments - Add Markers**: coloured markers on the source clips — Yellow laughter, Pink kids talking, Red shouts, Fuchsia cheering,
   Purple singing, Green reaction words (the marker note holds what was said).
4. **Moments - Best Moments Timeline**: a new timeline of the top 20 / 40 / 80 moments, only laughter, only kids, or the 3 openers, in the order they happened.
5. **Moments - Search Transcript**: type words (comma-separated) → a timeline of every clip where they were said.
Engines: faster-whisper large-v3 (speech, on the GPU) and PANNs (AudioSet sound events). Automatic Hindi transcripts have mistakes — use them to *find*, not to quote.

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
| Resolve froze while a script ran | Normal for caption sync / route map / key detection — wait; the Console (Workspace → Console) shows progress. |
| "Couldn't find the trip folder" (Moments) | Import some of the trip's footage (from `<trip>\Footage`) into the project first. |
| Moments: only speech, no laughter / cheering | The sound-event model isn't downloaded — run `.\Tools\setup_word_timing.ps1` again, then **Moments - Analyse Trip** (it only adds what's missing). |
| Moment analysis is very slow | It fell back to the CPU — check `<trip>\_spp_moments\analyse_log.txt` for "GPU not available"; re-run `setup_word_timing.ps1`. |
| Key Transition picked the wrong key | Change it in the window before placing. Relative keys (D / Bm) share notes — either sounds right. |
| No folders 20–24 in the SFX library | `Tools\freesound_key.txt` missing when `make_sfx.ps1` ran — add the key and run it again. |
| A sound is missing in the bin after a rebuild | Run **SFX - Import Library** / **Music - Import Library** again (only new files are added). |
