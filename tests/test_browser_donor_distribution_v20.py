"""V20 read-only candidate geometry probe: independent gates and no-op parity."""
from __future__ import annotations
import json, shutil, subprocess
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
ENGINE=ROOT/"web/static/browser-fallback.js"
APP=ROOT/"web/static/app.js"

def node(script: str) -> dict:
    p=subprocess.run(["node","-e",script,str(ENGINE)],
                     capture_output=True,text=True,check=True,timeout=60)
    return json.loads(p.stdout)

def test_v20_only_opted_in_research_mode_probes_candidate_geometry():
    app=APP.read_text(encoding="utf-8")
    engine=ENGINE.read_text(encoding="utf-8")
    assert "allowNearPalette: true, maxMerges: 1, captureCandidateGeometry: true" in app
    assert "allowNearPalette: false, maxMerges: 1" in app
    assert "config.captureCandidateGeometry===true" in engine
    assert "selectiveMergeCandidateGeometry: analysis.metrics.selectiveMergeCandidateGeometry" in engine
    assert "maxSmallFraction: 0.0015" in engine
    assert "minBoundingSide: 5" in engine
    assert "maxAspectRatio: 3.0" in engine

@pytest.mark.skipif(shutil.which("node") is None,reason="Node.js unavailable")
def test_pair_probe_separates_area_width_aspect_and_contact_independently():
    result=node(r"""
const core=require(process.argv[1])._core;
function run(box){
 const width=100,height=100;const labels=new Int32Array(width*height);
 const slots=[[],[]];
 for(let y=0;y<height;y++)for(let x=0;x<width;x++){
  const i=y*width+x,id=(x>=box[0]&&x<box[2]&&y>=box[1]&&y<box[3])?1:0;
  labels[i]=id;slots[id].push(i);
 }
 const mk=id=>({
  id,sourceId:id,label:id,pixels:slots[id],count:slots[id].length,
  minX:id?box[0]:0,minY:id?box[1]:0,
  maxX:id?box[2]-1:99,maxY:id?box[3]-1:99,
  borderTouches:id?0:400,rgb:id?[103,104,108]:[100,102,110],
  lab:[40,0,0]
 });
 const h={built:{components:[mk(0),mk(1)],componentIds:labels},
         groups:[],selectedCount:2};
 const p={assignments:[0,1],colors:[[120,120,120],[123,122,121]],
          palette:[]};
 const settings={allowNearPalette:true,maxMerges:1,
                 captureCandidateGeometry:true};
 const withProbe=core.mergeAcceptedPaletteRegions(h,p,width,height,settings);
 const withoutProbe=core.mergeAcceptedPaletteRegions(h,p,width,height,
                                    {...settings,captureCandidateGeometry:false});
 const a=withProbe.metrics.candidateGeometry;
 const b=withoutProbe.metrics.candidateGeometry;
 const copy={...withProbe.metrics};delete copy.candidateGeometry;
 const parity={...withoutProbe.metrics};delete parity.candidateGeometry;
 return {record:a[0],records:a.length,
         disabled:b===null,metricsIdentical:JSON.stringify(copy)===JSON.stringify(parity),
         labelsIdentical:Array.from(withProbe.hierarchy.built.componentIds)
                         .every((x,i)=>x===withoutProbe.hierarchy.built.componentIds[i])};
}
const large=run([25,25,35,35]); // 100 pixels: over default 15-pixel cap
const narrow=run([40,20,43,50]); // width 3, length 30, aspect 10
const compact=run([40,40,45,45]); // 5x5, still over the 15-pixel default cap
process.stdout.write(JSON.stringify({large,narrow,compact}));
""")
    for name in ("large","narrow","compact"):
        sample=result[name]
        assert sample["records"] == 1
        assert sample["disabled"] and sample["metricsIdentical"] and sample["labelsIdentical"]
        row=sample["record"]
        assert len(row["gates"]) == 11
        assert row["sharedEdges"] > 0
        assert row["donorFillFraction"] == 1
        assert row["donorPixels"] == row["donorBoxWidth"] * row["donorBoxHeight"]
        assert row["crossPalette"]
    large=result["large"]["record"]
    assert not large["gates"]["area"]
    assert large["gates"]["minSide"] and large["gates"]["aspect"]
    narrow=result["narrow"]["record"]
    assert not narrow["gates"]["area"]
    assert not narrow["gates"]["minSide"]
    assert not narrow["gates"]["aspect"]
    compact=result["compact"]["record"]
    assert compact["gates"]["minSide"] and compact["gates"]["aspect"]
    assert not compact["gates"]["area"]

@pytest.mark.skipif(shutil.which("node") is None,reason="Node.js unavailable")
def test_probe_uses_full_label_grid_and_cannot_override_merge_rejection():
    result=node(r"""
const core=require(process.argv[1])._core,w=80,h=80;
const labels=new Int32Array(w*h),pixels=[[],[]];
for(let y=0;y<h;y++)for(let x=0;x<w;x++){
 const i=y*w+x,id=x>=15&&x<21&&y>=16&&y<22?1:0;
 labels[i]=id;pixels[id].push(i);
}
const mk=id=>({id,sourceId:id,pixels:pixels[id],count:pixels[id].length,
 minX:id?15:0,maxX:id?20:79,minY:id?16:0,maxY:id?21:79,
 rgb:id?[130,130,130]:[110,110,110],lab:[0,0,0],borderTouches:id?0:100});
const hdata={built:{components:[mk(0),mk(1)],componentIds:labels},selectedCount:2,groups:[]};
const palette={assignments:[0,1],colors:[[20,20,20],[220,220,220]],palette:[]};
const output=core.mergeAcceptedPaletteRegions(hdata,palette,w,h,{
  captureCandidateGeometry:true,allowNearPalette:true,maxMerges:1
});
process.stdout.write(JSON.stringify({
 count:output.hierarchy.built.components.length,
 applied:output.metrics.applied,
 evaluated:output.metrics.evaluated,
 records:output.metrics.candidateGeometry.length,
 palettePass:output.metrics.candidateGeometry[0].gates.paletteDistance,
 total:output.metrics.rejected
}));
""")
    assert result == {"count":2,"applied":0,"evaluated":1,
                      "records":1,"palettePass":False,"total":1}
