from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from minimalize_engine import MinimalizeConfig, minimalize


def parser():
    p=argparse.ArgumentParser(description="Evaluate v0.3 Character Structure detection.")
    p.add_argument("--max-side",type=int,default=220)
    return p


def main():
    args=parser().parse_args()
    root=Path(__file__).parents[1]
    corpus=root/"tests/assets/corpus"
    out=root/"examples/character_structure_alpha1"
    out.mkdir(parents=True,exist_ok=True)

    files=sorted(
        p for p in corpus.iterdir()
        if p.suffix.lower() in {".png",".jpg",".jpeg",".webp"}
    )
    rows=[]
    for p in files:
        cfg=MinimalizeConfig.from_level(
            4,
            analysis_max_side=args.max_side,
            target_max_shapes=30,
            line_mode="none",
            enable_auto_retry=False,
        )
        scene=minimalize(p,cfg)
        ch=scene.metadata.get("character",{})
        parts=ch.get("structure",{}).get("parts",[])
        types=[x["part_type"] for x in parts]
        graph=ch.get("structure",{}).get("pose_graph") or {}
        row={
            "file":p.name,
            "subject_mode":scene.metadata.get("subject_mode",False),
            "character_enabled":ch.get("enabled",False),
            "preset":ch.get("structure",{}).get("preset"),
            "head":"head" in types,
            "face":"face" in types,
            "hair":"hair" in types,
            "torso":"torso" in types,
            "left_arm":"left_arm" in types,
            "right_arm":"right_arm" in types,
            "left_leg":"left_leg" in types,
            "right_leg":"right_leg" in types,
            "props":types.count("prop"),
            "pose_confidence":graph.get("confidence"),
        }
        rows.append(row)
        print(json.dumps(row,ensure_ascii=False))

    (out/"report.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf-8")
    with (out/"report.csv").open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys()))
        w.writeheader();w.writerows(rows)

    subject=[r for r in rows if r["character_enabled"]]
    summary={
        "images":len(rows),
        "character_images":len(subject),
        "face_rate":sum(r["face"] for r in subject)/max(1,len(subject)),
        "hair_rate":sum(r["hair"] for r in subject)/max(1,len(subject)),
        "torso_rate":sum(r["torso"] for r in subject)/max(1,len(subject)),
        "both_arms_rate":sum(r["left_arm"] and r["right_arm"] for r in subject)/max(1,len(subject)),
        "both_legs_rate":sum(r["left_leg"] and r["right_leg"] for r in subject)/max(1,len(subject)),
    }
    (out/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print("SUMMARY",json.dumps(summary))


if __name__=="__main__":
    main()
