<#
  Safar Pahad Parivar - (re)build the sound-effects library into <kit>\SFX  (first time ~10 minutes incl. a one-time ~850 MB strings download).
  The sounds are generated from code (Source\sfx), so they are identical on every PC and not stored in git.
  Usage (PowerShell, kit folder):   .\Tools\make_sfx.ps1
#>
$ErrorActionPreference = "Stop"
$Kit = Split-Path $PSScriptRoot -Parent
$py = Join-Path $Kit "Tools\.venv\Scripts\python.exe"
if (-not (Test-Path $py)) { throw "Run .\Tools\setup_word_timing.ps1 first (installs the kit's Python tools)." }
& $py -c "import scipy" 2>$null; if ($LASTEXITCODE -ne 0) { & $py -m pip install --no-cache-dir scipy }

# Recorded instruments for the Strings set: VSCO-2 Community Edition (CC0 / public domain), strings + orchestral percussion only (~850 MB, once)
$vs = Join-Path $Kit "Source\_vsco"
if (-not (Test-Path (Join-Path $vs "LICENSE"))) {
  Write-Host "Downloading recorded strings (VSCO-2 CE, public domain) - one time, ~850 MB..."
  git clone --filter=blob:none --no-checkout https://github.com/sgossner/VSCO-2-CE.git $vs
  git -C $vs sparse-checkout init --no-cone
  $sp = @("/Strings/Violin Section/", "/Strings/Solo Violin/", "/Strings/Viola Section/", "/Strings/Cello Section/",
          "/Strings/Solo Contrabass/", "/Strings/Harp/", "/Percussion/Timpani/", "/Percussion/gongHit_*",
          "/Percussion/susCymb1-cresc-*", "/Percussion/susCymb1-bow-*", "/Percussion/BDrumNewhit_*",
          "/Percussion/Triangle3-Hit_*", "/Miscellania Raw/Misc 2/NepaleseBells/", "/LICENSE")
  Set-Content -Path (Join-Path $vs ".git\info\sparse-checkout") -Value $sp -Encoding ASCII
  git -C $vs checkout master
}
& $py (Join-Path $Kit "Source\sfx\sfx_gen.py") --out (Join-Path $Kit "SFX") --samples $vs
Write-Host "`nDone. In Resolve: Workspace > Scripts > Safar Pahad Parivar > SFX - Import Library"
