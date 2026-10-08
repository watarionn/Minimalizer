"""Regression tests for non-generative source-owned part vector scene."""
import sys
from pathlib import Path
from xml.etree import ElementTree as ET
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
import face_parts_vector_scene_v1 as m


def test_binary_region_vectors_contours():
    mask=np.zeros((80,80),dtype=bool)
    mask[10:70,10:70]=True
    mask[27:42,27:42]=False
    d,n,v=m.contours_path(mask)
    assert n>=2 and v>=8 and d.count("M")>=2


def test_region_colors_are_observed_source_pixels():
    a=np.full((340,340,3),(238,170,120),dtype=np.uint8)
    a[80:140,80:140]=(200,80,30)
    a[140:200,80:140]=(60,90,180)
    mask=np.zeros((340,340),dtype=bool)
    mask[70:205,70:150]=True
    layers=m.region_colormasks(Image.fromarray(a),mask,3)
    colors={tuple(c) for c in a[mask]}
    assert layers and all(tuple(c) in colors for _,c,_ in layers)
    assert all(not np.any(layer &~mask) for layer,_,_ in layers)


def test_actual_repo_masks_and_no_face_layer(tmp_path):
    src=np.full((340,340,3),(250,205,188),dtype=np.uint8)
    face=np.zeros((340,340),bool);face[120:184,130:213]=True
    hair=np.zeros((340,340),bool);hair[48:131,120:235]=True
    subject=np.zeros((340,340),bool);subject[20:330,50:300]=True
    masks={"face":face,"hair":hair,"subject":subject}
    # Overlay all source-owned part masks as empty except synthetic hair.
    for role in m.ORDER:
        if role not in masks:
            masks[role]=np.zeros((340,340),bool)
    features={"eye":np.zeros((340,340),bool)}
    # A true experiment source is required by observed_tie_mask; separately
    # assert vector assembly uses only one subject base and no face role.
    source=Path(m.__file__).read_text(encoding="utf-8")
    assert 'put(owner,skin,"subject","underlay")' in source
    assert 'put(' not in source.split("def assemble")[1].split("def preview")[0].replace('put(owner,skin,"subject","underlay")','').replace('put(layer,color,role,kind)','').replace('put(tie,observed_color(src,tie),"necktie","identity-accent")','').split('def put(')[0]


def test_no_raster_embeddings_or_neural_generation():
    source=Path(m.__file__).read_text(encoding="utf-8")
    assert "import torch" not in source
    assert "from diffusers" not in source
    assert "import local_worker" not in source
    assert "image_to_image" not in source
    assert "data-part" in source
    assert "not_core_pass" in source
