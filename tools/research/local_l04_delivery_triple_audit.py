"""Delivery-only audit for an A-owned Local L04 Stage8 triple.

Lane B does not judge or repair image semantics, owner quality, Golden quality,
or the source/expanded vertex policy.  It verifies that the exact A-owned
signed source, Stage8 JSON and expanded SVG are linked, safe to display, and
can be rasterized by a real browser without changing any artifact.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path


_GATE_PATH = Path(__file__).with_name("local_l04_source_stage8_svg_triple_gate.py")
_SPEC = importlib.util.spec_from_file_location("local_l04_triple_gate", _GATE_PATH)
if _SPEC is None or _SPEC.loader is None:  # pragma: no cover - installation failure
    raise RuntimeError("L04_TRIPLE_GATE_IMPORT_FAILED")
_GATE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_GATE)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_delivery(*, source_path: Path, stage8_json_path: Path,
                   expanded_svg_path: Path, expected_source_sha256: str,
                   expected_stage8_json_sha256: str,
                   expected_expanded_svg_sha256: str) -> dict:
    """Return B delivery evidence without promoting any A quality decision."""
    lineage = _GATE.evaluate_paths(
        source_path=source_path,
        stage8_json_path=stage8_json_path,
        expanded_svg_path=expanded_svg_path,
        expected_source_sha256=expected_source_sha256,
        expected_stage8_json_sha256=expected_stage8_json_sha256,
        expected_expanded_svg_sha256=expected_expanded_svg_sha256,
    )
    record = json.loads(stage8_json_path.read_text(encoding="utf-8"))
    return {
        "schema": "minimalizer/local-l04/delivery-triple-audit/v1",
        "case": lineage["case"],
        "three_artifact_hashes_verified": lineage["three_artifact_hashes_verified"],
        "safe_expanded_svg": True,
        "source_stage8_svg_cross_links_verified": True,
        "source_vertex_measurement": record["original_stage8_source_ring_vertices"],
        "expanded_svg_vertex_measurement": record["expanded_svg_vertices"],
        "vertex_policy": "OUT_OF_SCOPE_FOR_LANE_B_DELIVERY",
        "a_image_quality": "OUT_OF_SCOPE_FOR_LANE_B_DELIVERY",
        "browser_render": "NOT_RUN",
        "B_L04_delivery": "PASS",
        "A_L04_quality": "NOT_JUDGED",
        "release_authorized": False,
    }


def render_with_chrome(*, expanded_svg_path: Path, output_png: Path,
                       chrome: Path) -> str:
    """Render only the supplied SVG to a private PNG and return its SHA-256."""
    output_png.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [str(chrome), "--headless=new", "--disable-gpu", "--no-sandbox",
         "--hide-scrollbars", "--default-background-color=00000000",
         "--window-size=2000,2000", f"--screenshot={output_png}",
         expanded_svg_path.resolve().as_uri()],
        capture_output=True, text=True, check=False,
    )
    if completed.returncode != 0 or not output_png.is_file() or not output_png.stat().st_size:
        raise RuntimeError("CHROMIUM_L04_DELIVERY_RENDER_FAILED")
    return _sha256(output_png)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("stage8_json", type=Path)
    parser.add_argument("expanded_svg", type=Path)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--stage8-json-sha256", required=True)
    parser.add_argument("--expanded-svg-sha256", required=True)
    parser.add_argument("--chrome", type=Path)
    parser.add_argument("--rendered-png", type=Path)
    args = parser.parse_args()
    if (args.chrome is None) != (args.rendered_png is None):
        parser.error("--chrome and --rendered-png must be supplied together")
    result = audit_delivery(
        source_path=args.source, stage8_json_path=args.stage8_json,
        expanded_svg_path=args.expanded_svg,
        expected_source_sha256=args.source_sha256,
        expected_stage8_json_sha256=args.stage8_json_sha256,
        expected_expanded_svg_sha256=args.expanded_svg_sha256,
    )
    if args.chrome is not None:
        result["browser_render"] = {
            "status": "PASS",
            "png_sha256": render_with_chrome(
                expanded_svg_path=args.expanded_svg,
                output_png=args.rendered_png, chrome=args.chrome,
            ),
        }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
