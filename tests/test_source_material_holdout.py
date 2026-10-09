from pathlib import Path
import hashlib
import sys
import numpy as np
import pytest
sys.path.insert(0, str(Path(__file__).parents[1] / "tools" / "research"))
import source_material_holdout as h


def test_checked_file_fail_closed_on_sha_and_traversal(tmp_path):
    (tmp_path / 'source.png').write_bytes(b'source')
    rec = {'file':'source.png','sha256':hashlib.sha256(b'source').hexdigest()}
    assert h.checked_file(tmp_path, rec).is_file()
    with pytest.raises(ValueError, match='SHA mismatch'):
        h.checked_file(tmp_path, {**rec,'sha256':'0'*64})
    with pytest.raises(ValueError, match='path'):
        h.checked_file(tmp_path, {**rec,'file':'../escape.png'})


def test_original_rgb_error_independent_of_mask_overlap():
    img = np.full((120,120,3), 188, dtype=np.uint8)
    wrong = img.copy();wrong[20:60,20:60] = (40,90,220)
    mask = np.zeros((120,120), bool);mask[20:60,20:60] = True
    assert h.source_mae(img,img,mask) == 0
    assert h.source_mae(img,wrong,mask) > 0
    with pytest.raises(ValueError): h.source_mae(img,wrong,np.zeros_like(mask))


def test_edge_negative_control_rejects_offset_square():
    src = np.zeros((120,120,3),np.uint8)
    src[8:33,30:70] = 255
    mask = np.zeros((120,120),bool);mask[8:33,30:70] = True
    metric = h.boundary_support(src,mask)
    assert metric['source_edge_support_vs_shifted_delta'] > 0.1
    assert metric['edge_geometry_semantics_proven'] is False


def test_legacy_pale_probe_is_not_semantic_ownership():
    src = np.full((120,120,3), (245,226,221),np.uint8)
    mask = np.zeros((120,120),bool); mask[10:40,10:40] = True
    info = h.legacy_pale_probe(src,mask)
    assert info['retained_fraction'] == 1.0
    assert info['material_is_visor_frame_proven'] is False
    assert info['policy'] == 'GC001_PALE_COLOR_TRANSFER_NOT_AUTHORIZED'


def test_svg_rejects_embedded_source_bitmap(tmp_path):
    svg = tmp_path/'unsafe.svg'
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg"><image href="data:image/png;base64,AAAA"/></svg>')
    with pytest.raises(ValueError, match='raster embedding'):
        h.verify_svg(svg)
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0H10"/></svg>')
    assert '<path' in h.verify_svg(svg)
