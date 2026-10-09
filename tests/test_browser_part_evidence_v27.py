"""v27 browser semantic evidence contract. Observers never own pixels or parts."""
from __future__ import annotations
import json,shutil,subprocess
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/"web/static/browser-part-evidence-v27.js"

def node(script):
    p=subprocess.run(["node","--input-type=module","-e",script,str(MODULE)],
      capture_output=True,text=True,check=True,timeout=45,cwd=ROOT)
    return json.loads(p.stdout.strip())

BASE=r"""
import {pathToFileURL} from 'node:url';
await import(pathToFileURL(process.argv[1]).href);
const api=globalThis.MinimalizerBrowserPartEvidenceV27;
const w=100,h=100,n=w*h;
const fg={provider:"browser-u2netp",model:"u2netp",
  probability:new Float32Array(n).fill(.98),
  confidence:new Float32Array(n).fill(.91)};
const classes=new Uint8Array(256*256).fill(4),
  probs=new Float32Array(256*256).fill(.95),
  margins=new Float32Array(256*256).fill(.82);
const multi={categories:classes,probability:probs,margins,
  modelSha256:api.MODEL_SHA,provider:"senty-au/selfie_multiclass_256x256-ONNX"};
const edgePixels=Array.from({length:50},(_,i)=>(30+i)*w+25);
const edge={version:"browser-structural-evidence-v26",width:w,height:h,
 provenance:{visibleOutputAuthority:false,partAuthority:false},
 segments:[{evidenceId:"source-edge-3025",pixelIndices:edgePixels}]};
"""

def test_load_not_production_and_no_new_package_dependency():
    source=MODULE.read_text(encoding="utf-8")
    html=(ROOT/"web/static/index.html").read_text(encoding="utf-8")
    app=(ROOT/"web/static/app.js").read_text(encoding="utf-8")
    assert 'src="static/browser-part-evidence-v27.js"' in html
    assert 'visibleOutputAuthority:false' in source
    assert 'semanticPart:"unbound"' in source
    assert "browserFallbackQualityParam === \"group\"" in app
    assert "browserPartEvidenceV27" not in app
    assert "partOwnershipAuthority:false" in source
    assert "./vendor/onnxruntime/ort.wasm.min.mjs" in source
    assert "MODEL_SHA" in source and "POSE_SHA" in source

@pytest.mark.skipif(not shutil.which("node"),reason="Node unavailable")
def test_validated_clothing_cue_does_not_grant_ownership():
    got=node(BASE+r"""
const result=api.bindObservations(edge,fg,multi,null,w,h);
const copy=api.bindObservations(edge,fg,multi,null,w,h);
console.log(JSON.stringify({
  garment:result.summary.garmentCueSegments,
  armL:result.summary.leftArmCueSegments,armR:result.summary.rightArmCueSegments,
  classCount:result.summary.acceptedClassPixels[4],
  semantic:result.segments[0].semanticPart,
  confidence:result.segments[0].bindingConfidence,
  roles:result.segments[0].roleCandidates.map(x=>x.role),
  render:result.provenance.visibleOutputAuthority,
  ownership:result.provenance.partOwnershipAuthority,
  deterministic:JSON.stringify(result)===JSON.stringify(copy)
}));
""")
    assert got["garment"]==1 and got["armL"]==got["armR"]==0
    assert got["classCount"]>0 and got["semantic"]=="unbound"
    assert got["confidence"]==0 and got["render"] is False
    assert got["ownership"] is False and got["deterministic"]
    assert got["roles"]==["clothing_observation"]

@pytest.mark.skipif(not shutil.which("node"),reason="Node unavailable")
def test_arm_correlates_pose_geometry_and_verified_multiclass():
    got=node(BASE+r"""
const l=Array.from({length:33},()=>({x:.8,y:.8,visibility:0,presence:0}));
for(const [index,y] of [[11,.25],[13,.50],[15,.80]])
  l[index]={x:.25,y,visibility:.95,presence:.95};
const pose={status:"pose_observed",provider:"mediapipe-tasks-vision",
  modelSha256:api.POSE_SHA,landmarks:l};
const result=api.bindObservations(edge,fg,multi,pose,w,h);
console.log(JSON.stringify({left:result.summary.leftArmCueSegments,
 right:result.summary.rightArmCueSegments,pose:result.summary.poseStatus,
 roles:result.segments[0].roleCandidates.map(x=>x.role),
 semantic:result.segments[0].semanticPart,
 cue:result.summary.poseCuePixels}));
""")
    assert got["left"]==1 and got["right"]==0
    assert got["pose"]=="observed"
    assert "left_arm_pose_corridor" in got["roles"]
    assert got["semantic"]=="unbound"
    assert got["cue"]["left_arm"]>0 and got["cue"]["right_arm"]==0

@pytest.mark.skipif(not shutil.which("node"),reason="Node unavailable")
def test_wrong_model_sha_and_bad_pose_never_produce_part_authority():
    got=node(BASE+r"""
const l=Array.from({length:33},()=>({x:.25,y:.50,visibility:.9,presence:.9}));
const pose={status:"pose_observed",provider:"mediapipe-tasks-vision",
  modelSha256:"wrong",landmarks:l};
const untrusted={...multi,modelSha256:"wrong"};
const result=api.bindObservations(edge,fg,untrusted,pose,w,h);
console.log(JSON.stringify({
 clothes:result.summary.garmentCueSegments,
 left:result.summary.leftArmCueSegments,
 known:result.summary.multiclassStatus,
 pose:result.summary.poseStatus,unbound:result.summary.unbound,
 owner:result.segments[0].semanticPart
}));
""")
    assert got=={"clothes":0,"left":0,"known":"unavailable",
      "pose":"withheld_unverified_pose","unbound":1,"owner":"unbound"}

@pytest.mark.skipif(not shutil.which("node"),reason="Node unavailable")
def test_malformed_foreground_or_v26_not_accepted():
    got=node(BASE+r"""
let a=false,b=false,c=false;
try{api.bindObservations(edge,{...fg,provider:"fabricated"},multi,null,w,h)}
catch{a=true}
try{api.bindObservations({...edge,width:90},fg,multi,null,w,h)}
catch{b=true}
try{api.bindObservations({...edge,segments:[
  {evidenceId:"corrupt",pixelIndices:[999999]}]},fg,multi,null,w,h)}
catch{c=true}
console.log(JSON.stringify({a,b,c}));
""")
    assert got=={"a":True,"b":True,"c":True}
