import numpy as np
from minimalizer_zerobase.production.semantic_edge_regions import propose_edge_regions

def test_small_contrast_patch_is_not_required_to_keep_its_color_yet():
    # Characterizes the current failure boundary: spatial proposals may absorb a compact accent.
    rgb=np.full((48,48,3),[235,235,235],np.uint8)
    mask=np.zeros((48,48),bool);mask[4:44,4:44]=1
    rgb[20:28,22:26]=[40,210,55]
    regions=propose_edge_regions(rgb,mask,cell_size=8,max_regions=20)
    assert regions
    # TODO(next stage): strengthen this characterization into a survival requirement.
