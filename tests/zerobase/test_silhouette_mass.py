import numpy as np
from minimalizer_zerobase.production.structural_motifs import silhouette_mass
def test_silhouette_mass_never_leaves_authority():
 m=np.zeros((60,60),bool);m[5:55,10:50]=1;m[20:25,10:18]=0
 s=silhouette_mass(m)
 assert not np.any(s&~m)
def test_silhouette_mass_keeps_broad_subject_support():
 m=np.zeros((60,60),bool);m[5:55,10:50]=1
 s=silhouette_mass(m)
 assert s.sum()>=m.sum()*.75
def test_silhouette_mass_deterministic():
 m=np.zeros((40,40),bool);m[4:36,8:32]=1
 assert np.array_equal(silhouette_mass(m),silhouette_mass(m))
