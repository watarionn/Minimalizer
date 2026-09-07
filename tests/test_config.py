from minimalize_engine.config import MinimalizeConfig


def test_level4_defaults():
    c = MinimalizeConfig.from_level(4)
    assert c.analysis_max_side == 640
    assert c.palette_colors == 6
    assert c.target_max_shapes == 50
    assert c.enable_composition_skeleton is True
