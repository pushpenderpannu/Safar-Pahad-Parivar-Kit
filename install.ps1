<#
  Safar Pahad Parivar - kit installer for DaVinci Resolve (Windows)

  Copies the kit's Resolve menu scripts and title templates into Resolve's
  user folders, and records where the kit lives so the scripts can find it.

  Usage (PowerShell, from the kit folder):
      .\install.ps1
  If scripts are blocked:  powershell -ExecutionPolicy Bypass -File .\install.ps1
#>
$ErrorActionPreference = "Stop"
$Kit     = $PSScriptRoot
$Fusion  = Join-Path $env:APPDATA "Blackmagic Design\DaVinci Resolve\Support\Fusion"
$SrcScr  = Join-Path $Kit "Resolve\Scripts"
$SrcTpl  = Join-Path $Kit "Resolve\Templates"
$DstScr  = Join-Path $Fusion "Scripts"
$DstTpl  = Join-Path $Fusion "Templates"

if (-not (Test-Path $Fusion)) { throw "Resolve user folder not found: $Fusion  (is DaVinci Resolve installed and run at least once?)" }

Write-Host "Kit:      $Kit"
Write-Host "Resolve:  $Fusion`n"

# Replace our own folders cleanly (never touches other scripts/templates)
$ours = @(
  @{ src = Join-Path $SrcScr "Utility\Safar Pahad Parivar";          dst = Join-Path $DstScr "Utility\Safar Pahad Parivar" },
  @{ src = Join-Path $SrcTpl "Edit\Titles\Safar Pahad Parivar";       dst = Join-Path $DstTpl "Edit\Titles\Safar Pahad Parivar" }
)
foreach ($o in $ours) {
  if (Test-Path $o.dst) { Remove-Item $o.dst -Recurse -Force }
  New-Item -ItemType Directory -Force -Path (Split-Path $o.dst) | Out-Null
  Copy-Item $o.src $o.dst -Recurse -Force
  $n = (Get-ChildItem $o.dst -Recurse -File).Count
  Write-Host ("Installed {0,3} files -> {1}" -f $n, $o.dst)
}

# Tell the menu scripts where the kit is (used by 'Import Brand Graphics')
Set-Content -Path (Join-Path $DstScr "Utility\Safar Pahad Parivar\kit_path.txt") -Value $Kit -Encoding UTF8
Write-Host "`nKit path recorded."

Write-Host @"

Done. Next:
  1. Restart DaVinci Resolve (it only scans title templates at start-up).
  2. Once: Workspace > Scripts > Safar Pahad Parivar > Setup Render Presets
  3. Titles appear under: Effects > Titles > Safar Pahad Parivar
"@
