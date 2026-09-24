<#
  Safar Pahad Parivar - create the standard folder set for a new video.

  Usage:
      .\Tools\new_video.ps1 -Name "2026-06 Dharchula Panchachuli"
      .\Tools\new_video.ps1 -Name "2026-10 Chopta Tungnath" -Root "F:\Video Editing\Projects"
#>
param(
  [Parameter(Mandatory = $true)][string]$Name,
  [string]$Root = (Join-Path (Split-Path $PSScriptRoot -Parent | Split-Path -Parent) "Projects")
)
$ErrorActionPreference = "Stop"
$P = Join-Path $Root $Name
$dirs = @(
  "01_Footage",            # dump camera/phone files here, then run Tools\spp_sort_media.py on it
  "02_Audio\VO", "02_Audio\Music", "02_Audio\SFX",
  "03_Graphics",           # thumbnails, maps, stills made for this video
  "04_Exports",            # final renders (YouTube, Shorts)
  "05_Resolve",            # exported .drp project backups
  "06_Docs"                # script, VO text, notes, GPS data
)
foreach ($d in $dirs) { New-Item -ItemType Directory -Force -Path (Join-Path $P $d) | Out-Null }
Write-Host "Created: $P"
Write-Host @"

Next:
  1. Copy footage into 01_Footage, then sort it:
       python "$(Join-Path $PSScriptRoot 'spp_sort_media.py')" "$(Join-Path $P '01_Footage')" --apply
  2. In Resolve: new project named "$Name"
       Workspace > Scripts > Safar Pahad Parivar > New Timeline - YouTube 16x9
       Workspace > Scripts > Safar Pahad Parivar > Import Brand Graphics
  3. When done: File > Export Project -> save the .drp into 05_Resolve
"@
