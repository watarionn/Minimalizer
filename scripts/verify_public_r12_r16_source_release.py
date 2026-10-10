"""R12-R16 combined fail-closed engineering and release evidence matrix.

This is not a source-geometry repair algorithm or release automation.
It crosschecks immutable coordinate-free research evidence against the
archived external source/renderer reports and creates honest per-stage
research outcomes without generating, copying or modifying imagery.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CASES=("GC001","Raden")
GOLDENS=("Kyoko","Noel","Ririka")
FILES={
  "gc_gap":ROOT/"docs/zerobase/evidence/sa1034_gc001_vertex_budget_gap_20261008.json",
  "raden_gap":ROOT/"docs/zerobase/evidence/sa1034_raden_vertex_budget_gap_20261008.json",
  "sa1041":ROOT/"docs/zerobase/evidence/sa1041_two_source_full_character_gate_20261008.json",
  "sa1060":ROOT/"docs/research/evidence/sa1060_release_preflight_20261009.json",
  "sa1060a":ROOT/"docs/research/evidence/sa1060a_gc001_arm_numeric_20261009.json",
  "sa1060b":ROOT/"docs/research/evidence/sa1060b_c01_coordinate_free_20261009.json",
  "sa1060c":ROOT/"docs/research/evidence/sa1060c_c02a_coordinate_free_20261009.json",
  "sa1060d":ROOT/"docs/research/evidence/sa1060d_c02b1_coordinate_free_20261009.json",
}

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()

def required_data(paths:dict[str,Path])->dict:
    data={}
    for label,path in paths.items():
        data[label]=json.loads(path.read_text(encoding="utf-8"))
    return data

def frozen_external(root:Path)->dict[str,Path]:
    folder=lambda name:root/f"LibraryConvergence_{name}_20261010"
    return {
      "r4":folder("R4")/"full-scene/public_r4_matrix.json",
      "r4_components":folder("R4")/"layer-isolation/public_r4_component_attribution.json",
      "r6":folder("R6")/"public_r6_release_no_go.json",
      "r7":folder("R7")/"public_r7_review_packet.json",
      "r11":folder("R11")/"public_r11_live_host_readonly.json",
    }

def verify_authorities(source:dict,external:dict):
    expected={
      "gc_gap":"sa10.34-vertex-gap-v1",
      "raden_gap":"sa10.34-vertex-gap-v1",
      "sa1041":"sa10.41-two-character-full-svg-browser-research-v1",
      "sa1060":"non-promoting-frozen-evidence-audit-v1",
      "r4":"public-r4-native-vs-resvg-full-scene-v1",
      "r4_components":"public-r4-component-attribution-v1",
      "r6":"public-r6-conservative-release-admission-v1",
      "r7":"public-r7-unsigned-original-source-review-packet-v1",
      "r11":"public-r11-real-host-readonly-cache-admission-v1",
    }
    for key,version in expected.items():
        obj=source[key] if key in source else external[key]
        if obj.get("schema",obj.get("version"))!=version:
            raise ValueError("wrong original frozen report schema: "+key)
    if external["r6"]["status"]!="NO_GO" or (
        external["r6"]["blockedGateCount"]!=8 or
        external["r6"]["releaseAuthorized"] is not False):
        raise ValueError("R6 frozen release evidence tampered")
    if external["r7"]["humanGoldenSigned"] is not False or (
        external["r7"]["r6NoGoSHA256"]!=sha(external["r6_path"])):
        raise ValueError("R7 source Golden signed/lineage tampered")
    if external["r11"]["status"]!="LIVE_HOST_HTTP_AUDIT_PASS_RELEASE_NO_GO":
        raise ValueError("R11 actual host evidence missing")

def original_budget_gap(source:dict)->dict:
    cases={}
    for key,expected_case in (("gc_gap","GC001"),("raden_gap","Raden")):
        gap=source[key]
        full=source["sa1041"][expected_case]
        previous=source["sa1060"]["case_summary"][expected_case]
        if gap["case"]!=expected_case or len(gap["parts"])!=11:raise ValueError("source owner inventory missing")
        old=sum(p["old_ring_vertices"] for p in gap["parts"])
        adaptive=sum(p["adaptive_ring_vertices"] for p in gap["parts"])
        exact=sum(p["exact_ring_vertices"] for p in gap["parts"])
        owners=[p["owner"] for p in gap["parts"]]
        if len(set(owners))!=11 or not {"face","left_arm","right_arm","accessory_or_held_object","unknown"}.issubset(set(owners)):
            raise ValueError("protected source owners missing")
        if old!=gap["old_total"] or adaptive!=gap["adaptive_total"] or (
            old!=full["original_ring_budget_limit"] or
            adaptive!=full["original_source_ring_vertices"] or
            old!=previous["unchanged_stage8_cap"] or
            adaptive!=previous["immutable_source_ring_vertices"] or
            adaptive-old!=previous["stage8_overrun"]):
            raise ValueError("original Stage8 and SA10.60 signed budget disagree")
        # Signed source ring costs and expanded deployed SVG costs are separate
        # accounting domains and may NOT substitute for one another.
        cases[expected_case]={
           "ownerCount":len(owners),
           "oldHistoricalVertexCap":old,
           "actualAdaptiveOriginalRingVertices":adaptive,
           "sourceExactRingVertices":exact,
           "overrun":adaptive-old,
           "overrunPct":round(100*(adaptive-old)/old,5),
           "historicalCompactSvgVertices":previous["research_svg_vertices"],
           "expandedSvgUnderHistoricalCapIsNotSourceStage8Pass":True,
           "originalSourceOwnerExactTopologyBrowserApproved":False,
           "originalSourceRingBudgetPass":False,
           "ownerVertexGap":[{"owner":p["owner"],"historicalCap":p["old_ring_vertices"],
                            "adaptiveSourceVertices":p["adaptive_ring_vertices"],
                            "extra":p["adaptive_extra_vs_old"],
                            "degenerateRings":p["degenerate_rings"]}
                            for p in gap["parts"]],
        }
        for x in gap["parts"]:
            if x["adaptive_ring_vertices"]-x["old_ring_vertices"]!=x["adaptive_extra_vs_old"]:
                raise ValueError("source owner vertex accounting inconsistent")
    return {
       "stage":"R12","status":"ORIGINAL_STAGE8_BUDGET_MEASURED_HOLD",
       "caseCount":2,"cases":cases,
       "optionA_OriginalOwnerPreservingCapPass":False,
       "optionB_VersionedPolicyUserApproved":False,
       "stage8Resolved":False,
       "releaseAuthorized":False,
    }

def protected_owner_gate(source:dict)->dict:
    record=source["sa1041"]
    if record["full_character_browser_exact_RGB_parity_gate"]!="FAIL" or (
        record["source_protected_face_left_right_arm_browser_gate"]!="FAIL"):
        raise ValueError("historical owner failures unexpectedly absent")
    cases={}
    for case in CASES:
        row=record[case]
        diffs={k:row[k+"_wrong_pixels"] for k in
               ("original_face","left_arm","right_arm")}
        if min(diffs.values())<=0 or row["full_scene_RGB_differing_pixels"]<=0:
            raise ValueError("expected frozen protected-region diagnostics changed")
        cases[case]={
          "fullSceneChromeWrongPixels":row["full_scene_RGB_differing_pixels"],
          "protectedFaceWrongPixels":row["original_face_wrong_pixels"],
          "leftArmWrongPixels":row["left_arm_wrong_pixels"],
          "rightArmWrongPixels":row["right_arm_wrong_pixels"],
          "originalSvgOwnerSemanticParityPass":False,
        }
    preflight=source["sa1060"]
    if not ("STAGE8_COMPRESSED_CANDIDATE_CHANGES_SOURCE_OWNERS" in preflight["blockers"]):
        raise ValueError("compressed candidate owner changes were suppressed")
    return {
      "stage":"R13","status":"SOURCE_PROTECTED_PARTS_AUDITED_HOLD",
      "cases":cases,
      "independentSourcePhotos":2,
      "firstBadStageOwnershipRecovered":False,
      "compressedProposalChangesOriginalOwnerLabels":True,
      "protectedArmsFaceSvgChromeExact":False,
      "tieAndStaffIndependentSemanticReviewSigned":False,
      "inventedSemanticROIs":False,
      "faceMicrofeaturesDrawingAllowed":False,
      "releaseAuthorized":False,
    }

def cross_renderer_gate(external:dict)->dict:
    full,parts=external["r4"],external["r4_components"]
    if [x["case"] for x in full["cases"]]!=list(GOLDENS) or (
       [x["case"] for x in parts["cases"]]!=list(GOLDENS)):
        raise ValueError("R4 canonical Golden lineup changed")
    cases=[]
    for actual,split in zip(full["cases"],parts["cases"]):
        if actual["sourceSHA256"]!=split["sourceSHA256"]:raise ValueError("cross-engine SVG lineage mismatch")
        if not actual["chromeFrozenGoldenExact"] or (
            split["components"]["paths"]["differentPixels680"]!=0 or
            not split["components"]["paths"]["exact680"] or
            split["components"]["facet"]["differentPixels680"]<=0 or
            actual["chromeVsResvg680"]["differentPixels"]<=0):
            raise ValueError("R4 renderer decomposition no longer matches hold")
        cases.append({
          "case":actual["case"],"sourceSHA256":actual["sourceSHA256"],
          "frozenChrome340Exact":True,
          "sourcePathOnlyDpr2DifferentPixels":0,
          "frozenFacetOnlyDpr2DifferentPixels":split["components"]["facet"]["differentPixels680"],
          "wholeSceneDpr2DifferentPixels":actual["chromeVsResvg680"]["differentPixels"],
          "fullSceneRendererParityPassed":False,
        })
    return {
      "stage":"R14","status":"CROSS_RENDERER_FACET_DPR2_EXPLAINED_HOLD",
      "cases":cases,
      "frozenFacetResamplingSpecificDiscrepancy":True,
      "pathOnlyDpr2Exact":True,
      "fullSceneDpr2Exact":False,
      "noResvgReplacementApproved":True,
      "releaseAuthorized":False,
    }

def human_gate(external:dict,source:dict)->dict:
    review=external["r7"]
    if [x["case"] for x in review["cases"]]!=list(GOLDENS):
        raise ValueError("R7 unsigned Golden source case IDs missing")
    for row in review["cases"]:
        check=row["humanPartReview"]
        if len(check)!=8 or any(value is not None for value in check.values()):
            raise ValueError("R7 Golden human approval may not be forged")
        if row.get("reviewStatus")!="PENDING":raise ValueError("unexpected signed Golden in research chain")
    if source["sa1060"]["reviewed_signed_cases"]!=2:
        raise ValueError("original Stage8 signed corpus count changed")
    r11=external["r11"]
    live=r11["liveResponseMeasurements"]
    if live["css"]["maxAgeSeconds"]!=604800 or live["app"]["maxAgeSeconds"]!=604800:
        raise ValueError("live hosting cache contract changed: re-review needed")
    return {
        "stage":"R15","status":"HUMAN_DEVICE_LICENSE_SIGNOFF_PENDING",
        "publicGoldenPackets":3,
        "sourceStage8IndependentAuthenticatedCases":2,
        "originalStage8CorpusApproved18":False,
        "phase14Approved78":False,
        "manualQualityReviewAllPending":True,
        "physicalIphoneSafariTestObserved":False,
        "mpl2RedistributionLegalApproval":False,
        "actualLiveHostingRollbackCertified":False,
        "realLiveFixedUrlOneWeekCacheMeasured":True,
        "releaseAuthorized":False,
    }

def final_gate(stages:dict,external:dict)->dict:
    original=external["r6"]
    failures=[item["gate"] for item in original["blockedGates"]]
    if len(failures)!=8 or any(v["releaseAuthorized"] is not False
        for v in stages.values()):
        raise ValueError("R16 signed release integrity mismatch")
    return {
      "stage":"R16","status":"FINAL_RELEASE_GATE_NO_GO",
      "R12ToR15EngineeringAuditsCompleted":True,
      "stageStatuses":{k:v["status"] for k,v in stages.items()},
      "baselineR6GatesPass":7,"baselineR6GatesBlocked":8,
      "unresolvedOriginalR6ReleaseGates":failures,
      "candidateSourcePixelChanges":0,
      "realNewOwnerCorrectionsAccepted":0,
      "humanApprovalSigned":False,
      "productionApproved":False,
      "productionPromoted":False,
      "githubMainMerged":False,
      "localMinimalizerTouched":False,
      "releaseAuthorized":False,
    }

def run(canonical_root:Path,out:Path)->dict:
    if out.exists():raise FileExistsError("R12-R16 evidence output exists")
    input_files=dict(FILES)
    input_files.update(frozen_external(canonical_root))
    source=required_data(FILES)
    ext_paths=frozen_external(canonical_root)
    external=required_data(ext_paths)
    external["r6_path"]=ext_paths["r6"]
    verify_authorities(source,external)
    results={
       "R12":original_budget_gap(source),
       "R13":protected_owner_gate(source),
       "R14":cross_renderer_gate(external),
       "R15":human_gate(external,source),
    }
    results["R16"]=final_gate(results,external)
    out.mkdir(parents=True)
    evidence={"version":"public-r12-r16-immutable-source-release-matrix-v1",
              "sourceSHA256":{key:sha(path) for key,path in input_files.items()},
              "results":results,
              "engineeringDiagnosticsAllComplete":True,
              "actualUserReleaseApproved":False,
              "baselinePolicyPreserved":True,
              "status":"RESEARCH_COMPLETE_PRODUCT_NO_GO"}
    (out/"public_r12_r16_source_release_gate.json").write_text(
        json.dumps(evidence,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for stage,obj in results.items():
        (out/(stage.lower()+"_assessment.json")).write_text(
            json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return evidence

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--canonical-root",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    state=run(a.canonical_root,a.out)
    print("R12_R16_RESEARCH_LEDGER_COMPLETE",len(state["results"]),
          "stages","RELEASE",state["results"]["R16"]["status"],flush=True)

if __name__=="__main__":main()
