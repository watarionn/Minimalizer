"""Regression for manually reviewed GC001 one-piece goggles morphology.

Annotation is NOT a transferable model, nor pixel-perfect semantic ground truth.
"""
import sys
from pathlib import Path
from xml.etree import ElementTree as ET
import numpy as np
from PIL import Image
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
import goggle_single_visor_annotation as m

def test_one_piece_lens_and_frame_partition():
    whole,lens,frame=m.visible_masks()
    assert int(whole.sum())==2680
    assert int(lens.sum())==1663
    assert int(frame.sum())==1017
    assert np.array_equal(whole,lens|frame)
    assert not np.any(lens&frame)
    assert not whole[100:].any()
    assert not whole[:30].any()

def test_original_color_only_paths_on_synthetic_source():
    rgb=np.full((340,340,3),[235,110,30],np.uint8)
    _,lens,frame=m.visible_masks()
    rgb[lens]=[210,160,59]
    rgb[frame]=[228,230,230]
    layers,budget=m.build_paths(Image.fromarray(rgb,"RGB"),lens,frame)
    assert set(budget)=={"visor_lens","visor_frame"}
    assert layers
    for role,kind,d,color,n,v in layers:
        assert color in ((210,160,59),(228,230,230))
        assert role in ("visor_lens","visor_frame")
        assert d and n>0 and v>=3

def test_standalone_svg_is_role_owned_without_face_or_raster():
    root=ET.Element("{%s}svg"%m.NS)
    m.append_paths(root,[("visor_lens","base","M 110 50 L 112 50 L 112 52 Z",(205,162,74),1,3)])
    path=root.findall(".//{%s}path"%m.NS)
    assert len(path)==1 and path[0].get("data-part")=="visor_lens"
    assert not root.findall(".//{%s}image"%m.NS)

def test_subject_plate_is_rejected():
    root=ET.Element("{%s}svg"%m.NS)
    ET.SubElement(root,"{%s}path"%m.NS,{"data-part":"subject","d":"M 0 0 L 1 0 L 1 1 Z"})
    with pytest.raises(AssertionError):
        m.append_paths(root,[])

def test_no_artificial_two_lens_split_or_hallucination():
    script=Path(m.__file__).read_text(encoding="utf-8")
    assert "single_wraparound_lens_and_outer_frame" in script
    assert '"boundary_pixel_perfect_verified":False' in script
    assert '"hidden_region_filled":False' in script
    assert '"full_character_golden_pass":False' in script
    assert "from diffusers" not in script and "import torch" not in script
