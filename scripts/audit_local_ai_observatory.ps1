param([switch]$Json)
$here=Split-Path -Parent $MyInvocation.MyCommand.Path
if($Json){
 $m=& powershell -ExecutionPolicy Bypass -File "$here\audit_model_residency.ps1" -Json|ConvertFrom-Json
 $r=& powershell -ExecutionPolicy Bypass -File "$here\audit_runtime_duplication.ps1" -Json|ConvertFrom-Json
 [pscustomobject]@{timestamp=(Get-Date).ToString('o');model_residency=$m;runtime_duplication=$r}|ConvertTo-Json -Depth 10
}else{
 '=== MODEL RESIDENCY ==='; & powershell -ExecutionPolicy Bypass -File "$here\audit_model_residency.ps1"
 '=== RUNTIME DUPLICATION ==='; & powershell -ExecutionPolicy Bypass -File "$here\audit_runtime_duplication.ps1"
}
