import numpy as np
from minimalizer_zerobase.production.semantic_edge_regions import edge_map,propose_edge_regions
def test_edge_map_detects_internal_contrast():
 a=np.zeros((30,30,3),np.uint8);a[:,:15]=20;a[:,15:]=230;e=edge_map(a)
 assert e[:,14:16].mean()>e[:,:8].mean()
def test_proposals_stay_inside_semantic_authority():
 a=np.full((40,40,3),200,np.uint8);m=np.zeros((40,40),bool);m[5:35,5:35]=1;a[5:35,5:20]=[20,30,50];a[5:35,20:35]=[230,230,220]
 r=propose_edge_regions(a,m,cell_size=8,max_regions=6)
 assert len(r)>=2 and all(np.all(x.mask<=m) for x in r)
