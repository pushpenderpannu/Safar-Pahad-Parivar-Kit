# Safar Pahad Parivar - smooth playback after grading: turn on 'Render Cache Color Output' for every video clip on
# this timeline in one go (same as right-click a clip -> Render Cache Color Output, but for all of them).
# Resolve then renders the graded clips in the background whenever you stop for a few seconds (red bar above the
# timeline turns blue). Run again to switch it off for all clips (e.g. while you are still changing the grade a lot).
# Cache files go to the cache folder in Project Settings > Master Settings > Working Folders.
import os
try:
    resolve
except NameError:
    try:
        resolve = app.GetResolve()
    except Exception:
        resolve = bmd.scriptapp("Resolve")

proj = resolve.GetProjectManager().GetCurrentProject()
tl = proj.GetCurrentTimeline() if proj else None


def main():
    if not tl:
        print("Open a timeline first."); return
    clips = []
    for t in range(1, tl.GetTrackCount("video") + 1):
        for it in tl.GetItemListInTrack("video", t) or []:
            if it.GetMediaPoolItem():          # real footage (titles / generators are skipped)
                clips.append(it)
    if not clips:
        print("No video clips on this timeline."); return
    on = sum(1 for it in clips if it.GetIsColorOutputCacheEnabled())
    turn_on = on < len(clips) / 2.0
    if turn_on and proj.GetSetting("perfRenderCacheMode") == "none":
        proj.SetSetting("perfRenderCacheMode", "smart")
        print("Render cache was off for this project - set to Smart (Playback > Render Cache).")
    if turn_on and proj.GetSetting("perfAutoRenderCacheEnable") != "1":
        proj.SetSetting("perfAutoRenderCacheEnable", "1")
    n = sum(1 for it in clips if it.SetColorOutputCache(turn_on))
    if turn_on:
        print("Render cache ON for %d of %d clips." % (n, len(clips)))
        print("Stop playback and leave Resolve idle: it renders them in the background (red bar -> blue).")
        print("Cache folder: " + str(proj.GetSetting("perfCacheClipsLocation")))
    else:
        print("Render cache OFF for %d clips. (Delete old cache files: Playback > Delete Render Cache > All.)" % n)


main()
