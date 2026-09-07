from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from minimalize_engine import MinimalizeConfig, minimalize


def parser():
    p=argparse.ArgumentParser(description="Evaluate v0.3-alpha2 face/hair rules.")
    p.add_argument("--max-side",type=int,default=220)
    return p


def main():
    args=parser().parse_args()
    root=Path(__file__).parents[1]
    corpus=root/"tests/assets/corpus"
    out=root/"examples/character_face_hair_alpha2"
    out.mkdir(parents=True,exist_ok=True)

    rows=[]
    for p in sorted(corpus.iterdir()):
        if p.suffix.lower() not in {".png",".jpg",".jpeg",".webp"}:
            continue

        cfg=MinimalizeConfig.from_level(
            4,
            analysis_max_side=args.max_side,
            target_max_shapes=30,
            line_mode="none",
            enable_auto_retry=False,
        )
        scene=minimalize(p,cfg)
        ch=scene.metadata.get("character",{})
        details=ch.get("details",{})
        face=details.get("face",{})
        hair=details.get("hair",{})
        layout=face.get("layout") or {}

        eye_count=int(layout.get("left_eye") is not None)+int(layout.get("right_eye") is not None)
        row={
            "file":p.name,
            "character_enabled":ch.get("enabled",False),
            "face_shapes":face.get("shape_count",0),
            "eye_count":eye_count,
            "mouth":layout.get("mouth") is not None,
            "face_confidence":layout.get("confidence"),
            "hair_shapes":hair.get("shape_count",0),
            "hair_flows":len(hair.get("flows",[])),
            "bang_flows":sum(f.get("flow_type")=="bangs" for f in hair.get("flows",[])),
            "side_hair_flows":sum(f.get("flow_type")=="side_hair" for f in hair.get("flows",[])),
            "back_hair_flows":sum(f.get("flow_type")=="back_hair" for f in hair.get("flows",[])),
            "quality":scene.metadata.get("quality",{}).get("score"),
            "shape_count":scene.metadata.get("shape_count"),
        }
        rows.append(row)
        print(json.dumps(row,ensure_ascii=False))

    subject=[r for r in rows if r["character_enabled"]]
    summary={
        "images":len(rows),
        "character_images":len(subject),
        "face_shape_rate":sum(r["face_shapes"]>0 for r in subject)/max(1,len(subject)),
        "two_eye_rate":sum(r["eye_count"]>=2 for r in subject)/max(1,len(subject)),
        "at_least_one_eye_rate":sum(r["eye_count"]>=1 for r in subject)/max(1,len(subject)),
        "mouth_rate":sum(r["mouth"] for r in subject)/max(1,len(subject)),
        "hair_shape_rate":sum(r["hair_shapes"]>0 for r in subject)/max(1,len(subject)),
        "hair_flow_rate":sum(r["hair_flows"]>0 for r in subject)/max(1,len(subject)),
        "mean_face_shapes":sum(r["face_shapes"] for r in subject)/max(1,len(subject)),
        "mean_hair_shapes":sum(r["hair_shapes"] for r in subject)/max(1,len(subject)),
        "mean_hair_flows":sum(r["hair_flows"] for r in subject)/max(1,len(subject)),
    }

    (out/"report.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf-8")
    with (out/"report.csv").open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys()))
        w.writeheader();w.writerows(rows)
    (out/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print("SUMMARY",json.dumps(summary))


if __name__=="__main__":
    main()
