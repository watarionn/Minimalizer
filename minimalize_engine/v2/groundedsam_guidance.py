from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any, Sequence

import numpy as np
from numpy.typing import NDArray
from PIL import Image

from minimalize_engine.v2.analysis_guidance import AnalysisGuidance, SemanticGuide

GROUNDED_SAM_LABELS = ("hair", "face-skin", "limb", "accessory")
DEFAULT_GROUNDING_DINO_MODEL = "IDEA-Research/grounding-dino-tiny"
DEFAULT_SAM_MODEL = "facebook/sam-vit-base"
DEFAULT_GROUNDING_PROMPT = (
    "hair. face. arm. hand. leg. ribbon. bow. hat. headband. "
    "necklace. earrings. microphone. accessory."
)


@dataclass(frozen=True, slots=True)
class GroundedSamConfig:
    detector_model: str = DEFAULT_GROUNDING_DINO_MODEL
    sam_model: str = DEFAULT_SAM_MODEL
    prompt: str = DEFAULT_GROUNDING_PROMPT
    detection_threshold: float = 0.20
    detection_full_confidence: float = 0.40
    text_threshold: float = 0.20
    subject_threshold: float = 0.50
    hair_max_subject_ratio: float = 0.50
    face_max_subject_ratio: float = 0.15
    limb_max_subject_ratio: float = 0.45
    accessory_max_subject_ratio: float = 0.30
    device: str = "auto"
    local_files_only: bool = False

    def __post_init__(self) -> None:
        if not self.detector_model or not self.sam_model or not self.prompt:
            raise ValueError("Grounded-SAM model ids and prompt must be non-empty")
        bounded = (
            self.detection_threshold,
            self.detection_full_confidence,
            self.text_threshold,
            self.subject_threshold,
            self.hair_max_subject_ratio,
            self.face_max_subject_ratio,
            self.limb_max_subject_ratio,
            self.accessory_max_subject_ratio,
        )
        if any(not 0.0 <= float(value) <= 1.0 for value in bounded):
            raise ValueError("Grounded-SAM thresholds and ratios must be within [0, 1]")
        if self.detection_full_confidence <= self.detection_threshold:
            raise ValueError(
                "detection_full_confidence must exceed detection_threshold"
            )
        if self.device not in {"auto", "cpu", "cuda"}:
            raise ValueError("Grounded-SAM device must be auto, cpu, or cuda")


@dataclass(slots=True)
class GroundedSamRuntime:
    torch: Any
    detector_processor: Any
    detector_model: Any
    sam_processor: Any
    sam_model: Any
    device: str
    dtype: Any


def _load_runtime_modules():
    try:
        torch = import_module("torch")
        transformers = import_module("transformers")
    except ImportError as exc:
        raise RuntimeError(
            "Grounded-SAM is optional; install torch and transformers "
            "in the isolated high-quality semantic environment"
        ) from exc
    return torch, transformers


def create_groundedsam_runtime(
    config: GroundedSamConfig | None = None,
) -> GroundedSamRuntime:
    active = config or GroundedSamConfig()
    torch, transformers = _load_runtime_modules()
    device = active.device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("Grounded-SAM CUDA was requested but is unavailable")
    dtype = torch.float16 if device == "cuda" else torch.float32

    detector_processor = transformers.AutoProcessor.from_pretrained(
        active.detector_model,
        local_files_only=active.local_files_only,
    )
    detector_model = (
        transformers.AutoModelForZeroShotObjectDetection.from_pretrained(
            active.detector_model,
            dtype=dtype,
            local_files_only=active.local_files_only,
        )
        .to(device)
        .eval()
    )
    sam_processor = transformers.SamProcessor.from_pretrained(
        active.sam_model,
        local_files_only=active.local_files_only,
    )
    sam_model = (
        transformers.SamModel.from_pretrained(
            active.sam_model,
            dtype=dtype,
            local_files_only=active.local_files_only,
        )
        .to(device)
        .eval()
    )
    return GroundedSamRuntime(
        torch=torch,
        detector_processor=detector_processor,
        detector_model=detector_model,
        sam_processor=sam_processor,
        sam_model=sam_model,
        device=device,
        dtype=dtype,
    )


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
            "ribbon",
            "bow",
            "hat",
            "headband",
            "necklace",
            "earring",
            "microphone",
            "accessory",
        )
    ):
        return "accessory"
    return None


def _evidence_confidence(
    score: float,
    sam_iou: float,
    config: GroundedSamConfig,
) -> float:
    span = config.detection_full_confidence - config.detection_threshold
    detection = np.clip(
        (float(score) - config.detection_threshold) / span,
        0.0,
        1.0,
    )
    mask_quality = np.clip(float(sam_iou), 0.0, 1.0)
    return float(detection * mask_quality)


def _max_subject_ratio(
    semantic_label: str,
    config: GroundedSamConfig,
) -> float:
    return {
        "hair": config.hair_max_subject_ratio,
        "face-skin": config.face_max_subject_ratio,
        "limb": config.limb_max_subject_ratio,
        "accessory": config.accessory_max_subject_ratio,
    }[semantic_label]


def semantic_maps_from_detections(
    *,
    subject_prob: NDArray[np.float32],
    raw_labels: Sequence[str],
    scores: Sequence[float],
    masks: NDArray[np.bool_],
    sam_ious: Sequence[float],
    config: GroundedSamConfig | None = None,
) -> NDArray[np.float32]:
    active = config or GroundedSamConfig()
    subject = np.asarray(subject_prob)
    mask_array = np.asarray(masks)
    if subject.dtype != np.float32 or subject.ndim != 2:
        raise ValueError("subject_prob must be float32 with shape (H, W)")
    if mask_array.ndim != 3 or mask_array.shape[1:] != subject.shape:
        raise ValueError("Grounded-SAM masks must have shape (N, H, W)")
    if not (
        len(raw_labels)
        == len(scores)
        == len(mask_array)
        == len(sam_ious)
    ):
        raise ValueError("Grounded-SAM detection arrays must have equal length")

    result = np.zeros(
        (len(GROUNDED_SAM_LABELS), *subject.shape),
        dtype=np.float32,
    )
    subject_binary = subject >= active.subject_threshold
    subject_count = max(int(subject_binary.sum()), 1)
    for raw_label, score, mask, sam_iou in zip(
        raw_labels, scores, mask_array, sam_ious
    ):
        semantic_label = _canonical_label(raw_label)
        if semantic_label is None:
            continue
        confidence = _evidence_confidence(score, sam_iou, active)
        if confidence <= 0.0:
            continue
        binary_mask = np.asarray(mask, dtype=bool)
        subject_ratio = float(
            (binary_mask & subject_binary).sum() / subject_count
        )
        if subject_ratio > _max_subject_ratio(semantic_label, active):
            continue
        channel = GROUNDED_SAM_LABELS.index(semantic_label)
        candidate = (
            binary_mask.astype(np.float32)
            * confidence
            * np.clip(subject, 0.0, 1.0)
        )
        result[channel] = np.maximum(result[channel], candidate)
    return result


def _run_groundedsam(
    source_rgb: NDArray[np.uint8],
    *,
    subject_prob: NDArray[np.float32],
    config: GroundedSamConfig,
    runtime: GroundedSamRuntime,
) -> NDArray[np.float32]:
    torch = runtime.torch
    image = Image.fromarray(source_rgb, mode="RGB")
    detector_inputs = runtime.detector_processor(
        images=image,
        text=config.prompt,
        return_tensors="pt",
    )
    detector_inputs = {
        key: (
            value.to(runtime.device)
            if hasattr(value, "to")
            else value
        )
        for key, value in detector_inputs.items()
    }
    if runtime.device == "cuda":
        detector_inputs["pixel_values"] = detector_inputs["pixel_values"].to(
            runtime.dtype
        )
    with torch.inference_mode():
        detector_outputs = runtime.detector_model(**detector_inputs)

    target_sizes = torch.tensor(
        [[source_rgb.shape[0], source_rgb.shape[1]]],
        device=runtime.device,
    )
    detection = runtime.detector_processor.post_process_grounded_object_detection(
        detector_outputs,
        detector_inputs["input_ids"],
        threshold=config.detection_threshold,
        text_threshold=config.text_threshold,
        target_sizes=target_sizes,
    )[0]
    boxes = detection["boxes"].detach().cpu()
    if len(boxes) == 0:
        return np.zeros(
            (len(GROUNDED_SAM_LABELS), *subject_prob.shape),
            dtype=np.float32,
        )
    raw_labels = detection["text_labels"]
    scores = detection["scores"].detach().cpu().numpy()
    sam_inputs = runtime.sam_processor(
        image,
        input_boxes=[boxes.tolist()],
        return_tensors="pt",
    )
    sam_inputs = {
        key: (
            value.to(runtime.device)
            if hasattr(value, "to")
            else value
        )
        for key, value in sam_inputs.items()
    }
    if runtime.device == "cuda":
        sam_inputs["pixel_values"] = sam_inputs["pixel_values"].to(
            runtime.dtype
        )
    with torch.inference_mode():
        sam_outputs = runtime.sam_model(
            **sam_inputs,
            multimask_output=False,
        )
    masks = runtime.sam_processor.image_processor.post_process_masks(
        sam_outputs.pred_masks.detach().cpu(),
        sam_inputs["original_sizes"].detach().cpu(),
        sam_inputs["reshaped_input_sizes"].detach().cpu(),
    )[0][:, 0].numpy()
    sam_ious = sam_outputs.iou_scores.detach().cpu().numpy()[0, :, 0]
    return semantic_maps_from_detections(
        subject_prob=subject_prob,
        raw_labels=raw_labels,
        scores=scores,
        masks=masks,
        sam_ious=sam_ious,
        config=config,
    )


def build_groundedsam_semantic_guide(
    source_rgb: NDArray[np.uint8],
    *,
    subject_prob: NDArray[np.float32],
    config: GroundedSamConfig | None = None,
    runtime: GroundedSamRuntime | None = None,
) -> SemanticGuide:
    source = np.asarray(source_rgb)
    subject = np.asarray(subject_prob)
    if source.dtype != np.uint8 or source.ndim != 3 or source.shape[2] != 3:
        raise ValueError("source_rgb must be uint8 with shape (H, W, 3)")
    if subject.dtype != np.float32 or subject.shape != source.shape[:2]:
        raise ValueError(
            "subject_prob must be float32 and match source resolution"
        )
    active = config or GroundedSamConfig()
    active_runtime = runtime or create_groundedsam_runtime(active)
    maps = _run_groundedsam(
        source,
        subject_prob=subject,
        config=active,
        runtime=active_runtime,
    )
    return SemanticGuide(
        labels=GROUNDED_SAM_LABELS,
        confidence_maps=maps,
        provider="grounded-sam",
        model=f"{active.detector_model}+{active.sam_model}",
    )


def fuse_semantic_guides(
    primary: SemanticGuide | None,
    supplemental: SemanticGuide,
) -> SemanticGuide:
    if primary is None:
        return supplemental
    if primary.source_shape != supplemental.source_shape:
        raise ValueError("semantic guides must share source resolution")
    labels = list(primary.labels)
    for label in supplemental.labels:
        if label not in labels:
            labels.append(label)
    maps = np.zeros(
        (len(labels), *primary.source_shape),
        dtype=np.float32,
    )
    for label, confidence in zip(primary.labels, primary.confidence_maps):
        maps[labels.index(label)] = confidence
    for label, confidence in zip(
        supplemental.labels,
        supplemental.confidence_maps,
    ):
        index = labels.index(label)
        maps[index] = np.maximum(maps[index], confidence)
    return SemanticGuide(
        labels=tuple(labels),
        confidence_maps=maps,
        provider=f"{primary.provider}+{supplemental.provider}",
        model=f"{primary.model}+{supplemental.model}",
    )


def attach_groundedsam_semantics(
    source_rgb: NDArray[np.uint8],
    *,
    base_guidance: AnalysisGuidance,
    config: GroundedSamConfig | None = None,
    runtime: GroundedSamRuntime | None = None,
) -> AnalysisGuidance:
    if base_guidance.subject_prob is None:
        raise ValueError(
            "Grounded-SAM semantic guidance requires subject_prob "
            "as foreground authority"
        )
    supplemental = build_groundedsam_semantic_guide(
        source_rgb,
        subject_prob=base_guidance.subject_prob,
        config=config,
        runtime=runtime,
    )
    semantic = fuse_semantic_guides(
        base_guidance.semantic,
        supplemental,
    )
    return AnalysisGuidance(
        subject_prob=base_guidance.subject_prob,
        subject_confidence=base_guidance.subject_confidence,
        semantic=semantic,
        subject_provider=base_guidance.subject_provider,
        subject_model=base_guidance.subject_model,
    )
