import cv2
import numpy as np


def resize_for_analysis(image: np.ndarray, max_side: int):
    h, w = image.shape[:2]
    longest = max(h, w)
    if longest <= max_side:
        return image.copy(), 1.0
    scale = max_side / longest
    resized = cv2.resize(image, (round(w * scale), round(h * scale)), interpolation=cv2.INTER_AREA)
    return resized, scale
