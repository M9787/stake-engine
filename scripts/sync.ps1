# sync.ps1 - copy game source of truth (stake\game\) into the SDK clones.
# One direction only: edit in stake\game\, then run this. Generated output
# (math library\, web node_modules\, .svelte-kit\, static\, .mock-rgs\) in the clones is never touched.
# Usage: powershell -ExecutionPolicy Bypass -File scripts\sync.ps1 [-WhatIf]

param([switch]$WhatIf)

$root = Split-Path -Parent $PSScriptRoot
$pairs = @(
    @{ Src = 'game\math\seventh_veil'; Dst = 'math-sdk\games\seventh_veil'; Skip = @('library', '__pycache__') },
    @{ Src = 'game\web\seventh-veil';  Dst = 'web-sdk\apps\seventh-veil';   Skip = @('node_modules', '.svelte-kit', '.turbo', 'static', '.mock-rgs') }
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
if ($failed) { exit 1 }
exit 0
