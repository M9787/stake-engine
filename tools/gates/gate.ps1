<#
.SYNOPSIS
  Run every quality gate for one game and write build\<Game>\reports\gate.json (docs/10 section 8, plan v3.3 M11).
.DESCRIPTION
  -Fast    skips the slow math checks (snapshot verify, math stats) and the full e2e replay suite.
  -PreArt  art completeness (precheck art, sample assets, bundle budget) is reported but not failed:
           for a game whose owner art is not in yet (Oracle before M6d, test skins).
  Every step runs even after a failure; the exit code is 1 if any enforced step failed.
  Factory mode: the game's release.mode (game.json; missing = release; tools\gamedef\mode.py) is passed to the
  precheck step (--mode) and recorded as "mode" in gate.json. tools\package.ps1 needs a gate run in the game's mode.
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tools\gates\gate.ps1 -Game seventh_veil -PreArt
#>
param(
    [Parameter(Mandatory = $true)][string]$Game,
    [switch]$Fast,
    [switch]$PreArt
)
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$py = Join-Path $root 'math-sdk\env\Scripts\python.exe'
$vpy = Join-Path $root '.venv-assets\Scripts\python.exe'
$skinDir = (Get-ChildItem (Join-Path $root 'skins\*\game.json') | Where-Object { (Get-Content $_.FullName -Raw | ConvertFrom-Json).identity.gameId -eq $Game } | Select-Object -First 1).Directory
if (-not $skinDir) { Write-Host "FAIL: no skin with gameId $Game"; exit 1 }
$hasReference = (Test-Path (Join-Path $root "tools\golden\reference\$Game")) -or (Test-Path (Join-Path $root "game\math\$Game"))
$golden = Join-Path $skinDir.FullName 'golden.lock.json'
$gameDef = Get-Content (Join-Path $skinDir.FullName 'game.json') -Raw | ConvertFrom-Json
$mode = if ($gameDef.PSObject.Properties['release'] -and $gameDef.release.mode -eq 'test') { 'test' } else { 'release' }
Write-Host "gate $Game in $mode mode"
$results = @()

function Step([string]$name, [string]$tier, [bool]$enforced, [scriptblock]$cmd) {
    if ($Fast -and $tier -eq 'full') { $script:results += [pscustomobject]@{ step = $name; status = 'skipped'; seconds = 0; detail = '-Fast' }; return }
    $t0 = Get-Date
    $out = & $cmd 2>&1 | Out-String
    $code = $LASTEXITCODE
    $secs = [math]::Round(((Get-Date) - $t0).TotalSeconds, 1)
    # A tool that exits 0 but prints WARN lines broke only our own rules (core\policy.v1.json level 'ours').
    $warns = @($out -split "`n" | Where-Object { $_.TrimStart() -match '^WARN\b' }).Count
    $status = if ($code -eq 0) { if ($warns) { 'warn' } else { 'pass' } } elseif ($enforced) { 'FAIL' } else { 'todo' }
    $last = ($out.Trim() -split "`n" | Where-Object { $_.Trim() } | Select-Object -Last 1)
    $script:results += [pscustomobject]@{ step = $name; status = $status; seconds = $secs; warnings = $warns; detail = "$last".Trim() }
    Write-Host ("{0,-5} {1,-28} {2,6}s  {3}" -f $status, $name, $secs, "$last".Trim())
}

Push-Location $root
$env:GAME = $Game
Step 'sync' 'fast' $true { powershell -ExecutionPolicy Bypass -File scripts\sync.ps1 -Game $Game }
Step 'validate game.json' 'fast' $true { & $py tools\gamedef\validate.py (Join-Path $skinDir.FullName 'game.json') }
Step 'lint_skin' 'fast' $true { & $py tools\lint_skin.py --game $Game }
Step 'lint_core' 'fast' $true { & $py tools\lint_core.py }
Step 'generated files current' 'fast' $true { & $py tools\gen\check_generated.py --game $Game }
Step 'static folder current' 'fast' $true { & $py tools\gen\gen_web_static.py --game $Game --check }
Step 'asset prompts' 'fast' $true { & $py tools\assets\prompts.py --game $Game --check }
Step 'contract (books->handlers)' 'fast' $true { & $py scripts\books_to_stories.py --game $Game --check }
if ($hasReference) {
    Step 'config = reference' 'fast' $true { & $py tools\golden\compare_config.py $Game }
    Step 'books = reference (quick)' 'fast' $true { $env:PYTHONHASHSEED = '0'; Push-Location math-sdk; & $py ..\tools\golden\quick_books.py $Game 20; Pop-Location }
}
if (Test-Path $golden) {
    Step 'golden snapshot verify' 'full' $true { $env:PYTHONHASHSEED = '0'; & $py tools\golden\snapshot.py $Game --verify $golden }
}
Step 'math stats (critical tests)' 'full' $true { & $py scripts\math_stats.py $Game --brief }
Step 'currency formatting' 'fast' $true { node --experimental-strip-types scripts\check_amount.ts }
Step 'web build' 'fast' $true { powershell -ExecutionPolicy Bypass -File tools\web_build.ps1 -Game $Game }
Step 'no external URLs' 'fast' $true { powershell -ExecutionPolicy Bypass -File scripts\check_external_urls.ps1 -Game $Game }
Step 'no sample assets' 'fast' (-not $PreArt) { powershell -ExecutionPolicy Bypass -File tools\check_sample_assets.ps1 -Game $Game }
Step 'bundle budget' 'fast' (-not $PreArt) { & $py tools\gates\bundle_budget.py --game $Game }
Step 'licence audit (prod deps)' 'fast' $true { & $py tools\gates\licence_audit.py }
$testOnly = [bool](Get-Content (Join-Path $skinDir.FullName 'game.json') -Raw | ConvertFrom-Json).identity.testOnly
if ($testOnly) {
    $results += [pscustomobject]@{ step = 'package precheck'; status = 'skipped'; seconds = 0; detail = 'identity.testOnly: never packaged' }
} else {
    Step 'package precheck' 'full' $true { if ($PreArt) { & $py tools\assets\precheck.py --game $Game --mode $mode --pre-art } else { & $py tools\assets\precheck.py --game $Game --mode $mode } }
}
$e2eSpecs = if ($Fast) { 'm6c baseline' } else { 'm6c baseline replay' }
# A new game has no screenshot baselines yet: capture them on its first check and warn (review them in
# tools\e2e\baselines\<game>\), instead of failing every screenshot test.
$baseDir = Join-Path $root "tools\e2e\baselines\$Game"
$missing = @('1280x720', '1200x675', '400x225', '425x812') | Where-Object { -not (Test-Path (Join-Path $baseDir "$_.png")) }
if ($missing) {
    Step 'screenshot baselines (first run)' 'fast' $true { Push-Location tools\e2e; cmd /c "pnpm exec playwright test baseline --update-snapshots 2>&1"; $code = $LASTEXITCODE; Pop-Location; if ($code -eq 0) { Write-Output "WARN  [baselines.new] first screenshots captured in tools\e2e\baselines\$Game - review them once" }; $global:LASTEXITCODE = $code }
}
# cmd /c: the PowerShell pnpm shim mangles array arguments (test filters arrive empty).
# JSON reporter: per-test results in build\<Game>\reports\e2e.json for tools\release\checklist.py.
$env:PLAYWRIGHT_JSON_OUTPUT_NAME = Join-Path $root "build\$Game\reports\e2e.json"
Step "e2e ($e2eSpecs)" 'fast' $true { New-Item -ItemType Directory -Force (Split-Path $env:PLAYWRIGHT_JSON_OUTPUT_NAME) | Out-Null; Push-Location tools\e2e; cmd /c "pnpm exec playwright test $e2eSpecs --reporter=list,json 2>&1"; $code = $LASTEXITCODE; Pop-Location; $global:LASTEXITCODE = $code }
Pop-Location

$report = Join-Path $root "build\$Game\reports"
New-Item -ItemType Directory -Force $report | Out-Null
$failed = @($results | Where-Object { $_.status -eq 'FAIL' }).Count
$warnings = (@($results | ForEach-Object { if ($_.PSObject.Properties['warnings']) { [int]$_.warnings } else { 0 } }) | Measure-Object -Sum).Sum
[pscustomobject]@{
    game = $Game; mode = $mode; date = (Get-Date).ToString('s'); fast = [bool]$Fast; preArt = [bool]$PreArt
    gitHead = (git -C $root rev-parse --short HEAD); failed = $failed; warnings = [int]$warnings; steps = $results
} | ConvertTo-Json -Depth 4 | Set-Content -Encoding utf8 (Join-Path $report 'gate.json')
Write-Host ("{0}: gate {1} [{4} mode] ({2} failed, {3} warning(s), report build\{1}\reports\gate.json)" -f $(if ($failed) { 'FAIL' } else { 'OK' }), $Game, $failed, [int]$warnings, $mode)
exit $(if ($failed) { 1 } else { 0 })
