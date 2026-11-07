<#
.SYNOPSIS
  End-to-end proof of the factory editor (docs/10 plan v3.4): create a game from a template, apply a preset,
  fill test assets, run the build chain, the fast check, the submission pack, and confirm packaging refuses
  test assets. Drives the editor API exactly like its pages. Needs the editor running on 127.0.0.1:5174.
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tools\e2e\factory_flow.ps1 -Game zz_hands_on [-Keep]
#>
param([string]$Game = 'zz_hands_on', [switch]$Keep)
$ErrorActionPreference = 'Stop'
$E = 'http://127.0.0.1:5174'
$H = @{ Origin = $E }
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

function Post($path, $body) { Invoke-RestMethod -Method Post -Uri "$E$path" -Headers $H -ContentType 'application/json' -Body ($body | ConvertTo-Json -Depth 6) }
function RunJob($tool, $opts = @{}) {
    $t0 = Get-Date
    $job = Post "/api/game/$Game/jobs" @{ tool = $tool; opts = $opts }
    WaitJob $job $tool $t0
}
function WaitJob($job, $tool, $t0) {
    do { Start-Sleep -Milliseconds 1500; $j = (Invoke-RestMethod "$E/api/jobs/$($job.id)").job } while ($j.status -eq 'running')
    $secs = [math]::Round(((Get-Date) - $t0).TotalSeconds)
    "{0,-6} {1,-18} {2,5}s  {3}" -f $j.status, $tool, $secs, $j.plain
    if ($j.status -ne 'done') { throw "$tool $($j.status): $($j.plain)" }
}

"== create $Game from zz-smoke"
$r = Post '/api/games' @{ template = 'zz-smoke'; id = $Game; displayName = 'Hands On' }
"created $($r.id); validation ok=$($r.validation.ok)"
$t0 = Get-Date
$p = Post "/api/game/$Game/setup/preset" @{ preset = @{ board = '6x6'; volatility = 'medium'; wincap = 5000; bonusOneIn = 400; modes = @('base', 'ante', 'buy') } }
WaitJob $p.job 'apply_preset' $t0
$v = Invoke-RestMethod "$E/api/game/$Game/validate"
"validate: ok=$($v.ok) errors=$($v.errors.Count) warnings=$($v.warnings.Count)"
foreach ($step in 'sync', 'math_preview', 'sync', 'mock', 'test_assets', 'sync', 'web_build') { RunJob $step }
Post "/api/game/$Game/math-state" @{ stamp = $true } | Out-Null
$ms = Invoke-RestMethod "$E/api/game/$Game/math-state"
"math state: tier=$($ms.tier) stale=$($ms.stale)"
RunJob 'gate_fast'
RunJob 'event_ids' @{ version = '1' }
RunJob 'pack'
$pack = Invoke-RestMethod "$E/api/game/$Game/pack"
"pack: ready=$($pack.ready) blockers=$($pack.blockers.Count) warnings=$($pack.warnings.Count)"
$pack.blockers | ForEach-Object { "  blocker [$($_.rule)] $($_.message)" } | Select-Object -First 8
"studio fields: " + (($pack.studioFields | ForEach-Object { $_.label }) -join ' | ')
"== package must refuse (test assets, test game, preview math)"
$t0 = Get-Date
$job = Post "/api/game/$Game/jobs" @{ tool = 'package' }
do { Start-Sleep -Milliseconds 1500; $j = (Invoke-RestMethod "$E/api/jobs/$($job.id)").job } while ($j.status -eq 'running')
"package: $($j.status) (expected failed): $($j.plain)"
if ($j.status -ne 'failed') { throw 'package did not refuse' }
if (-not $Keep) {
    "== cleanup"
    $skin = Join-Path $root ("skins\" + $Game.Replace('_', '-'))
    foreach ($d in $skin, (Join-Path $root "math-sdk\games\$Game"), (Join-Path $root "build\$Game"), (Join-Path $root "web-sdk\apps\cluster-tumble\.mock-rgs\$Game")) {
        if (Test-Path $d) { cmd /c rmdir /s /q "$d" }
    }
    "removed $Game"
}
"OK: factory flow proven for $Game"
