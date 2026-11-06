# doctor.ps1 - read-only environment check. Installs nothing, changes nothing.
# Usage: powershell -ExecutionPolicy Bypass -File scripts\doctor.ps1
# Exit code: 0 if every required check passes, 1 otherwise.

$root = Split-Path -Parent $PSScriptRoot

# Load pins: .env overrides .env.example.
$cfg = @{}
foreach ($name in @('.env.example', '.env')) {
    $path = Join-Path $root $name
    if (Test-Path $path) {
        foreach ($line in Get-Content $path) {
            if ($line -match '^\s*([A-Z_]+)\s*=\s*(.+?)\s*$') { $cfg[$Matches[1]] = $Matches[2] }
        }
    }
}

function Get-ToolVersion($exe, $arg) {
    if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) { return $null }
    try { $out = & $exe $arg 2>&1 | Out-String } catch { return $null }
    if ($out -match '(\d+\.\d+(\.\d+)?)') { return $Matches[1] }
    return $null
}

$rows = @()
function Add-Row($tool, $want, $have, $ok, $fix, $required) {
    $script:rows += [pscustomobject]@{
        Tool = $tool; Want = $want; Have = $(if ($have) { $have } else { 'missing' })
        Status = $(if ($ok) { 'PASS' } elseif ($required) { 'FAIL' } else { 'WARN' })
        Fix = $(if ($ok) { '' } else { $fix })
    }
}

$node = Get-ToolVersion 'node' '-v'
Add-Row 'node' $cfg.NODE_VERSION $node ($node -eq $cfg.NODE_VERSION) `
    "fnm install $($cfg.NODE_VERSION); fnm use $($cfg.NODE_VERSION) (PROJECT.md section 3)" $true

$pnpm = Get-ToolVersion 'pnpm' '-v'
Add-Row 'pnpm' $cfg.PNPM_VERSION $pnpm ($pnpm -eq $cfg.PNPM_VERSION) `
    "corepack enable; corepack prepare pnpm@$($cfg.PNPM_VERSION) --activate (PROJECT.md section 3)" $true

$py = Get-ToolVersion 'python' '-V'
$pyOk = $py -and ([version]$py -ge [version]$cfg.PYTHON_MIN_VERSION)
Add-Row 'python' ">=$($cfg.PYTHON_MIN_VERSION)" $py $pyOk "install Python $($cfg.PYTHON_MIN_VERSION)+" $true

$git = Get-ToolVersion 'git' '--version'
Add-Row 'git' 'any' $git ([bool]$git) 'install Git for Windows' $true

$corepack = Get-ToolVersion 'corepack' '--version'
Add-Row 'corepack' 'any' $corepack ([bool]$corepack) 'ships with Node; reinstall Node' $true

$cargo = Get-ToolVersion 'cargo' '-V'
Add-Row 'cargo' $cfg.RUST_VERSION $cargo ($cargo -eq $cfg.RUST_VERSION) `
    "rustup install $($cfg.RUST_VERSION); see docs/01 optimizer setup (PROJECT.md section 3)" $false

foreach ($dir in @($cfg.MATH_SDK_DIR, $cfg.WEB_SDK_DIR)) {
    $exists = Test-Path (Join-Path $root $dir)
    Add-Row "dir $dir" 'cloned' $(if ($exists) { 'present' } else { $null }) $exists `
        'clone SDK (PROJECT.md section 6 M1)' $false
}

# web-sdk is not tracked here: its lockfile is pinned by the tracked copy core\web\pnpm-lock.yaml (plan v3.3 E3).
$lock = Join-Path $root 'web-sdk\pnpm-lock.yaml'
$lockCopy = Join-Path $root 'core\web\pnpm-lock.yaml'
if ((Test-Path $lock) -and (Test-Path $lockCopy)) {
    $same = (Get-FileHash $lock).Hash -eq (Get-FileHash $lockCopy).Hash
    Add-Row 'web lockfile' 'core\web copy' $(if ($same) { 'same' } else { 'differs' }) $same `
        'after a deliberate install run scripts\sync.ps1; otherwise restore: copy core\web\pnpm-lock.yaml to web-sdk\, then pnpm install --frozen-lockfile' $true
}

$rows | Format-Table -AutoSize | Out-String -Width 200 | Write-Host

$failed = @($rows | Where-Object { $_.Status -eq 'FAIL' }).Count
if ($failed -gt 0) { Write-Host "$failed required check(s) failed."; exit 1 }
Write-Host 'All required checks passed.'
exit 0
