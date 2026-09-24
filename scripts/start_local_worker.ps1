$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Local worker venv not found. Run scripts\setup_local_worker.ps1 first."
}
$Health = "http://127.0.0.1:28765/health"
try {
    $existing = Invoke-RestMethod -Uri $Health -TimeoutSec 1
    if ($existing.worker -eq "local-compute-v1") {
        Write-Host "Minimalizer Local Worker is already running."
        exit 0
    }
} catch {}
$LogDir = Join-Path $env:LOCALAPPDATA "Minimalizer\logs"
New-Item -ItemType Directory -Force $LogDir | Out-Null
$Log = Join-Path $LogDir "local-worker.log"
Set-Location $Root
$ErrorActionPreference = "Continue"
& $Python -m uvicorn local_worker.app:app --host 127.0.0.1 --port 28765 --workers 1 >> $Log 2>&1
exit $LASTEXITCODE
