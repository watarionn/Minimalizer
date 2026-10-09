"""Stage8 signed original: conservative exact duplicate-point and collinear-ring audit.
No candidate is promoted without source-owned mask raster & topology replay.
"""
import argparse,hashlib,json
from pathlib import Path
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def assess(p):
    components=p["parameters"]["components"]
    before=sum(len(ring) for ring in components)
    exact_repeat=0; collinear=0; degenerate=0
    for ring in components:
        if len(ring)<3:degenerate+=1
        exact_repeat+=sum(ring[i]==ring[i-1] for i in range(1,len(ring)))
        if len(ring)>=3:
            for i in range(len(ring)):
                a,b,c=ring[i-1],ring[i],ring[(i+1)%len(ring)]
                if (b[0]-a[0])*(c[1]-b[1])==(b[1]-a[1])*(c[0]-b[0]):collinear+=1
    return dict(owner=p.get("composition_part"),ringVertices=before,adjacentDuplicateOccurrences=exact_repeat,
                collinearOccurrences=collinear,degenerateRings=degenerate,
                verifiedRemovableVertices=0)
def analyze(base):
    output={"schema":"sa1034-conservative-ring-replay-audit-v1","status":"NO_CHANGES_TO_ORIGINAL",
            "safePromotions":0,"golden":"HOLD","production":"UNCHANGED","cases":{}}
    for case in ("GC001","Raden"):
        folder=base/case
        source=folder/"phase8_adaptive_source_contour_research.json"
        doc=json.loads(source.read_text(encoding="utf-8"))
        if doc.get("no_new_material_or_owner") is not True:raise ValueError("source boundary authority absent")
        parts=doc["primitives_back_to_front"]
        if len(parts)!=11:raise ValueError("11 owner mismatch")
        result=[assess(p) for p in parts]
        expected={"GC001":3604,"Raden":2370}[case]
        observed=sum(v["ringVertices"] for v in result)
        if observed!=expected:raise ValueError(f"changed original {case} count {observed}")
        output["cases"][case]={"sha256":sha(source),"vertices":observed,"originalBudget":{"GC001":1887,"Raden":1412}[case],
           "provisionalDuplicateOccurrences":sum(v["adjacentDuplicateOccurrences"] for v in result),
           "provisionalCollinearOccurrences":sum(v["collinearOccurrences"] for v in result),
           "degenerateRingCount":sum(v["degenerateRings"] for v in result),
           "ownerEvidence":result,"trustedSafeReductions":0,
           "unverifiedCandidateCount":sum(v["adjacentDuplicateOccurrences"]+v["collinearOccurrences"] for v in result)}
    return output
if __name__=="__main__":
    a=argparse.ArgumentParser();a.add_argument("--source-root",type=Path,required=True);a.add_argument("--out",type=Path,required=True)
    arg=a.parse_args();result=analyze(arg.source_root);arg.out.parent.mkdir(parents=True,exist_ok=True)
    arg.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({k:{"vertices":v["vertices"],"duplicates":v["provisionalDuplicateOccurrences"],"collinear":v["provisionalCollinearOccurrences"]} for k,v in result["cases"].items()}))
