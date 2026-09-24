
# Safar Pahad Parivar - standard timeline template
import datetime
try:
    resolve
except NameError:
    try:
        resolve = app.GetResolve()
    except Exception:
        resolve = bmd.scriptapp("Resolve")

VIDEO_TRACKS = ["Main (A-Roll)", "B-Roll / Overlay", "GFX / Info Cards"]
AUDIO_TRACKS = ["Nat Sound / Dialogue", "VO",
                "Music 1", "Music 2", "Music 3",
                "SFX 1", "SFX 2", "SFX 3"]

def build(label, w, h, fps="30"):
    pm = resolve.GetProjectManager()
    proj = pm.GetCurrentProject()
    mp = proj.GetMediaPool()
    name = "SPP %s - %s" % (label, datetime.datetime.now().strftime("%Y-%m-%d %H%M"))
    tl = mp.CreateEmptyTimeline(name)
    if not tl:
        print("Could not create timeline"); return
    proj.SetCurrentTimeline(tl)
    tl.SetSetting("useCustomSettings", "1")
    tl.SetSetting("timelineResolutionWidth", str(w))
    tl.SetSetting("timelineResolutionHeight", str(h))
    tl.SetSetting("timelineFrameRate", fps)
    tl.SetSetting("timelineInputResMismatchBehavior", "scaleToCrop" if h > w else "scaleToFit")
    while tl.GetTrackCount("video") < len(VIDEO_TRACKS):
        tl.AddTrack("video")
    while tl.GetTrackCount("audio") < len(AUDIO_TRACKS):
        tl.AddTrack("audio", "stereo")
    for i, n in enumerate(VIDEO_TRACKS, 1):
        tl.SetTrackName("video", i, n)
    for i, n in enumerate(AUDIO_TRACKS, 1):
        tl.SetTrackName("audio", i, n)
    if tl.GetTrackCount("subtitle") < 1:
        tl.AddTrack("subtitle")
    print("Created", name)
    return tl

build("YouTube 16x9", 3840, 2160)
