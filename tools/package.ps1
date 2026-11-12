<#
.SYNOPSIS
  Package one game for Stake Engine upload: release\<Game>\<version>\ (release mode) or
  release\<Game>\<version>-test\ (test mode) (docs/10 plan v3.3 M11, Factory v3).
.DESCRIPTION
  Factory mode = game.json release.mode (missing = release; tools\gamedef\mode.py). Test mode allows any assets and
  skips our release-only art rules (core\policy.v1.json "modes"), but every Stake rule still applies: the folder is a
  real Studio upload set and may be submitted for review.
  1. tools\assets\precheck.py --mode <mode> (Stake-level rules active in the mode block: sims, testOnly, tiles, and
     test assets in release mode; our own rules only warn). Refuses on failure.
  2. Needs the last gate run (tools\gates\gate.ps1) to be full (no -Fast, no -PreArt), in the game's mode, 0 failures.
  3. Fresh web build (tools\web_build.ps1).
  4. tools\release\pack.py (submission pack). Refuses when the pack has a Stake-level blocker.
  5. Copies math publish files and the front end into the release folder {math,front}, tiles into tiles\.
  6. Writes manifest.json (mode, shas, pins, SDK SHAs, core version, gate report), UPLOAD.md (the Stake Studio
     upload steps) and copies build\<Game>\pack\* (submission.html, submission.md, pack.json, reports, shots).
  release\ is git-ignored except manifest.json and submission.md.
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
$mode = if ($gdef.PSObject.Properties['release'] -and $gdef.release.mode -eq 'test') { 'test' } else { 'release' }
Write-Host "package $Game $version in $mode mode"

& $py (Join-Path $root 'tools\assets\precheck.py') --game $Game --mode $mode
if ($LASTEXITCODE -ne 0) { Write-Host "REFUSED: precheck failed for $Game in $mode mode (fix the FAIL items above, then rerun)"; exit 1 }
$gate = Join-Path $root "build\$Game\reports\gate.json"
if (-not (Test-Path $gate)) { Write-Host "REFUSED: no gate report; run tools\gates\gate.ps1 -Game $Game first"; exit 1 }
$gateData = Get-Content $gate -Raw | ConvertFrom-Json
if ($gateData.failed -gt 0 -or $gateData.fast -or $gateData.preArt) { Write-Host "REFUSED: the last gate run must be a full run (no -Fast, no -PreArt) with 0 failures"; exit 1 }
$gateMode = if ($gateData.PSObject.Properties['mode'] -and $gateData.mode) { $gateData.mode } else { 'release' }
if ($gateMode -ne $mode) { Write-Host "REFUSED: the last gate ran in $gateMode mode but $Game is in $mode mode; rerun tools\gates\gate.ps1 -Game $Game"; exit 1 }

powershell -ExecutionPolicy Bypass -File (Join-Path $root 'tools\web_build.ps1') -Game $Game
if ($LASTEXITCODE -ne 0) { exit 1 }

# Submission pack from the fresh build (never --dry-run here). Exit 1 = a Stake-level blocker.
& $py (Join-Path $root 'tools\release\pack.py') --game $Game
if ($LASTEXITCODE -ne 0) { Write-Host "REFUSED: the submission pack lists Stake-level blockers (see BLOCK lines above or build\$Game\pack\submission.html)"; exit 1 }

$folder = if ($mode -eq 'test') { "$version-test" } else { $version }
$out = Join-Path $root "release\$Game\$folder"
if (Test-Path $out) { throw "release\$Game\$folder already exists: bump identity.version in game.json for a new release" }
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
    game = $Game; version = $version; mode = $mode; displayName = $gdef.identity.displayName; date = (Get-Date).ToString('s')
    core = [ordered]@{ family = $gdef.core.family; version = $gdef.core.version; gitDescribe = (git -C $root describe --always --dirty) }
    sdk = [ordered]@{ web = (git -C (Join-Path $root 'web-sdk') rev-parse HEAD); math = (git -C (Join-Path $root 'math-sdk') rev-parse HEAD) }
    gameJsonSha256 = (Get-FileHash (Join-Path $skinDir.FullName 'game.json')).Hash.ToLower()
    pins = $(if (Test-Path $golden) { (Get-Content $golden -Raw | ConvertFrom-Json).pins } else { $null })
    gate = [ordered]@{ date = $gateData.date; gitHead = $gateData.gitHead; failed = $gateData.failed; mode = $gateMode }
    math = @(ShaList "$out\math"); front = @(ShaList "$out\front"); tiles = @(ShaList "$out\tiles")
}
# Art sign-off is a release-mode record (test mode has no licence or sign-off output).
if ($mode -eq 'release') { $manifest.Insert(9, 'artSignoff', $(if (Test-Path $signoff) { Get-Content $signoff -Raw | ConvertFrom-Json } else { $null })) }
$manifest | ConvertTo-Json -Depth 6 | Set-Content -Encoding utf8 "$out\manifest.json"

# UPLOAD.md: the Stake Studio steps for this folder (owner's steps 2026-11-07; Start Sync from docs/05-publish.md).
$mathFiles = @(Get-ChildItem "$out\math" -File | ForEach-Object { $_.Name })
$tileFiles = @(Get-ChildItem "$out\tiles" -File -Filter *.png -ErrorAction SilentlyContinue | ForEach-Object { "tiles\$($_.Name)" })
$modeNote = if ($mode -eq 'test') {
    "Mode: TEST (factory test mode). Any assets were allowed and no licence checks ran, but every Stake rule was checked: this is a real upload set and may be submitted for review. 'TEST' appears only in this file and manifest.json, never in the game."
} else { 'Mode: RELEASE (every rule checked).' }
$upload = @"
# Upload $($gdef.identity.displayName) $version to Stake Engine

$modeNote

Folder: release\$Game\$folder. Use a Chromium browser (Chrome or Edge) for the Studio uploads.

## 1. Math
1. Stake Studio > your game > **Files** > **Import files** > **Math**.
2. Open the ``math`` folder and select **all of its contents** (not the folder itself): ``index.json``, the books files and the lookup CSVs ($($mathFiles.Count) files: $($mathFiles -join ', ')).
3. Press **Start Sync** and wait until it finishes.

## 2. Front end
1. **Files** > **Import files** > **Front end**.
2. Select the **whole ``front`` folder** (folder upload, Chromium browser).
3. Press **Start Sync** and wait until it finishes.

## 3. Publish
1. **Publish new version** for the **math**.
2. **Publish new version** for the **front end**.
3. Note the math version number: reviewer replay links need it (Submit page > Pick event IDs).

## 4. Test privately
1. Click **Play Game** in the sidebar. This is a private test, not visible to players.
2. Play one round in every mode ($(@($gdef.modes | ForEach-Object { $_.name }) -join ', ')) and one replay.
3. In the play modal, switch the **Social Mode** toggle on and play once more: no restricted words may appear.

## 5. Tile and cover
1. Open the **Media Editor**.
2. Make the 3:4 tile and the 16:9 cover from the source images in ``tiles\`` ($(if ($tileFiles.Count) { $tileFiles -join ', ' } else { 'none found' })).

## 6. Submit
Only when every step above is done and submission.html (this folder) says "Ready": fill the Studio form from section 1 of submission.html and press **Submit**.
"@
Set-Content -Encoding utf8 -Path "$out\UPLOAD.md" -Value $upload
# Submission documents: the pack written by tools\release\pack.py above.
Copy-Item (Join-Path $root "build\$Game\pack\*") $out -Recurse
Write-Host "OK: release\$Game\$folder [$mode mode] (math, front, tiles, manifest.json, UPLOAD.md, submission.html/.md, pack.json)"
