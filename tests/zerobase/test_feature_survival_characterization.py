import numpy as np
from minimalizer_zerobase.production.semantic_edge_regions import propose_edge_regions, propose_contrast_subregions

def test_compact_contrast_patch_survives_as_candidate():
 rgb=np.full((48,48,3),[235,235,235],np.uint8)
 mask=np.zeros((48,48),bool);mask[4:44,4:44]=1
 rgb[20:28,22:26]=[40,210,55]
 structural=propose_edge_regions(rgb,mask,cell_size=8,max_regions=20)
 accents=propose_contrast_subregions(rgb,mask,max_regions=4)
 assert structural
 assert any(r.rgb[1]>r.rgb[0]*1.25 and r.rgb[1]>r.rgb[2]*1.25 for r in accents)
 assert all(np.all(r.mask<=mask) for r in accents)
