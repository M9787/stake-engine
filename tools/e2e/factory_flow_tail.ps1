# Resume tools\e2e\factory_flow.ps1 at the check step for an existing game (editor on 127.0.0.1:5174).
# Usage: powershell -ExecutionPolicy Bypass -File tools\e2e\factory_flow_tail.ps1 -Game zz_hands_on
param([string]$Game = 'zz_hands_on')
$ErrorActionPreference = 'Stop'
$E = 'http://127.0.0.1:5174'
$H = @{ Origin = $E }
function Post([string]$path, $body) { Invoke-RestMethod -Method Post -Uri ($E + $path) -Headers $H -ContentType 'application/json' -Body ($body | ConvertTo-Json -Depth 6) }
function RunJob([string]$tool, $opts = @{}) {
    $t0 = Get-Date
    $job = Post "/api/game/$Game/jobs" @{ tool = $tool; opts = $opts }
    do { Start-Sleep -Milliseconds 1500; $j = (Invoke-RestMethod ($E + '/api/jobs/' + $job.id)).job } while ($j.status -eq 'running')
    Write-Host ("{0,-6} {1,-12} {2,5}s  {3}" -f $j.status, $tool, [math]::Round(((Get-Date) - $t0).TotalSeconds), $j.plain)
    return $j
}
$g = RunJob 'gate_fast'
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
(Get-Content (Join-Path $root "build\$Game\reports\gate.json") -Raw | ConvertFrom-Json).steps | Where-Object { $_.status -notin 'pass', 'skipped' } | ForEach-Object { Write-Host "   $($_.status) $($_.step): $($_.detail)" }
$null = RunJob 'event_ids' @{ version = '1' }
$null = RunJob 'pack'
$pack = Invoke-RestMethod "$E/api/game/$Game/pack"
Write-Host "pack: ready=$($pack.ready) blockers=$($pack.blockers.Count) warnings=$($pack.warnings.Count)"
$pack.blockers | Group-Object rule | ForEach-Object { Write-Host "   blocker [$($_.Name)] x$($_.Count): $($_.Group[0].message)" }
$pack.warnings | Group-Object rule | ForEach-Object { Write-Host "   warning [$($_.Name)] x$($_.Count): $($_.Group[0].message)" }
Write-Host ("studio fields: " + (($pack.studioFields | ForEach-Object { $_.label }) -join ' | '))
$p = RunJob 'package'
Write-Host "package (must refuse): $($p.status)"
if ($g.status -eq 'done' -and $p.status -eq 'failed') { Write-Host "OK: factory flow tail proven for $Game" } else { Write-Host "CHECK: gate=$($g.status) package=$($p.status)"; exit 1 }
