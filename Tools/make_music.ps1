<#
  Safar Pahad Parivar - (re)build the background-music library into <kit>\Music  (~12 tracks, ~10-15 min).
  Composed in code (Source\music\music_gen.py) and played with recorded instruments (VSCO-2 CE, CC0) plus synthesised
  tanpura / temple bells / wind, so it is identical on every PC and not stored in git.
  Usage (PowerShell, kit folder):   .\Tools\make_music.ps1            (all)
                                    .\Tools\make_music.ps1 Bansuri    (only tracks whose name contains "Bansuri")
#>
param([string]$Only = "")
$ErrorActionPreference = "Stop"
$Kit = Split-Path $PSScriptRoot -Parent
$py = Join-Path $Kit "Tools\.venv\Scripts\python.exe"
if (-not (Test-Path $py)) { throw "Run .\Tools\setup_word_timing.ps1 first (installs the kit's Python tools)." }
& $py -c "import scipy" 2>$null; if ($LASTEXITCODE -ne 0) { & $py -m pip install --no-cache-dir scipy }
& (Join-Path $PSScriptRoot "get_samples.ps1")
$a = @((Join-Path $Kit "Source\music\music_gen.py"), "--out", (Join-Path $Kit "Music"), "--samples", (Join-Path $Kit "Source\_vsco"))
if ($Only) { $a += @("--only", $Only) }
& $py @a
Write-Host "`nDone. In Resolve: Workspace > Scripts > Safar Pahad Parivar > Music - Import Library"
