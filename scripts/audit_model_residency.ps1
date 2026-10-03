param([switch]$Json)
$ErrorActionPreference = "SilentlyContinue"
function MB($n) { [math]::Round($n / 1MB, 1) }
$os = Get-CimInstance Win32_OperatingSystem
$gpuRaw = nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader,nounits 2>$null
$gpu = if ($gpuRaw) { ($gpuRaw -split ",") | ForEach-Object { $_.Trim() } } else { @($null,$null) }
$ollamaPs = $null
try { $ollamaPs = Invoke-RestMethod "http://127.0.0.1:11434/api/ps" -TimeoutSec 2 } catch {}
$rows = @()
$procs = Get-CimInstance Win32_Process | Where-Object { $_.Name -match "ollama|llama-server|python" }
foreach ($w in $procs) {
  $p = Get-Process -Id $w.ProcessId -ErrorAction SilentlyContinue
  if (-not $p) { continue }
  $isComfy = $w.CommandLine -match "ComfyUI"
  $isOllama = $w.Name -match "ollama|llama-server"
  if (-not ($isComfy -or $isOllama)) { continue }
  $parentAlive = [bool](Get-Process -Id $w.ParentProcessId -ErrorAction SilentlyContinue)
  $port = $null
  if ($w.CommandLine -match "--port\s+(\d+)") { $port = [int]$Matches[1] }
  elseif ($w.Name -eq "ollama.exe") { $port = 11434 }
  $established = 0
  if ($port) { $established = @(Get-NetTCPConnection -LocalPort $port -State Established).Count }
  $class = "OBSERVE"
  $reason = "Runtime present; inspect ownership before action."
  if ($w.Name -eq "ollama.exe") { $class = "REQUIRED_RUNTIME"; $reason = "Ollama service endpoint." }
  elseif ($w.Name -eq "llama-server.exe" -and -not $parentAlive -and $established -eq 0) {
    $class = "ORPHAN_CANDIDATE"; $reason = "Parent missing and no established client. Review before stopping."
  }
  elseif ($isComfy) { $class = "ON_DEMAND_RUNTIME"; $reason = "ComfyUI runtime; Private bytes are not model-weight proof." }
  $rows += [pscustomobject]@{
    pid=$w.ProcessId; ppid=$w.ParentProcessId; name=$w.Name; port=$port
    working_set_mb=MB($p.WorkingSet64); private_mb=MB($p.PrivateMemorySize64)
    parent_alive=$parentAlive; established_clients=$established
    classification=$class; reason=$reason
  }
}
$result = [pscustomobject]@{
  timestamp=(Get-Date).ToString("o")
  ram_used_gb=[math]::Round(($os.TotalVisibleMemorySize-$os.FreePhysicalMemory)/1MB,2)
  ram_free_gb=[math]::Round($os.FreePhysicalMemory/1MB,2)
  vram_used_mb=if($gpu.Count -gt 0){[int]$gpu[0]}else{$null}
  vram_free_mb=if($gpu.Count -gt 1){[int]$gpu[1]}else{$null}
  ollama_loaded_models=if($ollamaPs){@($ollamaPs.models).Count}else{$null}
  runtimes=$rows
}
if ($Json) { $result | ConvertTo-Json -Depth 5 } else { $result | Format-List timestamp,ram_used_gb,ram_free_gb,vram_used_mb,vram_free_mb,ollama_loaded_models; $rows | Format-Table -AutoSize }
