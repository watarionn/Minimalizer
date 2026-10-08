"""Contour fidelity comparisons on observed source geometry."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
import bangs_contour_fidelity_v1 as m

def test_unsimplified_has_at_least_as_many_vertices():
    arr=np.zeros((340,340),dtype=bool)
    arr[110:137,145:189]=True
    arr[119:130,167:174]=False
    _,_,n0=m.trace(arr,0.0)
    _,_,n6=m.trace(arr,0.6)
    assert n0>=n6>0

def test_no_invented_face_or_subject_skin_layer():
    text=Path(m.__file__).read_text(encoding="utf-8")
    assert '"data-part":"hair"' in text
    assert '"core_golden_pass":True' not in text
    assert "import torch" not in text
    assert "from diffusers" not in text

def test_epsilon_candidates_are_monotonic_and_contain_original():
    assert m.EPS==(0.6,0.3,0.0)
    assert all(m.EPS[i]>=m.EPS[i+1] for i in range(len(m.EPS)-1))
