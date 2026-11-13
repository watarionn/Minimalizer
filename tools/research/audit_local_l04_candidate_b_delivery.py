"""Run Lane B's delivery audit against the current-candidate L04 triple.

This adapter consumes the candidate-triple layout, calls the existing B
delivery-only audit for each case, and preserves the boundary that B does not
judge A image quality or authorize release.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from local_l04_delivery_triple_audit import audit_delivery, render_with_chrome


CASES = ("H04", "H06", "H08")


def _json(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ValueError(f"JSON_ROOT_NOT_OBJECT:{path.name}")
    return value


def audit_candidate_b_delivery(
    package: Path, *, chrome: Path | None = None, render_root: Path | None = None
) -> dict[str, Any]:
    package = package.resolve()
    results: dict[str, dict[str, Any]] = {}
    failures: list[str] = []
    for case in CASES:
        try:
            manifest = _json(package / case / "TRIPLE_MANIFEST.json")
            source_info = manifest["source"]
            stage_info = manifest["stage8_json"]
            svg_info = manifest["expanded_svg"]
            source_path = package / "sources" / str(source_info["path"])
            stage_path = package / case / str(stage_info["path"])
            svg_path = package / case / str(svg_info["path"])
            result = audit_delivery(
                source_path=source_path,
                stage8_json_path=stage_path,
                expanded_svg_path=svg_path,
                expected_source_sha256=str(source_info["sha256"]),
                expected_stage8_json_sha256=str(stage_info["sha256"]),
                expected_expanded_svg_sha256=str(svg_info["sha256"]),
            )
            if chrome is not None:
                if render_root is None:
                    raise ValueError("RENDER_ROOT_REQUIRED")
                png = render_root / case / "B_L04_delivery_replay.png"
                result["browser_render"] = {
                    "status": "PASS",
                    "png_sha256": render_with_chrome(
                        expanded_svg_path=svg_path, output_png=png, chrome=chrome
                    ),
                }
            results[case] = result
            if result.get("B_L04_delivery") != "PASS":
                failures.append(f"{case}:B_L04_DELIVERY_NOT_PASS")
        except Exception as exc:  # fail closed and preserve the case name
            failures.append(f"{case}:{type(exc).__name__}:{exc}")
            results[case] = {"B_L04_delivery": "FAIL", "failure": str(exc)}
    return {
        "schema": "minimalizer/local-l04/candidate-b-delivery-audit/v1",
        "cases": results,
        "failures": failures,
        "B_L04_delivery": "PASS" if not failures else "FAIL",
        "A_L04_quality": "NOT_JUDGED",
        "release_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="現行L04 candidate tripleをB delivery監査へ接続する")
    parser.add_argument("package", type=Path)
    parser.add_argument("--chrome", type=Path)
    parser.add_argument("--render-root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit_candidate_b_delivery(
        args.package, chrome=args.chrome, render_root=args.render_root
    )
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["B_L04_delivery"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
