# Safar Pahad Parivar - create/refresh the SPP render presets (run once per machine)
# Built on Resolve's own YouTube / TikTok upload presets, resized where needed.
try:
    resolve
except NameError:
    try:
        resolve = app.GetResolve()
    except Exception:
        resolve = bmd.scriptapp("Resolve")

PLAN = [
    ("SPP YouTube 4K",    "YouTube - 2160p", {}),
    ("SPP YouTube 1080p", "YouTube - 1080p", {}),
    ("SPP Shorts 9x16",   "TikTok - 1080p",  {"FormatWidth": 1080, "FormatHeight": 1920}),
]
proj = resolve.GetProjectManager().GetCurrentProject()
existing = set(proj.GetRenderPresetList() or [])
for name, base, extra in PLAN:
    if not proj.LoadRenderPreset(base):
        print("Base preset missing:", base); continue
    proj.SetRenderSettings(dict(extra, SelectAllFrames=True))
    ok = proj.UpdateRenderPreset(name) if name in existing else proj.SaveAsNewRenderPreset(name)
    print(("Saved " if ok else "FAILED ") + name)
