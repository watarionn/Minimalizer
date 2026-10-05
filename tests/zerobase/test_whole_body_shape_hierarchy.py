import numpy as np
from minimalizer_zerobase.production.structural_motifs import hierarchical_shape_mass
def test_hierarchy_stays_inside_authority():
 m=np.zeros((60,60),bool);m[5:55,8:52]=1
 h=hierarchical_shape_mass(m)
 assert not np.any(h&~m)
def test_hierarchy_keeps_majority_of_simple_mass():
 m=np.zeros((60,60),bool);m[5:55,8:52]=1
 assert hierarchical_shape_mass(m).sum()>=m.sum()*.7
def test_hierarchy_is_deterministic():
 m=np.zeros((40,40),bool);m[4:36,8:32]=1
 assert np.array_equal(hierarchical_shape_mass(m),hierarchical_shape_mass(m))
