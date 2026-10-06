from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

FACE_RASTER_GUARD_VERSION = "sa7.38-v1"


@dataclass(frozen=True)
class FaceRasterGuardResult:
    version: str
    rgb: np.ndarray
    fill_rgb: tuple[int, int, int]
    face_pixels: int
    changed_face_pixels: int
    changed_outside_face_pixels: int

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "fill_rgb": list(self.fill_rgb),
            "face_pixels": self.face_pixels,
            "changed_face_pixels": self.changed_face_pixels,
            "changed_outside_face_pixels": self.changed_outside_face_pixels,
        }


def _observed_representative_rgb(
    source_rgb: np.ndarray,
    face_mask: np.ndarray,
) -> tuple[int, int, int]:
    source = np.asarray(source_rgb, dtype=np.uint8)
    face = np.asarray(face_mask, dtype=bool)
    values = source[face]
    if len(values) == 0:
        raise ValueError("face mask is empty")

    median = np.median(values, axis=0).astype(np.float32)
    distances = np.linalg.norm(values.astype(np.float32) - median, axis=1)
    chosen = values[int(np.argmin(distances))]
    return tuple(int(v) for v in chosen)


def apply_face_raster_guard(
    rendered_rgb: np.ndarray,
    source_rgb: np.ndarray,
    face_mask: np.ndarray,
) -> FaceRasterGuardResult:
    """Flatten final rendered face pixels to one observed source color.

    This is a deterministic post-render safety guard. It only mutates pixels
    inside the authorized semantic face mask. Golden, adopted-baseline pixels,
    face-feature proposals, and generative reconstruction are not inputs.
    """
    rendered = np.asarray(rendered_rgb, dtype=np.uint8)
    source = np.asarray(source_rgb, dtype=np.uint8)
    face = np.asarray(face_mask, dtype=bool)

    if rendered.ndim != 3 or rendered.shape[2] != 3:
        raise ValueError("rendered_rgb must be HxWx3")
    if source.shape != rendered.shape:
        raise ValueError("source/rendered image shape mismatch")
    if face.shape != rendered.shape[:2]:
        raise ValueError("face mask shape mismatch")
    face_pixels = int(face.sum())
    if face_pixels < 16:
        raise ValueError("face mask is too small")

    fill_rgb = _observed_representative_rgb(source, face)
    output = rendered.copy()
    before = output.copy()
    output[face] = np.asarray(fill_rgb, dtype=np.uint8)

    changed = np.any(output != before, axis=2)
    changed_face = int((changed & face).sum())
    changed_outside = int((changed & ~face).sum())
    if changed_outside != 0:
        raise AssertionError("face raster guard changed pixels outside face mask")

    return FaceRasterGuardResult(
        version=FACE_RASTER_GUARD_VERSION,
        rgb=output,
        fill_rgb=fill_rgb,
        face_pixels=face_pixels,
        changed_face_pixels=changed_face,
        changed_outside_face_pixels=changed_outside,
    )
