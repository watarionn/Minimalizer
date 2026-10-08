"""v23 isolated major-color-plane geometry and preservation contracts."""
from __future__ import annotations
import json
import subprocess
import shutil
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
BROWSER=ROOT/"web/static/browser-fallback.js"
CONTOUR=ROOT/"web/static/canonical-contour.js"
APP=ROOT/"web/static/app.js"

def js(code):
    p=subprocess.run(["node","-e",code,str(BROWSER),str(CONTOUR)],
                     capture_output=True,text=True,check=True,timeout=70)
    return json.loads(p.stdout)

def test_profile_is_only_opt_in_and_facet_unchanged():
    app=APP.read_text(encoding="utf-8")
    contour=CONTOUR.read_text(encoding="utf-8")
    browser=BROWSER.read_text(encoding="utf-8")
    assert 'browserFallbackQualityParam === "plane"' in app
    assert 'browserFallbackQualityProfile() === "plane" ? "plane-safe"' in app
    assert 'geometryMode === "plane-safe"' in browser
    assert 'planeMajorRegionFraction: 0.035' in contour
    assert '"plane-safe"' in contour
    assert 'facetDeviationPx: 2.35' in contour
    assert 'facetMaxIoULoss: 0.0025' in contour
    assert 'maxSilhouetteChangedPixels:0' in browser
    assert 'protectThinComponents:true' in browser
    assert 'maxChangedPixelFraction:0.008' in browser
    assert 'planeQualityGate: analysis.metrics.planeQualityGate' in browser

@pytest.mark.skipif(shutil.which("node") is None,reason="Node.js missing")
def test_plane_mode_has_deterministic_shared_chain_and_region_iou_gate():
    result=js(r"""
const contour=require(process.argv[2]);
const n=48,labels=new Int32Array(n*n);
for(let y=0;y<n;y++)for(let x=0;x<n;x++){
  const i=y*n+x;
  labels[i]=(x>=8&&x<33&&y>=10&&y<35)?1:0;
}
const facet=contour.simplifyLabels(labels,n,n,2,{geometryMode:"facet-safe"});
const plane=contour.simplifyLabels(labels,n,n,2,{geometryMode:"plane-safe"});
const repeat=contour.simplifyLabels(labels,n,n,2,{geometryMode:"plane-safe"});
process.stdout.write(JSON.stringify({
 mode:plane.metrics.geometryMode,
 baseline:facet.metrics.simplifiedVertexCount,
 refined:plane.metrics.simplifiedVertexCount,
 minIoU:plane.metrics.minRegionIoU,
 deterministic:JSON.stringify(plane.loopsByRegion)===JSON.stringify(repeat.loopsByRegion),
 defaultThreshold:contour.DEFAULTS.facetDeviationPx,
 planeThreshold:contour.DEFAULTS.planeDeviationPx
}));
""")
    assert result["mode"]=="plane-safe"
    assert result["deterministic"]
    assert result["minIoU"]>=.90
    assert result["defaultThreshold"]==2.35
    assert result["planeThreshold"]==3.2

@pytest.mark.skipif(shutil.which("node") is None,reason="Node.js missing")
def test_plane_rejects_bad_configs_and_leaves_lite_facet_behavior_untouched():
    result=js(r"""
const engine=require(process.argv[1])._core;
const contour=require(process.argv[2]);
const w=25,h=25,rgba=new Uint8ClampedArray(w*h*4);
for(let i=0;i<w*h;i++){
 const shade=Math.floor((i%w)/5)*30;
 rgba[i*4]=shade;rgba[i*4+1]=shade;rgba[i*4+2]=shade;rgba[i*4+3]=255;
}
const scenarios=[
 {structuralMode:"spectral-exact",canonicalContourLite:true,geometryMode:"plane-safe"},
 {structuralMode:"l0-lite-jacobi",canonicalContourLite:false,geometryMode:"plane-safe"},
 {structuralMode:"l0-lite-jacobi",canonicalContourLite:true,geometryMode:"plane-safe",autoSelectiveMerge:true},
];
const blocked=scenarios.map(o=>{try{engine.analyzeRgba(rgba,w,h,o);return false}
 catch(e){return String(e.message).includes("V23 plane-safe needs")||String(e.message).includes("V22 automatic profile")}})
const old=contour.simplifyLabels(new Int32Array(w*h),w,h,1,{geometryMode:"facet-safe"});
process.stdout.write(JSON.stringify({blocked,oldMode:old.metrics.geometryMode}));
""")
    assert all(result["blocked"])
    assert result["oldMode"]=="facet-safe"
