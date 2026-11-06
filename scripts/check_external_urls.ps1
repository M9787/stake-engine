# check_external_urls.ps1 - fail if the frontend build references an external host.
# Stake Engine serves games as static files and forbids loading anything from outside the bundle.
# Scans the uploaded part of the build: .svelte-kit\output\client and \prerendered, plus the
# folders we actually upload when they exist: web-sdk\apps\<app>\build, build\<gameId>\dist and upload\front (docs/05 step 4).
# Allowed hosts appear only in licence headers and code comments of bundled libraries (not requests).
# Usage: powershell -ExecutionPolicy Bypass -File scripts\check_external_urls.ps1 [-Game <gameId>]
# Exit code: 0 = no external URLs, 1 = hits found or no build output.

param([string]$Game = 'seventh_veil')

$root = Split-Path -Parent $PSScriptRoot
# Same map as tools\gamedef\gamectx.py: games with a legacy app folder, else the core app (M10).
$legacy = @{ 'seventh_veil' = 'seventh-veil' }
$app = if ($legacy.ContainsKey($Game)) { $legacy[$Game] } else { 'cluster-tumble' }
$out = Join-Path $root "web-sdk\apps\$app\.svelte-kit\output"
if (-not (Test-Path $out)) { Write-Host "FAIL  no build output at $out"; exit 1 }
$scan = @((Join-Path $out 'client'), (Join-Path $out 'prerendered'))
foreach ($extra in @("web-sdk\apps\$app\build", "build\$Game\dist", 'upload\front')) {
    $dir = Join-Path $root $extra
    if (Test-Path $dir) { $scan += $dir; Write-Host "scan  $extra" }
}

# Strings that are not requests: XML namespaces, spec/licence/doc links inside library code,
# and the SvelteKit placeholder origin.
$allow = @(
    '^https?://www\.w3\.org/',
    '^https?://example\.com',
    '^https?://localhost',
    '^https?://(github\.com|svelte\.dev|kit\.svelte\.dev|pixijs\.com|reactjs\.org|developer\.mozilla\.org|tc39\.es|stately\.ai|lingui\.dev|opensource\.org|scripts\.sil\.org|fb\.me|g\.co|goo\.gl|bit\.ly|web\.dev|mathiasbynens\.be|jsperf\.com|www\.khronos\.org|registry\.khronos\.org|webglreport\.com|en\.wikipedia\.org|stackoverflow\.com|lodash\.com|npms\.io|openjsf\.org|underscorejs\.org|www\.opensource\.org|www\.pixijs\.com|www\.codeandweb\.com)(/|$)'
)

$hits = @{}
Get-ChildItem $scan -Recurse -File -Include *.js, *.html, *.css, *.json | ForEach-Object {
    $file = $_.FullName.Substring($root.Length + 1)
    foreach ($m in (Select-String -Path $_.FullName -Pattern 'https?://[A-Za-z0-9.\-]+[^\s"''`)<>]*' -AllMatches)) {
        foreach ($u in $m.Matches.Value) {
            if (-not ($allow | Where-Object { $u -match $_ })) {
                $host_ = ([uri]$u).Host
                if (-not $hits.ContainsKey($host_)) { $hits[$host_] = "$u  ($file)" }
            }
        }
    }
}

if ($hits.Count -eq 0) { Write-Host 'ok    no external URLs in build output'; exit 0 }
Write-Host "FAIL  $($hits.Count) external host(s):"
$hits.GetEnumerator() | Sort-Object Name | ForEach-Object { Write-Host "  $($_.Name): $($_.Value)" }
exit 1
