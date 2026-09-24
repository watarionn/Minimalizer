$matches = Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -and
    $_.CommandLine -match "uvicorn" -and
    $_.CommandLine -match "local_worker.app:app" -and
    $_.CommandLine -match "28765"
}
foreach ($proc in $matches) {
    Stop-Process -Id $proc.ProcessId -Force
}
Write-Host "Minimalizer Local Worker stopped."
