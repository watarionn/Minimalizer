"""v25 connected source-area research regression. No new pixels, colors, or face parts."""
from __future__ import annotations
import json
from pathlib import Path
import shutil
import subprocess
import pytest

ROOT=Path(__file__).resolve().parents[1]
JS=ROOT/"web/static/browser-color-groups-v25.js"
ENGINE=ROOT/"web/static/browser-fallback.js"
APP=ROOT/"web/static/app.js"
INDEX=ROOT/"web/static/index.html"

def node(code: str):
    p=subprocess.run(["node","-e",code,str(JS)],cwd=ROOT,
      capture_output=True,text=True,check=True,timeout=45)
    return json.loads(p.stdout)

def test_research_opt_in_and_original_mode_is_untouched():
    app=APP.read_text(encoding="utf-8")
    engine=ENGINE.read_text(encoding="utf-8")
    html=INDEX.read_text(encoding="utf-8")
    assert 'browserFallbackQualityParam === "group"' in app
    assert 'colorGroupRefine: browserFallbackQualityProfile() === "group"' in app
    assert "static/browser-color-groups-v25.js" in html
    assert html.index("static/browser-color-groups-v25.js")<html.index("static/browser-fallback.js")
    assert "config.colorGroupRefine===true" in engine
    assert "groupPlaneQualityGate" in engine
    assert "compareRegionRenderFidelity" in engine
    assert "colorPlaneRefine: browserFallbackQualityProfile() === \"color\"" in app

@pytest.mark.skipif(shutil.which("node") is None,reason="Node unavailable")
def test_connected_group_uses_real_source_and_preserves_original_labels():
    data=node(r"""
const group=require(process.argv[1]);
const w=40,h=40,ids=new Int32Array(w*h),rgba=new Uint8ClampedArray(w*h*4);
const pixels=[[],[]];
for(let y=0;y<h;y++)for(let x=0;x<w;x++){
 const i=y*w+x,id=x<20?0:1;ids[i]=id;pixels[id].push(i);
 const c=id?220:20;rgba[4*i]=rgba[4*i+1]=rgba[4*i+2]=c;rgba[4*i+3]=255;
}
// 3x10 source-observed material patch on the left of an existing boundary.
for(let y=16;y<26;y++)for(let x=17;x<20;x++){
 const i=y*w+x;rgba[4*i]=rgba[4*i+1]=rgba[4*i+2]=220;
}
const built={componentIds:ids,components:pixels.map((p,id)=>({
 id,pixels:p,count:p.length,minX:id?20:0,minY:0,maxX:id?39:19,maxY:39,borderTouches:80
}))},palette={colors:[[20,20,20],[220,220,220]],assignments:[0,1]};
const opts={minGroupPixels:4,lowerYFraction:.2,maxDepth:6};
const a=group.propose(built,palette,rgba,w,h,opts);
const b=group.propose(built,palette,rgba,w,h,opts);
const moved=a.metrics.pixels;
process.stdout.write(JSON.stringify({
 count:a.metrics.movedPixels,groups:a.metrics.groups,candidates:a.metrics.candidates,
 allSourcePositive:moved.every(i=>rgba[4*i]===220&&ids[i]===0&&a.built.componentIds[i]===1),
 originalIntact:ids[19+20*w]===0,originalPaletteIntact:palette.colors[0][0]===20,
 total:a.built.components.reduce((n,c)=>n+c.count,0),
 repeat:JSON.stringify(a.metrics)===JSON.stringify(b.metrics),
 sameLabelBytes:Array.from(a.built.componentIds).every((v,i)=>v===b.built.componentIds[i])
}));
""")
    assert data["count"]>=4
    assert data["groups"]==1
    assert data["candidates"]>=1
    assert data["allSourcePositive"] and data["originalIntact"] and data["originalPaletteIntact"]
    assert data["total"]==1600
    assert data["repeat"] and data["sameLabelBytes"]

@pytest.mark.skipif(shutil.which("node") is None,reason="Node unavailable")
def test_bridge_removal_rejected_and_no_evidence_is_byte_identical():
    data=node(r"""
const group=require(process.argv[1]);
const w=40,h=40,ids=new Int32Array(w*h),rgba=new Uint8ClampedArray(w*h*4),pixels=[[],[]];
for(let y=0;y<h;y++)for(let x=0;x<w;x++){
 const i=y*w+x,id=x<6?0:1;ids[i]=id;pixels[id].push(i);
 const c=id?220:20;rgba[4*i]=rgba[4*i+1]=rgba[4*i+2]=c;rgba[4*i+3]=255;
}
const built={componentIds:ids,components:pixels.map((p,id)=>({
 id,pixels:p,count:p.length,minX:id?6:0,minY:0,maxX:id?39:5,maxY:39,borderTouches:70
}))},palette={colors:[[20,20,20],[220,220,220]]};
const opts={lowerYFraction:.2,minGroupPixels:4,maxDepth:8,maxSeeds:20};
const unchanged=group.propose(built,palette,rgba,w,h,opts);
for(let x=0;x<6;x++){const i=20*w+x;rgba[4*i]=rgba[4*i+1]=rgba[4*i+2]=220;}
const split=group.propose(built,palette,rgba,w,h,opts);
const invalid=[];
for(const opt of [{maxGroupPixels:1},{maxDepth:0},{lowerYFraction:-1},{minGroupPixels:401}]){
 try {group.propose(built,palette,rgba,w,h,opt);invalid.push(false)}
 catch {invalid.push(true)}
}
process.stdout.write(JSON.stringify({
 unchanged:unchanged.built===built,
 moved:split.metrics.movedPixels,unchangedSplit:split.built===built,
 topologyRejected:split.metrics.topologyRejected,invalid
}));
""")
    assert data=={"unchanged":True,"moved":0,"unchangedSplit":True,
      "topologyRejected":1,"invalid":[True,True,True,True]}

@pytest.mark.skipif(shutil.which("node") is None,reason="Node unavailable")
def test_rendered_source_gate_rejects_imaginary_quality_gain():
    data=node(r"""
const group=require(process.argv[1]);
const src=new Uint8ClampedArray([20,20,20,255,50,50,50,255]);
const before=new Uint8ClampedArray([20,20,20,255,50,50,50,255]);
const good=new Uint8ClampedArray([20,20,20,255,50,50,50,255]);
const bad=new Uint8ClampedArray([220,220,220,255,50,50,50,255]);
globalThis.MinimalizerOpenCvRaster={renderShapesRgba:shapes=>shapes===0?before:bad};
const regression=group.compareSource(src,0,1,2,1);
globalThis.MinimalizerOpenCvRaster={renderShapesRgba:shapes=>shapes===0?before:good};
const nochange=group.compareSource(src,0,1,2,1);
process.stdout.write(JSON.stringify({
 regression:regression.reason,regressionPass:regression.pass,
 unchanged:nochange.reason,unchangedPass:nochange.pass
}));
""")
    assert data=={"regression":"source_rgb_regression","regressionPass":False,
      "unchanged":"no_visible_change","unchangedPass":False}
