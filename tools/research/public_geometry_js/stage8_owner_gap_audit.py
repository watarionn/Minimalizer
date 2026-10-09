"""Fail-closed, provenance-aware SA10.34 Stage8 vertex owner attribution.
This tool NEVER deletes components, adjusts vertices, or passes a production gate.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

EXPECTED = {"GC001":{"baseline":1887,"observed":3604}, "Raden":{"baseline":1412,"observed":2370}}
def audit(root: Path):
    output={"schema":"minimalizer-stage8-owner-gap-audit-v1","researchOnly":True,
            "production":"UNCHANGED","golden":"HOLD","cases":{}}
    for case,expected in EXPECTED.items():
        path=root/case/"vertex_budget_breakdown.json"
        data=path.read_bytes()
        x=json.loads(data)
        if x.get("schema")!="sa10.34-vertex-gap-v1" or x.get("case")!=case:
            raise ValueError("wrong signed Stage8 audit schema")
        if x.get("old_total")!=expected["baseline"] or x.get("adaptive_total")!=expected["observed"]:
            raise ValueError("Stage8 totals changed without independent verification")
        parts=x.get("parts")
        if not isinstance(parts,list) or len(parts)!=11:
            raise ValueError("expected 11 signed owners")
        old=adaptive=0
        seen=set()
        for p in parts:
            owner=p["owner"]
            if owner in seen or not isinstance(owner,str):raise ValueError("duplicate owner")
            seen.add(owner)
            for k in ("old_ring_vertices","adaptive_ring_vertices","exact_ring_vertices",
                      "adaptive_extra_vs_old","degenerate_rings"):
                if not isinstance(p[k],int) or p[k]<0 and k!="adaptive_extra_vs_old":
                    raise ValueError("invalid owner vertex data")
            if p["adaptive_ring_vertices"]-p["old_ring_vertices"]!=p["adaptive_extra_vs_old"]:
                raise ValueError("inconsistent delta")
            old+=p["old_ring_vertices"];adaptive+=p["adaptive_ring_vertices"]
        if old!=expected["baseline"] or adaptive!=expected["observed"]:
            raise ValueError("signed owner totals do not reconcile")
        gap=adaptive-old
        ranking=sorted(({"owner":p["owner"],"sourceVertexDelta":p["adaptive_extra_vs_old"],
             "degenerateRingsObserved":p["degenerate_rings"],"sourceVertices":p["adaptive_ring_vertices"]}
            for p in parts),key=lambda p:(-p["sourceVertexDelta"],p["owner"]))
        positive=sum(max(0,p["sourceVertexDelta"]) for p in ranking)
        output["cases"][case]={
            "breakdownSha256":hashlib.sha256(data).hexdigest(),
            "baselineSourceVertices":old,"adaptiveSourceVertices":adaptive,
            "historicalCap":old,"overBudgetBy":gap,"deficitPctOfHistoricalCap":round(100*gap/old,3),
            "positiveInflation":positive,
            "negativeOffsets":positive-gap,
            "topContributors":ranking,
            "safeRemovableVerticesConfirmed":0,
            "vertexBudgetGate":"FAIL",
            "reconstructionNote":"No component, ring, owner or vertex deletion authorized by count-only evidence."}
    return output

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    result=audit(a.root)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:{"overBudgetBy":v["overBudgetBy"],"largestSource":v["topContributors"][0]["owner"]} for k,v in result["cases"].items()}))
