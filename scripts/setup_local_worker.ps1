$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    py -3.11 -m venv .venv --system-site-packages
}
$Python = Join-Path $Root ".venv\Scripts\python.exe"
& $Python -m pip install --upgrade pip
& $Python -m pip install fastapi==0.141.1 "uvicorn[standard]==0.52.4" python-multipart==0.0.32
& $Python -c "import rembg, rtmlib, onnxruntime, fastapi, uvicorn; print('Local worker dependencies: OK')"
& (Join-Path $Root "scripts\install_local_worker_autostart.ps1")
Write-Host "Minimalizer Local Worker setup complete."
