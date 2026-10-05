from minimalizer_zerobase.production.authorized_geometry import _topology_bbox

def test_topology_bbox_tracks_strongest_occupied_cell():
    m={"mask_descriptor":{"grid":[4,4],"occupancy":[[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,1]]}}
    x,y,w,h=_topology_bbox(m,(0,0,100,100),0)
    assert x>=62.5 and y>=62.5
    assert x+w<=100 and y+h<=100

def test_topology_bbox_is_deterministic_for_ordinal():
    m={"mask_descriptor":{"grid":[4,4],"occupancy":[[1,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0.5]]}}
    assert _topology_bbox(m,(10,20,80,120),1)==_topology_bbox(m,(10,20,80,120),1)

def test_topology_bbox_falls_back_without_descriptor():
    assert _topology_bbox({},(1,2,3,4),0)==(1,2,3,4)
