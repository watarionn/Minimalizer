import numpy as np
from minimalizer_zerobase.production.structural_motifs import coarse_part_block
def test_coarse_block_stays_inside_authority():
 m=np.zeros((60,60),bool);m[5:55,8:52]=1;m[20:25,8:15]=0
 z=coarse_part_block(m);assert not np.any(z&~m)
def test_coarse_block_is_meaningfully_smaller_but_major():
 m=np.zeros((60,60),bool);m[5:55,8:52]=1
 z=coarse_part_block(m);assert m.sum()*.55<=z.sum()<m.sum()*.8
def test_coarse_block_deterministic():
 m=np.zeros((40,40),bool);m[4:36,8:32]=1
 assert np.array_equal(coarse_part_block(m),coarse_part_block(m))
