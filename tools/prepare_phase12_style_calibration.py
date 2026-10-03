from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image


DEFAULT_CORPUS = Path(
    r"C:\Users\watar\Documents\Minimalizer\_eval_assets\approved78_full"
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare a deterministic, full-canvas Phase 12 style-calibration pair "
            "from an exact Approved-78 source/reference binding."
        )
    )
    parser.add_argument("--order", type=int, required=True)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("artifacts/phase12_style_calibration_inputs"),
    )
    parser.add_argument("--max-side", type=int, default=512)
    return parser.parse_args()


def _resize(image: Image.Image, max_side: int) -> Image.Image:
    width, height = image.size
    scale = min(1.0, float(max_side) / max(width, height))
    target = (
        max(1, int(round(width * scale))),
        max(1, int(round(height * scale))),
    )
    if target == image.size:
        return image.copy()
    return image.resize(target, Image.Resampling.LANCZOS)


def main() -> int:
    args = parse_args()
    manifest_path = args.corpus / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    case = next(
        (row for row in manifest.get("cases", []) if int(row.get("order", -1)) == args.order),
        None,
    )
    if case is None:
        raise RuntimeError(f"Approved-78 order not found: {args.order}")

    source = args.corpus / "inputs" / str(case["input_file"])
    reference = args.corpus / "references" / str(case["approved_file"])
    if not source.is_file() or not reference.is_file():
        raise FileNotFoundError("Approved-78 source/reference pair is incomplete")
    if sha256_file(source) != str(case["input_sha256"]):
        raise RuntimeError("Approved-78 source SHA mismatch")
    if sha256_file(reference) != str(case["approved_sha256"]):
        raise RuntimeError("Approved-78 reference SHA mismatch")

    case_dir = args.output_root / f"{args.order:02d}_{case['character']}"
    case_dir.mkdir(parents=True, exist_ok=True)
    derived_source = case_dir / f"{case['character']}_stylecal_source.png"
    derived_reference = case_dir / f"{case['character']}_stylecal_reference.png"

    with Image.open(source) as image:
        src = _resize(image.convert("RGBA"), args.max_side)
        src.save(derived_source, format="PNG", optimize=False)
        source_original_size = list(image.size)
    with Image.open(reference) as image:
        ref = _resize(image.convert("RGB"), args.max_side)
        ref.save(derived_reference, format="PNG", optimize=False)
        reference_original_size = list(image.size)

    if src.size != ref.size:
        # Style comparison is performed in the source calibration space.
        ref = ref.resize(src.size, Image.Resampling.LANCZOS)
        ref.save(derived_reference, format="PNG", optimize=False)

    binding = {
        "schema_version": "1.0.0",
        "purpose": "phase12-source-aligned-style-calibration",
        "order": args.order,
        "character": case["character"],
        "canonical_source": {
            "path": str(source),
            "filename": case["input_file"],
            "sha256": case["input_sha256"],
            "size": source_original_size,
        },
        "approved_reference": {
            "path": str(reference),
            "filename": case["approved_file"],
            "sha256": case["approved_sha256"],
            "size": reference_original_size,
        },
        "derived_source": {
            "path": str(derived_source),
            "sha256": sha256_file(derived_source),
            "size": list(src.size),
            "transform": {
                "kind": "full-canvas-uniform-downscale",
                "max_side": args.max_side,
                "resampler": "PIL-LANCZOS",
                "crop": False,
            },
        },
        "derived_reference": {
            "path": str(derived_reference),
            "sha256": sha256_file(derived_reference),
            "size": list(src.size),
            "transform": {
                "kind": "comparison-only-resize-to-derived-source-space",
                "resampler": "PIL-LANCZOS",
                "crop": False,
            },
        },
        "constraints": {
            "canonical_files_modified": False,
            "reference_used_as_render_input": False,
            "visual_source_content_changed": "scale-only",
            "valid_for": ["phase12-style-calibration"],
            "not_valid_for": ["canonical-approved78-sha-replay"],
        },
    }
    binding_path = case_dir / "binding.json"
    binding_path.write_text(
        json.dumps(binding, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(binding, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
