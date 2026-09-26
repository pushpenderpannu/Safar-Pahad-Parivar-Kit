<#
  Safar Pahad Parivar - download (once) / update the recorded instruments used by the Strings sounds and the music:
  VSCO-2 Community Edition (CC0 public domain) - strings, flute, upright piano, harp, glockenspiel, marimba, timpani, gong, bells.
  Only the folders the kit uses are fetched (~1.1 GB) into Source\_vsco (not in git).  Called by make_sfx.ps1 and make_music.ps1.
#>
$ErrorActionPreference = "Stop"
$Kit = Split-Path $PSScriptRoot -Parent
$vs = Join-Path $Kit "Source\_vsco"
$sp = @("/Strings/Violin Section/", "/Strings/Solo Violin/", "/Strings/Viola Section/", "/Strings/Cello Section/",
        "/Strings/Solo Contrabass/", "/Strings/Harp/", "/Percussion/Timpani/", "/Percussion/gongHit_*",
        "/Percussion/susCymb1-cresc-*", "/Percussion/susCymb1-bow-*", "/Percussion/BDrumNewhit_*",
        "/Percussion/Triangle3-Hit_*", "/Miscellania Raw/Misc 2/NepaleseBells/", "/LICENSE",
        "/Woodwinds/Flute/", "/Keys/Upright Piano/Player_dyn1_*", "/Keys/Upright Piano/Player_dyn2_*",
        "/Keys/Upright Piano/MappingChart.txt", "/Keys/Upright Piano/Info.txt", "/Percussion/Glock/", "/Percussion/Marimba/",
        "/Percussion/Xylo/", "/VSCO 1 Percussion/drums/snare/drum1/", "/VSCO 1 Percussion/drums/other/Bongos/",
        "/VSCO 1 Percussion/varWood/")
if (-not (Test-Path (Join-Path $vs ".git"))) {
  Write-Host "Downloading recorded instruments (VSCO-2 CE, public domain) - one time, ~1.1 GB..."
  git clone --filter=blob:none --no-checkout https://github.com/sgossner/VSCO-2-CE.git $vs
  git -C $vs sparse-checkout init --no-cone
}
$f = Join-Path $vs ".git\info\sparse-checkout"
$have = if (Test-Path $f) { Get-Content $f } else { @() }
$need = $sp | Where-Object { $have -notcontains $_ }
if ($need -or -not (Test-Path (Join-Path $vs "Woodwinds\Flute"))) {
  Write-Host "Fetching instruments: $($need -join ', ')"
  Set-Content -Path $f -Value $sp -Encoding ASCII
  git -C $vs checkout master
  git -C $vs sparse-checkout reapply
}
