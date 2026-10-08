"""V21 explicit one-pair same-color merge with deterministic render rollback."""
from __future__ import annotations
import json
import shutil
import subprocess
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
ENGINE=ROOT/"web/static/browser-fallback.js"
APP=ROOT/"web/static/app.js"


def js(script):
    proc=subprocess.run(["node","-e",script,str(ENGINE)],text=True,
                        capture_output=True,check=True,timeout=80)
    return json.loads(proc.stdout)


def test_only_research_engine_exposes_target_no_global_cut_or_app_ui():
    app=APP.read_text(encoding="utf-8")
    engine=ENGINE.read_text(encoding="utf-8")
    assert 'targetedPair: null' in engine
    assert 'maxTargetDonorFraction: 0.06' in engine
    assert 'targetedMergeStatus' in engine
    assert 'maxSilhouetteChangedPixels:0' in engine
    assert 'protectedRects:[]' in engine
    assert 'protectedColors:[]' in engine
    assert 'browserFallbackQualityParam === "targeted"' not in app
    assert "captureCandidateGeometry: true" in app
    assert "result.metrics.vertexCount>=base.metrics.vertexCount" in engine
    assert '"no_vertex_gain"' in engine
    assert 'hierarchyTargetMax: 30' not in app
    trial=(ROOT/"tools/run_browser_targeted_v21_chrome.py").read_text(encoding="utf-8")
    assert '"protectedColors":[[68,37,36]]' in trial
    assert '"x0":0,"y0":100,"x1":60,"y1":225' in trial


@pytest.mark.skipif(shutil.which("node") is None,reason="Node.js unavailable")
def test_targeted_single_same_palette_merges_only_selected_large_donor():
    record=js(r"""
const core=require(process.argv[1])._core;
const width=100,height=100,labels=new Int32Array(width*height);
const areas=[[],[]];
for(let y=0;y<height;y++)for(let x=0;x<width;x++){
 const k=(x>=30&&x<50&&y>=30&&y<50)?1:0;
 const i=y*width+x;
 labels[i]=k;areas[k].push(i);
}
const mk=(id)=>({
 id,sourceId:id,label:id,pixels:areas[id],count:areas[id].length,
 minX:id?30:0,minY:id?30:0,maxX:id?49:99,maxY:id?49:99,
 rgb:id?[101,103,104]:[100,102,105],lab:[45,0,0],borderTouches:id?0:400,
});
const h={built:{components:[mk(0),mk(1)],componentIds:labels},
         groups:[],selectedCount:2};
const p={colors:[[120,120,120],[120,120,120]],assignments:[0,0],palette:[]};
const copy=Array.from(labels);
const base=core.mergeAcceptedPaletteRegions(h,p,width,height,{allowNearPalette:false,maxMerges:1});
const accepted=core.mergeAcceptedPaletteRegions(h,p,width,height,{
 allowNearPalette:false,maxMerges:1,targetedPair:{donorId:1,recipientId:0},
 maxTargetDonorFraction:.06,
});
const backwards=core.mergeAcceptedPaletteRegions(h,p,width,height,{
 allowNearPalette:false,maxMerges:1,targetedPair:{donorId:0,recipientId:1}
});
const missing=core.mergeAcceptedPaletteRegions(h,p,width,height,{
 allowNearPalette:false,maxMerges:1,targetedPair:{donorId:1,recipientId:9}
});
const otherPal=core.mergeAcceptedPaletteRegions(h,{...p,assignments:[0,1]},width,height,{
 allowNearPalette:false,maxMerges:1,targetedPair:{donorId:1,recipientId:0}
});
const tooSmall=core.mergeAcceptedPaletteRegions(h,p,width,height,{
 allowNearPalette:false,maxMerges:1,targetedPair:{donorId:1,recipientId:0},
 maxTargetDonorFraction:.03
});
const result={
 base:base.metrics.applied,merged:accepted.metrics.applied,
 status:accepted.metrics.targetStatus,choice:accepted.metrics.chosenTarget,
 assignments:accepted.palette.assignments,colors:accepted.palette.colors,
 shapes:accepted.hierarchy.built.components.length,
 complete:accepted.hierarchy.built.componentIds.every(x=>x===0),
 unchangedOriginal:labels.every((x,i)=>x===copy[i]),
 backwards:backwards.metrics.targetStatus,backwardsMerged:backwards.metrics.applied,
 missing:missing.metrics.targetStatus,otherPalette:otherPal.metrics.targetStatus,
 tooSmall:tooSmall.metrics.targetStatus,
};
process.stdout.write(JSON.stringify(result));
""")
    assert record["base"]==0
    assert record["merged"]==1
    assert record["status"]=="pre_raster_accepted"
    assert record["choice"]["donorId"]==1
    assert record["choice"]["recipientId"]==0
    assert record["choice"]["donorPixels"]==400
    assert record["choice"]["samePalette"] is True
    assert record["assignments"]==[0]
    assert record["colors"]==[[120,120,120]]
    assert record["shapes"]==1
    assert record["complete"] and record["unchangedOriginal"]
    assert record["backwards"]=="orientation_rejected"
    assert record["backwardsMerged"]==0
    assert record["missing"]=="not_found"
    assert record["otherPalette"]=="palette_rejected"
    assert record["tooSmall"]=="area_or_shape_rejected"


@pytest.mark.skipif(shutil.which("node") is None,reason="Node.js unavailable")
def test_target_cannot_disable_protection_or_merge_multiple_pairs():
    r=js(r"""
const core=require(process.argv[1])._core;
const checks=[
 {allowNearPalette:true,maxMerges:1,targetedPair:{donorId:1,recipientId:0}},
 {allowNearPalette:false,maxMerges:2,targetedPair:{donorId:1,recipientId:0}},
 {allowNearPalette:false,maxMerges:1,targetedPair:{donorId:1,recipientId:0},maxTargetDonorFraction:.07},
 {allowNearPalette:false,maxMerges:1,targetedPair:{donorId:1,recipientId:1}},
 {allowNearPalette:false,maxMerges:1,targetedPair:{donorId:-1,recipientId:0}},
];
const bad=checks.map(x=>{
 try {
  core.mergeAcceptedPaletteRegions({built:{components:[],componentIds:new Int32Array(1)}},
    {colors:[],assignments:[]},1,1,x);
  return false;
 } catch(e) {return String(e.message).includes("V21 targeted merge requires");}
});
process.stdout.write(JSON.stringify({bad}));
""")
    assert all(r["bad"])


@pytest.mark.skipif(shutil.which("node") is None,reason="Node.js unavailable")
def test_raster_gate_protects_full_silhouette_roi_and_selected_palette_color():
    result=js(r"""
const core=require(process.argv[1])._core;
global.MinimalizerOpenCvRaster={renderShapesRgba:(shapes,w,h)=>{
 const px=new Uint8ClampedArray(w*h*4);
 for(let i=0;i<w*h;i++){
  const p=i*4;
  const v=(shapes[0]?.colors||[])[i]??0;
  const rgb=v===0?[255,255,255]:v===1?[149,211,27]:v===2?[65,66,74]:[30,30,30];
  for(let k=0;k<3;k++)px[p+k]=rgb[k];
  px[p+3]=255;
 }
 return px;
}};
const initial=Array(100).fill(0);
initial[30]=1;initial[33]=2;
const tryColors=(edit,opts)=>{
 const changed=initial.slice();edit(changed);
 return core.compareRegionRenderFidelity([{colors:initial}],[{colors:changed}],10,10,{
  maxChangedPixelFraction:1,maxRgbMeanAbsoluteError:255,maxColorMassDeltaFraction:1,
  protectedColors:[[149,211,27]],
  protectedRects:[{x0:3,y0:3,x1:5,y1:4}],
  ...opts
 });
};
const exact=tryColors(x=>{});
const tie=tryColors(x=>{x[30]=3});
const roi=tryColors(x=>{x[33]=3});
const silhouette=tryColors(x=>{x[90]=3});
process.stdout.write(JSON.stringify({exact,tie,roi,silhouette}));
""")
    assert result["exact"]["pass"]
    assert result["tie"]["reason"]=="protected_feature"
    assert result["tie"]["colorProtected"] is False
    assert result["roi"]["reason"]=="protected_feature"
    assert result["roi"]["protectedChanged"]==1
    assert result["silhouette"]["reason"]=="protected_feature"
    assert result["silhouette"]["silhouetteChanged"]==1
