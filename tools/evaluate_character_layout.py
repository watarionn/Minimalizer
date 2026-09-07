from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from minimalize_engine import MinimalizeConfig, minimalize
from minimalize_engine.character.layout import shapes_bounds


def parser():
    p=argparse.ArgumentParser(description="Evaluate v0.3-alpha6 Character Layout.")
    p.add_argument("--max-side",type=int,default=220)
    return p


def _scene(path:Path,max_side:int,enabled:bool):
    return minimalize(
        path,
        MinimalizeConfig.from_level(
            4,
            analysis_max_side=max_side,
            target_max_shapes=32,
            line_mode="none",
            enable_auto_retry=False,
            enable_character_layout=enabled,
        ),
    )


def _off_metrics(scene,on_layout):
    x0,y0,x1,y1=shapes_bounds(scene.shapes)
    w,h=scene.width,scene.height
    top=y0/max(h,1)
    foot=1-y1/max(h,1)
    left=x0/max(w,1)
    right=1-x1/max(w,1)

    # Character Layout OFF still applies the legacy canvas padding transform.
    before=on_layout["visual_center_before"][0]
    source_x=on_layout["source_shape_bbox"][0]
    source_x1=on_layout["source_shape_bbox"][2]
    span=max(1e-6,source_x1-source_x)
    # Recover the padding transform from the final bbox widths.
    final_span=max(1e-6,x1-x0)
    scale=final_span/span
    tx=x0-source_x*scale
    visual_x=before*scale+tx
    target_x=on_layout["target_visual_center"][0]
    center_error=abs(visual_x-target_x)/max(w,1)
    return {
        "top":top,
        "foot":foot,
        "left":left,
        "right":right,
        "center_error":center_error,
        "clipped":x0<0 or y0<0 or x1>w or y1>h,
    }


def main():
    args=parser().parse_args()
    root=Path(__file__).parents[1]
    corpus=root/"tests/assets/corpus"
    out=root/"examples/character_layout_alpha6"
    out.mkdir(parents=True,exist_ok=True)

    rows=[]
    for path in sorted(corpus.iterdir()):
        if path.suffix.lower() not in {".png",".jpg",".jpeg",".webp"}:
            continue
        on=_scene(path,args.max_side,True)
        if not on.metadata.get("character",{}).get("enabled",False):
            continue
        off=_scene(path,args.max_side,False)

        layout=on.metadata["character"]["layout"]
        offm=_off_metrics(off,layout)
        q_on=on.metadata.get("quality",{})
        q_off=off.metadata.get("quality",{})

        row={
            "file":path.name,
            "preset":layout["preset"],
            "scale":layout["scale"],
            "translate_x":layout["translate_x"],
            "translate_y":layout["translate_y"],
            "pose_bias_x":layout["pose_bias_x"],
            "top_on":layout["headroom_ratio"],
            "top_off":offm["top"],
            "foot_on":layout["footroom_ratio"],
            "foot_off":offm["foot"],
            "top_error_on":abs(layout["headroom_ratio"]-.055),
            "top_error_off":abs(offm["top"]-.055),
            "foot_error_on":abs(layout["footroom_ratio"]-.040),
            "foot_error_off":abs(offm["foot"]-.040),
            "center_error_on":layout["metrics"]["center_error"],
            "center_error_off":offm["center_error"],
            "side_balance_on":abs(layout["left_margin_ratio"]-layout["right_margin_ratio"]),
            "side_balance_off":abs(offm["left"]-offm["right"]),
            "clipped_on":layout["metrics"]["clipped"],
            "clipped_off":offm["clipped"],
            "quality_on":q_on.get("score"),
            "quality_off":q_off.get("score"),
            "silhouette_on":q_on.get("silhouette_similarity"),
            "silhouette_off":q_off.get("silhouette_similarity"),
        }
        rows.append(row)
        print(json.dumps(row,ensure_ascii=False))

    def mean(key):
        vals=[r[key] for r in rows if isinstance(r.get(key),(int,float)) and not isinstance(r.get(key),bool)]
        return sum(vals)/max(1,len(vals))

    summary={
        "character_images":len(rows),
        "mean_scale":mean("scale"),
        "mean_abs_translate_x":sum(abs(r["translate_x"]) for r in rows)/max(1,len(rows)),
        "mean_abs_translate_y":sum(abs(r["translate_y"]) for r in rows)/max(1,len(rows)),
        "mean_top_error_on":mean("top_error_on"),
        "mean_top_error_off":mean("top_error_off"),
        "mean_foot_error_on":mean("foot_error_on"),
        "mean_foot_error_off":mean("foot_error_off"),
        "mean_center_error_on":mean("center_error_on"),
        "mean_center_error_off":mean("center_error_off"),
        "mean_side_balance_on":mean("side_balance_on"),
        "mean_side_balance_off":mean("side_balance_off"),
        "clipped_on":sum(r["clipped_on"] for r in rows),
        "clipped_off":sum(r["clipped_off"] for r in rows),
        "mean_quality_on":mean("quality_on"),
        "mean_quality_off":mean("quality_off"),
        "mean_silhouette_on":mean("silhouette_on"),
        "mean_silhouette_off":mean("silhouette_off"),
    }

    (out/"report.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf-8")
    with (out/"report.csv").open("w",newline="",encoding="utf-8-sig") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0].keys()))
        writer.writeheader();writer.writerows(rows)
    (out/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print("SUMMARY",json.dumps(summary))


if __name__=="__main__":
    main()
