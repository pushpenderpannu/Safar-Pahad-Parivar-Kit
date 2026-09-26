<#
  Safar Pahad Parivar - (re)build the sound-effects library into <kit>\SFX  (first time ~10 minutes incl. a one-time ~1.1 GB instruments download).
  The sounds are generated from code (Source\sfx), so they are identical on every PC and not stored in git.
  Usage (PowerShell, kit folder):   .\Tools\make_sfx.ps1
#>
$ErrorActionPreference = "Stop"
$Kit = Split-Path $PSScriptRoot -Parent
$py = Join-Path $Kit "Tools\.venv\Scripts\python.exe"
if (-not (Test-Path $py)) { throw "Run .\Tools\setup_word_timing.ps1 first (installs the kit's Python tools)." }
& $py -c "import scipy" 2>$null; if ($LASTEXITCODE -ne 0) { & $py -m pip install --no-cache-dir scipy }

# Recorded instruments for the Strings set (VSCO-2 Community Edition, CC0) - downloaded once into Source\_vsco
& (Join-Path $PSScriptRoot "get_samples.ps1")
$vs = Join-Path $Kit "Source\_vsco"
& $py (Join-Path $Kit "Source\sfx\sfx_gen.py") --out (Join-Path $Kit "SFX") --samples $vs
# real field recordings (rain, car, birds, water, temple) - CC0 from freesound, fetched once with Tools\spp_freesound.py
if (-not (Test-Path (Join-Path $Kit "Source\_cc0\manifest.json")) -and (Test-Path (Join-Path $PSScriptRoot "freesound_key.txt"))) {
  & $py (Join-Path $PSScriptRoot "spp_freesound.py")
}
& $py (Join-Path $Kit "Source\sfx\field_gen.py") --out (Join-Path $Kit "SFX")
& $py (Join-Path $Kit "Source\sfx\make_library_doc.py") (Join-Path $Kit "SFX\sfx_catalog.json") (Join-Path $Kit "Docs\SFX_Library.md")
Write-Host "`nDone. In Resolve: Workspace > Scripts > Safar Pahad Parivar > SFX - Import Library"
