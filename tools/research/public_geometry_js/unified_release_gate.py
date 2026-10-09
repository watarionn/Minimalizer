"""Research-only unified fail-closed MinimalizerPublic release gate.
Input is metadata evidence produced independently from SHA-signed sources.
Never allows budget policy mutation or human Golden auto-approval.
"""
import json, argparse, hashlib
from pathlib import Path

LIMITS={"GC001":{"stage8":1887,"rendered":1887},"Raden":{"stage8":1412,"rendered":1412}}
def evaluate(evidence):
    if not isinstance(evidence,dict) or set(evidence.get("cases",{}))!={"GC001","Raden"}:
        raise ValueError("both signed original cases required")
    report={"schema":"minimalizer-public-unified-gate-v1","cases":{},"release":"HOLD","production":"UNCHANGED"}
    all_pass=True
    for name,limits in LIMITS.items():
        x=evidence["cases"][name]
        for key in ("sourceSha256","maskManifestSha256","candidateSha256"):
            if not isinstance(x.get(key),str) or len(x[key])!=64 or any(ch not in "0123456789abcdef" for ch in x[key].lower()):
                raise ValueError(f"{name} missing signed {key}")
        for key in ("stage8OriginalVertices","renderedVertices","shapeCount","alphaOutsideDpr4","alphaMissingDpr4"):
            if not isinstance(x.get(key),int) or isinstance(x[key],bool) or x[key]<0:
                raise ValueError(f"{name} invalid {key}")
        if not isinstance(x.get("nonfaceRgbMAE"),(int,float)) or not 0<=x["nonfaceRgbMAE"]<1000:
            raise ValueError("invalid RGB error")
        comparisons=x.get("champion",{})
        if not isinstance(comparisons.get("nonfaceRgbMAE"),(int,float)) or not 0<=comparisons["nonfaceRgbMAE"]<1000:
            raise ValueError("missing champion metric")
        checks={
            "stage8_budget":x["stage8OriginalVertices"]<=limits["stage8"],
            "rendered_vertex_budget":x["renderedVertices"]<=limits["rendered"],
            "shape_budget":x["shapeCount"]<=40,
            "source_alpha_no_outside":x["alphaOutsideDpr4"]==0,
            "source_alpha_no_missing":x["alphaMissingDpr4"]==0,
            "champion_nonregression":x["nonfaceRgbMAE"]<=comparisons["nonfaceRgbMAE"],
            "face_policy":x.get("faceFeaturesHidden") is True,
            "chromium_checked":x.get("chromiumValidated") is True,
            "safari_checked":x.get("safariValidated") is True,
            "human_golden":x.get("humanGoldenApproved") is True,
        }
        passed=all(checks.values())
        all_pass &=passed
        report["cases"][name]={"checks":checks,"allGatesPass":passed,
            "failures":[k for k,v in checks.items() if not v],
            "limits":limits,
            "measurements":{k:x[k] for k in ("stage8OriginalVertices","renderedVertices","shapeCount",
                "alphaOutsideDpr4","alphaMissingDpr4","nonfaceRgbMAE")}}
    # Research runner is intentionally incapable of releasing regardless of input.
    report["allNumericAndReviewChecksPass"]=all_pass
    report["manualProductionAuthorizationRequired"]=True
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("evidence",type=Path);p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    source=a.evidence.read_bytes()
    result=evaluate(json.loads(source))
    result["evidenceSha256"]=hashlib.sha256(source).hexdigest()
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"release":result["release"],"cases":{k:v["failures"] for k,v in result["cases"].items()}},ensure_ascii=False))
if __name__=="__main__":main()
