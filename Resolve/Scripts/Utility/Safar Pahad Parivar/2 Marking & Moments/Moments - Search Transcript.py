# Safar Pahad Parivar - search what was said on the trip (Hindi or English words) and get a timeline of every hit.
# e.g. बर्फ, पानी, पिहू, wow, "papa dekho".  Each hit gets a marker with the sentence.
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


def ask():
    try:
        ui = resolve.Fusion().UIManager
        disp = bmd.UIDispatcher(ui)
        win = disp.AddWindow({"ID": "SQ", "WindowTitle": "SPP Search Transcript", "Geometry": [500, 300, 380, 110]},
                             ui.VGroup([ui.Label({"Text": "Word(s) to find (Hindi or English):"}), ui.LineEdit({"ID": "q"}),
                                        ui.HGroup([ui.Button({"ID": "ok", "Text": "Search"}), ui.Button({"ID": "cancel", "Text": "Cancel"})])]))
        it = win.GetItems()
        res = {}

        def done(ev, ok):
            if ok:
                res["q"] = it["q"].Text
            disp.ExitLoop()
        win.On.ok.Clicked = lambda ev: done(ev, True)
        win.On.cancel.Clicked = lambda ev: done(ev, False)
        win.On.SQ.Close = lambda ev: done(ev, False)
        win.Show(); disp.RunLoop(); win.Hide()
        return res.get("q")
    except Exception as e:
        print("(no dialog: %s)" % e)
        return None


if not data:
    print("No transcript yet - run 'Moments - Analyse Trip' first.")
else:
    import unicodedata
    norm = lambda s: unicodedata.normalize("NFC", s.lower()).replace("ँ", "ं").replace("़", "")
    q = ask()
    if q:
        terms = [norm(t) for t in q.split(",") if t.strip()]
        hits = []
        for c in data["clips"]:
            for s in c["speech"]:
                if any(t.strip() in norm(s["text"]) for t in terms):
                    hits.append((c["file"], max(0, s["a"] - 1.0), s["b"] + 1.0, s["text"][:60], s["text"], "word"))
        hits.sort(key=lambda h: h[0])
        print("%d hits for '%s'" % (len(hits), q))
        for h in hits[:60]:
            print("  %s  %d:%02d  %s" % (os.path.basename(h[0]), int(h[1]) // 60, int(h[1]) % 60, h[4]))
        if hits:
            M.build_timeline(proj, "Search - " + q[:30], hits, handle=0.0)
