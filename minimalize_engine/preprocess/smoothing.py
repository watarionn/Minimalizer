import cv2
import numpy as np


def apply_smoothing(image: np.ndarray, strength: float) -> np.ndarray:
    strength = max(0.0, min(1.0, float(strength)))
    if strength <= 0.0:
        return image.copy()
    # Odd kernel, deliberately modest. Downsampling already removes much detail.
    k = 1 + 2 * int(round(1 + strength * 3))
    return cv2.GaussianBlur(image, (k, k), sigmaX=0)
