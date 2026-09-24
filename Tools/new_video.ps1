<#
  Safar Pahad Parivar - create the standard folders for a trip and a video in it.
  Footage lives once per TRIP; each VIDEO made from that trip gets its own folder + Resolve project.

  Usage:
      .\Tools\new_video.ps1 -Trip "2026-10 Chopta Tungnath" -Video "01 Main Film"
      .\Tools\new_video.ps1 -Trip "2026-10 Chopta Tungnath" -Video "02 Shorts"      # adds a video to an existing trip
#>
param(
  [Parameter(Mandatory = $true)][string]$Trip,
  [Parameter(Mandatory = $true)][string]$Video,
  [string]$Root = (Join-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) "Projects")
)
$ErrorActionPreference = "Stop"
$TripDir  = Join-Path $Root $Trip
$VideoDir = Join-Path $TripDir $Video
New-Item -ItemType Directory -Force -Path (Join-Path $TripDir "Footage") | Out-Null
foreach ($d in @("Audio\VO","Audio\Music","Audio\SFX","Graphics","Exports","Resolve","Resolve Media","Docs")) {
  New-Item -ItemType Directory -Force -Path (Join-Path $VideoDir $d) | Out-Null
}
Write-Host "Trip:  $TripDir"
Write-Host "Video: $VideoDir"
Write-Host @"

Next:
  1. Copy the trip's camera/phone files into:  $TripDir\Footage
     then sort them (dry run first, then --apply):
       python "$(Join-Path $PSScriptRoot 'spp_sort_media.py')" "$TripDir\Footage"
       python "$(Join-Path $PSScriptRoot 'spp_sort_media.py')" "$TripDir\Footage" --apply
  2. In Resolve: create a project named "$Video" (or a clear name), then
       File > Project Settings > Master Settings > Working Folders >
         Project media location  =  $VideoDir\Resolve Media
       Workspace > Scripts > Safar Pahad Parivar > New Timeline - YouTube 16x9
       Workspace > Scripts > Safar Pahad Parivar > Import Brand Graphics
  3. Music/SFX you download (e.g. Epidemic Sound): save into $VideoDir\Audio\...
  4. When done: File > Export Project -> save the .drp into $VideoDir\Resolve
"@
