from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from minimalizer_zerobase.evaluation.fragmentation_ownership import (
    build_fragmentation_ownership_report,
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Trace Phase 14 tiny components to Phase 7-12 ownership."
    )
    parser.add_argument("--case-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    subject = cv2.imread(
        str(args.case_dir / "phase_03" / "03_subject_mask.png"),
        cv2.IMREAD_GRAYSCALE,
    )
    if subject is None:
        raise ValueError("missing Phase 3 subject mask")
    report = build_fragmentation_ownership_report(
        phase7_payload=_load(args.case_dir / "phase_07" / "07_masses.json"),
        phase8_payload=_load(args.case_dir / "phase_08" / "08_importance.json"),
        phase9_payload=_load(args.case_dir / "phase_09" / "09_palette.json"),
        phase11_payload=_load(args.case_dir / "phase_11" / "11_composition.json"),
        phase12_payload=_load(
            args.case_dir / "phase_12" / "12_simplification.json"
        ),
        subject_area=int(np.count_nonzero(subject)),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8")
    args.output.write_bytes(raw)
    print(json.dumps(report["summary"], sort_keys=True))
    print(hashlib.sha256(raw).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
