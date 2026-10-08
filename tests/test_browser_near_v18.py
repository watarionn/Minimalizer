from __future__ import annotations
import json, subprocess, shutil
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
ENGINE=ROOT/"web/static/browser-fallback.js"
APP=ROOT/"web/static/app.js"

def node(source):
    p=subprocess.run(["node","-e",source,str(ENGINE)],capture_output=True,text=True,check=True,timeout=60)
    return json.loads(p.stdout)

def test_v18_opt_in_only():
    app=APP.read_text(encoding="utf-8")
    engine=ENGINE.read_text(encoding="utf-8")
    assert 'browserFallbackQualityParam === "near"' in app
    assert 'allowNearPalette: true' in app
    assert "maxChangedPixelFraction: 0.0015" in engine
    assert "maxRegionColorError: 8" in engine
    assert 'allowNearPalette: false' in engine

@pytest.mark.skipif(not shutil.which("node"),reason="node absent")
def test_cross_palette_region_recolor_budget_and_unchanged_palette():
    result=node(r"""
const core=require(process.argv[1])._core;
const w=100,h=100,N=w*h;
const labels=new Int32Array(N),slots=[[],[]];
for(let y=0;y<h;y++)for(let x=0;x<w;x++){
 const i=y*w+x,id=x>=25&&x<35&&y>=25&&y<35?1:0;
 labels[i]=id;slots[id].push(i);
}
function group(id,rgb){
 return {id,sourceId:id,label:id,pixels:slots[id],count:slots[id].length,
 minX:id?25:0,minY:id?25:0,maxX:id?34:99,maxY:id?34:99,
 borderTouches:id?0:400,rgb,lab:[40,0,0]};
}
const base={built:{components:[group(0,[100,102,105]),group(1,[103,105,108])],
 componentIds:labels},groups:[],selectedCount:2};
const palette={colors:[[120,120,120],[125,122,120]],
 assignments:[0,1],palette:[{rgb:[120,120,120]},{rgb:[125,122,120]}]};
function run(changes){
 const copy={...base,built:{...base.built,components:base.built.components.map(z=>({
  ...z,pixels:z.pixels.slice(),rgb:z.rgb.slice()
 }))}};
 return core.mergeAcceptedPaletteRegions(copy,palette,w,h,{
 allowNearPalette:true,maxSmallFraction:.02,maxChangedPixelFraction:.02,
 maxRegionColorError:8,maxMerges:1,...changes
 });
}
const ok=run({});
const tooMuch=run({maxChangedPixelFraction:.0001});
const color=run({maxRegionColorError:2});
const strict=run({allowNearPalette:false});
process.stdout.write(JSON.stringify({
 accepted:ok.metrics.applied,changed:ok.metrics.changedPixels,
 color:ok.palette.colors,assignment:ok.palette.assignments,
 rejectedBudget:tooMuch.metrics.applied,rejectedColor:color.metrics.applied,
 rejectedStrict:strict.metrics.applied,baselineIntact:base.built.components.length===2
}));
""")
    assert result["accepted"] == 1
    assert result["changed"] == 100
    assert result["color"] == [[120,120,120]]
    assert result["assignment"] == [0]
    assert result["rejectedBudget"] == 0
    assert result["rejectedColor"] == 0
    assert result["rejectedStrict"] == 0
    assert result["baselineIntact"]

@pytest.mark.skipif(not shutil.which("node"),reason="node absent")
def test_near_mode_rejects_large_palette_difference():
    r=node(r"""
const core=require(process.argv[1])._core;
const w=100,h=100,labels=new Int32Array(w*h),pixels=[[],[]];
for(let y=0;y<h;y++)for(let x=0;x<w;x++){
 const i=y*w+x,id=(x>=30&&x<40&&y>=30&&y<40)?1:0;
 labels[i]=id;pixels[id].push(i);
}
const c=(id)=>({id,sourceId:id,label:id,pixels:pixels[id],
 count:pixels[id].length,minX:id?30:0,minY:id?30:0,maxX:id?39:99,maxY:id?39:99,
 borderTouches:id?0:400,rgb:id?[120,120,120]:[118,118,118],lab:[40,0,0]});
const base={built:{components:[c(0),c(1)],componentIds:labels},selectedCount:2,groups:[]};
const p={assignments:[0,1],colors:[[20,20,20],[230,230,230]],palette:[]};
const res=core.mergeAcceptedPaletteRegions(base,p,w,h,{
 allowNearPalette:true,maxSmallFraction:.02,maxChangedPixelFraction:.02,maxMerges:1
});
process.stdout.write(JSON.stringify(res.metrics));
""")
    assert r["applied"] == 0
    assert r["candidateNearPalette"] >= 1
    assert r["rejectedColorFidelity"] >= 1
