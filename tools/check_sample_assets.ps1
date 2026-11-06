<#
.SYNOPSIS
  Fail if a game ships any web-sdk sample asset (Stake: "sample assets are rejected"; docs/10 plan v3.3 M11).
.DESCRIPTION
  1. Hash match: every file in build\<Game>\web\static (and build\<Game>\dist if built) is compared by
     sha256 with every file under the SDK sample apps' static folders.
  2. Name scan: file names containing sample markers (MINING, mm_, MM_, SD2_, miningfont).
  Exit 0 = clean, 1 = sample asset found.
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tools\check_sample_assets.ps1 -Game seventh_veil
#>
param([Parameter(Mandatory = $true)][string]$Game)
$root = Split-Path -Parent $PSScriptRoot
$sampleApps = 'cluster', 'lines', 'ways', 'scatter', 'price', 'number-picker'
$sampleHashes = @{}
foreach ($app in $sampleApps) {
    $dir = Join-Path $root "web-sdk\apps\$app\static"
    if (-not (Test-Path $dir)) { continue }
    foreach ($f in Get-ChildItem $dir -Recurse -File) {
        $sampleHashes[(Get-FileHash $f.FullName -Algorithm SHA256).Hash] = "$app\" + $f.FullName.Substring($dir.Length + 1)
    }
}
$targets = @((Join-Path $root "build\$Game\web\static"), (Join-Path $root "build\$Game\dist")) | Where-Object { Test-Path $_ }
if (-not $targets) { Write-Host "FAIL: nothing to check for $Game (run scripts\sync.ps1 -Game $Game first)"; exit 1 }
$hits = @()
foreach ($t in $targets) {
    foreach ($f in Get-ChildItem $t -Recurse -File) {
        $rel = $f.FullName.Substring($root.Length + 1)
        $h = (Get-FileHash $f.FullName -Algorithm SHA256).Hash
        if ($sampleHashes.ContainsKey($h)) { $hits += "$rel  = sample $($sampleHashes[$h])" }
        elseif ($f.Name -cmatch '(MINING|mm_|MM_|SD2_|miningfont)') { $hits += "$rel  (sample name marker)" }
    }
}
$hits | Sort-Object -Unique | ForEach-Object { Write-Host "  $_" }
if ($hits) { Write-Host "FAIL: $(@($hits).Count) sample asset(s) in $Game ($($sampleHashes.Count) sample files checked)"; exit 1 }
Write-Host "OK: no sample assets in $Game ($($sampleHashes.Count) sample files checked)"
exit 0
