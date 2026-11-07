<#
.SYNOPSIS
  Package one game for Stake Engine upload: release\<Game>\<version>\ (docs/10 plan v3.3 M11).
.DESCRIPTION
  1. tools\assets\precheck.py (Stake-level rules of core\policy.v1.json block: sims, testOnly, test assets, tiles;
     our own art rules only warn). Refuses on failure.
  2. Fresh web build (tools\web_build.ps1).
  3. Copies math publish files and the front end into release\<Game>\<version>\{math,front}, tiles into tiles\.
  4. tools\release\pack.py (submission pack: Studio form fields, modes, rules, reviewer event IDs, checklist,
     licences, screenshots, upload list). Refuses when the pack has a Stake-level blocker.
  5. Writes manifest.json (shas, pins, SDK SHAs, core version, gate report) and copies build\<Game>\pack\*
     (submission.html, submission.md, pack.json, reports, shots) into the release folder.
  Run the full gate first: tools\gates\gate.ps1 -Game <id>. release\ is git-ignored except manifest.json and submission.md.
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tools\package.ps1 -Game seventh_veil
#>
param([Parameter(Mandatory = $true)][string]$Game)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $root 'math-sdk\env\Scripts\python.exe'
$skinDir = (Get-ChildItem (Join-Path $root 'skins\*\game.json') | Where-Object { (Get-Content $_.FullName -Raw | ConvertFrom-Json).identity.gameId -eq $Game } | Select-Object -First 1).Directory
if (-not $skinDir) { throw "no skin with gameId $Game" }
$gdef = Get-Content (Join-Path $skinDir.FullName 'game.json') -Raw | ConvertFrom-Json
$version = $gdef.identity.version

& $py (Join-Path $root 'tools\assets\precheck.py') --game $Game
if ($LASTEXITCODE -ne 0) { Write-Host "REFUSED: precheck failed for $Game (fix the items above, then rerun)"; exit 1 }
$gate = Join-Path $root "build\$Game\reports\gate.json"
if (-not (Test-Path $gate)) { Write-Host "REFUSED: no gate report; run tools\gates\gate.ps1 -Game $Game first"; exit 1 }
$gateData = Get-Content $gate -Raw | ConvertFrom-Json
if ($gateData.failed -gt 0 -or $gateData.fast -or $gateData.preArt) { Write-Host "REFUSED: the last gate run must be a full run (no -Fast, no -PreArt) with 0 failures"; exit 1 }

powershell -ExecutionPolicy Bypass -File (Join-Path $root 'tools\web_build.ps1') -Game $Game
if ($LASTEXITCODE -ne 0) { exit 1 }

# Submission pack from the fresh build (never --dry-run here). Exit 1 = a Stake-level blocker.
& $py (Join-Path $root 'tools\release\pack.py') --game $Game
if ($LASTEXITCODE -ne 0) { Write-Host "REFUSED: the submission pack lists Stake-level blockers (see BLOCK lines above or build\$Game\pack\submission.html)"; exit 1 }

$out = Join-Path $root "release\$Game\$version"
if (Test-Path $out) { throw "release\$Game\$version already exists: bump identity.version in game.json for a new release" }
New-Item -ItemType Directory -Force "$out\math", "$out\front", "$out\tiles" | Out-Null
$publish = Join-Path $root "math-sdk\games\$Game\library\publish_files"
Copy-Item "$publish\*" "$out\math" -Recurse
Copy-Item (Join-Path $root "build\$Game\dist\*") "$out\front" -Recurse
if (Test-Path (Join-Path $skinDir.FullName 'tiles')) { Copy-Item (Join-Path $skinDir.FullName 'tiles\*') "$out\tiles" }

function ShaList($dir) {
    Get-ChildItem $dir -Recurse -File | Sort-Object FullName | ForEach-Object {
        [pscustomobject]@{ file = $_.FullName.Substring($dir.Length + 1).Replace('\', '/'); sha256 = (Get-FileHash $_.FullName).Hash.ToLower(); bytes = $_.Length }
    }
}
$golden = Join-Path $skinDir.FullName 'golden.lock.json'
$signoff = Join-Path $skinDir.FullName 'art_signoff.json'
$manifest = [ordered]@{
    game = $Game; version = $version; displayName = $gdef.identity.displayName; date = (Get-Date).ToString('s')
    core = [ordered]@{ family = $gdef.core.family; version = $gdef.core.version; gitDescribe = (git -C $root describe --always --dirty) }
    sdk = [ordered]@{ web = (git -C (Join-Path $root 'web-sdk') rev-parse HEAD); math = (git -C (Join-Path $root 'math-sdk') rev-parse HEAD) }
    gameJsonSha256 = (Get-FileHash (Join-Path $skinDir.FullName 'game.json')).Hash.ToLower()
    pins = $(if (Test-Path $golden) { (Get-Content $golden -Raw | ConvertFrom-Json).pins } else { $null })
    artSignoff = $(if (Test-Path $signoff) { Get-Content $signoff -Raw | ConvertFrom-Json } else { $null })
    gate = [ordered]@{ date = $gateData.date; gitHead = $gateData.gitHead; failed = $gateData.failed }
    math = @(ShaList "$out\math"); front = @(ShaList "$out\front"); tiles = @(ShaList "$out\tiles")
}
$manifest | ConvertTo-Json -Depth 6 | Set-Content -Encoding utf8 "$out\manifest.json"
# Submission documents: the pack written by tools\release\pack.py above.
Copy-Item (Join-Path $root "build\$Game\pack\*") $out -Recurse
Write-Host "OK: release\$Game\$version (math, front, tiles, manifest.json, submission.html/.md, pack.json)"
