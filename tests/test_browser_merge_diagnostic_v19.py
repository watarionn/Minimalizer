from __future__ import annotations
import json,subprocess,shutil
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
ENGINE=ROOT/"web/static/browser-fallback.js"
APP=ROOT/"web/static/app.js"
def js(script):
    r=subprocess.run(["node","-e",script,str(ENGINE)],capture_output=True,text=True,check=True,timeout=60)
    return json.loads(r.stdout)
def test_v19_is_not_an_enabled_production_default():
    app=APP.read_text(encoding="utf-8")
    engine=ENGINE.read_text(encoding="utf-8")
    assert 'browserFallbackQualityParam === "near"' in app
    assert "compareRegionRenderFidelity" in engine
    assert 'selectiveMergeRenderGate' in engine
    assert 'selectiveMergeRejectReasons' in engine
    assert 'maxColorMassDeltaFraction:0.0015' in engine

@pytest.mark.skipif(not shutil.which("node"),reason="node required")
def test_reject_reason_is_deterministic_and_counts_each_pair_once():
    obj=js(r"""
const core=require(process.argv[1])._core;
const w=20,h=20,ids=new Int32Array(w*h),slots=[[],[]];
for(let y=0;y<h;y++)for(let x=0;x<w;x++){
 const i=y*w+x,k=x<10?0:1;ids[i]=k;slots[k].push(i);
}
const base={built:{componentIds:ids,components:[0,1].map(id=>({
 id,sourceId:id,count:slots[id].length,pixels:slots[id],
 minX:id?10:0,maxX:id?19:9,minY:0,maxY:19,borderTouches:40,
 rgb:id?[205,205,205]:[15,15,15],lab:[20,0,0]
}))},groups:[],selectedCount:2};
const palette={assignments:[0,1],colors:[[10,10,10],[210,210,210]],palette:[]};
const a=core.mergeAcceptedPaletteRegions(base,palette,w,h,{allowNearPalette:true});
const b=core.mergeAcceptedPaletteRegions(base,palette,w,h,{allowNearPalette:true});
process.stdout.write(JSON.stringify({a:a.metrics,b:b.metrics}));
""")
    assert obj["a"]==obj["b"]
    m=obj["a"]
    assert m["applied"]==0
    assert m["evaluated"]==1
    assert m["rejectReasons"]["donorAreaOrAspect"]==1
    assert sum(m["rejectReasons"].values())==m["rejected"]

@pytest.mark.skipif(not shutil.which("node"),reason="node required")
def test_render_gate_accepts_identity_and_rejects_pixel_changes_and_missing_raster():
    obj=js(r"""
const core=require(process.argv[1])._core;
const before=core.compareRegionRenderFidelity([],[],10,10,{});
global.MinimalizerOpenCvRaster={renderShapesRgba:(shapes,w,h)=>{
 const bytes=new Uint8ClampedArray(w*h*4);
 const change=shapes.length?shapes[0].change:0;
 for(let i=0;i<w*h;i++){bytes[i*4]=i<change?200:10;bytes[i*4+3]=255;}
 return bytes;
}};
const identical=core.compareRegionRenderFidelity([{change:0}],[{change:0}],10,10,{});
const different=core.compareRegionRenderFidelity([{change:0}],[{change:5}],10,10,{});
const relaxed=core.compareRegionRenderFidelity([{change:0}],[{change:5}],10,10,{
 maxChangedPixelFraction:.1,maxRgbMeanAbsoluteError:10,maxColorMassDeltaFraction:.1});
process.stdout.write(JSON.stringify({before,identical,different,relaxed}));
""")
    assert obj["before"]["pass"] is False
    assert obj["before"]["reason"]=="raster_missing"
    assert obj["identical"]["pass"] is True
    assert obj["identical"]["changedPixels"]==0
    assert obj["different"]["pass"] is False
    assert obj["different"]["changedPixels"]==5
    assert obj["relaxed"]["pass"] is True
