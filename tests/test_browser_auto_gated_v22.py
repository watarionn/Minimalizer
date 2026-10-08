"""v22 opt-in auto candidate ranking, thin-stroke guard and previous baseline."""
from __future__ import annotations
import json
import subprocess
import shutil
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
JS=ROOT/"web/static/browser-fallback.js"
APP=ROOT/"web/static/app.js"

def run_js(script):
    result=subprocess.run(["node","-e",script,str(JS)],
                          capture_output=True,text=True,check=True,timeout=90)
    return json.loads(result.stdout)

def test_auto_is_opt_in_research_route():
    a=APP.read_text(encoding="utf-8")
    s=JS.read_text(encoding="utf-8")
    assert 'browserFallbackQualityParam === "auto"' in a
    assert 'autoSelectiveMerge: browserFallbackQualityProfile() === "auto"' in a
    assert '"Minimalizer Browser Fallback v12 · AUTO (research)"' in a
    assert 'autoMergeStatus: analysis.metrics.autoMergeStatus' in s
    assert 'protectThinComponents:true' in s
    assert 'maxTargetDonorFraction:0.06' in s
    assert 'maxChangedPixelFraction:0.0015' in s
    assert 'rankAutomaticPaletteMergeCandidates' in s

@pytest.mark.skipif(shutil.which("node") is None,reason="Node required")
def test_ranking_ignores_bad_palettes_width_aspect_and_large_donors():
    r=run_js(r"""
const core=require(process.argv[1])._core;
function row(d,rgb,other={}){
  const gates={area:false,minSide:true,aspect:true,palette:true,
   protectedArea:true,paletteDistance:true,paletteError:true,recolorBudget:true,
   sourceRgbDistance:true,sharedEdges:true,sharedRatio:true};
  return {donorId:d,recipientId:d+1,crossPalette:false,donorAreaFraction:.04,
     donorPixels:400,sourceRgbDistance:rgb,sharedPerimeterFraction:.4,
     gates,...other};
}
const ranked=core.rankAutomaticPaletteMergeCandidates([
  row(5,3),row(2,2),row(8,1,{crossPalette:true}),
  row(10,1,{gates:{...row(0,0).gates,minSide:false}}),
  row(14,1,{donorAreaFraction:.07}),
  row(1,2,{sharedPerimeterFraction:.5}),
],{maxCandidates:3});
const invalid=(()=>{try{core.rankAutomaticPaletteMergeCandidates([],{
 maxDonorFraction:.2});return false}catch(e){return true}})();
process.stdout.write(JSON.stringify({ranked,invalid}));
""")
    assert [x["donorId"] for x in r["ranked"]]==[1,2,5]
    assert r["invalid"]

@pytest.mark.skipif(shutil.which("node") is None,reason="Node required")
def test_thin_diagonal_staff_is_auto_protected_without_character_specific_roi():
    r=run_js(r"""
const core=require(process.argv[1])._core;
const w=80,h=80;
const baseline=new Uint8ClampedArray(w*h*4);
for(let i=0;i<w*h;i++){
 baseline[4*i]=170;baseline[4*i+1]=172;baseline[4*i+2]=180;baseline[4*i+3]=255;
}
for(let y=10;y<65;y++){
 for(let dx=0;dx<3;dx++){
   const x=5+Math.round((y-10)*.48)+dx,i=4*(y*w+x);
   baseline[i]=68;baseline[i+1]=37;baseline[i+2]=36;
 }
}
const thin=core.protectThinColorComponents(baseline,w,h);
const staffPixel=31*w+15;
const changed=baseline.slice();
changed[4*staffPixel]=170;changed[4*staffPixel+1]=172;
changed[4*staffPixel+2]=180;
global.MinimalizerOpenCvRaster={renderShapesRgba:(shapes)=>shapes[0].pixels};
const check=(extra)=>core.compareRegionRenderFidelity(
 [{pixels:baseline}],[{pixels:changed}],w,h,{
 maxChangedPixelFraction:.9,maxRgbMeanAbsoluteError:255,
 maxColorMassDeltaFraction:.9,...extra,
});
process.stdout.write(JSON.stringify({
 staffProtected:thin.mask[staffPixel],componentCount:thin.protectedComponents,
 unguarded:check({}),guarded:check({protectThinComponents:true}),
}));
""")
    assert r["staffProtected"]==1
    assert r["componentCount"]>=1
    assert r["unguarded"]["pass"]
    assert not r["guarded"]["pass"]
    assert r["guarded"]["reason"]=="protected_feature"
    assert r["guarded"]["thinChanged"]>=1

@pytest.mark.skipif(shutil.which("node") is None,reason="Node required")
def test_auto_rejects_wrong_modes_before_processing_source():
    r=run_js(r"""
const core=require(process.argv[1])._core,rgba=new Uint8ClampedArray(4*4*4);
const values=[
 {autoSelectiveMerge:true,structuralMode:"spectral-exact",canonicalContourLite:true,geometryMode:"facet-safe"},
 {autoSelectiveMerge:true,structuralMode:"l0-lite-jacobi",canonicalContourLite:true,geometryMode:"corner-aware"},
 {autoSelectiveMerge:true,structuralMode:"l0-lite-jacobi",canonicalContourLite:false,geometryMode:"facet-safe"},
 {autoSelectiveMerge:true,structuralMode:"l0-lite-jacobi",canonicalContourLite:true,geometryMode:"facet-safe",selectiveRegionMerge:true},
];
const errors=values.map(opts=>{try{core.analyzeRgba(rgba,4,4,opts);return ""}
catch(e){return String(e.message)}});
process.stdout.write(JSON.stringify({errors}));
""")
    assert all("V22 automatic profile requires unchanged Facet preprocessing" in e for e in r["errors"])
