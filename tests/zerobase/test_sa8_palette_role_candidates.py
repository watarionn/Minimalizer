import numpy as np

from minimalizer_zerobase.production.palette_role_candidates import propose_palette_role_candidates


def test_palette_and_primitive_budgets_are_independent():
    image=np.zeros((40,40,3),dtype=np.uint8)
    mask=np.zeros((40,40),dtype=bool)
    for y,x in ((2,2),(2,26),(26,2),(26,26)):
        mask[y:y+10,x:x+10]=True
        image[y:y+10,x:x+10]=[180,60,30]
    candidates=propose_palette_role_candidates(
        image,mask,"major_clothing",palette_role_budget=1,primitive_budget=4
    )
    assert len(candidates)==4
    assert {item.palette_role_index for item in candidates}=={0}


def test_primitive_budget_bounds_candidates_without_changing_palette_identity():
    image=np.zeros((40,40,3),dtype=np.uint8)
    mask=np.zeros((40,40),dtype=bool)
    for y,x in ((2,2),(2,26),(26,2),(26,26)):
        mask[y:y+10,x:x+10]=True
        image[y:y+10,x:x+10]=[180,60,30]
    candidates=propose_palette_role_candidates(
        image,mask,"hair",palette_role_budget=1,primitive_budget=2
    )
    assert len(candidates)==2
    assert all(item.palette_role_index==0 for item in candidates)


def test_candidates_are_exact_source_subsets():
    image=np.zeros((24,24,3),dtype=np.uint8)
    mask=np.zeros((24,24),dtype=bool)
    mask[2:10,2:10]=True
    mask[14:22,14:22]=True
    image[mask]=[220,80,30]
    candidates=propose_palette_role_candidates(image,mask,"hair",palette_role_budget=1)
    assert len(candidates)==2
    assert all(np.all(item.mask <= mask) for item in candidates)
    assert sum(item.pixel_count for item in candidates)==int(mask.sum())


def test_candidate_order_is_deterministic():
    image=np.zeros((30,30,3),dtype=np.uint8)
    mask=np.zeros((30,30),dtype=bool)
    mask[2:14,2:14]=True
    mask[20:28,20:28]=True
    image[mask]=[210,90,40]
    a=propose_palette_role_candidates(image,mask,"hair",palette_role_budget=1)
    b=propose_palette_role_candidates(image,mask,"hair",palette_role_budget=1)
    assert [(x.component_id,x.pixel_count,x.rgb) for x in a]==[(x.component_id,x.pixel_count,x.rgb) for x in b]


def test_zero_primitive_budget_fails_closed():
    image=np.full((20,20,3),120,dtype=np.uint8)
    mask=np.ones((20,20),dtype=bool)
    assert propose_palette_role_candidates(image,mask,"torso",primitive_budget=0)==()
