from __future__ import annotations

import argparse
import json

from minimalizer_zerobase.refine.abstraction_spatial import compare_confidence_npz


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("reference")
    parser.add_argument("candidate")
    parser.add_argument("--threshold",type=float,default=0.20)
    parser.add_argument("--grid-size",type=int,default=8)
    args=parser.parse_args()
    result=compare_confidence_npz(args.reference,args.candidate,active_threshold=args.threshold,grid_size=args.grid_size)
    payload={label:{
        "coverage": round(value.coverage,6),
        "centroid": round(value.centroid,6),
        "bbox": round(value.bbox,6),
        "occupancy": round(value.occupancy,6),
        "score": round(value.score,6),
    } for label,value in result.items()}
    print(json.dumps(payload,ensure_ascii=False,sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
