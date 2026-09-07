from pathlib import Path
import cv2
import numpy as np


def save_rgb(path, image_rgb):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
    cv2.imencode(path.suffix or ".png", bgr)[1].tofile(str(path))


def debug_dir(config):
    if not config.debug_mode or not config.debug_output_dir:
        return None
    p = Path(config.debug_output_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p
