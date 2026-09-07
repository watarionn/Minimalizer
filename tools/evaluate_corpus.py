from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from minimalize_engine import MinimalizeConfig, minimalize
from minimalize_engine.io.image_exporter import export_png
from minimalize_engine.io.svg_exporter import export_svg


def parser():
    p=argparse.ArgumentParser(description="Evaluate Minimalizer against the bundled visual corpus.")
    p.add_argument("--start",type=int,default=0)
    p.add_argument("--end",type=int)
    p.add_argument("--max-side",type=int,default=320)
    p.add_argument("--level",type=int,default=4)
    p.add_argument("--auto-retry",action="store_true")
    return p


def main():
    args=parser().parse_args()
    root=Path(__file__).parents[1]
    corpus=root/"tests/assets/corpus"
    out=root/"examples/corpus_v020"
    out.mkdir(parents=True,exist_ok=True)

    files=sorted([p for p in corpus.iterdir() if p.suffix.lower() in {".png",".jpg",".jpeg",".webp"}])
    subset=files[args.start:args.end]
    rows=[]

    for p in subset:
        cfg=MinimalizeConfig.from_level(
            args.level,
            analysis_max_side=args.max_side,
            target_max_shapes=36,
            line_mode="none",
            enable_auto_retry=args.auto_retry,
        )
        scene=minimalize(p,cfg)
        stem=p.stem
        export_png(scene,out/f"{stem}_minimal.png")
        export_svg(scene,out/f"{stem}_minimal.svg")
        q=scene.metadata.get("quality",{})
        row={
            "file":p.name,
            "scene_mode":"subject" if scene.metadata.get("subject_mode") else "general",
            "shapes":scene.metadata.get("shape_count"),
            "regions":scene.metadata.get("region_count"),
            "quality":q.get("score"),
            "minimality":q.get("minimality_score"),
            "identity":q.get("identity_score"),
            "complexity":q.get("complexity_score"),
            "silhouette":q.get("silhouette_similarity"),
            "patterns":len(scene.metadata.get("pattern_groups",[])),
            "auto_retry":scene.metadata.get("auto_retry_attempts",0),
        }
        rows.append(row)
        print(json.dumps(row,ensure_ascii=False))

    partial=out/f"report_{args.start}_{args.end if args.end is not None else 'end'}.json"
    partial.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf-8")
    if rows:
        with (out/f"report_{args.start}_{args.end if args.end is not None else 'end'}.csv").open("w",newline="",encoding="utf-8-sig") as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0].keys()))
            w.writeheader();w.writerows(rows)


if __name__=="__main__":
    main()
