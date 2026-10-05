import numpy as np
from minimalizer_zerobase.production.cross_part_region_graph import build_cross_part_region_graph,composed_regions
def test_touching_similar_regions_merge_across_parts():
 rgb=np.full((30,30,3),255,np.uint8);a=np.zeros((30,30),bool);b=a.copy();a[5:20,5:15]=1;b[5:20,15:25]=1
 rgb[a]=[30,40,60];rgb[b]=[35,45,65]
 g=build_cross_part_region_graph(rgb,{"torso":a,"left_arm":b},max_regions_per_part=1)
 assert len(g.edges)>=1
 assert len(composed_regions(g))==1
def test_different_colors_remain_distinct_even_when_touching():
 rgb=np.zeros((20,20,3),np.uint8);a=np.zeros((20,20),bool);b=a.copy();a[:,0:10]=1;b[:,10:20]=1;rgb[a]=[10,10,20];rgb[b]=[230,230,220]
 g=build_cross_part_region_graph(rgb,{"a":a,"b":b},max_regions_per_part=1)
 assert len(composed_regions(g))==2
