# One command to make the live site functional:
#   1. start the Django API locally (if not already running)
#   2. expose it through a Cloudflare quick tunnel (no card, no signup)
#   3. point the deployed Firebase frontend at the tunnel URL and redeploy
#
# Run from the project root:  .\live.bat   (or: powershell -File make-live.ps1)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$py   = Join-Path $root ".venv\Scripts\python.exe"
$cf   = Join-Path $root "tools\cloudflared.exe"

Write-Host "== Step 1: backend API ==" -ForegroundColor Cyan
$listening = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if (-not $listening) {
    Start-Process -FilePath (Join-Path $root "run-backend.bat") -WindowStyle Hidden
    for ($i = 0; $i -lt 15; $i++) {
        Start-Sleep -Seconds 2
        try {
            Invoke-WebRequest -Uri "http://localhost:8000/health/" -TimeoutSec 5 | Out-Null
            break
        } catch { }
    }
    Write-Host "Backend started on port 8000."
} else {
    Write-Host "Backend already running on port 8000."
}

Write-Host "== Step 2: Cloudflare tunnel ==" -ForegroundColor Cyan
$existing = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match "cloudflared\.exe.*--url" }
if ($existing) {
    Write-Host "Tunnel already running (PID $($existing.ProcessId))."
    $url = Select-String -Path (Join-Path $env:TEMP "opencode\cf.err") -Pattern "https://[a-z0-9-]+\.trycloudflare\.com" -ErrorAction SilentlyContinue |
        Select-Object -Last 1
    $publicUrl = $url.Matches.Value
    if (-not $publicUrl) { throw "Tunnel is running but its URL is unknown; kill cloudflared and re-run." }
} else {
    $outFile = Join-Path $env:TEMP "cloudflared-tunnel.out"
    Start-Process -FilePath $cf -ArgumentList "tunnel","--url","http://localhost:8000","--no-autoupdate" `
        -WorkingDirectory $root -WindowStyle Hidden `
        -RedirectStandardOutput $outFile -RedirectStandardError $outFile
    for ($i = 0; $i -lt 12; $i++) {
        Start-Sleep -Seconds 2
        $match = Select-String -Path $outFile -Pattern "https://[a-z0-9-]+\.trycloudflare\.com" -ErrorAction SilentlyContinue
        if ($match) { break }
    }
    if (-not $match) { throw "Could not get a tunnel URL. Check $outFile" }
    $publicUrl = $match.Matches.Value
    Write-Host "Tunnel: $publicUrl"
}
Write-Host "Public API URL: $publicUrl"

Write-Host "== Step 3: redeploy frontend config ==" -ForegroundColor Cyan
$rcPublic  = Join-Path $root "frontend\public\runtime-config.js"
$rcOut     = Join-Path $root "frontend\out\runtime-config.js"
$apiUrl    = "$publicUrl/api"
(Get-Content $rcPublic -Raw) -replace 'https://[a-z0-9.-]+/api', $apiUrl | Set-Content $rcPublic -Encoding UTF8
if (Test-Path $rcOut) { Copy-Item $rcPublic $rcOut -Force }
Write-Host "runtime-config.js -> $apiUrl"

# Bump the runtime-config cache-buster inside the built HTML so browsers never
# reuse a cached copy of the config from an older deploy (no rebuild needed).
$stamp = [string][DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
$htmlFiles = Get-ChildItem (Join-Path $root "frontend\out") -Recurse -Filter *.html -ErrorAction SilentlyContinue
foreach ($f in $htmlFiles) {
    $content = Get-Content $f.FullName -Raw
    if ($content -match 'runtime-config\.js\?v=[^"]*') {
        $content = [regex]::Replace($content, 'runtime-config\.js\?v=[^"]*', "runtime-config.js?v=$stamp")
        Set-Content $f.FullName -Value $content -Encoding UTF8 -NoNewline
    }
}
Write-Host "Cache-buster bumped to $stamp in $($htmlFiles.Count) HTML files."

Push-Location (Join-Path $root "frontend")
try {
    npx --yes firebase-tools deploy --only hosting --project new-school-management-system
    if ($LASTEXITCODE -ne 0) { throw "Firebase deploy failed." }
} finally {
    Pop-Location
}
Write-Host ""
Write-Host "DONE. Live site: https://new-school-management-system.web.app" -ForegroundColor Green
Write-Host "Login: admin@demo.school / Demo@12345"
Write-Host "NOTE: the live link works while this PC is running and connected."
