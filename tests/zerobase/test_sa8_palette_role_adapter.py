import numpy as np

from minimalizer_zerobase.semantic_abstraction.palette_role_adapter import adapt_palette_roles


def test_one_palette_role_preserves_two_disconnected_components():
    image=np.zeros((32,32,3),dtype=np.uint8)
    mask=np.zeros((32,32),dtype=bool)
    mask[2:12,2:12]=True
    mask[20:30,20:30]=True
    image[mask]=[220,80,30]
    report=adapt_palette_roles(image,mask,"hair")
    assert report.palette_role_count == 1
    assert report.component_count == 2
    assert len(report.roles[0].components) == 2
    assert report.roles[0].components[0].component_id != report.roles[0].components[1].component_id


def test_palette_budget_is_not_component_budget():
    image=np.zeros((40,40,3),dtype=np.uint8)
    mask=np.zeros((40,40),dtype=bool)
    for y,x in ((2,2),(2,26),(26,2),(26,26)):
        mask[y:y+10,x:x+10]=True
        image[y:y+10,x:x+10]=[180,60,30]
    report=adapt_palette_roles(image,mask,"major_clothing",max_roles=1)
    assert report.palette_budget == 1
    assert report.palette_role_count == 1
    assert report.component_count == 4


def test_small_component_is_rejected_without_removing_role():
    image=np.zeros((32,32,3),dtype=np.uint8)
    mask=np.zeros((32,32),dtype=bool)
    mask[2:22,2:22]=True
    mask[28:30,28:30]=True
    image[mask]=[200,70,20]
    report=adapt_palette_roles(image,mask,"hair",min_component_ratio=.02)
    assert report.palette_role_count == 1
    assert report.component_count == 1


def test_multiple_palette_roles_remain_source_derived():
    image=np.zeros((32,32,3),dtype=np.uint8)
    mask=np.zeros((32,32),dtype=bool)
    mask[2:30,2:16]=True
    mask[2:30,16:30]=True
    image[2:30,2:16]=[220,70,20]
    image[2:30,16:30]=[30,60,210]
    report=adapt_palette_roles(image,mask,"major_clothing",max_roles=2)
    assert report.palette_role_count == 2
    colors={role.rgb for role in report.roles}
    assert (220,70,20) in colors
    assert (30,60,210) in colors


def test_adapter_is_deterministic():
    image=np.zeros((36,36,3),dtype=np.uint8)
    mask=np.zeros((36,36),dtype=bool)
    mask[2:16,2:16]=True
    mask[20:34,20:34]=True
    image[mask]=[210,90,40]
    a=adapt_palette_roles(image,mask,"hair")
    b=adapt_palette_roles(image,mask,"hair")
    assert [(r.rgb,[c.component_id for c in r.components]) for r in a.roles] == [(r.rgb,[c.component_id for c in r.components]) for r in b.roles]
    assert all(np.array_equal(ca.mask,cb.mask) for ra,rb in zip(a.roles,b.roles) for ca,cb in zip(ra.components,rb.components))


def test_adapter_has_no_production_authority():
    image=np.full((16,16,3),120,dtype=np.uint8)
    mask=np.ones((16,16),dtype=bool)
    report=adapt_palette_roles(image,mask,"torso")
    assert report.production_authority is False
    assert report.production_output_changed is False


def test_empty_tiny_input_fails_closed_to_empty_report():
    image=np.zeros((8,8,3),dtype=np.uint8)
    mask=np.zeros((8,8),dtype=bool)
    mask[:2,:2]=True
    report=adapt_palette_roles(image,mask,"hair")
    assert report.roles == ()
    assert report.component_count == 0


def test_source_inputs_are_not_mutated():
    image=np.full((20,20,3),90,dtype=np.uint8)
    mask=np.ones((20,20),dtype=bool)
    before_image=image.copy(); before_mask=mask.copy()
    adapt_palette_roles(image,mask,"torso")
    assert np.array_equal(image,before_image)
    assert np.array_equal(mask,before_mask)
