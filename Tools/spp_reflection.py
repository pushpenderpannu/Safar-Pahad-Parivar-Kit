"""
Safar Pahad Parivar - windshield / window reflection remover.

When the phone films through the car's windshield or a side window, the glass reflects the dashboard, the phone,
hands and clothes.  While the car moves the landscape slides past, but the reflection stays still in the frame.
This tool finds what stays still (over a sliding window of ~8 seconds), keeps only the part that looks like a
reflection (a faint layer added on top of moving scenery - not the car's bonnet or the window frame, which are
solid) and subtracts it, in linear light, from every frame.  The cleaned copy is written next to the trip:

    <trip>\\_spp_clean\\<clip>__f<first>-<last>.mp4     (HEVC 10-bit, same size / frame rate, video only)
    <trip>\\_spp_clean\\<clip>__f<first>-<last>.jpg     (before | after | the reflection that was removed)

    .venv\\Scripts\\python.exe Tools\\spp_reflection.py clean "<clip>" [--in 12.5 --out 40] [--strength 0.85]
    .venv\\Scripts\\python.exe Tools\\spp_reflection.py preview "<clip>" [--at 20] [--strength 0.85]   (just the jpg)
    .venv\\Scripts\\python.exe Tools\\spp_reflection.py scan "<trip or folder>"     (score every clip, report + sheet)
    .venv\\Scripts\\python.exe Tools\\spp_reflection.py jobs "<jobs.json>"          (queue written by Resolve)

Works best: phone on a mount (or held steady against the glass) while driving.  Less well: hand-held with a lot of
movement, sharp hairpins where the sun swings across the dashboard, reflections over plain bright sky.
"""
import argparse, json, os, subprocess, sys, threading, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi
from PIL import Image

NOWIN = 0x08000000 if os.name == "nt" else 0
EST_W = 640            # estimation width (reflections on glass are out of focus - low resolution is enough)
SAMPLE_FPS = 4.0       # frames per second looked at for the estimate
WINDOW = 8.0           # seconds of driving that make up one reflection estimate
KEY_STEP = 1.0         # a new estimate every second, blended in between
HANDLE = 1.0           # extra seconds cleaned before / after the used part of the clip
Q = 160                # reflection levels in the look-up table


# ---------------------------------------------------------------- colour (Rec.709 / phone video)
def dec(v):
    v = np.asarray(v, np.float32)
    return np.where(v < 0.081, v / 4.5, ((v + 0.099) / 1.099) ** (1 / 0.45)).astype(np.float32)


def enc(l):
    l = np.clip(np.asarray(l, np.float32), 0, 1)
    return np.where(l < 0.018, l * 4.5, 1.099 * l ** 0.45 - 0.099).astype(np.float32)


# ---------------------------------------------------------------- probing
def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, creationflags=NOWIN, **kw)


def probe(path):
    r = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
             "stream=width,height,r_frame_rate,nb_frames,duration:stream_side_data=rotation:format=duration,start_time",
             "-of", "json", path], text=True)
    j = json.loads(r.stdout or "{}")
    s = (j.get("streams") or [{}])[0]
    num, den = (s.get("r_frame_rate") or "30/1").split("/")
    fps = float(num) / float(den or 1)
    dur = float(s.get("duration") or j.get("format", {}).get("duration") or 0)
    return {"w": int(s.get("width", 0)), "h": int(s.get("height", 0)), "fps": fps, "fps_str": s.get("r_frame_rate") or "30/1",
            "dur": dur, "start": float(j.get("format", {}).get("start_time") or 0)}


# ---------------------------------------------------------------- reading frames
_CUDA = {}


def hw(path):
    """['-hwaccel', 'cuda'] when the NVIDIA decoder can read this kind of file (8x faster), else []."""
    ext = Path(path).suffix.lower()
    if ext not in _CUDA:
        r = run(["ffmpeg", "-nostdin", "-v", "error", "-hwaccel", "cuda", "-i", path, "-frames:v", "1", "-f", "null", "-"])
        _CUDA[ext] = r.returncode == 0 and b"rror" not in r.stderr
    return ["-hwaccel", "cuda"] if _CUDA[ext] else []


def read_small(path, t0, t1, info, fps=SAMPLE_FPS, width=EST_W, keyonly=False):
    """Frames between t0 and t1 (seconds from the clip start), small, linear light, float32 (n, h, w, 3)."""
    w = width
    h = int(round(info["h"] * w / info["w"] / 2)) * 2
    cmd = ["ffmpeg", "-nostdin", "-v", "error"] + hw(path) + (["-skip_frame", "nokey"] if keyonly else []) + [
           "-ss", f"{max(0, t0):.3f}", "-i", path, "-t", f"{max(0.1, t1 - t0):.3f}",
           "-an"] + (["-fps_mode", "passthrough"] if keyonly else []) + [
           "-vf", ("" if keyonly else f"fps={fps},") + f"scale={w}:{h}:flags=area:in_range=tv:in_color_matrix=bt709:out_range=pc,format=rgb24",
           "-f", "rawvideo", "-"]
    raw = run(cmd).stdout
    n = len(raw) // (w * h * 3)
    x = np.frombuffer(raw[:n * w * h * 3], np.uint8).reshape(n, h, w, 3)
    return LIN8[x], w, h


LIN8 = dec(np.arange(256) / 255.0)


# ---------------------------------------------------------------- the estimate
LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)
VEIL = 0.75            # how much of the broad, featureless glare to take off too (the shaped reflection: all of it)


def moving_mask(stack, step=None):
    """1 where the scenery keeps changing behind the glass (trees and rocks rushing past), 0 on still or
    slowly-drifting things (bonnet, window frame, sky, the far view straight ahead)."""
    luma = ndi.gaussian_filter(stack @ LUMA, (0, 1, 1))
    n = len(luma)
    st = step or max(1, int(round(SAMPLE_FPS / 2)))
    st = min(st, max(1, n // 4))
    a, b = luma[:-st], luma[st:]
    d = np.abs(b - a) / ((a + b) / 2 + 0.03)
    frac = (d > 0.10).mean(axis=0)
    move = np.clip((frac - 0.30) / 0.30, 0, 1)
    return ndi.gaussian_filter(ndi.grey_opening(move, size=5), 2).astype(np.float32)


def floor_of(luma_stack, move):
    """What never went away (luma): the darkest the picture got at each pixel, minus the scenery's broad floor."""
    h = luma_stack.shape[1]
    low = np.percentile(luma_stack, 5, axis=0)
    k = max(9, int(h / 2) | 1)
    m = np.where(move > 0.5, low, 1.0)
    big = ndi.gaussian_filter(ndi.minimum_filter(m, size=k), h / 8)
    return np.clip(low - big, 0, None) * move, big


LAST = {}


def pattern(stack, veil=VEIL, step=None, force=False):
    """The reflection pattern of a long stretch of video (n, h, w, 3) -> (pattern rgb, move mask, base, score).
    A reflection is there the whole time; scenery changes.  The stretch is cut into chunks and only what is
    present in every chunk is kept.  Of that, the shaped part (edges, blobs) is taken completely and the
    broad glare only partly (a broad grey floor could also be the road or the haze of the valley).
    Brightness is found per pixel; the colour of the reflection only as a soft average (no colour blotches)."""
    n, h, w, _ = stack.shape
    move = moving_mask(stack, step)
    luma = stack @ LUMA
    K = int(np.clip(n // 6, 2, 4))
    parts = np.array_split(np.arange(n), K)
    fl = [floor_of(luma[p], move) for p in parts]
    common = np.min([f[0] for f in fl], axis=0)
    base = fl[0][1]
    # does the same SHAPE come back in every chunk?  (a reflection does, scenery doesn't)
    shapes = [np.clip(f[0] - ndi.gaussian_filter(f[0], h / 12), 0, None) for f in fl]
    sel = move > 0.5
    if K >= 2 and sel.sum() > 200:
        cs = []
        for i in range(K):
            for j in range(i + 1, K):
                a_, b_ = shapes[i][sel], shapes[j][sel]
                cs.append(float(np.corrcoef(a_, b_)[0, 1]) if a_.std() > 1e-6 and b_.std() > 1e-6 else 0.0)
        agree = float(np.clip((np.mean(cs) - 0.12) / 0.20, 0, 1))
        LAST["corr"] = round(float(np.mean(cs)), 3)
    else:
        agree = 0.3
    # is the scenery really sweeping past (driving)?  A still camera (waterfall, selfie, tripod) keeps the same
    # picture for seconds - its foam, faces and rocks would look like a 'still layer' too.
    hp = ndi.gaussian_filter(luma, (0, 1.5, 1.5)) - ndi.gaussian_filter(luma, (0, h / 15, h / 15))
    lag = max(2, n // 10)
    cc = []
    for i in range(0, n - lag, max(1, (n - lag) // 12)):
        a_, b_ = hp[i].ravel(), hp[i + lag].ravel()
        if a_.std() > 1e-6 and b_.std() > 1e-6:
            cc.append(float(np.corrcoef(a_, b_)[0, 1]))
    sweep = 1 - (float(np.median(cc)) if cc else 1.0)
    LAST["sweep"] = round(sweep, 3)
    agree *= float(np.clip((sweep - 0.5) / 0.3, 0, 1))
    if force:                                       # 'Strong': trust the still layer even when the check is unsure
        agree = max(agree, 0.6)
    LAST["agree"] = agree
    broad = ndi.gaussian_filter(common, h / 12)
    shaped = np.clip(common - broad, 0, None)
    # never touch what is always bright (sky, snow, clouds): a reflection there hardly shows, and removing the
    # 'floor' of the sky would blotch it.  Reflections are faint: at most ~0.15 of full brightness.
    floor_raw = np.percentile(luma, 5, axis=0)
    keep_off = np.clip((0.30 - ndi.gaussian_filter(floor_raw, 3)) / 0.15, 0, 1)
    rl = np.minimum(ndi.gaussian_filter(shaped + veil * broad, 1.2), 0.15) * move * agree * keep_off
    low = np.percentile(stack, 5, axis=0)
    col = ndi.gaussian_filter(low, (h / 8, h / 8, 0))
    col = col / (col @ LUMA + 1e-4)[..., None]
    col = np.clip(col, 0.6, 1.4)
    refl = rl[..., None] * col
    visible = enc(base + rl) - enc(base)
    score = float((visible * move).sum() / (move.sum() + 1e-6) * 100) if move.mean() > 0.05 else 0.0
    return refl.astype(np.float32), move, base, score


def gain(stack_local, pat, move):
    """How strong the pattern is right now (sun on the dashboard changes): 0 .. 1.3."""
    fl, _ = floor_of(stack_local @ LUMA, move)
    p = pat @ LUMA
    sel = (p > 0.004) & (move > 0.5)
    if sel.sum() < 50:
        return 1.0
    r = fl[sel] / (p[sel] + 1e-6)
    return float(np.clip(np.percentile(r, 40), 0, 1.3))


def estimates(path, info, t0, t1, keyonly=False, force=False):
    """Reflection estimates every KEY_STEP seconds over [t0, t1] -> (times, refl stack (k, h, w, 3), scores).
    The pattern comes from blocks of up to a minute; its strength is followed second by second."""
    a = max(0.0, min(t0 - 15, t1 - 40))
    b = min(info["dur"], max(t1 + 15, t0 + 40))
    frames, w, h = read_small(path, a, b, info, keyonly=keyonly)
    if keyonly and len(frames) < 20:
        keyonly = False
        frames, w, h = read_small(path, a, b, info)
    if len(frames) < 12:
        raise SystemExit("not enough video to look at (need 5+ seconds of driving)")
    ft = a + np.arange(len(frames)) * ((b - a) / len(frames) if keyonly else 1 / SAMPLE_FPS)
    nblk = max(1, int(round((b - a) / 60)))
    edges = np.linspace(a, b, nblk + 1)
    blocks = []
    for i in range(nblk):
        sel = (ft >= edges[i]) & (ft <= edges[i + 1])
        blocks.append(((edges[i] + edges[i + 1]) / 2,) + pattern(frames[sel], step=1 if keyonly else None, force=force))
    keys = np.arange(t0, t1 + KEY_STEP * 0.99, KEY_STEP) if t1 > t0 else np.array([t0])
    out, scores = [], []
    for tk in keys:
        cs = np.array([bl[0] for bl in blocks])
        j = int(np.clip(np.searchsorted(cs, tk), 1, len(cs) - 1)) if len(cs) > 1 else 0
        if len(cs) > 1:
            i0 = j - 1
            f = float(np.clip((tk - cs[i0]) / (cs[j] - cs[i0]), 0, 1))
            pat = blocks[i0][1] * (1 - f) + blocks[j][1] * f
            move = np.maximum(blocks[i0][2], blocks[j][2]); sc = blocks[i0][4] * (1 - f) + blocks[j][4] * f
        else:
            pat, move, sc = blocks[0][1], blocks[0][2], blocks[0][4]
        sel = (ft >= tk - WINDOW / 2) & (ft <= tk + WINDOW / 2)
        g = gain(frames[sel], pat, move) if sel.sum() >= 6 else 1.0
        out.append(pat * g)
        scores.append(sc * g)
    R = np.stack(out)
    if len(R) >= 3:                                   # calm the estimate over time (no flicker)
        R = ndi.uniform_filter1d(R, 5, axis=0, mode="nearest")
    return keys, R, scores


# ---------------------------------------------------------------- applying at full resolution
def make_lut(strength):
    """lut[q * 256 + v] = 10-bit output for 8-bit input v with reflection level q removed (linear light)."""
    lv = (np.arange(Q) / (Q - 1)) ** 2 * 0.6 * strength                    # reflection levels 0 .. 0.6 (linear)
    lin = LIN8[None, :] - lv[:, None]
    out = enc(np.clip(lin, 0, 1)) * 1023 + 0.5
    return out.astype(np.uint16).ravel()


def level_index(refl_small, W, H):
    """Full-size look-up base index (q * 256) per plane, in ffmpeg's gbrp order (G, B, R)."""
    q = np.sqrt(np.clip(refl_small / 0.6, 0, 1)) * (Q - 1)
    planes = []
    for c in (1, 2, 0):
        im = Image.fromarray(q[..., c].astype(np.float32), "F").resize((W, H), Image.BILINEAR)
        planes.append((np.asarray(im) + 0.5).astype(np.uint16) * np.uint16(256))
    return planes


STD_FPS = [(23.976, "24000/1001"), (24.0, "24"), (25.0, "25"), (29.97, "30000/1001"), (30.0, "30"), (50.0, "50"),
           (59.94, "60000/1001"), (60.0, "60")]


def fps_rational(f):
    for v, r in STD_FPS:
        if abs(float(f) - v) < 0.006:
            return r
    return "%.3f" % float(f)


def guess_fps(info):
    """What Resolve will call the clip's frame rate (phones write '30' but vary; Resolve uses 29.97 then)."""
    f = info["fps"]
    return 29.97 if abs(f - 30) < 0.5 else 59.94 if abs(f - 60) < 0.5 else f


def clean(path, fin=None, fout=None, strength=0.85, fps=None, out_dir=None, log=print):
    """Clean source frames fin..fout (Resolve's frame numbers at 'fps', time based) plus handles."""
    info = probe(path)
    fps = float(fps or guess_fps(info))
    rate = fps_rational(fps)
    last = int(info["dur"] * fps) - 1
    f0 = 0 if fin is None else max(0, int(fin) - int(HANDLE * fps))
    f1 = last if fout is None else min(last, int(fout) + int(HANDLE * fps))
    t_first, t_last = f0 / fps, f1 / fps
    trip = trip_of(path)
    od = Path(out_dir) if out_dir else Path(trip or Path(path).parent) / "_spp_clean"
    od.mkdir(parents=True, exist_ok=True)
    stem = f"{Path(path).stem}__f{f0}-{f1}_s{int(round(strength * 100))}"
    outp, prev, meta = od / (stem + ".mp4"), od / (stem + ".jpg"), od / (stem + ".json")
    log(f"estimating the reflection ({t_last - t_first:.0f} s of video)...")
    keys, R, scores = estimates(path, info, t_first, t_last, force=strength >= 0.99)
    W, H = info["w"], info["h"]
    lut = make_lut(strength)
    # R is estimated in linear light at EST_W; remember keys relative to the first frame
    idx_cache = {}
    lock = threading.Lock()

    def base_for(t):
        k = int(np.clip(round((t - keys[0]) / KEY_STEP * 4), 0, (len(keys) - 1) * 4))   # quarter-second steps
        with lock:
            if k not in idx_cache:
                pos = k / 4
                i = int(np.floor(pos)); j = min(i + 1, len(keys) - 1); a = pos - i
                r = R[i] * (1 - a) + R[j] * a
                idx_cache.clear() if len(idx_cache) > 6 else None
                idx_cache[k] = level_index(r, W, H)
            return idx_cache[k]

    n = f1 - f0 + 1
    dcmd = ["ffmpeg", "-nostdin", "-v", "error"] + hw(path) + ["-ss", f"{t_first:.4f}", "-i", path, "-an", "-frames:v", str(n),
            "-vf", f"fps=fps={rate}:start_time=0:round=near,"
                   "scale=in_range=tv:in_color_matrix=bt709:out_range=pc:threads=8,format=gbrp",
            "-f", "rawvideo", "-"]
    if nvenc_ok():
        venc = ["-c:v", "hevc_nvenc", "-preset", "p5", "-tune", "hq", "-rc", "vbr", "-cq", "17", "-b:v", "0",
                "-maxrate", "180M", "-bufsize", "360M", "-profile:v", "main10"]
    else:
        venc = ["-c:v", "libx265", "-preset", "medium", "-crf", "16", "-x265-params", "log-level=error"]
    ecmd = (["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gbrp10le", "-s", f"{W}x{H}",
             "-r", rate, "-i", "-",
             "-vf", "scale=in_range=pc:out_range=tv:out_color_matrix=bt709:threads=8,format=p010le"]
            + venc + ["-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                      "-tag:v", "hvc1", str(outp) + ".part.mp4"])
    dp = subprocess.Popen(dcmd, stdout=subprocess.PIPE, creationflags=NOWIN, bufsize=0)
    ep = subprocess.Popen(ecmd, stdin=subprocess.PIPE, creationflags=NOWIN, bufsize=0)
    fsz = W * H * 3
    tt = t_first + np.arange(n) / fps
    pool = ThreadPoolExecutor(max(2, min(12, (os.cpu_count() or 4) - 2)))

    def work(buf, t):
        base = base_for(t)
        planes = np.frombuffer(buf, np.uint8).reshape(3, H, W)
        out = np.empty((3, H, W), np.uint16)
        for c in range(3):
            np.take(lut, base[c] + planes[c], out=out[c])
        return out

    import queue
    t_start = time.time()
    q_out = queue.Queue(maxsize=16)
    count = {"read": 0, "done": 0}

    def reader():                                    # decode -> pool (keeps order through futures)
        for k in range(n):
            buf = bytearray(fsz)
            mv, got = memoryview(buf), 0
            while got < fsz:
                m = dp.stdout.readinto(mv[got:])
                if not m:
                    break
                got += m
            if got < fsz:
                break
            q_out.put(pool.submit(work, buf, tt[k]))
            count["read"] += 1
        q_out.put(None)

    def writer():
        while True:
            fut = q_out.get()
            if fut is None:
                break
            ep.stdin.write(memoryview(fut.result()).cast("B"))
            count["done"] += 1
            d = count["done"]
            if d % 90 == 0:
                sp = d / (time.time() - t_start)
                log(f"  {d}/{n} frames  ({sp:.1f} fps, ~{(n - d) / max(sp, 0.1) / 60:.1f} min left)")

    th = [threading.Thread(target=reader, daemon=True), threading.Thread(target=writer, daemon=True)]
    [x.start() for x in th]
    [x.join() for x in th]
    i = count["done"]
    ep.stdin.close(); ep.wait(); dp.wait()
    if ep.returncode != 0 or not os.path.exists(str(outp) + ".part.mp4"):
        raise SystemExit("encoding failed")
    os.replace(str(outp) + ".part.mp4", outp)
    make_preview(path, info, keys, R, strength, prev, t_mid=(t_first + t_last) / 2)
    json.dump({"source": os.path.abspath(path), "first_frame": f0, "last_frame": f1, "frames_written": i,
               "strength": strength, "fps": fps, "score": round(float(np.mean(scores)), 2),
               "made": time.strftime("%Y-%m-%d %H:%M")}, open(meta, "w"), indent=1)
    log(f"done: {outp.name}  ({i} frames, {(time.time() - t_start) / 60:.1f} min)")
    return str(outp), f0, f1


_NV = None


def nvenc_ok():
    global _NV
    if _NV is None:
        r = run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=s=256x256:d=0.1", "-c:v", "hevc_nvenc",
                 "-profile:v", "main10", "-pix_fmt", "p010le", "-f", "null", "-"])
        _NV = r.returncode == 0
    return _NV


# ---------------------------------------------------------------- preview / scan
def frame_at(path, t, width):
    info = probe(path)
    h = int(round(info["h"] * width / info["w"] / 2)) * 2
    raw = run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{t:.2f}", "-i", path, "-frames:v", "1", "-vf",
               f"scale={width}:{h}:flags=area:in_range=tv:in_color_matrix=bt709:out_range=pc,format=rgb24",
               "-f", "rawvideo", "-"]).stdout
    return np.frombuffer(raw[:width * h * 3], np.uint8).reshape(h, width, 3)


def make_preview(path, info, keys, R, strength, out, t_mid):
    k = int(np.argmin(np.abs(keys - t_mid)))
    W = 960
    img = frame_at(path, keys[k], W)
    h = img.shape[0]
    rr = np.stack([np.asarray(Image.fromarray(R[k][..., c], "F").resize((W, h), Image.BILINEAR)) for c in range(3)], -1)
    lin = LIN8[img] - rr * strength
    after = (enc(np.clip(lin, 0, 1)) * 255 + 0.5).astype(np.uint8)
    plate = (enc(np.clip(rr * strength * 3, 0, 1)) * 255).astype(np.uint8)
    sheet = Image.new("RGB", (W * 3 + 40, h + 44), (7, 18, 43))
    for i, (im, lab) in enumerate(((img, "original"), (after, "cleaned"), (plate, "reflection removed (x3)"))):
        sheet.paste(Image.fromarray(im), (10 + i * (W + 10), 34))
        from PIL import ImageDraw
        ImageDraw.Draw(sheet).text((14 + i * (W + 10), 10), lab, fill=(244, 176, 62))
    sheet.save(out, quality=88)


def preview(path, at=None, strength=0.85, out=None, fast=False):
    info = probe(path)
    t = info["dur"] / 2 if at is None else at
    keys, R, scores = estimates(path, info, t, t, keyonly=fast, force=strength >= 0.99)
    trip = trip_of(path)
    od = Path(trip or Path(path).parent) / "_spp_clean"
    od.mkdir(exist_ok=True)
    out = out or str(od / f"{Path(path).stem}__preview_{int(t)}s.jpg")
    make_preview(path, info, keys, R, strength, out, t)
    print(json.dumps({"preview": out, "score": round(scores[0], 2)}))
    return out


def scan(folder):
    """Score every video in a trip: how much still reflection sits over moving scenery (0 none .. 10+ strong)."""
    folder = Path(folder)
    look = folder / "Footage" if (folder / "Footage").is_dir() else folder     # a trip: only its footage, not renders
    vids = sorted(p for p in look.rglob("*") if p.suffix.lower() in (".mp4", ".mov") and "_spp_" not in str(p))
    od = (folder if (folder / "Footage").is_dir() else Path(trip_of(str(folder)) or folder)) / "_spp_clean"
    od.mkdir(parents=True, exist_ok=True)
    cache_p = od / "scan.json"
    cache = json.load(open(cache_p, encoding="utf-8")) if cache_p.exists() else {}
    for i, p in enumerate(vids):
        key = str(p)
        st = p.stat()
        if key in cache and cache[key].get("mtime") == int(st.st_mtime):
            continue
        try:
            info = probe(key)
            if info["dur"] < 4:
                cache[key] = {"mtime": int(st.st_mtime), "score": 0, "note": "too short"}
                continue
            fr, w, h = read_small(key, 0, info["dur"], info, width=320, keyonly=True)
            if len(fr) < 12:
                fr, w, h = read_small(key, 0, info["dur"], info, fps=min(3.0, 120 / info["dur"]), width=320)
            s = pattern(fr, step=1)[3] if len(fr) >= 12 else 0.0
            cache[key] = {"mtime": int(st.st_mtime), "score": round(s, 2), "dur": round(info["dur"], 1)}
            print(f"[{i + 1}/{len(vids)}] {p.name}: {s:.1f}", flush=True)
        except Exception as e:
            cache[key] = {"mtime": int(st.st_mtime), "score": 0, "note": str(e)[:120]}
        if i % 10 == 0:
            json.dump(cache, open(cache_p, "w", encoding="utf-8"), indent=0)
    json.dump(cache, open(cache_p, "w", encoding="utf-8"), indent=0)
    rows = sorted(((v.get("score", 0), k) for k, v in cache.items() if os.path.exists(k)), reverse=True)
    with open(od / "reflection_report.csv", "w", encoding="utf-8") as fh:
        fh.write("score,level,file\n")
        for s, k in rows:
            fh.write(f"{s},{level(s)},\"{k}\"\n")
    strong = [(s, k) for s, k in rows if s >= 1.5][:24]
    if strong:
        tiles = []
        for s, k in strong:
            try:
                im = Image.fromarray(frame_at(k, cache[k].get("dur", 10) / 2, 320))
                tiles.append((im, f"{s:.1f} {level(s)}  {Path(k).name}"))
            except Exception:
                pass
        from PIL import ImageDraw
        cols = 4
        th = max(t[0].height for t in tiles) + 22
        S = Image.new("RGB", (cols * 330, ((len(tiles) + cols - 1) // cols) * th), (7, 18, 43))
        for i, (im, lab) in enumerate(tiles):
            x, y = (i % cols) * 330 + 5, (i // cols) * th
            S.paste(im, (x, y + 20))
            ImageDraw.Draw(S).text((x, y + 4), lab, fill=(244, 176, 62))
        S.save(od / "reflection_sheet.jpg", quality=85)
    print(json.dumps({"report": str(od / "reflection_report.csv"), "clips": len(rows),
                      "strong": sum(1 for s, _ in rows if s >= 4), "some": sum(1 for s, _ in rows if 1.5 <= s < 4)}))


def level(s):
    return "strong" if s >= 4 else "some" if s >= 1.5 else "little" if s >= 0.6 else "none"


def trip_of(path):
    d = Path(path).resolve().parent
    for p in [d] + list(d.parents):
        if (p / "Footage").is_dir():
            return str(p)
    return None


# ---------------------------------------------------------------- job queue from Resolve
def jobs(jpath):
    jp = Path(jpath)
    J = json.load(open(jp, encoding="utf-8"))
    status = jp.with_suffix(".status.json")
    logf = open(str(jp)[:-5] + "_log.txt", "a", encoding="utf-8")

    def say(s):
        print(s, flush=True)
        logf.write(s + "\n"); logf.flush()

    def save():
        json.dump(J, open(status, "w", encoding="utf-8"), indent=1)

    for k, job in enumerate(J["jobs"]):
        if job.get("state") == "done" and os.path.exists(job.get("output", "")):
            continue
        job["state"] = "working"; save()
        say(f"\n[{k + 1}/{len(J['jobs'])}] {Path(job['file']).name}  frames {job['in']}-{job['out']}")
        try:
            outp, f0, f1 = clean(job["file"], job["in"], job["out"], job.get("strength", 0.85), job.get("fps"),
                                 log=say)
            job.update(state="done", output=outp, first_frame=f0, last_frame=f1)
        except BaseException as e:
            job.update(state="failed", error=str(e)[:300])
            say(f"  failed: {e}")
        save()
    J["finished"] = time.strftime("%H:%M")
    save()
    say("\nAll done. In Resolve run  Workspace > Scripts > Safar Pahad Parivar > Reflection - Clean Selected Clips  again"
        " to put the cleaned clips on the timeline.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("clean"); c.add_argument("file"); c.add_argument("--in", dest="tin", type=float)
    c.add_argument("--out", dest="tout", type=float); c.add_argument("--strength", type=float, default=0.85)
    c.add_argument("--frames", action="store_true", help="--in/--out are frame numbers, not seconds")
    c.add_argument("--fps", type=float, help="frame rate Resolve uses for the clip (default: guessed)")
    p = sub.add_parser("preview"); p.add_argument("file"); p.add_argument("--at", type=float)
    p.add_argument("--strength", type=float, default=0.85); p.add_argument("--out")
    p.add_argument("--fast", action="store_true", help="look at key frames only (a few seconds instead of ~20)")
    s = sub.add_parser("scan"); s.add_argument("folder")
    j = sub.add_parser("jobs"); j.add_argument("jobs")
    a = ap.parse_args()
    if a.cmd == "clean":
        fps = a.fps or guess_fps(probe(a.file))
        conv = (lambda v: v) if a.frames else (lambda v: None if v is None else int(round(v * fps)))
        clean(a.file, conv(a.tin), conv(a.tout), a.strength, fps)
    elif a.cmd == "preview":
        preview(a.file, a.at, a.strength, a.out, a.fast)
    elif a.cmd == "scan":
        scan(a.folder)
    else:
        jobs(a.jobs)


if __name__ == "__main__":
    main()
