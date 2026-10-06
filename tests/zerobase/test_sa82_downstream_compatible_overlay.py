import numpy as np
from minimalizer_zerobase.production.downstream_compatible_overlay import propose_downstream_compatible_overlays

def fx():
 a=np.zeros((40,40,3),np.uint8);m=np.zeros((40,40),bool)
 for y,x in ((2,2),(2,26),(26,2),(26,26)):m[y:y+10,x:x+10]=1;a[y:y+10,x:x+10]=[180,60,30]
 return a,m

def test_rejects_candidate_mostly_overwritten_downstream():
 a,m=fx();d=np.zeros_like(m);d[2:12,2:12]=1;d[2:12,26:36]=1;d[26:36,2:12]=1
 out=propose_downstream_compatible_overlays(a,m,"major_clothing",(),(d,),palette_role_budget=1,overlay_budget=4,max_downstream_overlap_ratio=.2)
 assert all(x.downstream_overlap_ratio<=.2 for x in out)
 assert all(not np.any(x.visible_mask&d) for x in out)

def test_established_and_downstream_are_both_excluded():
 a,m=fx();e=np.zeros_like(m);e[2:12,2:12]=1;d=np.zeros_like(m);d[2:12,26:36]=1
 out=propose_downstream_compatible_overlays(a,m,"hair",(e,),(d,),palette_role_budget=1,overlay_budget=4)
 union=np.logical_or.reduce([x.visible_mask for x in out])
 assert not np.any(union&e) and not np.any(union&d)

def test_overlay_budget_hard_and_deterministic():
 a,m=fx();x=propose_downstream_compatible_overlays(a,m,"hair",(),(),palette_role_budget=1,overlay_budget=2)
 y=propose_downstream_compatible_overlays(a,m,"hair",(),(),palette_role_budget=1,overlay_budget=2)
 assert len(x)==2
 assert [(z.candidate.component_id,z.visible_gain_pixels) for z in x]==[(z.candidate.component_id,z.visible_gain_pixels) for z in y]

def test_zero_budget_fails_closed():
 a,m=fx();assert propose_downstream_compatible_overlays(a,m,"hair",(),(),overlay_budget=0)==()
