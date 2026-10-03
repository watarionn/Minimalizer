param([switch]$Json)
$ErrorActionPreference="SilentlyContinue"
function MB($n){if($null-eq$n){return $null};[math]::Round($n/1MB,1)}
$all=@(Get-CimInstance Win32_Process);$by=@{};foreach($p in $all){$by[[int]$p.ProcessId]=$p}
$tcp=@(Get-NetTCPConnection -ErrorAction SilentlyContinue);$lis=@{};foreach($c in($tcp|Where-Object State -eq 'Listen')){if(-not$lis.ContainsKey([int]$c.OwningProcess)){$lis[[int]$c.OwningProcess]=@()};$lis[[int]$c.OwningProcess]+=[int]$c.LocalPort}
$rows=@()
foreach($w in $all){
 $cmd=[string]$w.CommandLine;$role=$null;$owner=$null
 if($cmd-match'local_worker\.app:app'){$role='MINIMALIZER_LOCAL_WORKER';$owner=if($cmd-match'Documents\\Minimalizer-local-worker'){'Minimalizer-local-worker-legacy'}else{'Minimalizer'}}
 elseif($w.Name-eq'pythonw.exe'-and$cmd-match'rlo\.py serve'){$role='RLO_SERVER';$owner='RLO'}
 elseif($cmd-match'holoscope_collab\\rinka_command_bridge\.py'){$role='RINKA_COMMAND_BRIDGE';$owner='OllamaPersonaRuntime'}
 elseif($cmd-match'ComfyUI.*main\.py|main\.py.*ComfyUI'){$role='COMFYUI';$owner=if($cmd-match'8191'){'MitsubaRuntime'}elseif($cmd-match'8188'){'Reference3DStudio'}else{'ComfyUI'}}
 elseif($cmd-match'portfolio.*http\.server|http\.server.*portfolio'){$role='PORTFOLIO_HTTP_SERVER';$owner='Portfolio'}
 elseif($w.Name-eq'ollama.exe'){$role='OLLAMA';$owner='Minimalizer/Ollama'}
 elseif($w.Name-eq'llama-server.exe'){$role='LLAMA_SERVER';$owner='Ollama'}
 if(-not$role){continue}; $hasListener=$lis.ContainsKey([int]$w.ProcessId); if(($role -eq 'MINIMALIZER_LOCAL_WORKER' -or $role -eq 'COMFYUI' -or $role -eq 'PORTFOLIO_HTTP_SERVER') -and -not $hasListener){continue}
 $p=Get-Process -Id $w.ProcessId -ErrorAction SilentlyContinue;$ports=if($lis.ContainsKey([int]$w.ProcessId)){@($lis[[int]$w.ProcessId]|Sort-Object -Unique)}else{@()};$pa=$by.ContainsKey([int]$w.ParentProcessId)
 $cl='OBSERVE';$rs='Inspect ownership before action.'
 if($role-eq'OLLAMA'){$cl='REQUIRED_RUNTIME';$rs='Ollama service.'}
 elseif($role-eq'LLAMA_SERVER'-and$pa){$cl='REQUIRED_CHILD';$rs='Managed by live parent.'}
 elseif($role-eq'COMFYUI'){$cl='VALID_PARALLEL_ON_DEMAND';$rs='Project-owned ComfyUI runtime.'}
 elseif($role-eq'MINIMALIZER_LOCAL_WORKER'){if($ports-contains28764){$cl='REQUIRED_RUNTIME';$rs='Primary current worker.'}elseif($ports-contains28765){$cl='LEGACY_REVIEW';$rs='Legacy/Tailscale endpoint; never auto-stop.'}else{$cl='DUPLICATE_CANDIDATE';$rs='Additional Local Worker endpoint.'}}
 elseif($role-eq'RLO_SERVER'){if($ports.Count-gt0){$cl='REQUIRED_RUNTIME';$rs='Active RLO listener.'}else{$cl='ORPHAN_DUPLICATE_CANDIDATE';$rs='No listening endpoint.'}}
 elseif($role-eq'RINKA_COMMAND_BRIDGE'){if($pa){$cl='REQUIRED_RUNTIME';$rs='Live launcher parent.'}else{$cl='ORPHAN_DUPLICATE_CANDIDATE';$rs='Duplicate command with missing parent.'}}
 elseif($role-eq'PORTFOLIO_HTTP_SERVER'){$cl='DEV_RESIDUE_CANDIDATE';$rs='Development server; review before stop.'}
 $rows+=[pscustomobject]@{pid=[int]$w.ProcessId;ppid=[int]$w.ParentProcessId;role=$role;owner=$owner;ports=$ports;working_set_mb=if($p){MB($p.WorkingSet64)}else{$null};private_mb=if($p){MB($p.PrivateMemorySize64)}else{$null};parent_alive=$pa;classification=$cl;reason=$rs;command=$cmd}
}
$groups=@($rows|Group-Object role|ForEach-Object{[pscustomobject]@{role=$_.Name;count=$_.Count;candidate_count=@($_.Group|Where-Object {$_.classification -match 'CANDIDATE|LEGACY_REVIEW'}).Count}})
$result=[pscustomobject]@{timestamp=(Get-Date).ToString('o');runtimes=$rows;groups=$groups}
if($Json){$result|ConvertTo-Json -Depth 7}else{$groups|Format-Table -AutoSize;$rows|Select pid,role,owner,@{n='ports';e={$_.ports-join','}},parent_alive,classification|Format-Table -AutoSize}

