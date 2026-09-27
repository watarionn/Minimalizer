from __future__ import annotations
import cv2
import numpy as np
from .contracts import AnalyzerAdapter, Evidence, Provenance
from minimalizer_zerobase.core.coordinates import CoordinateSpace

class OpenCVContourAdapter(AnalyzerAdapter):
    adapter_id = "opencv.contours.v1"

    def __init__(self, low_threshold: int = 80, high_threshold: int = 160, min_area: float = 16.0):
        self.low_threshold = low_threshold
        self.high_threshold = high_threshold
        self.min_area = min_area

    def analyze(self, image, coordinate_space: CoordinateSpace) -> list[Evidence]:
        arr = np.asarray(image)
        gray = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY) if arr.ndim == 3 else arr.astype(np.uint8)
        edges = cv2.Canny(gray, self.low_threshold, self.high_threshold)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        records = []
        for contour in contours:
            area = float(cv2.contourArea(contour))
            if area < self.min_area: continue
            x, y, w, h = cv2.boundingRect(contour)
            pts = [[int(p[0][0]), int(p[0][1])] for p in contour]
            records.append((x, y, -area, w, h, pts, area))
        records.sort(key=lambda r: r[:5])
        provenance = Provenance("OpenCVContourAdapter", cv2.__version__)
        return [Evidence(f"contour-{i:04d}", "contour", coordinate_space, provenance,
            geometry={"bbox":[x,y,w,h],"points":pts,"area":area},
            normalization={"ordering":"bbox_xy_area_desc","thresholds":[self.low_threshold,self.high_threshold]})
            for i,(x,y,_,w,h,pts,area) in enumerate(records)]
