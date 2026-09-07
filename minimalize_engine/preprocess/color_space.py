import cv2
import numpy as np


def rgb_to_lab(image: np.ndarray) -> np.ndarray:
    # OpenCV 8-bit Lab is sufficient for deterministic clustering in v0.1.
    return cv2.cvtColor(image, cv2.COLOR_RGB2LAB)


def lab_to_rgb(image: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(image, cv2.COLOR_LAB2RGB)
