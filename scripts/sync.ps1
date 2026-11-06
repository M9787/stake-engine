# sync.ps1 - copy the source of truth into the SDK clones.
# Math (since M8, 2026-11-06): core\math\cluster_tumble + one generated shim per skins\*\game.json
# (tools\gen\gen_shim.py). game\math\seventh_veil is the hand-written reference, no longer synced.
# Web: game\web\seventh-veil (until M10 moves it to core\web).
# One direction only: edit in stake\game\, then run this. Generated output
# (math library\, web node_modules\, .svelte-kit\, .mock-rgs\) in the clones is never touched.
# static\ (images, fonts, audio) is mirrored like source since 2026-10-28 (instruction 13).
# Usage: powershell -ExecutionPolicy Bypass -File scripts\sync.ps1 [-WhatIf]

param([switch]$WhatIf)

$root = Split-Path -Parent $PSScriptRoot
$pairs = @(
    @{ Src = 'game\web\seventh-veil';  Dst = 'web-sdk\apps\seventh-veil';   Skip = @('node_modules', '.svelte-kit', '.turbo', '.mock-rgs') }
)

$failed = 0
foreach ($p in $pairs) {
    $src = Join-Path $root $p.Src
    $dst = Join-Path $root $p.Dst
    if (-not (Test-Path $src)) { Write-Host "skip  $($p.Src) (not created yet)"; continue }
    $args = @($src, $dst, '/MIR', '/XD') + $p.Skip + @('/NJH', '/NJS', '/NP', '/NDL')
    if ($WhatIf) { $args += '/L' }
    robocopy @args | Where-Object { $_.Trim() } | ForEach-Object { Write-Host "  $_" }
    # robocopy: 0-7 = success, 8+ = failure
    if ($LASTEXITCODE -ge 8) { Write-Host "FAIL  $($p.Src) -> $($p.Dst) (robocopy $LASTEXITCODE)"; $failed++ }
    else { Write-Host "ok    $($p.Src) -> $($p.Dst)" }
}
$py = Join-Path $root 'math-sdk\env\Scripts\python.exe'
if ($WhatIf) { Write-Host "skip  math core + shims (-WhatIf)" }
else {
    & $py (Join-Path $root 'tools\gen\gen_shim.py')
    if ($LASTEXITCODE -ne 0) { Write-Host "FAIL  tools\gen\gen_shim.py"; $failed++ }
    # Skin data for the web app ($skin -> build\<gameId>\web, M10). Needs the game's math output.
    foreach ($g in Get-ChildItem (Join-Path $root 'skins\*\game.json')) {
        $id = (Get-Content $g.FullName -Raw | ConvertFrom-Json).identity.gameId
        if (-not (Test-Path (Join-Path $root "math-sdk\games\$id\library\configs\config_fe_$id.json"))) {
            Write-Host "skip  skin data $id (no math output yet: build the math first)"; continue
        }
        foreach ($gen in @('gen_rules.py', 'gen_skin_ts.py')) {
            & $py (Join-Path $root "tools\gen\$gen") --game $id | Out-Null
            if ($LASTEXITCODE -ne 0) { Write-Host "FAIL  tools\gen\$gen --game $id"; $failed++ }
        }
        Write-Host "ok    skins -> build\$id\web (rules + skin.generated.ts)"
    }
}
if ($failed) { exit 1 }
exit 0
