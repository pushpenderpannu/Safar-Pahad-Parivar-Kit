
# Safar Pahad Parivar - tag selected clips by shot type (clip colour + keyword)
try:
    resolve
except NameError:
    try:
        resolve = app.GetResolve()
    except Exception:
        resolve = bmd.scriptapp("Resolve")
ALL_TAGS = ["Hero Shot","A-Roll Family Talk","B-Roll Scenery","Road Drive","Drone Aerial",
            "Timelapse","Kids Moment","Stay Food Local","Reject"]
def tag(label, color):
    proj = resolve.GetProjectManager().GetCurrentProject()
    tl = proj.GetCurrentTimeline()
    items = []
    if tl:
        items = tl.GetSelectedClips() or []
    mpis = []
    for it in items:
        if color: it.SetClipColor(color)
        else: it.ClearClipColor()
        m = it.GetMediaPoolItem()
        if m: mpis.append(m)
    if not items:
        mpis = proj.GetMediaPool().GetSelectedClips() or []
    for m in mpis:
        if color: m.SetClipColor(color)
        else: m.ClearClipColor()
        kw = [k.strip() for k in (m.GetMetadata("Keywords") or "").split(",") if k.strip()]
        kw = [k for k in kw if k not in ALL_TAGS]
        if label: kw.append(label)
        m.SetMetadata({"Keywords": ", ".join(kw)})
    print("Tagged %d timeline / %d media pool clips as %s" % (len(items), len(mpis), label or "(cleared)"))

tag('Reject', 'Chocolate')
