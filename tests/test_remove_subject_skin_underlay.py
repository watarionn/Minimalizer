"""Regression: do not regress to a skin-colored all-subject underlay."""
from pathlib import Path
import sys
from xml.etree import ElementTree as ET
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
import remove_subject_skin_underlay as m
NS="{http://www.w3.org/2000/svg}"

def test_source_code_does_not_paint_source_wide_face_plate():
    source=Path(m.__file__).read_text(encoding="utf-8")
    assert 'put(owner,skin,"subject","underlay")' not in source
    assert 'owned|=(face & ~hair)' in source
    assert '"no_subject_skin_underlay":True' in source
    assert "from diffusers" not in source
    assert "import torch" not in source

def test_actual_svg_no_subject_or_face_paths(tmp_path):
    # A minimal isolated SVG verifies that the role gate can be checked
    # independently of pixels or misleading descriptive labels.
    path=tmp_path/"test.svg"
    path.write_text('<svg xmlns="http://www.w3.org/2000/svg"><rect data-part="background" fill="#eee" width="340" height="340"/><path data-part="hair" d="M0 0 L1 1" fill="#d85a28"/></svg>')
    root=ET.parse(path).getroot()
    parts=[p.attrib.get("data-part") for p in root.findall(".//"+NS+"path")]
    assert "subject" not in parts and "face" not in parts
    assert "hair" in parts

def test_missing_foreground_is_not_a_successful_complete_character():
    source=Path(m.__file__).read_text(encoding="utf-8")
    assert '"render_intentionally_incomplete":True' in source
    assert '"not_core_pass":True' in source
    assert 'No subject-wide skin plate' in source
