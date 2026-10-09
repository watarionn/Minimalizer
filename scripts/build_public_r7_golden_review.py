"""MinimalizerPublic R7: source-grounded unsigned Golden human-review packet.

Makes *review artifacts only* from immutable source archives, no image generation,
semantic ROI inference, candidate promotion, or production route modification.
PIL only lays pixels into labeled diagnostic panels, originals are never rewritten.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from verify_public_v34_svgo_chrome import CASES, SIZE, check_sha, mismatched_pixels

PANEL=340
GAP=12
HEADER=38
COLS=3
ROWS=2
TITLE_H=40
SLOTS=(
    ("SOURCE ORIGINAL","source"),
    ("SEGMENTATION (UNSIGNED)","anime_seg_mask"),
    ("FROZEN FACET","facet"),
    ("V32 GOLDEN (UNSIGNED)","connected_fine"),
    ("V34 CHROME (UNSIGNED)","local_safe_chrome"),
)
REVIEW_FIELDS=(
    "samePersonAndSourceIdentity",
    "wholeSilhouetteMatch",
    "leftAndRightArmStructure",
    "neckTieShapeAndOriginalRGB",
    "staffOrHeldObjectPreservation",
    "clothingInteriorColorOwnership",
    "noInventedEyesMouthOrFacialDetails",
    "overallQualityHumanGolden",
)

def sha(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load_png(path:Path)->Image.Image:
    with Image.open(path) as im:
        if im.size!=SIZE:
            raise ValueError(f"wrong Golden dimensions: {path} {im.size}")
        return im.convert("RGBA")

def rgba_difference(a:Image.Image,b:Image.Image)->int:
    if a.size!=b.size:
        raise ValueError("no image resizing accepted for Golden comparisons")
    return mismatched_pixels(a.tobytes(),b.tobytes())

def review_canvas(images:dict[str,Image.Image], name:str)->Image.Image:
    # Labels and checkerboard are OUTSIDE source pixels; no change to input PNGs.
    width=COLS*(PANEL+GAP)+GAP
    height=TITLE_H+ROWS*(PANEL+HEADER+GAP)+GAP
    canvas=Image.new("RGB",(width,height),(247,247,247))
    d=ImageDraw.Draw(canvas)
    font=ImageFont.load_default()
    d.text((GAP,11),f"{name} | SOURCE-GROUNDED RESEARCH | NOT APPROVED",
           fill=(25,25,25),font=font)
    for index,(title,key) in enumerate(SLOTS):
        col=index%COLS;row=index//COLS
        x=GAP+col*(PANEL+GAP)
        y=TITLE_H+GAP+row*(PANEL+HEADER+GAP)
        d.text((x+3,y+11),title,fill=(10,10,10),font=font)
        # Neutral checkerboard reveals transparency in the source pixels.
        chess=Image.new("RGBA",SIZE,(255,255,255,255))
        check=ImageDraw.Draw(chess)
        for yy in range(0,PANEL,20):
            for xx in range(0,PANEL,20):
                if (xx//20+yy//20)%2==0:
                    check.rectangle((xx,yy,min(xx+19,PANEL-1),min(yy+19,PANEL-1)),
                                    fill=(230,230,230,255))
        chess.alpha_composite(images[key])
        canvas.paste(chess.convert("RGB"),(x,y+HEADER))
    dx=GAP+2*(PANEL+GAP)
    dy=TITLE_H+GAP+(PANEL+HEADER+GAP)
    d.text((dx,dy+18),"REVIEW STATUS: PENDING",fill=(120,20,20),font=font)
    d.text((dx,dy+44),"DO NOT MARK GOLDEN OR PARTS AS PASS",fill=(80,80,80),font=font)
    d.text((dx,dy+67),"Unknown part boundaries require human review.",fill=(70,70,70),font=font)
    d.text((dx,dy+91),"Source mask is diagnostic, not ground truth.",fill=(70,70,70),font=font)
    d.text((dx,dy+114),"SVG v34 is hybrid raster + RGB paths.",fill=(70,70,70),font=font)
    return canvas

def inspect_sources(v32:Path,v34:Path,r4:Path,r6:Path)->dict:
    release=json.loads(r6.read_text(encoding="utf-8"))
    if release.get("version")!="public-r6-conservative-release-admission-v1" or (
        release.get("status")!="NO_GO" or release.get("releaseAuthorized") is not False or
        release.get("blockedGateCount")<1):
        raise ValueError("R7 must be anchored to frozen R6 NO_GO verdict")
    snapshots=[]
    for name in CASES:
        paths={key:(v34/f"{name}_{key}.png" if key=="local_safe_chrome" else
                   v32/f"{name}_{key}.png") for _,key in SLOTS}
        svg=v34/f"{name}_local_safe.svg"
        # Validate ALL original inputs by the canonical v32/v34 archive SHA
        for key,p in paths.items():
            check_sha(v34 if key=="local_safe_chrome" else v32,
                "v34_evidence_manifest.json" if key=="local_safe_chrome" else
                "v32_evidence_manifest.json",p)
        check_sha(v34,"v34_evidence_manifest.json",svg)
        images={key:load_png(p) for key,p in paths.items()}
        ref=images["connected_fine"]
        chrome=images["local_safe_chrome"]
        r4_render=r4/f"{name}_chrome_340.png"
        r4_rgba=load_png(r4_render)
        frozen_vs_v34=rgba_difference(ref,chrome)
        r4_vs_v34=rgba_difference(r4_rgba,chrome)
        if frozen_vs_v34!=0 or r4_vs_v34!=0:
            raise ValueError("independent frozen v32/v34/R4 artifacts do not agree: "+name)
        snapshots.append({
            "case":name,"paths":paths,"images":images,"svg":svg,"r4":r4_render,
            "frozenVsV34Diff":frozen_vs_v34,
            "r4VsV34Diff":r4_vs_v34,
            "sourceVsV32Diff":rgba_difference(images["source"],ref),
            "sourceSegmentationIsSemanticAuthority":False,
        })
    return {"snapshots":snapshots,"r6SHA256":sha(r6)}

def execute(v32:Path,v34:Path,r4:Path,r6:Path,out:Path)->dict:
    if out.exists():
        raise FileExistsError("R7 never overwrites existing output")
    resolved=inspect_sources(v32,v34,r4,r6)
    out.mkdir(parents=True)
    cases=[]
    for x in resolved["snapshots"]:
        name=x["case"]
        canvas=review_canvas(x["images"],name)
        destination=out/f"{name}_source_golden_review.png"
        canvas.save(destination,format="PNG",optimize=False)
        cases.append({
            "case":name,"sourceSHA256":sha(x["paths"]["source"]),
            "segmentationDiagnosticSHA256":sha(x["paths"]["anime_seg_mask"]),
            "frozenFacetSHA256":sha(x["paths"]["facet"]),
            "v32GoldenSHA256":sha(x["paths"]["connected_fine"]),
            "v34SvgSHA256":sha(x["svg"]),
            "v34ChromeSHA256":sha(x["paths"]["local_safe_chrome"]),
            "independentR4ChromeSHA256":sha(x["r4"]),
            "reviewGalleryFile":destination.name,
            "reviewGallerySHA256":sha(destination),
            "sourceVsV32DifferentPixelsDiagnostic":x["sourceVsV32Diff"],
            "frozenV32VsV34PixelDiff":x["frozenVsV34Diff"],
            "independentR4ChromeVsV34PixelDiff":x["r4VsV34Diff"],
            "humanPartReview":{key:None for key in REVIEW_FIELDS},
            "partROIAutomaticallyInvented":False,
            "sourceSegmentationSemanticAuthority":False,
            "reviewStatus":"PENDING",
        })
    result={
        "version":"public-r7-unsigned-original-source-review-packet-v1",
        "r6NoGoSHA256":resolved["r6SHA256"],
        "cases":cases,
        "allThreeSourceOriginalsIncluded":len(cases)==3,
        "allFrozenCrossVersionsPixelExact":all(
            x["frozenV32VsV34PixelDiff"]==x["independentR4ChromeVsV34PixelDiff"]==0
            for x in cases),
        "humanGoldenSigned":False,"semanticPartOwnersSigned":False,
        "staffArmTieFaceCertified":False,"stage8OriginalRingBudgetApproved":False,
        "safariDeviceReviewed":False,"releaseAuthorized":False,
        "productionPromoted":False,"localMinimalizerTouched":False,
        "status":"PENDING_HUMAN_REVIEW_NO_GO",
    }
    instruction=[
        "# MinimalizerPublic R7 Golden original-source human-review packet",
        "",
        "**UNSIGNED / PENDING. These panels are not quality approvals.**",
        "",
        "Each contact sheet contains the archived ORIGINAL source photo, an **unsigned**",
        "source segmentation diagnostic, frozen Facet, v32 Golden and v34 Chrome at",
        "unaltered native 340×340 input resolution. The display-only neutral checkerboard",
        "reveals transparent pixels. Do not infer source-owner identities from color alone.",
        "",
        "## Manual review per Golden",
    ]
    for x in cases:
        instruction+=["",f"### {x['case']}",
            f"![{x['case']} source and Golden comparison]({x['reviewGalleryFile']})",
            ""]
        for key in REVIEW_FIELDS:
            instruction.append(f"- [ ] {key}: **not reviewed**")
        instruction+=["- Reviewer: **not supplied**",
            "- Review date/device: **not supplied**",
            "- Human Golden decision: **PENDING**",
            ""]
    instruction+=["## Release constraints",
        "",
        "- R6 remains NO_GO; R7 does not sign review fields or change any release gate.",
        "- No autogenerated arm/tie/staff semantic ROIs or claimed Golden acceptance.",
        "- v32 and v34 have exact RGBA pixel parity, but this **does not certify**",
        "  faithfulness to the original source photo or part preservation.",
        "- Archived source photos, frozen SVGs, and original images were not modified.",
        "- Real iPhone Safari/DPR, resvg full-scene DPR2, Stage8 ring budget,",
        "  ownership, MPL notice review and production rollback remain separately gated.",
        ""]
    (out/"GOLDEN_HUMAN_REVIEW_PENDING.md").write_text(
        "\n".join(instruction),encoding="utf-8")
    (out/"public_r7_review_packet.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result

def main():
    p=argparse.ArgumentParser()
    for arg in ("v32","v34","r4","r6","out"):
        p.add_argument("--"+arg,type=Path,required=True)
    a=p.parse_args()
    result=execute(a.v32,a.v34,a.r4,a.r6,a.out)
    print("R7_REVIEW_PACKET_COMPLETE",len(result["cases"]),
          "source-original cases; status",result["status"],flush=True)
if __name__=="__main__":main()
