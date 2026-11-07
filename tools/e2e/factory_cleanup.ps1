# Remove what tests\factory.spec.ts leaves in the zz_smoke test skin (uploads, ingested files, lock,
# provenance, editor jobs, contact sheets), so zz_smoke is back on procedural fallbacks.
# Usage: powershell -ExecutionPolicy Bypass -File tools\e2e\factory_cleanup.ps1
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$skin = Join-Path $root 'skins\zz-smoke'
foreach ($p in 'art_in', 'assets', 'assets.lock.json', 'art_signoff.json') {
    $t = Join-Path $skin $p
    if (Test-Path $t) { Remove-Item -Recurse -Force $t }
}
foreach ($p in 'jobs', 'contact_land.png', 'contact_port.png', 'contact_all.png') {
    $t = Join-Path $root "build\zz_smoke\$p"
    if (Test-Path $t) { Remove-Item -Recurse -Force $t }
}
Write-Host 'ok    zz_smoke test assets removed'
