# Safar Pahad Parivar — Video Kit

Everything that makes a **@safar.pahad.parivar** video look and work the same: Resolve menu scripts,
title templates, brand graphics, tools and the source to rebuild all of it.
This folder is the **single source of truth** — Resolve gets its copies from here via `install.ps1`.

## Set up a PC (new or rebuilt)
1. Install DaVinci Resolve Studio, Git (+ Git LFS), Python 3, ffmpeg (`choco install ffmpeg`).
2. `git clone <your-remote> "F:\Video Editing\_Safar Pahad Parivar Kit"` then `git lfs pull`
3. In PowerShell inside the kit: `.\install.ps1`
4. Restart Resolve, then once: **Workspace → Scripts → Safar Pahad Parivar → Setup Render Presets**

## What's inside
| Folder | Contents |
|---|---|
| `Resolve\Scripts\Utility\Safar Pahad Parivar` | Menu scripts: New Timeline (YouTube 16x9 / Shorts 9x16), Tag Shot Type (9 colours), Import Brand Graphics, Setup Render Presets |
| `Resolve\Templates\Edit\Titles\Safar Pahad Parivar` | OGraf titles: Info Card, Altitude Counter, Peak Callout, Pop-up Title, Credits (+ bundled fonts) |
| `Graphics` | Intro (5s), End card (15s), Watermarks (16x9 and Shorts) — 4K, transparent |
| `Brand` | Logo lock-ups, brand board, mock-ups |
| `Tools` | `spp_sort_media.py` (sort footage by true orientation), `new_video.ps1` (standard project folders) |
| `Docs` | Cheat sheet, VO scripts |
| `Source` | Generators for every graphic/template, fonts, reference images |

## One video = one Resolve project
Keep each video in its own Resolve project (fast, isolated — editing one can never change another).
Consistency comes from this kit, not from a shared project.

```
F:\Video Editing\
  _Safar Pahad Parivar Kit\      <- this repo (git)
  Projects\
    2026-06 Dharchula Panchachuli\
      01_Footage\  (Horizontal / Vertical / Square / Photos after sorting)
      02_Audio\    VO / Music / SFX
      03_Graphics\ 04_Exports\ 05_Resolve\ (.drp backups) 06_Docs\
```
Create one with: `.\Tools\new_video.ps1 -Name "2026-06 Dharchula Panchachuli"`

## Backups — what git covers and what it doesn't
- **This kit** → git remote (GitHub/GitLab/your server). Large binaries go through **Git LFS** (see `.gitattributes`).
- **Footage** is too big for git → back up `Projects\` to an external drive / NAS / cloud drive.
- **Resolve projects** live in Resolve's database → *File → Export Project* (.drp) into `05_Resolve`, and turn on
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
