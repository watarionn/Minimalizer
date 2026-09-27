from __future__ import annotations
import numpy as np
from skimage.segmentation import slic
from .contracts import AnalyzerAdapter, Evidence, Provenance
from minimalizer_zerobase.core.coordinates import CoordinateSpace

class SLICRegionAdapter(AnalyzerAdapter):
    adapter_id = "skimage.slic.v1"

    def __init__(self, n_segments: int = 64, compactness: float = 12.0):
        self.n_segments = n_segments
        self.compactness = compactness

    def analyze(self, image, coordinate_space: CoordinateSpace) -> list[Evidence]:
        arr = np.asarray(image)
        labels = slic(arr, n_segments=self.n_segments, compactness=self.compactness,
                      start_label=0, channel_axis=-1 if arr.ndim == 3 else None,
                      convert2lab=arr.ndim == 3, enforce_connectivity=True)
        out = []
        provenance = Provenance("SLICRegionAdapter", "skimage")
        for label in sorted(int(x) for x in np.unique(labels)):
            ys, xs = np.where(labels == label)
            x0, x1, y0, y1 = int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())
            geometry = {"bbox":[x0,y0,x1-x0+1,y1-y0+1], "centroid":[float(xs.mean()),float(ys.mean())], "pixel_count":int(xs.size)}
            out.append(Evidence(f"slic-{label:04d}", "region", coordinate_space, provenance,
                geometry=geometry, normalization={"ordering":"label_ascending","n_segments":self.n_segments,"compactness":self.compactness}))
        return out
