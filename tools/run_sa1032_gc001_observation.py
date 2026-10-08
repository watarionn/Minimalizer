"""GC001 observed face/hair contour benchmark; no production scene mutation."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import cv2
import numpy as np
from minimalizer_zerobase.reviewed_sa10.source_svg_contour_proposals import propose_existing_contour
from minimalizer_zerobase.reviewed_sa10.source_svg_evidence import proposal_svg_evidence

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--masks", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)
    results = {}
    for owner in ("face", "hair", "left_arm", "right_arm"):
        path = a.masks / f"{owner}.png"
        if not path.exists():
            results[owner] = {"status": "MISSING_MASK"}
            continue
        mask = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
        if mask is None:
            results[owner] = {"status": "UNREADABLE_MASK"}
            continue
        if mask.ndim == 3:
            mask = mask[:, :, 3] if mask.shape[2] == 4 else cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
        mask = (mask > 0).astype(np.uint8)
        results[owner] = {"pixels": int(np.count_nonzero(mask)), "shape": list(mask.shape)}
        if owner not in ("face", "hair"):
            results[owner]["status"] = "OBSERVED_ONLY_NOT_EDITABLE"
            continue
        proposal = propose_existing_contour(owner, mask, mask, require_improvement=True)
        results[owner]["status"] = "NO_PROVEN_IMPROVEMENT" if proposal is None else "PROPOSAL"
        if proposal is not None:
            svg = proposal_svg_evidence(proposal, width=mask.shape[1], height=mask.shape[0])
            (a.output / f"{owner}_diagnostic.svg").write_text(svg, encoding="utf-8")
            results[owner]["source_iou"] = proposal.source_iou
    (a.output / "metrics.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
