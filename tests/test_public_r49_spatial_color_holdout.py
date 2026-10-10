"""R49 held-out source-color evaluation cannot manufacture approval."""
import sys
from pathlib import Path
import numpy as np
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import verify_public_r49_spatial_color_holdout as r49

def test_spatial_heldout_blocks_partition_original_pixels():
    mask=np.zeros((340,340),dtype=bool)
    mask[40:150,90:190]=True
    folds=r49.split_folds(mask)
    assert len(folds)==4
    assert sum(int(x.sum()) for x in folds)==int(mask.sum())
    assert all(not np.any(folds[i]&folds[j])
               for i in range(4) for j in range(i+1,4))
def test_reject_wrong_original_mask_dimensions():
    with pytest.raises(ValueError,match="R49"):
        r49.split_folds(np.ones((32,32),dtype=bool))
def test_no_color_promotion_or_runtime_route_edit():
    source=(ROOT/"scripts/verify_public_r49_spatial_color_holdout.py").read_text(encoding="utf8")
    assert '"productionReleaseAuthorized":False' in source
    assert '"humanSemanticOwnerSignoff":False' in source
    assert '"originalStage8VertexBudgetApproved":False' in source
    for path in ("web/static/public-route.js","local_worker/frontend/local-route.js"):
        assert "verify_public_r49_spatial_color_holdout" not in (ROOT/path).read_text(encoding="utf8")
