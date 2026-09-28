# Safar Pahad Parivar - sync SPP Captions to the real VO, word by word (with stressed words).
#
# 1. Subtitles on the subtitle track (typed, or Timeline > Create Subtitles from Audio). Optional: if there are
#    none, captions are made from the VO automatically (check spelling afterwards).
#    Put *stars* around a word to force it to be stressed, e.g.  ये नज़ारा *बेमिसाल* था
# 2. VO clips on the audio track named "VO".
# 3. At least one "SPP Captions" title on a video track (Effects > Titles > Safar Pahad Parivar).
# Then run this. Resolve pauses while it listens (about 1 minute per 10 minutes of VO on the GPU).
import json, os, subprocess, tempfile
try:
    resolve
except NameError:
    try:
        resolve = app.GetResolve()
    except Exception:
        resolve = bmd.scriptapp("Resolve")

HERE = os.path.join(os.environ["APPDATA"], r"Blackmagic Design\DaVinci Resolve\Support\Fusion\Scripts\Utility\Safar Pahad Parivar")
KIT = r"F:\Video Editing\_Safar Pahad Parivar Kit"
try:
    with open(os.path.join(HERE, "kit_path.txt"), encoding="utf-8-sig") as fh:
        KIT = fh.read().strip() or KIT
except Exception:
    pass
PY = os.path.join(KIT, r"Tools\.venv\Scripts\python.exe")
WORKER = os.path.join(KIT, r"Tools\spp_word_timing.py")


def find_captions(tl):
    """(timeline item, OGrafLoader tool) for every SPP Captions title on the timeline."""
    found = []
    for t in range(1, tl.GetTrackCount("video") + 1):
        for it in tl.GetItemListInTrack("video", t) or []:
            try:
                comp = it.GetFusionCompByIndex(1) if it.GetFusionCompCount() else None
            except Exception:
                comp = None
            if not comp:
                continue
            for tool in (comp.GetToolList(False) or {}).values():
                try:
                    if "SPP-Captions" in str(tool.GetInput("TemplatePath") or ""):
                        found.append((it, tool))
                except Exception:
                    pass
    return found


# Resolve names OGraf inputs by position in the template's settings: 0 = SRT text, 1 = clip start (s)
TEXT_INPUT, START_INPUT = "DynParamText0", "DynParamNum1"


def main():
    proj = resolve.GetProjectManager().GetCurrentProject()
    tl = proj.GetCurrentTimeline() if proj else None
    if not tl:
        print("Open a timeline first."); return
    if not os.path.exists(PY):
        print("Word-timing engine not installed. In PowerShell run:\n  " +
              os.path.join(KIT, r"Tools\setup_word_timing.ps1")); return
    fps = float(tl.GetSetting("timelineFrameRate")); t0 = tl.GetStartFrame()

    cues = []
    for i in range(1, tl.GetTrackCount("subtitle") + 1):
        items = tl.GetItemListInTrack("subtitle", i) or []
        if items:
            cues = [{"a": (s.GetStart() - t0) / fps, "b": (s.GetEnd() - t0) / fps, "text": s.GetName() or ""}
                    for s in items]
            break

    vo = [i for i in range(1, tl.GetTrackCount("audio") + 1)
          if (tl.GetTrackName("audio", i) or "").strip().upper() in ("VO", "VOICE", "VOICEOVER", "VOICE OVER")]
    if not vo:
        print('No audio track named "VO". Rename your voiceover track to VO and run again.'); return
    clips = []
    for it in tl.GetItemListInTrack("audio", vo[0]) or []:
        mpi = it.GetMediaPoolItem()
        path = mpi.GetClipProperty("File Path") if mpi else ""
        if not path or not os.path.exists(path):
            continue
        clips.append({"file": path, "tl": (it.GetStart() - t0) / fps,
                      "src": max(0, it.GetLeftOffset() or 0) / fps, "dur": (it.GetEnd() - it.GetStart()) / fps})
    if not clips:
        print("The VO track has no audio clips."); return

    caps = find_captions(tl)
    if not caps:
        print("Add an 'SPP Captions' title to a video track first (Effects > Titles > Safar Pahad Parivar)."); return

    work = os.path.join(tempfile.gettempdir(), "spp_captions"); os.makedirs(work, exist_ok=True)
    job, out = os.path.join(work, "job.json"), os.path.join(work, "captions_words.json")
    json.dump({"cues": cues, "clips": clips, "model": "large-v3", "lang": "hi"},
              open(job, "w", encoding="utf-8"), ensure_ascii=False)
    print("Listening to %d VO clips, %d subtitles... (Resolve will pause)" % (len(clips), len(cues)))
    r = subprocess.run([PY, WORKER, job, out], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", creationflags=0x08000000)
    print(r.stdout[-3000:])
    if r.returncode != 0 or not os.path.exists(out):
        print("FAILED:\n" + r.stderr[-3000:]); return
    data = open(out, encoding="utf-8").read()

    for it, tool in caps:
        tool.SetInput(TEXT_INPUT, data)
        tool.SetInput(START_INPUT, round((it.GetStart() - t0) / fps, 3))
        print("Updated SPP Captions clip at %s" % it.GetStart())
    print("Done. Tip: put *stars* around a subtitle word to force a stress, then run again.")


main()
