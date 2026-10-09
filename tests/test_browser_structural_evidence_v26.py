"""V26 source-backed structural diagnostic: absence of semantic evidence means UNBOUND."""
from __future__ import annotations
import json
import shutil
import subprocess
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
MOD=ROOT/"web/static/browser-structural-evidence-v26.js"
HTML=ROOT/"web/static/index.html"
APP=ROOT/"web/static/app.js"

def node(body):
    p=subprocess.run(["node","-e",body,str(MOD)],cwd=ROOT,check=True,
      capture_output=True,text=True,timeout=30)
    return json.loads(p.stdout)

def test_opt_in_module_does_not_modify_app_or_existing_quality_routes():
    html=HTML.read_text(encoding="utf-8")
    script=MOD.read_text(encoding="utf-8")
    assert 'src="static/browser-structural-evidence-v26.js"' in html
    assert "visibleOutputAuthority:false" in script
    assert "semanticPart:\"unbound\"" in script
    app=APP.read_text(encoding="utf-8")
    assert "browserStructuralEvidenceV26" not in app
    assert "browserFallbackQualityParam === \"group\"" in app

@pytest.mark.skipif(not shutil.which("node"),reason="node unavailable")
def test_lost_edge_is_source_supported_connected_and_unbound():
    obj=node(r"""
const v=require(process.argv[1]);
const w=32,h=32,a=new Uint8ClampedArray(w*h*4),b=new Uint8ClampedArray(w*h*4);
const p=new Float32Array(w*h).fill(.96),c=new Float32Array(w*h).fill(.85);
for(let y=0;y<h;y++)for(let x=0;x<w;x++){
 const i=y*w+x;
 const source=x<16?30:220;
 for(let j=0;j<3;j++){a[4*i+j]=source;b[4*i+j]=90;}
 a[4*i+3]=b[4*i+3]=255;
}
const e={provider:"browser-u2netp",model:"u2netp",probability:p,confidence:c};
const first=v.observe(a,b,w,h,e),second=v.observe(a,b,w,h,e);
process.stdout.write(JSON.stringify({
 state:first.status,seg:first.summary.retainedSegmentCount,
 pixels:first.summary.retainedPixels,unbound:first.summary.unboundSegments,
 arm:first.summary.knownArmSegments,garment:first.summary.knownGarmentSegments,
 semantic:first.segments.map(x=>x.semanticPart),
 unchanged:a[4*15+16*w*4]===30,outputUnchanged:b[0]===90,
 deterministic:JSON.stringify(first)===JSON.stringify(second)
}));
""")
    assert obj["state"]=="evidence_only_unbound"
    assert obj["seg"]>=1 and obj["pixels"]>=8
    assert obj["unbound"]==obj["seg"]
    assert obj["arm"]==obj["garment"]==0
    assert set(obj["semantic"])=={"unbound"}
    assert obj["unchanged"] and obj["outputUnchanged"] and obj["deterministic"]

@pytest.mark.skipif(not shutil.which("node"),reason="node unavailable")
def test_missing_or_forged_foreground_is_fail_closed():
    obj=node(r"""
const v=require(process.argv[1]),w=32,h=32,n=w*h;
const a=new Uint8ClampedArray(n*4).fill(255),b=new Uint8ClampedArray(n*4).fill(0);
const e={probability:new Float32Array(n).fill(.95),
 confidence:new Float32Array(n).fill(.85)};
const missing=v.observe(a,b,w,h,null);
const forged=v.observe(a,b,w,h,{...e,provider:"fabricated",model:"u2netp"});
const low=v.observe(a,b,w,h,{...e,provider:"browser-u2netp",model:"u2netp",
  probability:new Float32Array(n).fill(.3)});
let bad=false;try{v.observe(a,b,w,h,{...e,provider:"browser-u2netp",model:"u2netp",
  probability:new Float32Array(15)});}catch(_){bad=true}
process.stdout.write(JSON.stringify({
 missing:missing.status,forged:forged.status,
 low:low.status,lowPixels:low.summary.eligibleSubjectPixels,
 missingSegments:missing.segments.length,bad
}));
""")
    assert obj=={"missing":"withheld_subject_evidence_unavailable",
       "forged":"withheld_unverified_subject_provider",
       "low":"no_supported_lost_boundaries","lowPixels":0,
       "missingSegments":0,"bad":True}

@pytest.mark.skipif(not shutil.which("node"),reason="node unavailable")
def test_only_rendered_flattened_source_internal_boundaries_are_evidence():
    obj=node(r"""
const v=require(process.argv[1]),w=32,h=32,n=w*h;
const a=new Uint8ClampedArray(n*4),b=new Uint8ClampedArray(n*4);
for(let i=0;i<n;i++){let x=i%w;for(let j=0;j<3;j++){
 a[4*i+j]=x<16?40:200;b[4*i+j]=x<16?40:200;}a[4*i+3]=b[4*i+3]=255;}
const subject={provider:"browser-u2netp",model:"u2netp",
 probability:new Float32Array(n).fill(.97),confidence:new Float32Array(n).fill(.85)};
const detected=v.observe(a,b,w,h,subject);
process.stdout.write(JSON.stringify({status:detected.status,
 pixels:detected.summary.rawLostBoundaryPixels,
 segments:detected.summary.retainedSegmentCount}));
""")
    assert obj=={"status":"no_supported_lost_boundaries","pixels":0,"segments":0}
