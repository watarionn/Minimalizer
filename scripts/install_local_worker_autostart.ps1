$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Startup = [Environment]::GetFolderPath("Startup")
$Launcher = Join-Path $Startup "Minimalizer Local Worker.cmd"
$StartScript = Join-Path $Root "scripts\start_local_worker.ps1"
$Content = @"
@echo off
start "" /min powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "$StartScript"
"@
Set-Content -Path $Launcher -Value $Content -Encoding ASCII
Write-Host "Installed Minimalizer Local Worker startup launcher:"
Write-Host $Launcher
