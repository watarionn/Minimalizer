import numpy as np
from minimalize_engine import MinimalizeConfig
from minimalize_engine.pipeline import _prepare_source
from minimalize_engine.preprocess.resize import resize_for_analysis


def test_rgb_prepare_source_avoids_duplicate_buffer():
    image=np.zeros((120,180,3),dtype=np.uint8)
    cfg=MinimalizeConfig.from_level(4)
    raw,source,alpha,has_alpha=_prepare_source(image,cfg)
    assert alpha is None
    assert has_alpha is False
    assert np.shares_memory(raw,image)
    assert np.shares_memory(source,image)


def test_analysis_resize_caps_large_input():
    image=np.zeros((2400,3600,3),dtype=np.uint8)
    resized,scale=resize_for_analysis(image,640)
    assert max(resized.shape[:2]) == 640
    assert 0 < scale < 1
