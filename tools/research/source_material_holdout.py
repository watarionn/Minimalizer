"""Independent source-material / edge holdout; no segmentation or production edits.

Use one frozen non-GC001 source, signed masks, real browser SVG and OpenCV
baseline. Compare to original RGB only on original alpha-visible pixels.
Nothing is declared a semantic part merely because its color passes a gate.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import numpy as np
from PIL import Image, ImageDraw

FORBIDDEN = {"image", "foreignObject"}


def checked_file(root: Path, record: dict) -> Path:
    rel = Path(record["file"])
    if rel.is_absolute() or ".." in rel.parts or not rel.parts:
        raise ValueError("Manifest path must stay within verified input root")
    path = root / rel
    if not path.is_file():
        raise FileNotFoundError(path)
    if hashlib.sha256(path.read_bytes()).hexdigest() != record["sha256"]:
        raise ValueError("Frozen source or artifact SHA mismatch: " + rel.as_posix())
    return path


def boundary_support(source_rgb: np.ndarray, mask: np.ndarray) -> dict:
    gray = cv2.cvtColor(source_rgb, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(cv2.GaussianBlur(gray, (3, 3), 0.5), 60, 130, L2gradient=True) > 0
    distance = cv2.distanceTransform((~edges).astype(np.uint8), cv2.DIST_L2, 3)
    kernel = np.ones((3, 3), np.uint8)
    perimeter = cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_GRADIENT, kernel) > 0
    shifted = np.zeros_like(mask)
    offset = min(55, mask.shape[0] // 4)
    shifted[offset:] = mask[:-offset]
    shifted_perimeter = cv2.morphologyEx(shifted.astype(np.uint8), cv2.MORPH_GRADIENT, kernel) > 0
    if not np.any(perimeter) or not np.any(shifted_perimeter):
        raise ValueError("Mask cannot provide a real and shifted perimeter")
    real = float(np.mean(distance[perimeter] <= 2.5))
    control = float(np.mean(distance[shifted_perimeter] <= 2.5))
    return {"source_canny_within_2_5px": round(real, 5),
            "shifted_mask_negative_control": round(control, 5),
            "source_edge_support_vs_shifted_delta": round(real - control, 5),
            "edge_geometry_semantics_proven": False}


def source_mae(source: np.ndarray, candidate: np.ndarray, mask: np.ndarray) -> float:
    if source.shape != candidate.shape or mask.shape != source.shape[:2] or not np.any(mask):
        raise ValueError("Nonempty mask and aligned RGB images required")
    return round(float(np.abs(source.astype(np.int16) - candidate.astype(np.int16))[mask].mean()), 5)


def legacy_pale_probe(source: np.ndarray, mask: np.ndarray) -> dict:
    # Frozen GC001 color thresholds: a falsification probe, NOT segmentation.
    spread = source.max(axis=2).astype(np.int16) - source.min(axis=2).astype(np.int16)
    pale = (source.min(axis=2) > 138) & (spread < 91) & (source.mean(axis=2) > 178)
    retained = int(np.sum(mask & pale))
    return {"retained_pixels": retained,
            "retained_fraction": round(retained / int(mask.sum()), 5),
            "material_is_visor_frame_proven": False,
            "policy": "GC001_PALE_COLOR_TRANSFER_NOT_AUTHORIZED"}


def verify_svg(svg_path: Path) -> str:
    raw = svg_path.read_bytes()
    root = ET.fromstring(raw)
    if root.tag.rsplit("}", 1)[-1] != "svg":
        raise ValueError("Expected real vector SVG")
    if any(el.tag.rsplit("}", 1)[-1] in FORBIDDEN for el in root.iter()):
        raise ValueError("Source raster embedding forbidden")
    return raw.decode("utf-8")


def render_chromium(svg: str, out_png: Path, size: tuple[int, int]) -> dict:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=shutil.which("chromium") or shutil.which("google-chrome"), args=["--no-sandbox", "--disable-gpu"])
        try:
            page = browser.new_page(viewport={"width": size[0], "height": size[1]}, device_scale_factor=1)
            page.set_content('<html><style>html,body{margin:0;padding:0}svg{display:block}</style><body>' + svg + '</body></html>')
            region = page.locator("svg")
            box = region.bounding_box()
            if box is None or (round(box["width"]), round(box["height"])) != size:
                raise ValueError("SVG viewport does not match original source")
            region.screenshot(path=str(out_png))
            return {"engine": "Chromium (Playwright)", "version": browser.version}
        finally:
            browser.close()


def evaluate(root: Path, manifest: dict, out: Path) -> dict:
    source_path = checked_file(root, manifest["source"])
    svg_path = checked_file(root, manifest["svg"])
    baseline_path = checked_file(root, manifest["baseline"])
    if manifest["case_id"] == "GC001_IMG_1205":
        raise ValueError("GC001 is training/reference, not independent holdout")
    source_rgba = np.asarray(Image.open(source_path).convert("RGBA"), np.uint8)
    source = source_rgba[:, :, :3]
    visible = source_rgba[:, :, 3] > 0
    size = (source.shape[1], source.shape[0])
    baseline = np.asarray(Image.open(baseline_path).convert("RGB"), np.uint8)
    if baseline.shape != source.shape:
        raise ValueError("Baseline/source dimensions differ")
    out.mkdir(parents=True, exist_ok=True)
    chrome_file = out / "holdout_actual_chromium.png"
    chrome_details = render_chromium(verify_svg(svg_path), chrome_file, size)
    chrome = np.asarray(Image.open(chrome_file).convert("RGB"), np.uint8)
    if chrome.shape != source.shape:
        raise ValueError("Browser screenshot/source dimensions differ")
    roles = {}
    error = np.abs(source.astype(np.int16) - chrome.astype(np.int16)).mean(axis=2)
    observed = np.zeros(visible.shape, bool)
    for role, spec in sorted(manifest["masks"].items()):
        pixels = np.asarray(Image.open(checked_file(root, spec)).convert("L")) > 0
        if pixels.shape != visible.shape:
            raise ValueError("Signed role mask dimension mismatch: " + role)
        mask = pixels & visible
        if int(mask.sum()) < 50:
            raise ValueError("Missing original visible signed role: " + role)
        observed |= mask
        baseline_mae = source_mae(source, baseline, mask)
        chrome_mae = source_mae(source, chrome, mask)
        roles[role] = {"signed_mask_pixels": int(pixels.sum()),
            "source_visible_mask_pixels": int(mask.sum()),
            "alpha_excluded_pixels": int(np.sum(pixels & ~visible)),
            "opencv_source_mae": baseline_mae,
            "chromium_svg_source_mae": chrome_mae,
            "svg_minus_opencv_source_mae": round(chrome_mae - baseline_mae, 5),
            "source_edge": boundary_support(source, mask),
            "legacy_gc001_pale_negative_transfer": legacy_pale_probe(source, mask)}
    heat = np.clip(error * 4, 0, 255).astype(np.uint8)
    heat[~observed] = 0
    Image.fromarray(heat, "L").save(out / "source_rgb_error_roles_heatmap.png")
    source_view = Image.new("RGBA", size, (238, 238, 236, 255))
    source_view.alpha_composite(Image.fromarray(source_rgba, "RGBA"))
    panels = [source_view.convert("RGB"), Image.fromarray(baseline), Image.fromarray(chrome), Image.fromarray(heat, "L").convert("RGB")]
    gallery = Image.new("RGB", (size[0]*4, size[1]+36), (238, 238, 236))
    draw = ImageDraw.Draw(gallery)
    for i, (name, panel) in enumerate(zip(("SOURCE", "OPENCV BASELINE", "CHROME SVG", "SOURCE RGB ERROR"), panels)):
        gallery.paste(panel, (i*size[0], 0))
        draw.text((i*size[0]+8, size[1]+8), name, fill=(35,35,35))
    gallery.save(out / "holdout_comparison.png")
    result = {"case_id": manifest["case_id"], "source_sha256": manifest["source"]["sha256"],
        "input_manifest_sha256": hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest(),
        "chromium": chrome_details, "roles": roles,
        "independent_source_rgb_audit_executed": True,
        "gc001_visor_material_transfer_proven": False,
        "positive_goggles_holdout": False,
        "full_character_golden_pass": False, "production_changed": False,
        "decision": "MEASUREMENT_PASS_SEMANTIC_TRANSFER_HOLD"}
    result["outputs"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob("*.png"))}
    (out / "holdout_metrics.json").write_text(json.dumps(result, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    report = evaluate(a.root, json.loads(a.manifest.read_text(encoding="utf-8")), a.out)
    print(json.dumps({"decision":report["decision"],"roles":report["roles"]},ensure_ascii=False))

if __name__ == "__main__":
    main()
