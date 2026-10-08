"""Smoke gates for deterministic part ownership source and SVG research isolation."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
import part_occlusion_ownership_v1 as m


def test_single_owner_priority_in_source():
    code=Path(m.__file__).read_text(encoding="utf-8")
    assert "incoming=masks[role]&owner&~owned" in code
    assert "owned|=incoming" in code
    assert "owned|=(face & ~hair)" in code  # bangs must not be reserved as skin
    assert "residual=owner&~owned" in code
    assert "region=regions[role]" in code
    assert "np.int32" in code and "dtype=np.int64" in code


def test_no_face_polygon_or_neural_models_in_research():
    code=Path(m.__file__).read_text(encoding="utf-8")
    assert 'put(owner,skin,"subject","underlay")' in code
    assert '"data-part":role' in code
    assert "import torch" not in code
    assert "from diffusers" not in code
    assert "import local_worker" not in code


def test_ownership_count_is_exposed_for_review():
    code=Path(m.__file__).read_text(encoding="utf-8")
    assert '"residual_source_pixels"' in code
    assert '"part_owned_pixels"' in code
    assert '"ownership":ownership' in code
