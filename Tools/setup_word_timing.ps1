<#
  Safar Pahad Parivar - install ALL the kit's Python engines (run once per PC, and again if a guide step says so).
  Creates Tools\.venv with:
    - faster-whisper + NVIDIA CUDA libraries   -> caption word timing, moment finder speech (GPU)
    - numpy / scipy / pillow                   -> GPS, route maps, sound effects, music, key finder, distance, phone voice
    - torch (CPU) + PANNs + its 312 MB model   -> moment finder sound events (laughter, cheering, singing...)
  The speech model (~3 GB) downloads automatically on the first caption sync / moment analysis.

  Usage (PowerShell, from the kit folder):   .\Tools\setup_word_timing.ps1
#>
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$py = Join-Path $env:LOCALAPPDATA "Programs\Python\Python313\python.exe"; if (-not (Test-Path $py)) { $py = "python" }
if (-not (Test-Path ".venv\Scripts\python.exe")) { & $py -m venv .venv }
$v = ".\.venv\Scripts\python.exe"
& $v -m pip install --no-cache-dir faster-whisper numpy scipy pillow pillow-heif nvidia-cublas-cu12 "nvidia-cudnn-cu12==9.*"
& $v -m pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
& $v -m pip install --no-cache-dir panns-inference librosa

# PANNs sound-event model (resumes if the download is interrupted - Zenodo can be slow)
$code = @'
import os, time, urllib.request as u
d = os.path.join(os.path.expanduser("~"), "panns_data"); os.makedirs(d, exist_ok=True)
lab = os.path.join(d, "class_labels_indices.csv")
if not os.path.exists(lab) or os.path.getsize(lab) < 1000:
    u.urlretrieve("http://storage.googleapis.com/us_audioset/youtube_corpus/v1/csv/class_labels_indices.csv", lab)
ck = os.path.join(d, "Cnn14_mAP=0.431.pth"); part = ck + ".part"
url = "https://zenodo.org/records/3987831/files/Cnn14_mAP%3D0.431.pth?download=1"
for attempt in range(30):
    if os.path.exists(ck):
        break
    have = os.path.getsize(part) if os.path.exists(part) else 0
    try:
        req = u.Request(url, headers={"Range": "bytes=%d-" % have, "User-Agent": "SPP"})
        with u.urlopen(req, timeout=60) as r, open(part, "ab" if r.status == 206 else "wb") as f:
            while True:
                b = r.read(1 << 20)
                if not b:
                    break
                f.write(b)
                print("\r  sound-event model: %d MB" % (os.path.getsize(part) >> 20), end="", flush=True)
        if os.path.getsize(part) > 300e6:
            os.replace(part, ck)
    except Exception as e:
        print("\n  retrying (%s)" % e); time.sleep(5)
print("\n  sound-event model:", "ready" if os.path.exists(ck) else "NOT finished - run this script again")
'@
$tmp = Join-Path $env:TEMP "spp_panns_download.py"
Set-Content -Path $tmp -Value $code -Encoding UTF8      # (a file, because PowerShell mangles quotes in -c "...")
& $v $tmp
Write-Host "`nKit Python engines ready. Next: .\Tools\make_sfx.ps1 and .\Tools\make_music.ps1 (once), then use the menu scripts in Resolve."
