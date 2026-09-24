# Safar Pahad Parivar — Editing Kit (Phase 1)

## 1. New timeline (one click)
Resolve → **Workspace → Scripts → Safar Pahad Parivar →**
- **New Timeline – YouTube 16x9** → 3840×2160, 30 fps, scale-to-fit
- **New Timeline – Shorts 9x16** → 1080×1920, 30 fps, scale-to-crop (fills the frame)

| Track | Name | Use |
|---|---|---|
| V1 | Main (A-Roll) | main story clips |
| V2 | B-Roll / Overlay | cutaways over A-roll |
| V3 | GFX / Info Cards | titles, info cards, map, watermark |
| A1 | Nat Sound / Dialogue | clips' own audio (family talk) lands here |
| A2 | VO | your voiceover |
| A3–A5 | Music 1–3 | music beds / crossfades |
| A6–A8 | SFX 1–3 | whooshes, ambience, pops |
| ST1 | Subtitles | Hindi VO captions |

## 2. Shot-type colours (select clips → Workspace → Scripts → Safar Pahad Parivar → Tag Shot Type)
Works on selected **timeline** clips (also tags their source), or selected **media pool** clips.

| Colour | Shot type |
|---|---|
| 🟧 Orange | Hero shot |
| 🟨 Yellow | A-roll / family talk |
| 🟩 Green | B-roll / scenery |
| 🟦 Blue | Road / drive |
| Teal | Drone / aerial |
| 🟪 Purple | Timelapse |
| Pink | Kids moment |
| Tan | Stay / food / local life |
| Chocolate | Reject |
Each tag also writes a **keyword**, so you can build Smart Bins (e.g. *Keywords contains "Hero Shot"*).

## 3. Render presets (Deliver page)
- **SPP YouTube 4K** · **SPP YouTube 1080p** · **SPP Shorts 9x16** (1080×1920)
Based on Resolve's own YouTube/TikTok upload presets.

## 4. Sorting a new trip's media
```
python Tools\spp_sort_media.py "F:\Video Editing\<Trip>"            # dry run – shows the plan
python Tools\spp_sort_media.py "F:\Video Editing\<Trip>" --apply    # moves into Horizontal / Vertical / Square / Photos
python Tools\spp_sort_media.py --undo "F:\Video Editing\<Trip>\_spp_sort_log_<date>.csv"
```
Reads true orientation (incl. phone rotation flags). Needs ffmpeg (already installed via Chocolatey).

## 5. VO audio recipe (Fairlight, on the VO track)
Your room has AC noise and no pop filter, so:
1. **Voice Isolation** on the VO track (start ~60–70).
2. **EQ:** high-pass at 80 Hz; small cut around 250–350 Hz if boomy; gentle lift at 3–5 kHz for clarity.
3. **De-esser** (sharp "स/श" sounds).
4. **Dialogue Leveler** or a compressor (ratio ~3:1) for even volume.
5. **Loudness:** final mix at **−14 LUFS integrated** for YouTube (Fairlight → Loudness meter); music sits ~15–20 dB under the voice.
Tip: a ₹300 pop filter + recording with the AC off will help more than any plugin.

## 6. Starting a new video
```
.\Tools\new_video.ps1 -Trip "2026-10 Chopta Tungnath" -Video "01 Main Film"
```
Then in Resolve: new project → Project Settings → Working Folders → *Project media location* = `<video>\Resolve Media`,
run **New Timeline** and **Import Brand Graphics**. Titles: **Effects → Titles → Safar Pahad Parivar**.

## 7. Animated Hindi captions (SPP Captions)
Resolve's built-in *animated* subtitles break Devanagari (matras and conjuncts come apart), so use **SPP Captions** instead.
The subtitle track (ST1) stays as the plain, editable source and the **.srt you upload to YouTube for CC**.
1. Make the subtitles as usual (type them, or *Timeline → Create Subtitles from Audio*), and fix the text.
2. Export them: **File → Export → Subtitle… → SRT**. Open the .srt in Notepad → Ctrl+A, Ctrl+C.
3. **Effects → Titles → Safar Pahad Parivar → SPP Captions** → drag it onto **V3** and stretch it over the whole VO section.
4. Inspector → paste into **SRT text**. Set **This clip starts at timeline time (s)**:
   - clip placed at the very start of the timeline → `0`;
   - otherwise type where the clip begins, in seconds (e.g. clip starts at 00:02:15 → `135`).
5. Pick **Animation**: `0` word pop · `1` karaoke (gold current word) · `2` simple fade.
   **Position**: `0` bottom · `1` raised (Shorts, clears the YouTube buttons) · `2` centre · `3` top. Optional dark **plate**.
6. Hide/disable ST1 when rendering so captions aren't shown twice (keep it for the YouTube .srt).
Edited the text? Export the SRT again and re-paste. Words animate whole, so Hindi always shapes correctly.
