"""R12 non-generative Stage8 candidate: prune only raster-invisible vertices.

Input is PRIVATE, source-SHA pinned adaptive Stage8 existing polygon owner scene.
Never publish vector coordinates to GitHub; save all candidate geometry only in
approved PRIVATE Google Drive. Exact old OpenCV raster per owner is the strict
acceptance invariant, NOT visual/semantic human acceptance or SVG browser parity.
No new shapes, source pixels, palettes, owners or face microfeatures.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

import cv2
import numpy as np
from minimalizer_zerobase.composition.semantic import rasterize_primitive_candidate
from minimalizer_zerobase.reviewed_sa10.source_exact_vector_replay import _vertex_budget

SOURCE={
 "GC001":("75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e",1887,3604),
 "Raden":("d9982c74a2d9a0a8cd3547f3f5cc603a809e942e6dcf62b98e36bfa019903a00",1412,2370),
}
EPS=(0.25,0.5,0.75,1.0,1.25,1.5,2.0,3.0)
VERSION="public-r12-private-exact-raster-invisible-vertex-prune-v1"

def sha(raw:bytes)->str:return hashlib.sha256(raw).hexdigest()

def sync(primitive:dict)->None:
    rings=primitive["parameters"]["rings"]
    primitive["parameters"]["components"]=[x["points"] for x in rings if x["depth"]%2==0]
    primitive["parameters"]["holes"]=[x["points"] for x in rings if x["depth"]%2==1]

def input_checks(case:str,obj:dict):
    expected,cap,vertices=SOURCE[case]
    if (obj.get("schema")!="sa10.34-adaptive-contour-scene-v1" or
        obj.get("original_source_sha256")!=expected or
        obj.get("research_only") is not True or
        obj.get("production_authorized") is not False or
        obj.get("no_new_primitive") is not True or
        obj.get("no_new_material_or_owner") is not True):
        raise ValueError("R12 input does not match frozen private source authority")
    prims=obj["primitives_back_to_front"]
    if len(prims)!=11:raise ValueError("signed source needs 11 original owners")
    owners=[p.get("source_mask_owner") for p in prims]
    if len(set(owners))!=11 or not {"face","left_arm","right_arm","unknown","accessory_or_held_object"}.issubset(owners):
        raise ValueError("protected owner missing")
    if any(p.get("primitive_type")!="polygon" or p.get("source_mask_replay") is not True
           for p in prims):
        raise ValueError("source-primitives must remain bound replayed polygons")
    raw=_vertex_budget(prims)["ring_vertices"]
    if raw!=vertices:raise ValueError(f"unsigned or wrong Stage8 source vertex total: {raw}")
    width=int(obj["coordinate_space"]["pixel_width"])
    height=int(obj["coordinate_space"]["pixel_height"])
    if (width,height)!=(340,340):
        raise ValueError("unexpected signed source space")
    return prims,cap,width,height

def evaluate(case:str,input_scene:Path,out:Path)->dict:
    if case not in SOURCE:raise ValueError("unsupported case")
    if out.exists():raise FileExistsError("research candidate directory exists")
    payload=json.loads(input_scene.read_text(encoding="utf-8"))
    originals,cap,width,height=input_checks(case,payload)
    candidate=copy.deepcopy(payload)
    rows=candidate["primitives_back_to_front"]
    existing_masks={
       p["source_mask_owner"]:rasterize_primitive_candidate(p,width=width,height=height)
       for p in originals}
    edits=[]
    attempted=0
    for primitive in rows:
        owner=primitive["source_mask_owner"]
        before=existing_masks[owner]
        rings=primitive["parameters"]["rings"]
        order=sorted(range(len(rings)),key=lambda i:len(rings[i]["points"]),reverse=True)
        for idx in order:
            ring=rings[idx]
            pts=ring["points"]
            if len(pts)<4:continue
            attempted+=1
            start=np.asarray(pts,dtype=np.float32).reshape(-1,1,2)
            selected=None
            for eps in EPS:
                reduced=cv2.approxPolyDP(start,eps,True).reshape(-1,2)
                if len(reduced)<3 or len(reduced)>=len(pts):continue
                # Actual source lattice integer coordinates only, no new point interpolation.
                candidate_points=reduced.astype(float).tolist()
                ring["points"]=candidate_points
                sync(primitive)
                current=rasterize_primitive_candidate(primitive,width=width,height=height)
                if np.array_equal(current,before):
                    if selected is None or len(candidate_points)<len(selected[0]):
                        selected=(candidate_points,eps)
                # Always reset before trying another epsilon.
                ring["points"]=pts
                sync(primitive)
            if selected is not None:
                ring["points"]=selected[0]
                sync(primitive)
                assert np.array_equal(
                   rasterize_primitive_candidate(primitive,width=width,height=height),before)
                edits.append({"owner":owner,"ringIndex":idx,
                              "verticesBefore":len(pts),"verticesAfter":len(selected[0]),
                              "epsilon":selected[1]})
    after=_vertex_budget(rows)["ring_vertices"]
    orig=_vertex_budget(originals)["ring_vertices"]
    exact=all(np.array_equal(
       rasterize_primitive_candidate(p,width=width,height=height),
       existing_masks[p["source_mask_owner"]]) for p in rows)
    if not exact or after>orig or len(rows)!=11:
        raise AssertionError("R12 cannot save any raster/ownership-changing candidate")
    record={
      "version":VERSION,"case":case,
      "originalSceneSHA256":sha(input_scene.read_bytes()),
      "signedOriginalSourceSHA256":SOURCE[case][0],
      "historicalOriginalStage8Cap":cap,
      "adaptiveStage8InputVertices":orig,
      "candidateVertices":after,
      "reducedVertices":orig-after,
      "sourceOriginalStage8BudgetPass":after<=cap,
      "candidateAgainstFrozenAdaptiveOwnerRasterExact":exact,
      "originalSourceTopologicalAndSemanticParityProven":False,
      "trueSvgChromeOwnerRasterParityProven":False,
      "humanVisualGatePassed":False,
      "attemptedNontrivialRings":attempted,
      "acceptedLocalExactRasterEdits":len(edits),
      "originalOwnersAndPalettesRetained":True,
      "noNewVisiblePixels":True,
      "productionPromoted":False,"releaseAuthorized":False,
      "status":"SOURCE_EXACT_RASTER_RESEARCH_HOLD",
    }
    candidate["production_authorized"]=False
    candidate["research_only"]=True
    out.mkdir(parents=True)
    geometry_path=out/(case+"_r12_private_raster_exact_scene.json")
    geometry_path.write_text(json.dumps(candidate,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    record["privateCandidateSHA256"]=sha(geometry_path.read_bytes())
    (out/(case+"_r12_coordinate_free_gate.json")).write_text(
       json.dumps(record,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return record

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--case",choices=sorted(SOURCE),required=True)
    p.add_argument("--input-scene",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=evaluate(a.case,a.input_scene,a.out)
    print("R12_PRIVATE_EXACT_RASTER_RESEARCH",result["case"],
          result["adaptiveStage8InputVertices"],"->",result["candidateVertices"],
          "budget cap",result["historicalOriginalStage8Cap"],
          "source budget pass",result["sourceOriginalStage8BudgetPass"],
          "RELEASE_HOLD",flush=True)
if __name__=="__main__":main()
