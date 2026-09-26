# Safar Pahad Parivar — Video Kit

Everything that makes a **@safar.pahad.parivar** video look and work the same: Resolve menu scripts,
title templates, brand graphics, tools and the source to rebuild all of it.
This folder is the **single source of truth** — Resolve gets its copies from here via `install.ps1`.

**📘 How to use everything: [Docs/SPP_Kit_Guide.md](Docs/SPP_Kit_Guide.md)** (with screenshots)

## Set up a PC (new or rebuilt)
1. Install DaVinci Resolve Studio, Git (+ Git LFS), Python 3, ffmpeg (`choco install ffmpeg`).
2. `git clone <your-remote> "F:\Video Editing\_Safar Pahad Parivar Kit"` then `git lfs pull`
3. In PowerShell inside the kit: `.\install.ps1`
4. Python tools (captions timing, GPS, route maps, sound): `.\Tools\setup_word_timing.ps1`, then `.\Tools\make_sfx.ps1` and `.\Tools\make_music.ps1`
5. Restart Resolve, then once: **Workspace → Scripts → Safar Pahad Parivar → Setup Render Presets**

## What's inside
| Folder | Contents |
|---|---|
| `Resolve\Scripts\Utility\Safar Pahad Parivar` | Menu scripts: New Timeline (YouTube 16x9 / Shorts 9x16), Tag Shot Type (9 colours), Import Brand Graphics, Setup Render Presets, Captions - Sync Words to VO, Info Cards - Fill from GPS, Route Map - Build from Timeline, SFX - Import Library / Auto Sound for Titles / Loop Fill / Remove Auto Sounds, Music - Import Library, Phone Voice - Selected Clips |
| `Resolve\Templates\Edit\Titles\Safar Pahad Parivar` | OGraf titles: Info Card, Altitude Counter, Peak Callout, Pop-up Title, Credits, Captions (animated Hindi subtitles), Route Map (+ bundled fonts) |
| `Graphics` | Intro (5s), End card (15s), Watermarks (16x9 and Shorts) — 4K, transparent |
| `Brand` | Logo lock-ups, brand board, mock-ups |
| `Tools` | `spp_sort_media.py` (sort footage by true orientation, with undo log), `new_video.ps1` (trip + video folders), `spp_word_timing.py` (word-timed captions), `spp_gps.py` (GPS lookup, stops, route maps, GPX, local API), `spp_phone_voice.py` (phone-call voice), `setup_word_timing.ps1` (installs the Python tools), `make_sfx.ps1` (builds the SFX library), `make_music.ps1` (builds the music library), `get_samples.ps1` (downloads the CC0 instrument recordings once) |
| `Docs` | User guide, cheat sheet, SFX library list, music library list + preview, VO scripts, Maps/GPS/terrain guide |
| `SFX` *(generated, not in git)* | 480 sound effects (Strings + Grand + Light) — `.\Tools\make_sfx.ps1`; the Strings set uses recorded instruments from VSCO-2 Community Edition (CC0), downloaded once into `Source\_vsco` |
| `Music` *(generated, not in git)* | 12 original background-music tracks (Slow Build, Temple Bells, Wind, Flute) — `.\Tools\make_music.ps1` |
| `Source` | Generators for every graphic/template, fonts, reference images |

## Folder layout: one trip, many videos — one Resolve project per video
Footage is stored **once per trip**; every video made from it (main film, Shorts, spin-offs) gets its own
folder and its own Resolve project (fast, isolated — editing one can never change another).
Consistency comes from this kit, not from a shared project.

```
F:\Video Editing\
  _Safar Pahad Parivar Kit\                         <- this repo (git)
  Projects\
    2026-06 Kumaon - Dharchula Darma Munsiyari\
      Footage\  Horizontal · Vertical · Square · Photos   (shared by all videos of the trip)
      01 Himalaya ki Sair\
        Audio\ (VO · Music · SFX)   Graphics\   Exports\   Docs\
        Resolve\        <- .drp backups
        Resolve Media\  <- Resolve "Project media location" (recordings, generated audio)
      02 Two Sides of Panchachuli\ ...
      03 Shorts\ ...
```
Create with: `.\Tools\new_video.ps1 -Trip "2026-10 Chopta Tungnath" -Video "01 Main Film"` (prints the next steps).

## Backups — what git covers and what it doesn't
- **This kit** → git remote (GitHub/GitLab/your server). Large binaries go through **Git LFS** (see `.gitattributes`).
- **Footage** is too big for git → back up `Projects\` to an external drive / NAS / cloud drive.
- **Music/SFX**: keep the files a video uses inside its `Audio` folder (not only in the Epidemic Sound app cache).
- **Resolve projects** live in Resolve's database → *File → Export Project* (.drp) into the video's `Resolve` folder, and turn on
  *Preferences → User → Project Save and Load → Project backups* pointing at a backed-up folder.

## Rebuilding graphics / templates (only needed when changing the design)
```
pip install playwright pillow
python -m playwright install chromium
python Source\brand\build_brand.py        # -> Brand\
python Source\brand\anim.py               # -> Graphics\ (intro, end card, watermarks; ~4 min)
python Source\templates\ograf_gen.py      # -> Resolve\Templates\...
python Source\templates\ograf_test.py     # renders test frames to Source\_build\ograf_shots
.\install.ps1                             # push changes into Resolve
```
Brand colours: Himalayan Gold `#F4B03E`, Night Navy `#07122B`, Snow `#F5F8FC`.
Fonts: Noto Sans Devanagari (titles/body), Poppins (English labels, numbers).
