<#
.SYNOPSIS
  Build the web app for one game and move the output to build\<Game>\dist (docs/10 plan v3.3, spike rule 5).
.DESCRIPTION
  Calls vite directly (turbo does not hash GAME, so its cache would be stale). On Windows vite can keep
  running after it prints "done", so success = the done line plus build\index.html; then the process tree
  is killed. Never build two games at the same time: every game shares the app's build\ folder.
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tools\web_build.ps1 -Game seventh_veil
#>
param(
    [Parameter(Mandatory = $true)][string]$Game,
    [string]$App = '',
    [int]$TimeoutSec = 900
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
if (-not $App) { $App = 'cluster-tumble' }
$appDir = Join-Path $root "web-sdk\apps\$App"
if (-not (Test-Path $appDir)) { throw "App folder missing: $appDir. Run scripts\sync.ps1 first." }
$out = Join-Path $appDir 'build'
$dist = Join-Path $root "build\$Game\dist"
$log = Join-Path $root "build\$Game\web_build.log"
New-Item -ItemType Directory -Force (Split-Path $log) | Out-Null
if (Test-Path $out) { Remove-Item -Recurse -Force $out }

$env:GAME = $Game
$t0 = Get-Date
$cmdLine = "pnpm exec vite build > `"$log`" 2>&1"
$p = Start-Process -FilePath 'cmd.exe' -ArgumentList @('/c', $cmdLine) -WorkingDirectory $appDir -PassThru -WindowStyle Hidden
$ok = $false
while (((Get-Date) - $t0).TotalSeconds -lt $TimeoutSec) {
    Start-Sleep -Milliseconds 1000
    $text = if (Test-Path $log) { Get-Content $log -Raw -ErrorAction SilentlyContinue } else { '' }
    if ($text -match '(?m)(✔ done|Wrote site to)' -and (Test-Path (Join-Path $out 'index.html'))) { $ok = $true; break }
    if ($p.HasExited) {
        Start-Sleep -Milliseconds 500
        $ok = Test-Path (Join-Path $out 'index.html')
        break
    }
}
if (-not $p.HasExited) { & taskkill /PID $p.Id /T /F | Out-Null }
$secs = [math]::Round(((Get-Date) - $t0).TotalSeconds)
if (-not $ok) {
    Write-Host "FAIL: web build for $Game did not finish (log: $log)"
    Get-Content $log -Tail 20
    exit 1
}
if (Test-Path $dist) { Remove-Item -Recurse -Force $dist }
New-Item -ItemType Directory -Force (Split-Path $dist) | Out-Null
Move-Item $out $dist
$files = Get-ChildItem $dist -Recurse -File
$mb = ($files | Measure-Object Length -Sum).Sum / 1MB
"OK: $Game built in ${secs}s -> build\$Game\dist ({0:N1} MB, {1} files)" -f $mb, $files.Count
