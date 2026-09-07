import cv2
from ..models import Region


def attach_contours(regions: list[Region]) -> list[Region]:
    for r in regions:
        contours, _ = cv2.findContours(r.mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            r.contour = max(contours, key=cv2.contourArea)
    return regions
