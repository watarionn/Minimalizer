"""Research v24: source-color supported pixel ownership and strict rendered rollback."""
from __future__ import annotations
import json,subprocess,shutil
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
ENGINE=ROOT/"web/static/browser-fallback.js"
APP=ROOT/"web/static/app.js"

def node(script):
    p=subprocess.run(["node","-e",script,str(ENGINE)],capture_output=True,text=True,check=True,timeout=75)
    return json.loads(p.stdout)

def test_color_boundary_mode_opt_in_only():
    a=APP.read_text(encoding="utf-8")
    b=ENGINE.read_text(encoding="utf-8")
    assert 'browserFallbackQualityParam === "color"' in a
    assert 'colorPlaneRefine: browserFallbackQualityProfile() === "color"' in a
    assert 'colorPlaneRefine===true' in b
    assert 'refineColorPlaneOwnership' in b
    assert 'protectThinComponents:true' in b
    assert 'colorPlaneQualityGate: analysis.metrics.colorPlaneQualityGate' in b

@pytest.mark.skipif(shutil.which("node") is None,reason="Node missing")
def test_source_supported_pixel_moves_preserve_components_and_palette():
    x=node(r"""
const core=require(process.argv[1])._core;
const w=40,h=40,labels=new Int32Array(w*h),rgba=new Uint8ClampedArray(w*h*4);
const pixels=[[],[]];
for(let y=0;y<h;y++)for(let x=0;x<w;x++) {
 const i=y*w+x,k=x<20?0:1;labels[i]=k;pixels[k].push(i);
 rgba[4*i]=k===0?30:210;rgba[4*i+1]=k===0?50:215;rgba[4*i+2]=k===0?65:220;rgba[4*i+3]=255;
}
for(let y=15;y<22;y++){const i=y*w+19;rgba[4*i]=210;rgba[4*i+1]=215;rgba[4*i+2]=220;}
const input={componentIds:labels,components:pixels.map((p,id)=>({
 id,sourceId:id,pixels:p,count:p.length,minX:id?20:0,minY:0,maxX:id?39:19,maxY:39,
 borderTouches:80,rgb:id?[210,215,220]:[30,50,65]
}))};
const palette={colors:[[30,50,65],[210,215,220]],assignments:[0,1]};
const trial=core.refineColorPlaneOwnership(input,palette,rgba,w,h,{
 maxMoves:10,lowerYFraction:.2,minGainSquared:2500
});
process.stdout.write(JSON.stringify({
 count:trial.metrics.movedPixels,
 candidates:trial.metrics.candidates,
 improvements:trial.metrics.sourceRgbErrorReduction,
 originalUntouched:labels[19+15*w]===0,
 moved:trial.built.componentIds[19+15*w]===1,
 assignments:palette.assignments,
 sizes:trial.built.components.map(x=>x.count),
 total:trial.built.components.reduce((n,c)=>n+c.count,0)
}));
""")
    assert x["count"]>0
    assert x["candidates"]>=x["count"]
    assert x["improvements"]>0
    assert x["originalUntouched"]
    assert x["moved"]
    assert x["assignments"]==[0,1]
    assert x["total"]==1600

@pytest.mark.skipif(shutil.which("node") is None,reason="Node missing")
def test_no_positive_source_difference_keeps_original_labels_identical():
    x=node(r"""
const core=require(process.argv[1])._core;
const w=40,h=40,labels=new Int32Array(w*h),rgba=new Uint8ClampedArray(w*h*4);
const pixels=[[],[]];
for(let i=0;i<w*h;i++){
 const id=i%w<20?0:1;labels[i]=id;pixels[id].push(i);
 rgba[i*4]=id?200:20;rgba[i*4+1]=id?200:20;rgba[i*4+2]=id?200:20;rgba[i*4+3]=255;
}
const built={componentIds:labels,components:pixels.map((p,id)=>({id,sourceId:id,
 pixels:p,count:p.length,minX:id?20:0,minY:0,maxX:id?39:19,maxY:39,borderTouches:80,
 rgb:id?[200,200,200]:[20,20,20]}))};
const trial=core.refineColorPlaneOwnership(built,{colors:[[20,20,20],[200,200,200]]},
 rgba,w,h,{});
const errors=[];
for(const opts of [{maxMoves:0},{maxMoves:1000},{lowerYFraction:-1}]) {
 try{core.refineColorPlaneOwnership(built,{colors:[]},rgba,w,h,opts);errors.push(false)}
 catch(e){errors.push(true)}
}
process.stdout.write(JSON.stringify({moves:trial.metrics.movedPixels,
 unchanged:trial.built===built,errors}));
""")
    assert x=={"moves":0,"unchanged":True,"errors":[True,True,True]}
