# Menu scripts — one section per command

Every command in **Workspace → Scripts → Safar Pahad Parivar**, with what you need first, how to run it, exactly what
changes in Resolve afterwards, how to redo / undo it, and what to do if it doesn't work.
(Short overview: `SPP_Kit_Guide.md` §0. Titles are in **Effects → Titles → Safar Pahad Parivar**.)

**Contents**
- [A. Before any script — a new project the right way](#a-before-any-script--a-new-project-the-right-way)
- [B. Running a script and reading its messages](#b-running-a-script-and-reading-its-messages)
- Project setup: [Setup Render Presets](#setup-render-presets) · [New Timeline - YouTube 16x9](#new-timeline---youtube-16x9) ·
  [New Timeline - Shorts 9x16](#new-timeline---shorts-9x16) · [Import Brand Graphics](#import-brand-graphics) ·
  [SFX - Import Library](#sfx---import-library) · [Music - Import Library](#music---import-library)
- Logging footage: [Tag Shot Type 0–9](#tag-shot-type-09) · [Moments - Analyse Trip](#moments---analyse-trip) ·
  [Moments - Add Markers](#moments---add-markers) · [Moments - Best Moments Timeline](#moments---best-moments-timeline) ·
  [Moments - Search Transcript](#moments---search-transcript)
- Titles & GPS: [Info Cards - Fill from GPS](#info-cards---fill-from-gps) · [Route Map - Build from Timeline](#route-map---build-from-timeline)
- Captions: [Captions - Sync Words to VO](#captions---sync-words-to-vo)
- Sound: [SFX - Auto Sound for Titles](#sfx---auto-sound-for-titles) · [SFX - Remove Auto Sounds](#sfx---remove-auto-sounds) ·
  [SFX - Land at Playhead](#sfx---land-at-playhead) · [SFX - Loop Fill (In to Out)](#sfx---loop-fill-in-to-out) ·
  [Music - Key Transition](#music---key-transition) · [Distance - Selected Clips](#distance---selected-clips) ·
  [Phone Voice - Selected Clips](#phone-voice---selected-clips)

---

## A. Before any script — a new project the right way
The kit is **already inside Resolve** (the menu scripts and the SPP titles were copied in by `install.ps1`).
**Do not import the kit folder into the Media Pool** — that only adds hundreds of files (tools, docs, sources) you never
use. The scripts bring in exactly what's needed (graphics, sounds, music) into their own bins.

1. **Project Manager → New Project**, named after the video (e.g. *Chopta 01 Main Film*).
2. *File → Project Settings → Master Settings → Working Folders → Project media location* = `<video>\Resolve Media`.
3. **Media Pool → Import Media** → the trip's footage: `<trip>\Footage\Horizontal` (and `Vertical` for Shorts).
   The footage must stay inside `<trip>\Footage` — GPS, route map and moments find the trip from that path.
4. Run, in this order: **New Timeline - YouTube 16x9** (or Shorts) → **Import Brand Graphics** → **SFX - Import Library** →
   **Music - Import Library** → **Moments - Analyse Trip**. (Once per PC: **Setup Render Presets**.)
5. Your Media Pool then looks like:
   ```
   Master
   ├─ (your footage)
   ├─ SPP Graphics      intro, end card, watermarks
   ├─ SPP SFX           01 Title Kits … 24 Temple & Town   (one sub-bin per category)
   ├─ SPP Music         01 Slow Build · 02 Temple Bells · 03 Wind · 04 Flute
   └─ SPP Moments Footage / SPP Distance / SPP Phone Voice   (appear later, when those scripts need them)
   ```
**Already imported the kit folder?** In the Media Pool right-click the *_Safar Pahad Parivar Kit* bin → **Remove Bin**
(the files stay on disk — Resolve only forgets them), then do step 4.

## B. Running a script and reading its messages
- Menu: **Workspace → Scripts → Safar Pahad Parivar → (script)**. Tag scripts are in the **Tag Shot Type** sub-menu.
- Messages ("Imported 846 new sounds…", "Filled 3 Info Card(s)…", errors) appear in **Workspace → Console** — open it the
  first few times; every section below lists the message you should see.
- Some scripts show a small window first (style / preset / how many). Some make Resolve **pause** while they work
  (captions, route map, key detection) — wait, it comes back.
- Scripts never delete your footage. The only things they remove are their own earlier results (noted per script).
- Not in the menu? Run `.\install.ps1` in the kit folder and restart Resolve.

---

# Project setup

## Setup Render Presets
**Use it for:** the three SPP render presets. **Once per PC** (presets are saved in your Resolve user settings, for all projects).
**Before:** any project open.
**How:** run it.
**You'll see:** Console: `Saved SPP YouTube 4K`, `Saved SPP YouTube 1080p`, `Saved SPP Shorts 9x16`.
On the **Deliver** page the presets appear in the preset row at the top (built on Resolve's YouTube 2160p / 1080p and
TikTok 1080p presets; Shorts is 1080×1920).
**Again / undo:** running again refreshes them. Delete a preset: Deliver page → right-click it → Delete.
**Problems:** `Base preset missing` → update Resolve (its built-in YouTube/TikTok presets are needed).

## New Timeline - YouTube 16x9
**Use it for:** every main video — a timeline with the kit's standard tracks.
**Before:** a project open (footage imported is fine but not needed).
**How:** run it.
**You'll see:**
- A new timeline **SPP YouTube 16x9 - 2026-10-02 1930** (date/time of creation) in the Media Pool, opened on the Edit page.
- Settings (its own, independent of the project): **3840×2160, 30 fps, scale to fit**.
- Tracks, already named:

  | Track | Name | Put here | Scripts that rely on the name |
  |---|---|---|---|
  | V1 | Main (A-Roll) | story clips | — |
  | V2 | B-Roll / Overlay | cutaways | — |
  | V3 | GFX / Info Cards | SPP titles, map, watermark | — |
  | A1 | Nat Sound / Dialogue | clips' own sound | — |
  | A2 | **VO** | your voice-over | *Captions - Sync Words to VO* looks for **VO** |
  | A3–A5 | Music 1–3 | music | — |
  | A6–A8 | **SFX 1–3** | sound effects | all *SFX* scripts put sounds on tracks named **SFX…** |
  | ST1 | Subtitles | Hindi subtitles | *Captions - Sync Words to VO* reads it |
- Console: `Created SPP YouTube 16x9 - …`.
**Again / undo:** each run makes another timeline. Delete one: Media Pool → right-click it → Delete Timelines. Rename freely,
but keep the track names **VO** and **SFX …**.
**Problems:** `Could not create timeline` → a project must be open (not the Project Manager).

## New Timeline - Shorts 9x16
Same as above but **1080×1920, 30 fps, scale to crop** (fills the vertical frame), named *SPP Shorts 9x16 - …*.
Use vertical footage from `<trip>\Footage\Vertical`. Route maps made on this timeline come out in portrait automatically.

## Import Brand Graphics
**Use it for:** the SPP intro (5 s), end card (15 s) and watermarks (16x9 and Shorts), 4K with transparency.
**Before:** a project open.
**How:** run it.
**You'll see:** a bin **SPP Graphics** with the `.mov` / `.png` files from the kit's `Graphics` folder.
Console: `Imported 4 new graphics from …\Graphics into 'SPP Graphics'`.
Then: intro at the start of V1 (or V3 over footage), end card at the end, watermark on V3 across the whole video.
**Again / undo:** running again adds only files not already in the bin. Undo: delete the bin (files stay on disk).

## SFX - Import Library
**Use it for:** putting the whole sound library into the project so you can browse and drag sounds.
**Before:** the library is built on this PC (`.\Tools\make_sfx.ps1`, once). A project open.
**How:** run it (≈1 minute the first time in a project).
**You'll see:** bin **SPP SFX** with a sub-bin per category — *01 Title Kits … 19 Music Transitions, 20 Rain & Weather,
21 Car & Road, 22 Birds, 23 Water, 24 Temple & Town*. Console: `Imported 846 new sounds into the 'SPP SFX' bin (846 in the library).`
File names tell you what they are: `SPP_Rain_Heavy_LOOP_30s_v02` = loopable 30 s bed, variation 2. Descriptions: `Docs\SFX_Library.md`.
**Again / undo:** after a library rebuild, run again — only new files are added. Undo: delete the bin.
**Problems:** `The SFX library isn't built yet` → run `.\Tools\make_sfx.ps1`. Tip: the other SFX scripts import what
they need themselves, so this is only for browsing.

## Music - Import Library
**Use it for:** the 12 SPP background-music tracks.
**Before:** `.\Tools\make_music.ps1` built them (once per PC). A project open.
**How:** run it.
**You'll see:** bin **SPP Music** with sub-bins *01 Slow Build, 02 Temple Bells, 03 Wind, 04 Flute*; the clips are **Purple**.
Console lists every track with length and mood. Keys and uses: `Docs\Music_Library.md`.
**Again / undo:** again → only new tracks. Undo: delete the bin.
**Problems:** `The music library isn't built yet` → `.\Tools\make_music.ps1`.

---

# Logging footage

## Tag Shot Type 0–9
**Use it for:** marking what each shot is while you watch — colour + keyword.
**Before:** select clips — on the **timeline** (the clip *and* its source in the Media Pool get tagged), or, with nothing
selected on the timeline, in the **Media Pool**.
**How:** Workspace → Scripts → Safar Pahad Parivar → **Tag Shot Type** → pick one:

| Script | Clip colour | Keyword |
|---|---|---|
| 1 Hero Shot | Orange | Hero Shot |
| 2 A-Roll Family Talk | Yellow | A-Roll Family Talk |
| 3 B-Roll Scenery | Green | B-Roll Scenery |
| 4 Road Drive | Blue | Road Drive |
| 5 Drone Aerial | Teal | Drone Aerial |
| 6 Timelapse | Purple | Timelapse |
| 7 Kids Moment | Pink | Kids Moment |
| 8 Stay Food Local | Tan | Stay Food Local |
| 9 Reject | Chocolate | Reject |
| 0 Clear Tag | (none) | removes the SPP keyword |
**You'll see:** the clips change colour (timeline and Media Pool); the keyword is added to the clip's metadata (other
keywords you typed are kept). Console: `Tagged 3 timeline / 3 media pool clips as Hero Shot`.
Then: **Smart Bin** (*File → New Smart Bin*, rule *Keywords contains "Kids Moment"*) = every kids clip, always up to date.
**Again / undo:** a new tag replaces the old SPP tag; **0 Clear Tag** removes it.
Tip: give it keyboard shortcuts (*DaVinci Resolve → Keyboard Customization*, search the script name) to tag while watching.

## Moments - Analyse Trip
**Use it for:** finding the family moments in all of a trip's footage — laughter, kids shouting / cheering, singing,
"wow / papa dekho" reactions, names — and a Hindi transcript of everything said.
**Before:** the trip's footage imported into the project (from `<trip>\Footage`); the Python engines installed
(`setup_word_timing.ps1`); an NVIDIA GPU makes it fast.
**How:** run it. It starts in the **background** — Resolve stays usable.
**You'll see:**
- Console: `Analysing the trip in the background: <trip>` and the log path.
- A minimised window **SPP Moments** in the taskbar (closes itself when done).
- In the trip folder a new folder **`_spp_moments`**: `Moments.md` (read this), `Transcript.md`, `moments.json`,
  `analyse_log.txt` (progress: `[123/295] VID….mp4 …`), `clips\` (cache).
- Time: ~15 min for 2 hours of footage the first time (the first ever run also downloads the 3 GB speech model);
  later runs only process new clips (seconds).
**Then:** open `Moments.md` (Notepad / VS Code): **3 opening candidates**, **top 40 moments** (score, clip, in–out, time,
who, what was said), **by day**. Then run the next three scripts.
**Again / undo:** run again after adding footage — only new clips are analysed. To redo everything delete `_spp_moments`.
**Problems:** `Couldn't find the trip folder` → import footage from `<trip>\Footage` first. Only speech moments, no
laughter/cheering → the sound model is missing: re-run `setup_word_timing.ps1`, then this again.

## Moments - Add Markers
**Use it for:** seeing the moments right on your clips.
**Before:** *Moments - Analyse Trip* finished.
**How:** run it.
**You'll see:** coloured **clip markers** on the footage in the Media Pool — visible in the **source viewer**, on those
clips in any timeline, and in the **Edit Index → Markers** list:
Yellow = laughter · Pink = kids talking · Red = shout / excitement · Fuchsia = cheering · Purple = singing ·
Green = reaction words ("wow", "देखो", names). The marker name is the kind + score (`Laughter 0.88`), the note holds what
was said, the marker length covers the moment. Clips not yet in the project are imported into a bin **SPP Moments Footage**.
Console: `45 moment markers added…`.
**Again / undo:** running again replaces the previous moment markers (only those; your own markers stay).

## Moments - Best Moments Timeline
**Use it for:** a selects reel of the best moments, in the order they happened — to find the cold open and the story.
**Before:** *Moments - Analyse Trip* finished.
**How:** run it → choose **Top 20 / Top 40 / Top 80 / All / Only laughter / Only kids / Opening candidates (3)**.
**You'll see:** a new timeline **Moments - Top 20** (etc.) with the moments back-to-back (each with ½ s extra either side)
and a **timeline marker** on each: kind + score, note = what was said. Console: `Timeline 'Moments - Top 20': 20 clips`.
Then copy the ones you like into your SPP timeline (select → Ctrl+C → your timeline → Ctrl+V).
**Again / undo:** each run makes a new timeline; delete it when done (Media Pool → Delete Timelines).

## Moments - Search Transcript
**Use it for:** "where did someone say…?" — बर्फ, पानी, पिहू, a place name.
**Before:** *Moments - Analyse Trip* finished.
**How:** run it → type the word(s); several words separated by commas (`बर्फ, पानी`). The transcript is in Devanagari —
English words spoken appear in Devanagari too (*guys* → `गाईज`).
**You'll see:** Console lists every hit (`VID2026….mp4  0:23  पहाड़ आ गया…`) and a new timeline **Search - बर्फ** with each
of those clips (1 s before to 1 s after the sentence) and a marker holding the sentence.
**Again / undo:** new timeline per search; delete when done.

---

# Titles & GPS

## Info Cards - Fill from GPS
**Use it for:** filling SPP Info Cards automatically — place (Hindi + English), altitude, date, time, weather, temperature.
**Before:**
- **SPP Info Card** titles placed on a track **above** the footage they describe (V3), their *Place (Hindi)* field **empty**.
- The footage comes from a trip folder (`…\<trip>\Footage\…`). Better paths: a Google Maps Timeline export in the trip folder.
- Internet (weather and place names). First run on a trip builds `_spp_gps_index.json` (~1 min).
**How:** run it.
**You'll see:** every empty card filled; the card animates with the new values. Console per card:
`card at 86400: धारचूला / Dharchula, 915 m, 23 जून 11:14 AM, 24°C`, then `Filled 3 Info Card(s)`.
**Again / undo:** cards already filled are skipped. To refresh one: clear its *Place (Hindi)* and run again. Check the
Hindi spelling — names come from OpenStreetMap; just type over them.
**Problems:** `no footage under it` → move the card over a footage clip. `can't find the trip folder` → footage isn't
inside `<trip>\Footage`. Empty / wrong place → no GPS near that time: add a Timeline export (see `Maps_GPS_and_Terrain.md`).

## Route Map - Build from Timeline
**Use it for:** the animated route map on real roads — relief map, dotted path growing, stops with arrive/leave times, running clock.
**Before:** the timeline contains the trip's footage (only its dates are used); optional: an **SPP Route Map** title on
the timeline (V3); internet (roads + map tiles).
**How:** run it. **Resolve pauses 1–3 minutes** while the map is made.
**You'll see:**
- Console: the date range, `Making the map…`, then `Loaded into 1 SPP Route Map title(s)` and the stops file path.
- Folder `<trip>\Route Maps\<timeline name>\` with `map.jpg`, `route.json`, **`stops.csv`**.
- The SPP Route Map title now shows your route (play it). No title on the timeline? Add one and pick `route.json` in its Inspector.
**Again / undo:** fix stop names or add a missed stop in `stops.csv` (Excel; a place name is enough) → save → run again.
Shorts timeline → the map is made in portrait.
**Problems:** `None of the footage is inside a trip folder` → import from `<trip>\Footage`. Straight lines / few stops →
add stops in `stops.csv` or a Google Timeline export.

---

# Captions

## Captions - Sync Words to VO
**Use it for:** word-by-word animated Hindi captions timed to your real voice, with stressed words highlighted.
**Before:**
1. Your VO clips on the audio track named **VO** (A2 on SPP timelines).
2. Subtitles on the subtitle track (type them or *Timeline → Create Subtitles from Audio*, then fix the spelling).
   No subtitles? It makes them from the VO — check the spelling afterwards. `*star*` a word to force a stress.
3. One **SPP Captions** title on a video track (V3), stretched over the VO part.
4. Python engines installed; the first run downloads the 3 GB speech model.
**How:** run it. **Resolve pauses** (~1 min per 10 min of VO on the GPU).
**You'll see:** the SPP Captions title now holds the timed text and its start time — play it: words pop in with the voice,
stressed words in gold. Console: `Listening to 4 VO clips, 38 subtitles…`, then `Updated SPP Captions clip at …`.
Then turn off the subtitle track's visibility (keep it for the YouTube .srt).
**Again / undo:** after changing subtitles or the VO edit just run again. Style (pop / karaoke / fade, position) is in
the title's Inspector.
**Problems:** `No audio track named "VO"` → rename your VO track to VO. `Add an 'SPP Captions' title…` → add one.
`Word-timing engine not installed` → `.\Tools\setup_word_timing.ps1`.

---

# Sound

## SFX - Auto Sound for Titles
**Use it for:** sound for every SPP title in one click, timed to each animation beat.
**Before:** SPP titles on the timeline (Info Card, Altitude Counter, Peak Callout, Pop-up Title, Credits, Route Map,
plus the SPP intro / end-card clips); the SFX library built (`make_sfx.ps1`). SFX tracks are found by name (**SFX 1–3**);
if there are none, it adds them.
**How:** run it → choose the style: **Strings** (real violins, harp, timpani — default) · **Grand** (deep cinematic) ·
**Light** (playful) · **Mix** (grand for big moments, light for small).
**You'll see:** **Lime-coloured** clips named `SPP_…` on the SFX tracks: card whoosh, row pops, rolling-number ticks that
slow with the digits, altitude landing, a pin drop + chime at each route stop, a trail loop while the route draws,
out-whoosh; logo sound on the intro. A new *SFX n* track appears if the others are busy.
Console: `Placed 24 Strings sounds (Lime clips on the SFX tracks)…`.
**Again / undo:** moved or changed titles → run again: it first deletes its previous Lime clips, then places fresh ones.
To keep a sound you adjusted, change its clip colour (it's then left alone). Remove all: *SFX - Remove Auto Sounds*.

## SFX - Remove Auto Sounds
**Use it for:** clearing everything *Auto Sound for Titles* placed.
**Before:** a timeline open.
**How:** run it.
**You'll see:** all **Lime** audio clips whose name starts with `SPP_` are deleted. Console: `Removed 24 auto sound(s).`
Clips you recoloured and sounds you placed yourself stay.
**Undo:** Ctrl+Z.

## SFX - Land at Playhead
**Use it for:** making a riser / swell / bridge / drum fill hit exactly on a cut (a waterfall reveal, the title slam, the
first beat of new music).
**Before:** the playhead on the moment; **one or more sounds selected in the Media Pool** (e.g. *SPP SFX → 16 Cinematic
Risers → SPP_Riser_Awe_8s_v01*).
**How:** run it.
**You'll see:** the sound on a free SFX track, starting **before** the playhead by its build-up time, so its big moment is
on the playhead. Console: `SPP_Riser_Awe_8s_v01: lands at the playhead (starts 8.00 s before) on SFX 2`.
**Undo:** Ctrl+Z or delete the clip. Tip: *Riser_Epic* = big hit, *Riser_Awe* = opens into a warm chord (waterfalls,
big mountains), *Riser_Tension* = cuts to silence.

## SFX - Loop Fill (In to Out)
**Use it for:** a bed of any length — rain, river, wind, birds, gravel tyres, a drone.
**Before:** **one** `_LOOP_` sound selected in the Media Pool (e.g. `SPP_Stream_Close_LOOP_30s_v05`); **In and Out**
set on the timeline (**I** / **O** keys) over the part to cover.
**How:** run it.
**You'll see:** the loop laid end to end from In to Out on a free SFX track (last copy trimmed); the joins are seamless.
Console: `Filled 74.0 s with 3 copies of … on SFX 1`.
Then: add short fades at both ends; ride the level under dialogue (−18 to −24 dB).
**Undo:** Ctrl+Z or delete the clips.
**Problems:** `Select exactly one sound…` → one clip only, in the Media Pool (not the timeline). `Set In and Out…` → press I and O on the timeline.

## Music - Key Transition
**Use it for:** changing from one music track to the next smoothly — a transition in the right musical keys.
**Before:** select **two music clips on the timeline** (the one ending and the one starting; Ctrl+click), or **one** clip
(for a swell into it or a tail at its end). Python engines installed.
**How:** run it → it listens to the last 20 s of the first clip and the first 20 s of the second (a few seconds; Resolve
pauses) → a window shows **Detected: D (0.84, also Bm) → E (0.77, also C#m)** → change the keys if you like, choose
**Bridge** (old key → new key, 5 s), **Swell into the new key** (3 s) or **Tail + Swell**, and the variation → *Place transition*.
**You'll see:** the transition on a free SFX track, its big moment exactly on the first frame of the new music (a tail
sits at the end of the old one). If that key pair isn't in the library it is made on the spot (~10 s) into
`SFX\_transitions` and imported into *SPP SFX → 19 Music Transitions*. Console names the file and track.
Then: fade the old music out under the bridge and bring the new one in on the landing.
**Undo:** delete the clip. Relative keys (D / Bm, E / C#m) share their notes — either one sounds right.

## Distance - Selected Clips
**Use it for:** making a sound come from far away — a bird across the valley, a temple bell from the next village,
a horn echoing off the mountains — without separate recordings.
**Before:** audio clip(s) selected on the timeline.
**How:** run it → choose **Near (~10 m) · Mid (~50 m) · Far (~200 m) · Very far (~600 m) · Across the valley (echoes)**;
optional *Keep the loudness* (change only tone and space; set the level with the fader).
**You'll see:** for each clip a processed copy **on a free audio track at exactly the same place** (it rings ~2 s longer —
reverb); the **original is switched off** (greyed, not deleted). The new file is saved in a `_distance` folder next to the
source and imported into a bin **SPP Distance**. Loops stay seamless. Console: `Distance (far): … -> SFX 2`.
**Undo:** delete the new clip, select the original, press **D** to switch it back on.

## Phone Voice - Selected Clips
**Use it for:** a line that should sound like a phone call (or a walkie-talkie).
**Before:** audio clip(s) selected on the timeline (a VO line or someone's dialogue).
**How:** run it → style **mobile · landline · speaker · walkie**; options *faint line hiss*, *tiny network glitches* (mobile).
**You'll see:** a processed copy on a free audio track at the same place (walkie adds a squelch just before/after); the
original is switched off. File: `<source>_phone-<style>_<start>s.wav` next to the source; bin **SPP Phone Voice**.
Then add phone sounds around it from *SPP SFX → 08 Phone*: ringtone / vibrate → pickup → *(voice)* → hang-up + call-ended beeps.
**Undo:** delete the new clip, select the original, press **D**.
