# dev_cert.ps1 - self-signed localhost certificate for the demo dev server (mock RGS).
# The SDK always calls https://{rgs_url}, so local play needs HTTPS. Uses Git for Windows' openssl.
# Output: web-sdk\apps\cluster-tumble\.mock-rgs\cert.pem + key.pem (git-ignored, dev only).
# Usage: powershell -ExecutionPolicy Bypass -File scripts\dev_cert.ps1

$root = Split-Path -Parent $PSScriptRoot
$dir = Join-Path $root 'web-sdk\apps\cluster-tumble\.mock-rgs'
New-Item -ItemType Directory -Force $dir | Out-Null
$openssl = (Get-Command openssl -ErrorAction SilentlyContinue).Source
if (-not $openssl) { $openssl = 'C:\Program Files\Git\usr\bin\openssl.exe' }
if (-not (Test-Path $openssl)) { Write-Host 'FAIL  openssl not found (install Git for Windows)'; exit 1 }
& $openssl req -x509 -newkey rsa:2048 -nodes -days 365 -subj '/CN=localhost' `
    -addext 'subjectAltName=DNS:localhost,IP:127.0.0.1' `
    -keyout (Join-Path $dir 'key.pem') -out (Join-Path $dir 'cert.pem') 2>$null
if ($LASTEXITCODE -ne 0) { Write-Host "FAIL  openssl exit $LASTEXITCODE"; exit 1 }
Write-Host "ok    $dir\cert.pem"
exit 0
