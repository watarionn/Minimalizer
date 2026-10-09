"""Independent source-edge/RGB audit and fail-closed visor material selection."""
from pathlib import Path
import sys
import cv2,numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
import visor_source_boundary_rgb_audit as audit
import visor_source_material_refinement as refine
from goggle_single_visor_annotation import visible_masks

def test_rgb_error_is_independent_of_mask_self_coverage():
    source=np.full((340,340,3),[221,230,238],np.uint8)
    result=source.copy();result[50:70,100:120]=[240,91,22]
    roi=np.zeros((340,340),bool);roi[40:90,90:150]=True
    true=audit.rgb_metrics(source,source,roi)
    wrong=audit.rgb_metrics(source,result,roi)
    assert true["source_rgb_mae"]==0
    assert wrong["source_rgb_mae"]>0
    assert wrong["source_rgb_abs_gt_40_pct"]>0

def test_source_canny_boundary_support_decreases_when_shifted():
    rgb=np.zeros((340,340,3),dtype=np.uint8)
    rgb[45:90,110:180]=220
    edge,distance=audit.source_edges(rgb)
    actual=np.zeros((340,340),bool);actual[45:90,110:180]=True
    shifted=np.zeros((340,340),bool);shifted[125:170,210:280]=True
    aligned=audit.source_edge_metrics(audit.perimeter(actual),distance)
    wrong=audit.source_edge_metrics(audit.perimeter(shifted),distance)
    assert aligned["source_canny_within_2px"]>.70
    assert wrong["source_canny_within_2px"]<.1

def test_source_pale_frame_excludes_warm_material_without_new_pixels():
    whole,lens,frame=visible_masks()
    rgb=np.full((340,340,3),[234,134,33],dtype=np.uint8)
    rgb[frame]=[238,240,241]
    coords=np.argwhere(frame)
    rgb[coords[:80,0],coords[:80,1]]=[243,119,34]
    source=Image.fromarray(rgb,"RGB")
    result_lens,result_frame,variant=refine.source_masks(source)
    assert np.array_equal(result_lens,lens)
    assert np.array_equal(result_frame,frame)
    assert np.all(variant["source_pale"]<=frame)
    assert int(variant["source_pale"].sum())==int(frame.sum())-80
    assert not np.any(variant["source_pale"][coords[:80,0],coords[:80,1]])

def test_acceptance_rejects_deleting_frame_or_degrading_lens():
    def record(name,n,frame,whole,lens,outside=0,verts=100):
        return {"variant":name,"source_frame_mask_pixels":n,
            "frame_source_mae":frame,"whole_visor_source_mae":whole,
            "lens_source_mae":lens,"changes_outside_reviewed_visor":outside,
            "all_visor_vertices":verts}
    rows=[record("all_removed",0,0,10,12),
          record("degrades_lens",600,20,19,40),
          record("scene_overspill",600,20,18,12,outside=1),
          record("valid_1",600,22,17,12,verts=800),
          record("valid_2",470,20,15,12,verts=700)]
    win=refine.select_rim_candidate(rows,1017,40,26,17)
    assert win["variant"]=="valid_2"
    assert refine.select_rim_candidate(rows[:3],1017,40,26,17) is None

def test_no_face_reconstruction_or_unverified_global_production():
    code=Path(refine.__file__).read_text(encoding="utf-8")
    assert '"semantic_frame_boundary_verified":False' in code
    assert '"full_character_golden_pass":False' in code
    assert '"production_changed":False' in code
    assert "from diffusers" not in code and "import torch" not in code
