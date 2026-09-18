from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

GROUNDING_DINO_MODEL = "IDEA-Research/grounding-dino-tiny"
SAM_MODEL = "facebook/sam-vit-base"
PROMPT = (
    "hair. face. arm. hand. leg. ribbon. bow. hat. headband. "
    "necklace. earrings. microphone. accessory."
)
SEMANTIC_LABELS = ("hair", "face-skin", "limb", "accessory")
MAX_SUBJECT_RATIO = {
    "hair": 0.50,
    "face-skin": 0.15,
    "limb": 0.45,
    "accessory": 0.30,
}


def _canonical_label(text: str) -> str | None:
    value = str(text).casefold()
    if "hair" in value:
        return "hair"
    if "face" in value:
        return "face-skin"
    if any(token in value for token in ("arm", "hand", "leg")):
        return "limb"
    if any(
        token in value
        for token in (
            "ribbon", "bow", "hat", "headband", "necklace",
            "earring", "microphone", "accessory",
        )
    ):
        return "accessory"
    return None


def _evidence_confidence(score: float, sam_iou: float) -> float:
    detection = float(np.clip((score - 0.20) / 0.20, 0.0, 1.0))
    mask_quality = float(np.clip(sam_iou, 0.0, 1.0))
    return detection * mask_quality


def _load_subject_probability(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("L"), dtype=np.float32) / 255.0


def _colorize(confidence_maps: np.ndarray) -> Image.Image:
    colors = np.asarray(
        [[220, 80, 180], [245, 195, 150], [80, 160, 235], [245, 190, 60]],
        dtype=np.uint8,
    )
    best = np.argmax(confidence_maps, axis=0)
    maximum = np.max(confidence_maps, axis=0)
    rgb = np.full((*maximum.shape, 3), 18, dtype=np.uint8)
    for index, color in enumerate(colors):
        rgb[(best == index) & (maximum >= 0.20)] = color
    return Image.fromarray(rgb, mode="RGB")


def _contact_tile(source: Image.Image, semantics: Image.Image, title: str) -> Image.Image:
    overlay = Image.blend(source, semantics, 0.45)
    target_height = 280
    resized: list[Image.Image] = []
    for image in (source, semantics, overlay):
        scale = target_height / image.height
        resized.append(
            image.resize(
                (max(1, round(image.width * scale)), target_height),
                Image.Resampling.LANCZOS,
            )
        )
    canvas = Image.new(
        "RGB",
        (sum(image.width for image in resized), target_height + 26),
        "white",
    )
    x = 0
    for image in resized:
        canvas.paste(image, (x, 26))
        x += image.width
    ImageDraw.Draw(canvas).text((5, 6), title, fill="black")
    return canvas


def _save_contact_sheet(tiles: list[Image.Image], path: Path) -> None:
    if not tiles:
        return
    width = max(tile.width for tile in tiles)
    height = sum(tile.height for tile in tiles)
    sheet = Image.new("RGB", (width, height), (230, 230, 230))
    y = 0
    for tile in tiles:
        sheet.paste(tile, (0, y))
        y += tile.height
    sheet.save(path, quality=92)


def _load_runtime():
    import torch
    from transformers import (
        AutoModelForZeroShotObjectDetection,
        AutoProcessor,
        SamModel,
        SamProcessor,
    )
    return torch, AutoProcessor, AutoModelForZeroShotObjectDetection, SamProcessor, SamModel


def _run_case(
    image_path: Path,
    subject_mask_path: Path,
    *,
    detector_processor,
    detector_model,
    sam_processor,
    sam_model,
    torch,
    device: str,
    dtype,
) -> tuple[dict, np.ndarray, Image.Image]:
    source = Image.open(image_path).convert("RGB")
    subject_probability = _load_subject_probability(subject_mask_path)
    if subject_probability.shape != (source.height, source.width):
        raise ValueError(f"subject mask shape mismatch: {image_path.stem}")
    started = time.perf_counter()
    if device == "cuda":
        torch.cuda.reset_peak_memory_stats()

    detector_inputs = detector_processor(images=source, text=PROMPT, return_tensors="pt")
    detector_inputs = {
        key: (value.to(device) if hasattr(value, "to") else value)
        for key, value in detector_inputs.items()
    }
    if device == "cuda":
        detector_inputs["pixel_values"] = detector_inputs["pixel_values"].to(dtype)

    with torch.inference_mode():
        detector_outputs = detector_model(**detector_inputs)

    target_sizes = torch.tensor([[source.height, source.width]], device=device)
    detections = detector_processor.post_process_grounded_object_detection(
        detector_outputs,
        detector_inputs["input_ids"],
        threshold=0.20,
        text_threshold=0.20,
        target_sizes=target_sizes,
    )[0]

    raw_labels = detections["text_labels"]
    boxes = detections["boxes"].detach().cpu()
    scores = detections["scores"].detach().cpu().numpy()
    confidence_maps = np.zeros(
        (len(SEMANTIC_LABELS), source.height, source.width),
        dtype=np.float32,
    )
    accepted: list[dict] = []
    rejected_oversize: list[dict] = []

    if len(boxes):
        sam_inputs = sam_processor(source, input_boxes=[boxes.tolist()], return_tensors="pt")
        sam_inputs = {
            key: (value.to(device) if hasattr(value, "to") else value)
            for key, value in sam_inputs.items()
        }
        if device == "cuda":
            sam_inputs["pixel_values"] = sam_inputs["pixel_values"].to(dtype)

        with torch.inference_mode():
            sam_outputs = sam_model(**sam_inputs, multimask_output=False)

        masks = sam_processor.image_processor.post_process_masks(
            sam_outputs.pred_masks.detach().cpu(),
            sam_inputs["original_sizes"].detach().cpu(),
            sam_inputs["reshaped_input_sizes"].detach().cpu(),
        )[0][:, 0].numpy()
        ious = sam_outputs.iou_scores.detach().cpu().numpy()[0, :, 0]

        subject_binary = subject_probability >= 0.50
        subject_count = max(int(subject_binary.sum()), 1)
        for raw_label, score, mask, sam_iou in zip(raw_labels, scores, masks, ious):
            semantic_label = _canonical_label(raw_label)
            if semantic_label is None:
                continue
            confidence = _evidence_confidence(float(score), float(sam_iou))
            if confidence <= 0.0:
                continue
            subject_ratio = float((mask.astype(bool) & subject_binary).sum() / subject_count)
            record = {
                "raw_label": str(raw_label),
                "semantic_label": semantic_label,
                "detection_score": float(score),
                "sam_iou": float(sam_iou),
                "evidence_confidence": confidence,
                "subject_ratio": subject_ratio,
            }
            if subject_ratio > MAX_SUBJECT_RATIO[semantic_label]:
                rejected_oversize.append(record)
                continue
            channel = SEMANTIC_LABELS.index(semantic_label)
            candidate = (
                mask.astype(np.float32)
                * confidence
                * subject_probability
            )
            confidence_maps[channel] = np.maximum(
                confidence_maps[channel],
                candidate,
            )
            record["active_area_ratio"] = float((candidate >= 0.20).mean())
            accepted.append(record)

    elapsed = time.perf_counter() - started
    active_area = {
        label: float((confidence_maps[index] >= 0.20).mean())
        for index, label in enumerate(SEMANTIC_LABELS)
    }
    active_union = (confidence_maps >= 0.20).any(axis=0)
    overlap = (confidence_maps >= 0.20).sum(axis=0) >= 2
    peak_memory_mb = (
        float(torch.cuda.max_memory_allocated() / (1024 * 1024))
        if device == "cuda"
        else 0.0
    )
    metrics = {
        "name": image_path.stem,
        "elapsed_seconds": elapsed,
        "accepted_detection_count": len(accepted),
        "rejected_oversize_count": len(rejected_oversize),
        "active_area_ratio": active_area,
        "active_union_ratio": float(active_union.mean()),
        "semantic_overlap_ratio": float(overlap.mean()),
        "peak_cuda_memory_mb": peak_memory_mb,
        "accepted": accepted,
        "rejected_oversize": rejected_oversize,
    }
    return metrics, confidence_maps, source


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate Grounded-SAM semantic-part guidance on a corpus."
    )
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("rembg_mask_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--detector-model", default=GROUNDING_DINO_MODEL)
    parser.add_argument("--sam-model", default=SAM_MODEL)
    parser.add_argument("--local-files-only", action="store_true")
    args = parser.parse_args()

    inputs = sorted(args.input_dir.glob("*.png"))
    if not inputs:
        raise SystemExit("no PNG inputs found")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    torch, AutoProcessor, AutoModel, SamProcessor, SamModel = _load_runtime()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32
    print(f"device={device}", flush=True)
    detector_processor = AutoProcessor.from_pretrained(
        args.detector_model,
        local_files_only=args.local_files_only,
    )
    detector_model = AutoModel.from_pretrained(
        args.detector_model,
        dtype=dtype,
        local_files_only=args.local_files_only,
    ).to(device).eval()
    sam_processor = SamProcessor.from_pretrained(
        args.sam_model,
        local_files_only=args.local_files_only,
    )
    sam_model = SamModel.from_pretrained(
        args.sam_model,
        dtype=dtype,
        local_files_only=args.local_files_only,
    ).to(device).eval()

    cases: list[dict] = []
    tiles: list[Image.Image] = []
    for image_path in inputs:
        subject_mask = args.rembg_mask_dir / f"{image_path.stem}_mask.png"
        if not subject_mask.exists():
            raise SystemExit(f"missing rembg mask: {subject_mask}")
        metrics, confidence_maps, source = _run_case(
            image_path,
            subject_mask,
            detector_processor=detector_processor,
            detector_model=detector_model,
            sam_processor=sam_processor,
            sam_model=sam_model,
            torch=torch,
            device=device,
            dtype=dtype,
        )
        np.savez_compressed(
            args.output_dir / f"{image_path.stem}_confidence.npz",
            labels=np.asarray(SEMANTIC_LABELS),
            confidence=confidence_maps,
        )
        title = (
            f"{image_path.stem} det={metrics['accepted_detection_count']} "
            f"t={metrics['elapsed_seconds']:.2f}s"
        )
        tiles.append(_contact_tile(source, _colorize(confidence_maps), title))
        cases.append(metrics)
        print(
            image_path.stem,
            metrics["active_area_ratio"],
            f"accepted={metrics['accepted_detection_count']}",
            f"rejected={metrics['rejected_oversize_count']}",
            f"t={metrics['elapsed_seconds']:.3f}s",
            flush=True,
        )

    summary = {
        "case_count": len(cases),
        "device": device,
        "detector_model": args.detector_model,
        "sam_model": args.sam_model,
        "prompt": PROMPT,
        "mean_elapsed_seconds": float(
            np.mean([case["elapsed_seconds"] for case in cases])
        ),
        "max_peak_cuda_memory_mb": float(
            max(case["peak_cuda_memory_mb"] for case in cases)
        ),
        "mean_active_area_ratio": {
            label: float(
                np.mean([case["active_area_ratio"][label] for case in cases])
            )
            for label in SEMANTIC_LABELS
        },
        "zero_area_cases": {
            label: [
                case["name"]
                for case in cases
                if case["active_area_ratio"][label] == 0.0
            ]
            for label in SEMANTIC_LABELS
        },
        "oversize_rejection_count": int(
            sum(case["rejected_oversize_count"] for case in cases)
        ),
        "mean_active_union_ratio": float(
            np.mean([case["active_union_ratio"] for case in cases])
        ),
        "mean_semantic_overlap_ratio": float(
            np.mean([case["semantic_overlap_ratio"] for case in cases])
        ),
        "max_subject_ratio": MAX_SUBJECT_RATIO,
    }
    report = {"summary": summary, "cases": cases}
    (args.output_dir / "report.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )
    _save_contact_sheet(tiles, args.output_dir / "contact_sheet.jpg")
    print(json.dumps(summary, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
