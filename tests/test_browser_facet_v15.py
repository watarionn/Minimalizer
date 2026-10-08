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


def test_facet_quality_opt_in_and_safe_defaults():
    app = APP.read_text(encoding="utf-8")
    engine = ENGINE.read_text(encoding="utf-8")
    contour = CONTOUR.read_text(encoding="utf-8")
    assert 'browserFallbackQualityParam === "facet"' in app
    assert '["exact", "sharp", "shape", "facet", "selective", "near", "auto"].includes(quality)' in app
    assert '["sharp", "shape", "facet", "selective", "near", "auto"].includes(browserFallbackQualityProfile())' in app
    assert 'browserFallbackQualityProfile() === "facet" ? "facet-safe"' in app
    assert 'FACET (experimental)' in app
    assert 'geometryMode: "baseline"' in engine
    assert 'config.geometryMode === "facet-safe"' in engine
    assert 'X-Minimalizer-Contour-Facet-Removed-Vertices' in engine
    assert 'X-Minimalizer-Contour-Geometry-Mode' in engine
    assert 'facetMaxIoULoss: 0.0025' in contour
    assert 'facetTrialsPerChain: 14' in contour


@pytest.mark.skipif(shutil.which("node") is None, reason="Node unavailable")
def test_facet_proposes_angular_straights_but_not_major_corners():
    result = _node(r"""
const c=require(process.argv[2]);
const opts={...c.DEFAULTS};
const raw=[
 [0,0],[1,1],[2,0],[3,1],[4,0],[5,1],[6,0],[8,0],
 [10,0],[12,0],[12,2],[12,4],[12,6],[12,8]
];
const edits=c._core.facetCandidateEdits(raw,raw,opts);
const again=c._core.facetCandidateEdits(raw,raw,opts);
const kept=edits.map(x=>x.index);
process.stdout.write(JSON.stringify({edits,again,kept}));
""")
    assert result["edits"] == result["again"]
    assert result["edits"]
    assert 9 not in result["kept"]  # corner from a long horizontal side to vertical
    assert all(0 < item["index"] < 13 for item in result["edits"])
    assert all(item["maxDeviation"] <= 2.35 for item in result["edits"])


@pytest.mark.skipif(shutil.which("node") is None, reason="Node unavailable")
def test_facet_preserves_original_lite_ownership_palette_and_v14_geometry_contract():
    result = _node(r"""
global.MinimalizerCanonicalContour=require(process.argv[2]);
global.MinimalizerOpenCvRaster=require(process.argv[3]);
const engine=require(process.argv[1]);
const w=48,h=40,rgba=new Uint8ClampedArray(w*h*4);
for(let y=0;y<h;y++)for(let x=0;x<w;x++){
 const i=(y*w+x)*4, boundary=21+(y%8<4?2:-2);
 const c=x<boundary?[230,55,42]:[38,160,210];
 rgba[i]=c[0];rgba[i+1]=c[1];rgba[i+2]=c[2];rgba[i+3]=255;
}
const opts={
 ...engine.DEFAULTS,structuralMode:"l0-lite-jacobi",canonicalContourLite:true,
 slicTargetMin:28,slicTargetMax:28,slicMinAverageArea:4,
 hierarchyTargetMin:8,hierarchyTargetMax:12,maxShapes:12,
};
const shape=engine._core.analyzeRgba(rgba,w,h,{...opts,geometryMode:"corner-aware"});
const facet=engine._core.analyzeRgba(rgba,w,h,{...opts,geometryMode:"facet-safe"});
const again=engine._core.analyzeRgba(rgba,w,h,{...opts,geometryMode:"facet-safe"});
const owner=(r)=>r.shapes.map(s=>({
  id:s.id,sourceId:s.sourceId,count:s.count,
  sourceRgb:s.sourceRgb,rgb:s.rgb,paletteId:s.paletteId,borderTouches:s.borderTouches
}));
process.stdout.write(JSON.stringify({
 owners:JSON.stringify(owner(shape))===JSON.stringify(owner(facet)),
 centers:JSON.stringify(shape.centers)===JSON.stringify(facet.centers),
 background:JSON.stringify(shape.background)===JSON.stringify(facet.background),
 repeatable:JSON.stringify(facet.shapes)===JSON.stringify(again.shapes),
 shapeMode:shape.metrics.contourGeometryMode,
 facetMode:facet.metrics.contourGeometryMode,
 structural:facet.metrics.structuralPreprocess,
 contour:facet.metrics.contourMethod,
 noMoreVertices:facet.metrics.vertexCount <= shape.metrics.vertexCount,
 iou:facet.metrics.contourMinRegionIoU,
 removed:facet.metrics.facetRemovedVertices,
 trials:facet.metrics.facetTrialCount,
 rejections:facet.metrics.facetRejectedCandidates
}));
""")
    assert result["owners"] and result["centers"] and result["background"]
    assert result["repeatable"]
    assert result["shapeMode"] == "corner-aware"
    assert result["facetMode"] == "facet-safe"
    assert result["structural"] == "l0-lite-jacobi"
    assert result["contour"] == "canonical-shared-chain"
    assert result["noMoreVertices"]
    assert result["iou"] >= 0.90
    assert result["trials"] >= result["removed"] >= 0
    assert result["rejections"] >= 0


@pytest.mark.skipif(shutil.which("node") is None, reason="Node unavailable")
def test_facet_fails_closed_on_mixed_structure_and_missing_runtime():
    result = _node(r"""
const engine=require(process.argv[1]);
const w=8,h=8,rgba=new Uint8ClampedArray(w*h*4);
for(let i=0;i<w*h;i++)rgba[i*4+3]=255;
const test=(opt)=>{try{engine._core.analyzeRgba(rgba,w,h,opt);return null}
catch(e){return String(e.message)}};
const noCanon=test({geometryMode:"facet-safe",structuralMode:"l0-lite-jacobi"});
const spectral=test({geometryMode:"facet-safe",structuralMode:"spectral-exact",canonicalContourLite:true});
const missingModule=test({geometryMode:"facet-safe",structuralMode:"l0-lite-jacobi",canonicalContourLite:true});
global.MinimalizerCanonicalContour=require(process.argv[2]);
const missingRaster=test({geometryMode:"facet-safe",structuralMode:"l0-lite-jacobi",canonicalContourLite:true});
process.stdout.write(JSON.stringify({noCanon,spectral,missingModule,missingRaster}));
""")
    assert "requires Lite preprocessing" in result["noCanon"]
    assert "requires Lite preprocessing" in result["spectral"]
    assert "requires shared-boundary" in result["missingModule"]
    assert "requires shared-boundary" in result["missingRaster"]


@pytest.mark.skipif(shutil.which("node") is None, reason="Node unavailable")
def test_facet_refuses_unknown_geometry_mode():
    result = _node(r"""
const contour=require(process.argv[2]);
const labels=new Int32Array(16);
let error="";
try{contour.simplifyLabels(labels,4,4,1,{geometryMode:"facet-random"});}
catch(e){error=String(e.message)}
process.stdout.write(JSON.stringify({error}));
""")
    assert "Unsupported geometry mode" in result["error"]
