# sync.ps1 - copy the source of truth into the SDK clones.
# Math (since M8, 2026-11-06): core\math\cluster_tumble + one generated shim per skins\*\game.json
# (tools\gen\gen_shim.py). game\math\seventh_veil is the hand-written reference, no longer synced.
# Web (since M10 slice 10.2b, 2026-11-07): ONE core app core\web\cluster-tumble -> web-sdk\apps\cluster-tumble.
# The skin comes in through the $skin alias (build\<gameId>\web), never through app code.
# One direction only: edit in stake\core\ or stake\skins\, then run this. Generated output
# (math library\, web node_modules\, .svelte-kit\, .mock-rgs\, build\) in the clones is never touched.
# Lockfile: web-sdk is not tracked here, so web-sdk\pnpm-lock.yaml is mirrored back to the tracked
# core\web\pnpm-lock.yaml after every sync (plan v3.3 E3). Order for any install: pnpm install -> sync -> doctor.
# Usage: powershell -ExecutionPolicy Bypass -File scripts\sync.ps1 [-Game <gameId>] [-WhatIf]

param([string]$Game = '', [switch]$WhatIf)

$root = Split-Path -Parent $PSScriptRoot
$pairs = @(
    @{ Src = 'core\web\cluster-tumble'; Dst = 'web-sdk\apps\cluster-tumble'; Skip = @('node_modules', '.svelte-kit', '.turbo', '.mock-rgs', 'build') }
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
$lock = Join-Path $root 'web-sdk\pnpm-lock.yaml'
$lockCopy = Join-Path $root 'core\web\pnpm-lock.yaml'
if (-not $WhatIf -and (Test-Path $lock)) {
    Copy-Item $lock $lockCopy -Force
    Write-Host "ok    web-sdk\pnpm-lock.yaml -> core\web\pnpm-lock.yaml (tracked copy)"
}
$py = Join-Path $root 'math-sdk\env\Scripts\python.exe'
if ($WhatIf) { Write-Host "skip  math core + shims (-WhatIf)" }
else {
    $shimArgs = @((Join-Path $root 'tools\gen\gen_shim.py'))
    if ($Game) { $shimArgs += @('--game', $Game) }
    & $py @shimArgs
    if ($LASTEXITCODE -ne 0) { Write-Host "FAIL  tools\gen\gen_shim.py"; $failed++ }
    # Skin data for the web app ($skin -> build\<gameId>\web, M10). Needs the game's math output.
    foreach ($g in Get-ChildItem (Join-Path $root 'skins\*\game.json')) {
        $id = (Get-Content $g.FullName -Raw | ConvertFrom-Json).identity.gameId
        if ($Game -and $id -ne $Game) { continue }
        $vpy = Join-Path $root '.venv-assets\Scripts\python.exe'
        if (Test-Path $vpy) { & $vpy (Join-Path $root 'tools\assets\audio.py') --game $id | Out-Null; if ($LASTEXITCODE -ne 0) { Write-Host "FAIL  tools\assets\audio.py --game $id"; $failed++ } }
        else { Write-Host "skip  audio sprite (asset tools missing: see PROJECT.md section 7)" }
        & $py (Join-Path $root 'tools\gen\gen_web_static.py') --game $id
        & $py (Join-Path $root 'tools\gen\gen_assets_ts.py') --game $id | Out-Null
        if ($LASTEXITCODE -ne 0) { Write-Host "FAIL  tools\gen\gen_web_static.py --game $id"; $failed++ }
        if (-not (Test-Path (Join-Path $root "math-sdk\games\$id\library\configs\config_fe_$id.json"))) {
            Write-Host "skip  skin data $id (no math output yet: build the math first)"; continue
        }
        & $py (Join-Path $root 'scripts\gen_fe_config.py') --game $id | Out-Null
        if ($LASTEXITCODE -ne 0) { Write-Host "FAIL  scripts\gen_fe_config.py --game $id"; $failed++ }
        foreach ($gen in @('gen_rules.py', 'gen_skin_ts.py')) {
            & $py (Join-Path $root "tools\gen\$gen") --game $id | Out-Null
            if ($LASTEXITCODE -ne 0) { Write-Host "FAIL  tools\gen\$gen --game $id"; $failed++ }
        }
        Write-Host "ok    skins -> build\$id\web (rules + skin.generated.ts)"
    }
}
if ($failed) { exit 1 }
exit 0
