#!/usr/bin/env python3
"""
Safar Pahad Parivar - media sorter
Sorts the files in a trip folder into  Horizontal / Vertical / Square / Photos.

* Reads each video's REAL orientation with ffprobe, including the rotation flag
  phones write (a "vertical" phone clip is often stored as 1920x1080 + rotate=90).
* Dry run by default - nothing moves until you add --apply.
* Every move is logged to a CSV so it can be undone with --undo <log.csv>.

Usage (PowerShell or cmd):
    python spp_sort_media.py "F:\\Video Editing\\Trip Folder"            # dry run, shows the plan
    python spp_sort_media.py "F:\\Video Editing\\Trip Folder" --apply    # actually move
    python spp_sort_media.py "F:\\Video Editing\\Trip Folder" --apply --recursive
    python spp_sort_media.py --undo "F:\\Video Editing\\Trip Folder\\_spp_sort_log_20260924_1730.csv"
"""
import argparse, csv, datetime, json, os, shutil, subprocess, sys

VIDEO_EXT = {".mp4", ".mov", ".m4v", ".mkv", ".avi", ".mts", ".m2ts", ".3gp", ".webm"}
PHOTO_EXT = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".dng", ".webp", ".tif", ".tiff", ".raw", ".arw", ".cr2", ".cr3", ".nef"}
OUT_DIRS = ("Horizontal", "Vertical", "Square", "Photos", "_Unreadable")

def find_ffprobe():
    for c in (shutil.which("ffprobe"),
              r"C:\ProgramData\chocolatey\bin\ffprobe.exe",
              r"C:\ffmpeg\bin\ffprobe.exe"):
        if c and os.path.exists(c):
            return c
    sys.exit("ffprobe not found. Install ffmpeg (e.g. 'choco install ffmpeg') and try again.")

def video_orientation(ffprobe, path):
    cmd = [ffprobe, "-v", "error", "-select_streams", "v:0",
           "-show_entries", "stream=width,height:stream_tags=rotate:stream_side_data=rotation",
           "-of", "json", path]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=30).stdout
        s = json.loads(out)["streams"][0]
    except Exception:
        return None, "unreadable"
    w, h = int(s.get("width", 0)), int(s.get("height", 0))
    rot = 0
    try:
        rot = int(float(s.get("tags", {}).get("rotate", 0)))
    except ValueError:
        pass
    for sd in s.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = int(float(sd["rotation"]))
    if abs(rot) % 180 == 90:
        w, h = h, w
    if not w or not h:
        return None, "unreadable"
    r = w / h
    kind = "Horizontal" if r > 1.1 else ("Vertical" if r < 0.9 else "Square")
    return kind, f"{w}x{h} rot={rot}"

def unique_dest(folder, name):
    base, ext = os.path.splitext(name)
    dest, n = os.path.join(folder, name), 1
    while os.path.exists(dest):
        dest = os.path.join(folder, f"{base}_{n}{ext}"); n += 1
    return dest

def collect(root, recursive):
    skip = {os.path.join(root, d) for d in OUT_DIRS}
    if not recursive:
        for f in sorted(os.listdir(root)):
            p = os.path.join(root, f)
            if os.path.isfile(p):
                yield p
        return
    for dp, dns, fns in os.walk(root):
        if any(dp == s or dp.startswith(s + os.sep) for s in skip):
            continue
        for f in sorted(fns):
            yield os.path.join(dp, f)

def sort(root, apply, recursive):
    root = os.path.abspath(root)
    ffprobe = find_ffprobe()
    plan, counts = [], {d: 0 for d in OUT_DIRS}
    for p in collect(root, recursive):
        ext = os.path.splitext(p)[1].lower()
        if ext in PHOTO_EXT:
            kind, info = "Photos", "photo"
        elif ext in VIDEO_EXT:
            kind, info = video_orientation(ffprobe, p)
            kind = kind or "_Unreadable"
        else:
            continue  # leave project files, sidecars etc. alone
        counts[kind] += 1
        plan.append((p, kind, info))
        print(f"{kind:<12} {info:<22} {os.path.relpath(p, root)}")

    print("\nSummary:", ", ".join(f"{k}: {v}" for k, v in counts.items() if v))
    if not apply:
        print("\nDRY RUN - nothing moved. Add --apply to move the files.")
        return
    log = os.path.join(root, f"_spp_sort_log_{datetime.datetime.now():%Y%m%d_%H%M%S}.csv")
    with open(log, "w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh); wr.writerow(["from", "to"])
        for src, kind, _ in plan:
            folder = os.path.join(root, kind); os.makedirs(folder, exist_ok=True)
            dest = unique_dest(folder, os.path.basename(src))
            shutil.move(src, dest); wr.writerow([src, dest])
    print(f"\nMoved {len(plan)} files. Undo log: {log}")

def undo(log):
    with open(log, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in reversed(rows):
        if os.path.exists(r["to"]):
            os.makedirs(os.path.dirname(r["from"]), exist_ok=True)
            shutil.move(r["to"], r["from"])
    for d in {os.path.dirname(r["to"]) for r in rows}:
        try:
            os.rmdir(d)  # only removes the folder if it is now empty
        except OSError:
            pass
    print(f"Restored {len(rows)} files.")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Safar Pahad Parivar media sorter")
    ap.add_argument("root", nargs="?", help="trip folder to sort")
    ap.add_argument("--apply", action="store_true", help="actually move files (default is dry run)")
    ap.add_argument("--recursive", action="store_true", help="also sort files inside subfolders")
    ap.add_argument("--undo", metavar="LOG_CSV", help="undo a previous run using its log")
    a = ap.parse_args()
    if a.undo:
        undo(a.undo)
    elif a.root:
        sort(a.root, a.apply, a.recursive)
    else:
        ap.print_help()
