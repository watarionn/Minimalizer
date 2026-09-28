[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot

function Invoke-Checked([string]$Label, [scriptblock]$Command) {
    Write-Host $Label
    & $Command
    if ($LASTEXITCODE -ne 0) { throw "$Label failed: $LASTEXITCODE" }
}

Push-Location $Root
try {
    Invoke-Checked '[1/4] Compile source tree' {
        python -m compileall -q minimalize_engine app gui tools tests web
    }

    $Tests = @(
        'tests/test_config.py','tests/test_global_shape_cleanup.py','tests/test_adaptive_polygon_simplify.py',
        'tests/test_high_resolution_guard.py','tests/test_target_style.py','tests/test_target_hierarchy.py',
        'tests/test_rinka_phase8_rescue.py','tests/test_semantic_shape_tree.py','tests/test_primitive_fit.py',
        'tests/test_rinka_phase9_semantic_primitives.py','tests/test_rinka_phase10_subject_segmentation.py',
        'tests/test_v020_bundle.py::test_corpus_manifest_contains_uploaded_images',
        'tests/test_web_api.py','tests/test_color_strip.py','tests/test_v2_default_migration.py'
    )
    Invoke-Checked '[2/4] Stable regressions and Web tests' {
        python -m pytest -q @Tests
    }

    $EvalDir = Join-Path $env:TEMP 'minimalizer-rinka-target-phase16-actions-zero'
    if (Test-Path $EvalDir) { Remove-Item -Recurse -Force $EvalDir }
    Invoke-Checked '[3/4] Phase 16 corpus evaluation' {
        python tools/evaluate_rinka_target.py --level 4 --max-side 220 --output-dir $EvalDir
    }
    $Summary = Get-Content (Join-Path $EvalDir 'summary_0_end.json') -Raw | ConvertFrom-Json
    if ($Summary.target_style_version -ne 'phase16' -or $Summary.count -ne 16) { throw 'Phase 16 corpus identity check failed' }
    if ($Summary.phase10_segmentation_activated_count -ne 4 -or $Summary.phase10_subject_planes_enabled_count -ne 4) { throw 'Phase 16 segmentation guard failed' }
    if ($Summary.phase10_total_subject_plane_count -gt 68 -or $Summary.phase10_mean_subject_plane_coverage -lt 0.75) { throw 'Phase 16 subject-plane guard failed' }
    if ($Summary.phase10_max_subject_plane_outside_ratio -gt 0.03 -or $Summary.total_target_global_low_value_subject_count -ne 0) { throw 'Phase 16 geometry guard failed' }
    if ($Summary.total_target_cap_removed -ne 0 -or $Summary.macro_shadow_blocked_count -ne 1) { throw 'Phase 16 safety guard failed' }

    Write-Host '[4/4] Real-server smoke'
    $Port = 18765
    $Server = Start-Process python -ArgumentList '-m','uvicorn','web.app:app','--host','127.0.0.1','--port',"$Port" -PassThru -WindowStyle Hidden
    try {
        $Ready = $false
        for ($i = 0; $i -lt 30; $i++) {
            try { Invoke-WebRequest "http://127.0.0.1:$Port/health" -UseBasicParsing | Out-Null; $Ready = $true; break } catch { Start-Sleep -Seconds 1 }
        }
        if (-not $Ready) { throw 'Uvicorn did not become ready' }
        $HomeContent = (Invoke-WebRequest "http://127.0.0.1:$Port/" -UseBasicParsing).Content
        if ($HomeContent -notmatch 'id="drop-zone"') { throw 'Home smoke failed' }
        $Info = Invoke-RestMethod "http://127.0.0.1:$Port/api/info"
        $V2 = Invoke-RestMethod "http://127.0.0.1:$Port/api/v2/info"
        if ($Info.web_version -ne '0.13.0' -or $V2.status -ne 'standard_default') { throw 'API smoke failed' }
    }
    finally {
        if ($Server -and -not $Server.HasExited) { Stop-Process -Id $Server.Id -Force }
    }

    Write-Output 'LOCAL_MERGE_VALIDATION_PASS'
}
finally {
    Pop-Location
}
