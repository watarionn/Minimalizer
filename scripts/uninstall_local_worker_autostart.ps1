$ErrorActionPreference = "Stop"
$Startup = [Environment]::GetFolderPath("Startup")
$Launcher = Join-Path $Startup "Minimalizer Local Worker.cmd"
if (Test-Path $Launcher) {
    Remove-Item $Launcher -Force
}
Write-Host "Removed Minimalizer Local Worker startup launcher."
