param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^https://[^/]+(?::[0-9]+)?$')]
    [string]$Origin
)

$ErrorActionPreference = "Stop"
$ConfigDir = Join-Path $env:LOCALAPPDATA "Minimalizer\config"
$OriginFile = Join-Path $ConfigDir "public-origin.txt"

New-Item -ItemType Directory -Force $ConfigDir | Out-Null
$normalized = $Origin.TrimEnd("/")
Set-Content -Path $OriginFile -Value $normalized -Encoding UTF8

Write-Host "Minimalizer public origin saved:"
Write-Host $normalized
Write-Host "Restart the Local Worker to apply the new CORS allowlist."
