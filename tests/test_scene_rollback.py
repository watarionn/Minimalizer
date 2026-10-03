from minimalizer_zerobase.refine.scene_rollback import *
def test_safe_scene_step_passes():
    assert accept_scene_step(SceneEvidence(.99,.60),SceneEvidence(.988,.595))
def test_silhouette_regression_rolls_back():
    assert not accept_scene_step(SceneEvidence(.99,.60),SceneEvidence(.98,.60))
def test_dino_regression_rolls_back():
    assert not accept_scene_step(SceneEvidence(.99,.60),SceneEvidence(.99,.58))
