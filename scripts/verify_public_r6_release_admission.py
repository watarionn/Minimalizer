"""MinimalizerPublic R6 release gate: fail-closed independent evidence ledger.

Read only canonical R1-R5 research results. Produces truthful NO_GO, never a
merge/deploy authorization. Human and mobile signoff cannot be auto-created.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

CASES=("Kyoko","Noel","Ririka")
RECORDS={
    "r1":("LibraryConvergence_R1_20261010","public_v34_svgo_gate.json"),
    "r2":("LibraryConvergence_R2_20261010","public_r2_gate.json"),
    "r3":("LibraryConvergence_R3_20261010","public_r3_gate.json"),
    "r4":("LibraryConvergence_R4_20261010/full-scene","public_r4_matrix.json"),
    "r4_component":("LibraryConvergence_R4_20261010/layer-isolation",
                   "public_r4_component_attribution.json"),
    "r5":("LibraryConvergence_R5_20261010","public_r5_browser_canary.json"),
}
VERSIONS={
    "r1":"public-v34-svgo-gate-v1",
    "r2":"public-r2-full-owner-geometry-v1",
    "r3":"public-r3-exact-lattice-v1",
    "r4":"public-r4-native-vs-resvg-full-scene-v1",
    "r4_component":"public-r4-component-attribution-v1",
    "r5":"r5-public-route-shadow-canary-v1",
}

def read_reports(root:Path):
    result={}
    fingerprints={}
    for key,(folder,name) in RECORDS.items():
        source=root/folder/name
        raw=source.read_bytes()
        obj=json.loads(raw)
        if obj.get("version")!=VERSIONS[key]:
            raise ValueError("wrong R6 evidence version: "+key)
        if not isinstance(obj.get("cases"),list) or len(obj["cases"])!=3:
            raise ValueError("R6 missing three Golden cases: "+key)
        if [c.get("case") for c in obj["cases"]]!=list(CASES):
            raise ValueError("R6 case order or identity changed: "+key)
        fingerprints[key]=hashlib.sha256(raw).hexdigest()
        result[key]=obj
    return result,fingerprints

def evaluate(records:dict,fingerprints:dict)->dict:
    if set(records)!=set(RECORDS) or set(fingerprints)!=set(RECORDS):
        raise ValueError("incomplete R6 input set")
    r1,r2,r3,r4,layer,r5=(records[k] for k in
        ("r1","r2","r3","r4","r4_component","r5"))
    sha_matching=all(
      r1["cases"][i]["sourceSHA256"]==
      r2["cases"][i]["sourceSHA256"]==
      r3["cases"][i]["sourceSHA256"]==
      r4["cases"][i]["sourceSHA256"]
      for i in range(3))
    layer_paths_exact=all(
      c["components"]["paths"]["exact340"] and
      c["components"]["paths"]["exact680"] and
      c["components"]["paths"]["differentPixels340"]==0 and
      c["components"]["paths"]["differentPixels680"]==0
      for c in layer["cases"])
    measured={
      "frozenSourceProvenanceConsistent":sha_matching,
      "r1SerializationGoldenPass":r1.get("allGoldenExact") is True,
      "r2WholeColorGroupChromePass":(r2.get("allGoldensExact") is True and
                                     r2.get("allColorGroupsVisited") is True and
                                     sum(c["visitedColorGroups"] for c in r2["cases"])==910 and
                                     all(c["wholeColorGroupAuditComplete"] and
                                         c["goldenExact"] and
                                         c["visitedColorGroups"]==c["totalColorGroups"]
                                         for c in r2["cases"])),
      "r3ExactLatticeResearchComplete":r3.get("allExact") is True,
      "r4ChromeFrozenNativePass":r4.get("chromeBaselinePass") is True,
      "r4PathsNativeAndDpr2Exact":layer_paths_exact,
      "r4WholeSceneDpr2Exact":(
          r4.get("crossRendererExact") is True and
          all(c["fullSceneCrossRendererExact"] and
              c["chromeVsResvg340"]["differentPixels"]==0 and
              c["chromeVsResvg680"]["differentPixels"]==0 for c in r4["cases"])),
      "r5PublicShadowCanarySafe":(r5.get("researchPass") is True and
                                  r5.get("allOffOnByteExact") is True and
                                  r5.get("missingObserverWasmFallbackByteExact") is True and
                                  all(c["offAndOnByteExact"] and
                                      c["offSHA256"]==c["onSHA256"]==c["onDiagnosticSHA256"]
                                      for c in r5["cases"])),
      "humanGoldenSigned":False,
      "sourceSemanticOwnersSigned":False,
      "protectedArmsTieStaffCertified":False,
      "stage8OriginalRingBudgetApproved":False,
      "realIphoneSafariDprSigned":False,
      "resvgMplNoticeReviewSigned":False,
      "productionSafeRollbackApproved":False,
    }
    diagnostics={
      "r4FullSceneDpr2DifferentPixels":{
       c["case"]:c["chromeVsResvg680"]["differentPixels"]
       for c in r4["cases"]},
      "r4PathsDpr2DifferentPixels":{
       c["case"]:c["components"]["paths"]["differentPixels680"]
       for c in layer["cases"]},
      "r4FacetDpr2DifferentPixels":{
       c["case"]:c["components"]["facet"]["differentPixels680"]
       for c in layer["cases"]},
      "r3ApprovedSourceVertexReduction":0,
      "r5InputIsRealOriginalSourcePhoto":False,
    }
    blocked=[{"gate":k,"reason":"missing human/device sign-off or failed measured condition"}
             for k,v in measured.items() if v is not True]
    return {
        "version":"public-r6-conservative-release-admission-v1",
        "evidenceSHA256":fingerprints,"cases":list(CASES),
        "gates":measured,"diagnostics":diagnostics,
        "blockedGateCount":len(blocked),"blockedGates":blocked,
        "researchEvidenceReadAndChecked":True,
        "productQualityImprovementVerified":False,
        "localMinimalizerModified":False,
        "releaseAuthorized":False,
        "mergeOrDeployPerformed":False,
        "status":"NO_GO",
        "nextRequiredWork":[
          "resolve or deliberately keep out of production resvg DPR2 Facet interpolation mismatch",
          "measure and satisfy original Stage8 contour/vertex budget with signed original authority",
          "review source-owned arms/tie/staff/face hidden boundary on genuine source photos",
          "independently sign human Golden visual review",
          "real iPhone Safari / high-DPR browser verification",
          "verify complete MPL-2.0 redistributed notice and license review",
          "rehearse production Public-only rollback without changing Local Minimalizer"
        ],
    }

def execute(root:Path,out:Path):
    if out.exists():raise FileExistsError("R6 evidence already exists")
    records,fingerprints=read_reports(root)
    result=evaluate(records,fingerprints)
    out.mkdir(parents=True)
    (out/"public_r6_release_no_go.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--canonical-root",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    a=parser.parse_args()
    result=execute(a.canonical_root,a.out)
    print("R6_EVIDENCE_LEDGER_COMPLETE",len(result["gates"]),"gates",
          result["blockedGateCount"],"blocked",result["status"],flush=True)
    if result["status"]!="NO_GO" or result["releaseAuthorized"]:
        raise SystemExit("R6 must never auto-authorize unsupported release")
if __name__=="__main__":main()
