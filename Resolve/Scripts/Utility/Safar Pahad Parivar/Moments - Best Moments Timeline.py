# Safar Pahad Parivar - build a new timeline of the best family moments, in the order they happened
# (each with a marker saying what it is and what was said).  A great first selects reel / opening finder.
import os, sys
try:
    resolve
except NameError:
    try:
        resolve = app.GetResolve()
    except Exception:
        resolve = bmd.scriptapp("Resolve")
_h = os.path.join(os.environ["APPDATA"], r"Blackmagic Design\DaVinci Resolve\Support\Fusion\Scripts\Utility\Safar Pahad Parivar")
_k = open(os.path.join(_h, "kit_path.txt"), encoding="utf-8-sig").read().strip()
sys.path.insert(0, os.path.join(_k, "Tools"))
import spp_resolve_common as C
import spp_moments_resolve as M
proj = resolve.GetProjectManager().GetCurrentProject()
trip = M.trip_from_project(proj) if proj else None

data = M.load(trip) if trip else None
if not data:
    print("No moments yet - run 'Moments - Analyse Trip' first.")
else:
    import spp_sfx_resolve as S
    choice = S.ask_choice(resolve, "SPP Best Moments", "How many moments?",
                          ["Top 20", "Top 40", "Top 80", "All", "Only laughter", "Only kids (talk, shouts, laughter)",
                           "Opening candidates (3)"], 0)
    if choice:
        ms = sorted(data["moments"], key=lambda m: -m["score"])
        if choice.startswith("Top"):
            ms = ms[: int(choice.split()[1])]
        elif choice == "Only laughter":
            ms = [m for m in ms if m["kind"] == "laugh"]
        elif choice.startswith("Only kids"):
            ms = [m for m in ms if m["child"] or m["kind"] in ("kids", "laugh", "shout")]
        elif choice.startswith("Opening"):
            ms = data.get("opens", [])
        ms = sorted(ms, key=lambda m: ((m.get("t") or 0) + m["a"]))
        spans = [(m["file"], m["a"], m["b"], "%s %.2f" % (m["label"], m["score"]), m["text"], m["kind"]) for m in ms]
        M.build_timeline(proj, "Moments - " + choice, spans)
