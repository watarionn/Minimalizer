from __future__ import annotations
import numpy as np
from skimage.segmentation import slic
from .contracts import AnalyzerAdapter, Evidence, Provenance
from minimalizer_zerobase.core.coordinates import CoordinateSpace

class SLICRegionAdapter(AnalyzerAdapter):
    adapter_id = "skimage.slic.v2"

    def __init__(self, n_segments: int = 64, compactness: float = 12.0,
                 min_foreground_ratio: float | None = None):
        self.n_segments = n_segments
        self.compactness = compactness
        self.min_foreground_ratio = min_foreground_ratio
        if min_foreground_ratio is not None and not 0.0 <= min_foreground_ratio <= 1.0:
            raise ValueError("min_foreground_ratio must be 0..1")

    def analyze(self, image, coordinate_space: CoordinateSpace) -> list[Evidence]:
        arr = np.asarray(image)
        alpha = arr[:, :, 3] if arr.ndim == 3 and arr.shape[2] >= 4 else None
        rgb = arr[:, :, :3] if arr.ndim == 3 and arr.shape[2] >= 3 else arr
        if self.min_foreground_ratio is not None and alpha is None:
            raise ValueError("foreground filtering requires an alpha channel or explicit foreground evidence")
        labels = slic(rgb, n_segments=self.n_segments, compactness=self.compactness,
                      start_label=0, channel_axis=-1 if rgb.ndim == 3 else None,
                      convert2lab=rgb.ndim == 3, enforce_connectivity=True)
        out = []
        provenance = Provenance("SLICRegionAdapter", "skimage")
        for label in sorted(int(x) for x in np.unique(labels)):
            ys, xs = np.where(labels == label)
            foreground_ratio = None if alpha is None else float(np.mean(alpha[ys, xs] > 0))
            if self.min_foreground_ratio is not None and foreground_ratio < self.min_foreground_ratio:
                continue
            x0, x1, y0, y1 = int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())
            geometry = {"bbox":[x0,y0,x1-x0+1,y1-y0+1], "centroid":[float(xs.mean()),float(ys.mean())], "pixel_count":int(xs.size)}
            normalization = {"ordering":"label_ascending","n_segments":self.n_segments,"compactness":self.compactness}
            if foreground_ratio is not None:
                normalization["foreground_ratio"] = round(foreground_ratio, 12)
                normalization["foreground_source"] = "alpha"
            if rgb.ndim == 3 and rgb.shape[2] >= 3:
                mean = rgb[ys, xs, :3].astype(np.float64).mean(axis=0)
                normalization["base_color"] = [int(round(float(v))) for v in mean]
            out.append(Evidence(f"slic-{label:04d}", "region", coordinate_space, provenance,
                semantic_label="foreground" if foreground_ratio is not None else None,
                geometry=geometry, normalization=normalization))
        return out
