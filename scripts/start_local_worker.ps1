$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Python = Join-Path $Root ".venv311\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Local worker venv not found. Run scripts\setup_local_worker.ps1 first."
}
$ConfigDir = Join-Path $env:LOCALAPPDATA "Minimalizer\config"
$OriginFile = Join-Path $ConfigDir "public-origin.txt"
if (Test-Path $OriginFile) {
    $ConfiguredOrigin = (Get-Content $OriginFile -Raw).Trim()
    if ($ConfiguredOrigin) {
        $env:MINIMALIZER_LOCAL_ALLOWED_ORIGINS = $ConfiguredOrigin
    }
}
$Health = "http://127.0.0.1:28764/health"
$StuckSeconds = 900
$stale = $false
try {
    $existing = Invoke-RestMethod -Uri $Health -TimeoutSec 1
    $busy = $existing.process.busy -eq $true
    $busySeconds = 0
    if ($null -ne $existing.process.busy_seconds) {
        $busySeconds = [double]$existing.process.busy_seconds
    }
    if ($existing.worker -eq "local-compute-v1" -and (-not $busy -or $busySeconds -lt $StuckSeconds)) {
        Write-Host "Minimalizer Local Worker is already running."
        exit 0
    }
    if ($busy -and $busySeconds -ge $StuckSeconds) {
        Write-Host "Restarting a stale Local Worker job ($([int]$busySeconds)s)."
        $stale = $true
    }
} catch {}
if ($stale) {
    $listener = Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 28764 -State Listen -ErrorAction SilentlyContinue
    if ($listener) {
        Stop-Process -Id $listener.OwningProcess -Force
        Start-Sleep -Milliseconds 700
    }
}
$LogDir = Join-Path $env:LOCALAPPDATA "Minimalizer\logs"
New-Item -ItemType Directory -Force $LogDir | Out-Null
$Log = Join-Path $LogDir "local-worker.log"
Set-Location $Root
$ErrorActionPreference = "Continue"
& $Python -m uvicorn local_worker.app:app --host 127.0.0.1 --port 28764 --workers 1 >> $Log 2>&1
exit $LASTEXITCODE
