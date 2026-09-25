<#
  Safar Pahad Parivar - install the word-timing engine used by "Captions - Sync Words to VO".
  Creates Tools\.venv with faster-whisper (+ NVIDIA CUDA libraries for the GPU).
  The speech model (~3 GB) downloads automatically on the first run.

  Usage (PowerShell, from the kit folder):   .\Tools\setup_word_timing.ps1
#>
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$py = Join-Path $env:LOCALAPPDATA "Programs\Python\Python313\python.exe"; if (-not (Test-Path $py)) { $py = "python" }
if (-not (Test-Path ".venv\Scripts\python.exe")) { & $py -m venv .venv }
.\.venv\Scripts\python.exe -m pip install --no-cache-dir faster-whisper numpy nvidia-cublas-cu12 "nvidia-cudnn-cu12==9.*"
Write-Host "`nWord-timing engine ready. In Resolve: Workspace > Scripts > Safar Pahad Parivar > Captions - Sync Words to VO"
