from __future__ import annotations
import json
import shutil
import subprocess
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
ENGINE=ROOT/"web/static/browser-fallback.js"
CONTOUR=ROOT/"web/static/canonical-contour.js"
RASTER=ROOT/"web/static/opencv-fill-raster.js"
APP=ROOT/"web/static/app.js"

def _node(script: str)->dict:
    result=subprocess.run(["node","-e",script,str(ENGINE),str(CONTOUR),str(RASTER)],
                          capture_output=True,text=True,check=True,timeout=90)
    return json.loads(result.stdout)

def test_selective_opt_in_and_prior_mode_preservation():
    app=APP.read_text(encoding="utf-8")
    engine=ENGINE.read_text(encoding="utf-8")
    assert 'browserFallbackQualityParam === "selective"' in app
    assert 'selectiveRegionMerge: browserFallbackQualityProfile() === "selective"' in app
    assert 'SELECTIVE (research)' in app
    assert 'selectiveMergeApplied' in engine
    assert "config.selectiveRegionMerge === true" in engine
    assert "minBoundingSide: 5" in engine
    assert "maxSourceRgbDistance: 16" in engine

@pytest.mark.skipif(shutil.which("node") is None,reason="Node absent")
def test_selective_accepts_only_safe_identical_palette_compact_adjacent_regions():
    result=_node(r"""
const core=require(process.argv[1])._core;
const w=20,h=20;
const labels=new Int32Array(w*h);
const slots=[[],[]];
for(let y=0;y<h;y++)for(let x=0;x<w;x++){
 const id=(x>=6&&x<11&&y>=6&&y<11)?1:0;
 const pixel=y*w+x;labels[pixel]=id;slots[id].push(pixel);
}
const mk=(id,rgb)=>({
 id,sourceId:id,label:id,pixels:slots[id],count:slots[id].length,
 minX:id===1?6:0,minY:id===1?6:0,maxX:id===1?10:19,maxY:id===1?10:19,
 borderTouches:id===1?0:80,rgb,lab:[40,0,0]
});
const base={built:{components:[mk(0,[100,105,110]),mk(1,[102,104,108])],componentIds:labels},
 groups:[],selectedCount:2};
const palette={colors:[[120,120,120],[120,120,120]],assignments:[0,0],palette:[{id:0,rgb:[120,120,120]}]};
const originalLabels=Array.from(labels);
const opts={maxSmallFraction:0.10,maxMerges:2,minSharedRatio:0.18};
const merged=core.mergeAcceptedPaletteRegions(base,palette,w,h,opts);
const again=core.mergeAcceptedPaletteRegions(base,palette,w,h,opts);
const different=core.mergeAcceptedPaletteRegions(base,{...palette,assignments:[0,1]},w,h,opts);
const highContrast=core.mergeAcceptedPaletteRegions({...base,built:{...base.built,
components:[mk(0,[100,105,110]),mk(1,[200,60,20])]}},palette,w,h,opts);
const tinyThin=core.mergeAcceptedPaletteRegions({...base,built:{...base.built,
components:[mk(0,[100,105,110]),{...mk(1,[102,104,108]),maxX:8}]}},palette,w,h,opts);
process.stdout.write(JSON.stringify({
 merges:merged.metrics.applied,deterministic:JSON.stringify(merged.hierarchy.built.componentIds)===JSON.stringify(again.hierarchy.built.componentIds),
 count:merged.hierarchy.built.components.length,
 colors:merged.palette.colors,
 preservedInput:JSON.stringify(originalLabels)===JSON.stringify(Array.from(labels)),
 newCoverage:Array.from(merged.hierarchy.built.componentIds).every(x=>x===0),
 rejectDifferent:different.metrics.applied,rejectContrast:highContrast.metrics.applied,
 rejectThin:tinyThin.metrics.applied,
}));
""")
    assert result["merges"] == 1
    assert result["deterministic"]
    assert result["count"] == 1
    assert result["colors"] == [[120,120,120]]
    assert result["preservedInput"] and result["newCoverage"]
    assert result["rejectDifferent"] == 0
    assert result["rejectContrast"] == 0
    assert result["rejectThin"] == 0

@pytest.mark.skipif(shutil.which("node") is None,reason="Node absent")
def test_real_analyzer_keeps_owner_and_palette_if_no_merge_qualifies():
    result=_node(r"""
global.MinimalizerCanonicalContour=require(process.argv[2]);
global.MinimalizerOpenCvRaster=require(process.argv[3]);
const api=require(process.argv[1]);
const w=40,h=40,rgba=new Uint8ClampedArray(w*h*4);
for(let y=0;y<h;y++)for(let x=0;x<w;x++){
 const i=(y*w+x)*4;
 const rgb=x<20?[210,55,42]:[45,90,220];
 for(let k=0;k<3;k++)rgba[i+k]=rgb[k];
 rgba[i+3]=255;
}
const options={
 ...api.DEFAULTS,structuralMode:"l0-lite-jacobi",canonicalContourLite:true,
 geometryMode:"facet-safe",slicTargetMin:24,slicTargetMax:24,
 slicMinAverageArea:4,hierarchyTargetMin:8,hierarchyTargetMax:12,maxShapes:12,
};
const baseline=api._core.analyzeRgba(rgba,w,h,options);
const selective=api._core.analyzeRgba(rgba,w,h,{...options,selectiveRegionMerge:true});
const repeat=api._core.analyzeRgba(rgba,w,h,{...options,selectiveRegionMerge:true});
const signature=r=>r.shapes.map(s=>({rgb:s.rgb,paletteId:s.paletteId,count:s.count}));
process.stdout.write(JSON.stringify({
 applied:selective.metrics.selectiveMergeApplied,
 count:selective.shapes.length,
 notMore:selective.shapes.length<=baseline.shapes.length,
 noUnintendedChange: selective.metrics.selectiveMergeApplied!==0 || (
 JSON.stringify(baseline.shapes)===JSON.stringify(selective.shapes) &&
 JSON.stringify(baseline.centers)===JSON.stringify(selective.centers)),
 repeatable:JSON.stringify(signature(selective))===JSON.stringify(signature(repeat)),
 minIoU:selective.metrics.contourMinRegionIoU,
}));
""")
    assert result["notMore"] and result["noUnintendedChange"] and result["repeatable"]
    assert result["minIoU"] >= 0.9

@pytest.mark.skipif(shutil.which("node") is None,reason="Node absent")
def test_selective_wrong_modes_fail_closed():
    result=_node(r"""
const api=require(process.argv[1]),rgba=new Uint8ClampedArray(4*4*4);
const check=(v)=>{try{api._core.analyzeRgba(rgba,4,4,v);return ""}
catch(e){return String(e.message)}};
process.stdout.write(JSON.stringify({
 a:check({selectiveRegionMerge:true,structuralMode:"spectral-exact",canonicalContourLite:true,geometryMode:"facet-safe"}),
 b:check({selectiveRegionMerge:true,structuralMode:"l0-lite-jacobi",canonicalContourLite:true,geometryMode:"corner-aware"}),
 c:check({selectiveRegionMerge:true,structuralMode:"l0-lite-jacobi",geometryMode:"facet-safe"}),
}));
""")
    assert all("requires Facet geometry and Lite preprocessing" in result[k] for k in "abc")
