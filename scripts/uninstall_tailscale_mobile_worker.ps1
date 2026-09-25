$ErrorActionPreference = "Stop"
if (-not (Get-Command tailscale -ErrorAction SilentlyContinue)) {
    throw "Tailscale CLI was not found."
}

& tailscale serve --https=28765 off
if ($LASTEXITCODE -ne 0) {
    throw "Failed to remove the Minimalizer Tailscale Serve route."
}
Write-Host "Removed Minimalizer Tailscale mobile route on HTTPS port 28765."
