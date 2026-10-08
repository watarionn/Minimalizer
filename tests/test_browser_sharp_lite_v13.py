from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "web/static/browser-fallback.js"
CONTOUR = ROOT / "web/static/canonical-contour.js"
RASTER = ROOT / "web/static/opencv-fill-raster.js"
APP = ROOT / "web/static/app.js"


def _node(source: str) -> dict:
    result = subprocess.run(
        ["node", "-e", source, str(ENGINE), str(CONTOUR), str(RASTER)],
        capture_output=True, text=True, check=True, timeout=60,
    )
    return json.loads(result.stdout)


def test_sharp_lite_opt_in_contract_and_unchanged_profiles():
    app = APP.read_text(encoding="utf-8")
    engine = ENGINE.read_text(encoding="utf-8")
    assert 'browserFallbackQualityParam === "sharp"' in app
    # The opt-in quality family can expand without changing the Sharp contract.
    assert 'return quality === "exact" || quality === "sharp" || quality === "shape" ? quality : "lite"' in app
    assert 'browserFallbackQualityProfile() === "sharp"' in app
    assert 'browserFallbackQualityProfile() === "exact"' in app
    assert 'structuralMode: browserFallbackStructuralMode()' in app
    assert 'canonicalContourLite: browserFallbackCanonicalContourLite()' in app
    assert 'canonicalContourLite: false' in engine
    assert 'X-Minimalizer-Browser-Quality-Profile' in engine
    assert 'SHARP LITE (experimental)' in app


@pytest.mark.skipif(shutil.which("node") is None, reason="Node unavailable")
def test_sharp_lite_is_same_structural_regions_palette_and_owner_as_lite():
    result = _node(r"""
global.MinimalizerOpenCvRaster = require(process.argv[3]);
global.MinimalizerCanonicalContour = require(process.argv[2]);
const api = require(process.argv[1]);
const w=54,h=45,rgba=new Uint8ClampedArray(w*h*4);
for(let y=0;y<h;y++)for(let x=0;x<w;x++){
  const i=(y*w+x)*4, band=x < 15 ? 0 : x < 28+(y%6<3?1:-1) ? 1 : 2;
  const colors=[[233,70,40],[40,145,70],[45,65,170]], c=colors[band];
  rgba[i]=c[0]+((x+y)%3);rgba[i+1]=c[1];rgba[i+2]=c[2];rgba[i+3]=255;
}
const options={...api.DEFAULTS,structuralMode:"l0-lite-jacobi",
  slicTargetMin:32,slicTargetMax:32,slicMinAverageArea:4,
  hierarchyTargetMin:9,hierarchyTargetMax:16,maxShapes:16};
const normal=api._core.analyzeRgba(rgba,w,h,options);
const sharp=api._core.analyzeRgba(rgba,w,h,{...options,canonicalContourLite:true});
const summary=(r)=>r.shapes.map(s=>({
  id:s.id,sourceId:s.sourceId,count:s.count,
  sourceRgb:s.sourceRgb,rgb:s.rgb,paletteId:s.paletteId,
  borderTouches:s.borderTouches
}));
const again=api._core.analyzeRgba(rgba,w,h,{...options,canonicalContourLite:true});
process.stdout.write(JSON.stringify({
  defaultMethod:normal.metrics.contourMethod,
  sharpMethod:sharp.metrics.contourMethod,
  defaultStructural:normal.metrics.structuralPreprocess,
  sharpStructural:sharp.metrics.structuralPreprocess,
  sameCenters:JSON.stringify(normal.centers)===JSON.stringify(sharp.centers),
  sameOwnerColors:JSON.stringify(summary(normal))===JSON.stringify(summary(sharp)),
  sameBackground:JSON.stringify(normal.background)===JSON.stringify(sharp.background),
  sameCanonical:JSON.stringify(sharp.shapes)===JSON.stringify(again.shapes),
  sharedVertices:sharp.metrics.contourSharedVertexCount,
  originalVertices:sharp.metrics.contourOriginalVertexCount,
  minIoU:sharp.metrics.contourMinRegionIoU,
}));
""")
    assert result["defaultMethod"] == "legacy-independent-rings"
    assert result["sharpMethod"] == "canonical-shared-chain"
    assert result["defaultStructural"] == result["sharpStructural"] == "l0-lite-jacobi"
    assert result["sameCenters"]
    assert result["sameOwnerColors"]
    assert result["sameBackground"]
    assert result["sameCanonical"]
    assert result["sharedVertices"] <= result["originalVertices"]
    assert result["minIoU"] >= 0.90


@pytest.mark.skipif(shutil.which("node") is None, reason="Node unavailable")
def test_sharp_lite_fails_closed_when_contour_or_raster_missing():
    result = _node(r"""
const engine=require(process.argv[1]);
const w=4,h=4,rgba=new Uint8ClampedArray(w*h*4);
for(let i=0;i<w*h;i++)rgba[i*4+3]=255;
let withoutBoth="",withoutRaster="";
try{engine._core.analyzeRgba(rgba,w,h,{canonicalContourLite:true});}
catch(e){withoutBoth=String(e.message);}
global.MinimalizerCanonicalContour=require(process.argv[2]);
try{engine._core.analyzeRgba(rgba,w,h,{canonicalContourLite:true});}
catch(e){withoutRaster=String(e.message);}
process.stdout.write(JSON.stringify({withoutBoth,withoutRaster}));
""")
    assert "requires shared-boundary contour" in result["withoutBoth"]
    assert "requires shared-boundary contour" in result["withoutRaster"]


@pytest.mark.skipif(shutil.which("node") is None, reason="Node unavailable")
def test_sharp_lite_no_spectral_module_needed():
    result = _node(r"""
global.MinimalizerOpenCvRaster=require(process.argv[3]);
global.MinimalizerCanonicalContour=require(process.argv[2]);
const engine=require(process.argv[1]);
const w=24,h=24,rgba=new Uint8ClampedArray(w*h*4);
for(let y=0;y<h;y++)for(let x=0;x<w;x++){
 const i=(y*w+x)*4, left=x < 12;
 rgba[i]=left?200:30;rgba[i+1]=left?60:120;rgba[i+2]=left?25:220;rgba[i+3]=255;
}
const s=engine._core.analyzeRgba(rgba,w,h,{canonicalContourLite:true,
 structuralMode:"l0-lite-jacobi",slicTargetMin:16,slicTargetMax:16,
 slicMinAverageArea:4,hierarchyTargetMin:4,hierarchyTargetMax:8});
process.stdout.write(JSON.stringify({
 contour:s.metrics.contourMethod,
 structural:s.metrics.structuralPreprocess,
 count:s.shapes.length
}));
""")
    assert result["contour"] == "canonical-shared-chain"
    assert result["structural"] == "l0-lite-jacobi"
    assert result["count"] > 0
