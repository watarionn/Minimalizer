from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def read_cv_image(path: str | Path, flags: int = cv2.IMREAD_UNCHANGED) -> np.ndarray | None:
    """Read an image without relying on OpenCV's Windows path decoding."""
    source = Path(path)
    if not source.is_file():
        return None
    try:
        encoded = np.fromfile(source, dtype=np.uint8)
    except OSError:
        return None
    if encoded.size == 0:
        return None
    return cv2.imdecode(encoded, flags)
