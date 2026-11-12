<#
.SYNOPSIS
  Proof that a factory game is a real Stake upload (Factory v3): full gate in the game's mode, Stake
  checklist, submission pack, package; then (optional) confirm Release mode refuses test assets.
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tools\e2e\real_game_proof.ps1 -Game zz_real_proof -CheckReleaseRefusal
#>
param([Parameter(Mandatory = $true)][string]$Game, [switch]$CheckReleaseRefusal)
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$py = Join-Path $root 'math-sdk\env\Scripts\python.exe'
Push-Location $root
$env:GAME = $Game
$t0 = Get-Date
"== full gate ($Game)"
powershell -ExecutionPolicy Bypass -File tools\gates\gate.ps1 -Game $Game *>&1 | Select-String '^(pass|FAIL|warn|todo|skipped)|gate ' | ForEach-Object { $_.Line }
$gate = $LASTEXITCODE
"gate exit=$gate ($([math]::Round(((Get-Date) - $t0).TotalMinutes, 1)) min)"
"== Stake checklist"
& $py tools\release\checklist.py --game $Game | Select-Object -Last 1
"== package"
powershell -ExecutionPolicy Bypass -File tools\package.ps1 -Game $Game *>&1 | Select-Object -Last 6
$ver = (Get-Content (Get-ChildItem skins\*\game.json | Where-Object { (Get-Content $_.FullName -Raw | ConvertFrom-Json).identity.gameId -eq $Game }).FullName -Raw | ConvertFrom-Json).identity.version
$rel = Get-ChildItem "release\$Game" -Directory -ErrorAction SilentlyContinue | Sort-Object LastWriteTime | Select-Object -Last 1
if ($rel) {
    "release folder: $($rel.FullName)"
    Get-ChildItem $rel.FullName | Select-Object Name | Format-Table -HideTableHeaders | Out-String
    "math files: " + ((Get-ChildItem "$($rel.FullName)\math" -File | Select-Object -ExpandProperty Name) -join ', ')
    "front index.html: $(Test-Path "$($rel.FullName)\front\index.html")"
    $m = Get-Content "$($rel.FullName)\manifest.json" -Raw | ConvertFrom-Json
    "manifest mode: $($m.mode)"
    "licence section in submission.md: $([bool](Select-String -Path "$($rel.FullName)\submission.md" -Pattern 'Licen[cs]e log|provenance' -Quiet))"
}
Pop-Location
