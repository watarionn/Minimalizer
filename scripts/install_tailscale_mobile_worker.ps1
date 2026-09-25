$ErrorActionPreference = "Stop"
$WorkerUrl = "http://127.0.0.1:28765"
$HttpsPort = 28765

if (-not (Get-Command tailscale -ErrorAction SilentlyContinue)) {
    throw "Tailscale CLI was not found."
}

$service = Get-Service Tailscale -ErrorAction SilentlyContinue
if (-not $service -or $service.Status -ne "Running") {
    throw "Tailscale service is not running."
}

$status = tailscale status --json | ConvertFrom-Json
if ($status.BackendState -ne "Running") {
    throw "Tailscale is not connected."
}

& tailscale serve --bg --https=$HttpsPort $WorkerUrl
if ($LASTEXITCODE -ne 0) {
    throw "Failed to configure Tailscale Serve."
}

$dns = $status.Self.DNSName.TrimEnd(".")
Write-Host "Minimalizer mobile Local Worker route is ready:"
Write-Host "https://${dns}:${HttpsPort}"
Write-Host "This route is tailnet-only. Tailscale Funnel is not enabled for this port."
