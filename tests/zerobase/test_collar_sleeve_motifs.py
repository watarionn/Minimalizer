import numpy as np
from minimalizer_zerobase.production.structural_motifs import boundary_band,collar_motif,sleeve_boundary_motifs
def test_boundary_band_stays_in_union():
 a=np.zeros((30,30),bool);b=np.zeros_like(a);a[5:25,5:15]=1;b[5:25,15:25]=1
 x=boundary_band(a,b,2);assert x.any();assert not np.any(x&~(a|b))
def test_collar_is_upper_and_inside_garment():
 g=np.zeros((40,40),bool);g[12:36,8:32]=1;h=np.zeros_like(g);h[3:14,14:26]=1
 c=collar_motif(g,h);assert c.any();assert not np.any(c&~g);assert np.where(c)[0].mean()<np.where(g)[0].mean()
def test_sleeve_boundaries_touch_torso_arm_union():
 t=np.zeros((40,40),bool);t[8:34,12:28]=1;l=np.zeros_like(t);l[10:30,4:13]=1;r=np.zeros_like(t);r[10:30,27:36]=1
 xs=sleeve_boundary_motifs(t,l,r);assert len(xs)==2
 assert all(x.any() and not np.any(x&~(t|l|r)) for x in xs)
