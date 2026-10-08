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


def test_shape_opt_in_keeps_other_profiles_and_metadata():
    app = APP.read_text(encoding="utf-8")
    engine = ENGINE.read_text(encoding="utf-8")
    assert 'browserFallbackQualityParam === "shape"' in app
    assert 'browserFallbackQualityProfile() === "shape"' in app
    assert 'browserFallbackCanonicalContourLite()' in app
    assert 'browserFallbackQualityProfile() === "shape" ? "corner-aware" : "baseline"' in app
    assert 'SHAPE (experimental)' in app
    assert 'geometryMode: "baseline"' in engine
    assert "cornerPrunedVertices" in engine
    assert 'X-Minimalizer-Contour-Geometry-Mode' in engine
    assert 'X-Minimalizer-Browser-Quality-Profile' in engine
    assert 'config.geometryMode === "corner-aware"' in engine


@pytest.mark.skipif(shutil.which("node") is None, reason="node unavailable")
def test_corner_aware_candidate_removes_short_stair_and_protects_major_corner():
    result = _node(r"""
const contour = require(process.argv[2]);
const opts = {...contour.DEFAULTS};
const raw = [
 [0,0], [1,0], [2,1], [3,0], [4,1], [5,0], [6,0],
 [8,0], [10,0], [12,0], [12,6], [12,12]
];
const first = contour._core.cornerAwareLineCandidate(raw,raw,1.65,opts);
const second = contour._core.cornerAwareLineCandidate(raw,raw,1.65,opts);
process.stdout.write(JSON.stringify({raw,first,second}));
""")
    assert result["first"] == result["second"]
    assert len(result["first"]) < len(result["raw"])
    assert result["first"][0] == [0, 0]
    assert result["first"][-1] == [12, 12]
    assert [12, 0] in result["first"]  # strong 90-degree corner with long arms


@pytest.mark.skipif(shutil.which("node") is None, reason="node unavailable")
def test_shape_does_not_change_structural_ownership_or_palette():
    result = _node(r"""
global.MinimalizerCanonicalContour=require(process.argv[2]);
global.MinimalizerOpenCvRaster=require(process.argv[3]);
const engine=require(process.argv[1]);
const w=52,h=48,rgba=new Uint8ClampedArray(w*h*4);
for(let y=0;y<h;y++)for(let x=0;x<w;x++){
 const i=(y*w+x)*4, boundary=24+(y%6<3?1:-1);
 const c=x<boundary?[220,55,45]:[50,110,220];
 rgba[i]=c[0];rgba[i+1]=c[1];rgba[i+2]=c[2];rgba[i+3]=255;
}
const opts={
 ...engine.DEFAULTS,structuralMode:"l0-lite-jacobi",canonicalContourLite:true,
 slicTargetMin:24,slicTargetMax:24,slicMinAverageArea:4,
 hierarchyTargetMin:8,hierarchyTargetMax:10,maxShapes:10,
};
const sharp=engine._core.analyzeRgba(rgba,w,h,opts);
const shape=engine._core.analyzeRgba(rgba,w,h,{...opts,geometryMode:"corner-aware"});
const repeated=engine._core.analyzeRgba(rgba,w,h,{...opts,geometryMode:"corner-aware"});
const digest=(r)=>r.shapes.map(s=>({
 id:s.id,sourceId:s.sourceId,count:s.count,sourceRgb:s.sourceRgb,
 rgb:s.rgb,paletteId:s.paletteId,borderTouches:s.borderTouches
}));
process.stdout.write(JSON.stringify({
 sameOwners:JSON.stringify(digest(sharp))===JSON.stringify(digest(shape)),
 samePalette:JSON.stringify(sharp.centers)===JSON.stringify(shape.centers),
 sameBackground:JSON.stringify(sharp.background)===JSON.stringify(shape.background),
 sameFullShape:JSON.stringify(shape.shapes)===JSON.stringify(repeated.shapes),
 sharpContour:sharp.metrics.contourMethod,shapeContour:shape.metrics.contourMethod,
 sharpGeometry:sharp.metrics.contourGeometryMode,shapeGeometry:shape.metrics.contourGeometryMode,
 structural:shape.metrics.structuralPreprocess,original:sharp.metrics.contourSharedVertexCount,
 simplified:shape.metrics.contourSharedVertexCount,minIoU:shape.metrics.contourMinRegionIoU,
 pruned:shape.metrics.cornerPrunedVertices, rejected:shape.metrics.cornerRejectedCandidates
}));
""")
    assert result["sameOwners"] and result["samePalette"] and result["sameBackground"]
    assert result["sameFullShape"]
    assert result["sharpContour"] == result["shapeContour"] == "canonical-shared-chain"
    assert result["sharpGeometry"] == "baseline"
    assert result["shapeGeometry"] == "corner-aware"
    assert result["structural"] == "l0-lite-jacobi"
    assert result["simplified"] <= result["original"]
    assert result["minIoU"] >= 0.90
    assert result["pruned"] >= 0
    assert result["rejected"] >= 0


@pytest.mark.skipif(shutil.which("node") is None, reason="node unavailable")
def test_shape_fails_closed_on_misconfigured_or_missing_geometry():
    result = _node(r"""
const api=require(process.argv[1]);
const w=8,h=8,rgba=new Uint8ClampedArray(w*h*4);
for(let i=0;i<w*h;i++)rgba[i*4+3]=255;
const check=opts=>{try{api._core.analyzeRgba(rgba,w,h,opts);return null}
  catch(e){return String(e.message)}};
const noCanonical=check({geometryMode:"corner-aware",structuralMode:"l0-lite-jacobi"});
const exactMix=check({geometryMode:"corner-aware",structuralMode:"spectral-exact",canonicalContourLite:true});
const missingRuntime=check({geometryMode:"corner-aware",structuralMode:"l0-lite-jacobi",canonicalContourLite:true});
global.MinimalizerCanonicalContour=require(process.argv[2]);
const noRaster=check({geometryMode:"corner-aware",structuralMode:"l0-lite-jacobi",canonicalContourLite:true});
process.stdout.write(JSON.stringify({noCanonical,exactMix,missingRuntime,noRaster}));
""")
    assert "requires Lite preprocessing" in result["noCanonical"]
    assert "requires Lite preprocessing" in result["exactMix"]
    assert "Sharp Lite requires shared-boundary" in result["missingRuntime"]
    assert "Sharp Lite requires shared-boundary" in result["noRaster"]


@pytest.mark.skipif(shutil.which("node") is None, reason="node unavailable")
def test_invalid_canonical_geometry_mode_refused():
    result = _node(r"""
const contour=require(process.argv[2]);
const labels=new Int32Array(16);labels.fill(0);
let message="";
try{contour.simplifyLabels(labels,4,4,1,{geometryMode:"unclear"});}
catch(e){message=String(e.message);}
process.stdout.write(JSON.stringify({message}));
""")
    assert "Unsupported geometry mode" in result["message"]
