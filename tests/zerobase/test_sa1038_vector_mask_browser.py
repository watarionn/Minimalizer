import json
import tempfile
import unittest
from pathlib import Path
from hashlib import sha256

import cv2
import numpy as np

from tools.run_sa1038_vector_mask_browser import (
    evaluate_real_chrome, prepare_vector_mask,
    prove_degenerate_rings_raster_neutral,
)


def parent_record():
    return {
        "primitive_id":"signed-lower-body",
        "primitive_type":"polygon",
        "semantic_part_id":"lower_body",
        "source_mask_owner":"lower_body",
        "parameters":{
            "components":[[[10,10],[50,10],[50,50],[10,50]]],
            "holes":[],
            "rings":[
                {"depth":0,"role":"fill",
                 "points":[[10,10],[50,10],[50,50],[10,50]]},
                {"depth":1,"role":"hole",
                 "points":[[25,25],[29,25],[29,29],[25,29]]},
                {"depth":1,"role":"hole","points":[[20,20]]},
            ],
        },
    }


def make_authority(tmp: Path):
    source="a"*64
    scene={
        "schema":"sa10.34-adaptive-contour-scene-v1",
        "original_source_sha256":source,
        "coordinate_space":{"pixel_width":64,"pixel_height":64},
        "primitives_back_to_front":[parent_record()]+[
            {"primitive_id":f"support-{i}","source_mask_owner":f"other-{i}"}
            for i in range(10)
        ],
    }
    outer=tmp/"phase8.json"
    outer.write_text(json.dumps(scene),encoding="utf-8")
    oldhash=sha256(outer.read_bytes()).hexdigest()
    materials=("dark_uniform","dark_uniform","white_shirt","white_shirt","green_necktie")
    cols=([30,38,71],[29,36,73],[247,249,253],[251,252,253],[148,211,26])
    panels=[]
    for i,(label,rgb) in enumerate(zip(materials,cols)):
        x=12+i*7
        panels.append({
            "schema":"sa10.36-uniform-material-panel-v1",
            "owner":"lower_body",
            "parent_primitive_id":"signed-lower-body",
            "material":label,
            "points":[[x,15],[x+5,15],[x+5,22],[x,22]],
            "color_rgb_observed":rgb,
            "additional_filled_geometric_subpath":True,
        })
    candidate={
        "schema":"sa10.37-apparel-simplified-scene-v1",
        "source_sha256":source,
        "stage8_outer_vector_sha256":oldhash,
        "apparel_material_polygons":panels,
    }
    candidate_path=tmp/"phase37.json"
    candidate_path.write_text(json.dumps(candidate),encoding="utf-8")
    metrics={
        "schema":"sa10.37-topology-locked-apparel-geometry-v1",
        "candidate_geometry_sha256":sha256(candidate_path.read_bytes()).hexdigest(),
        "case_source_sha256":source,
        "Stage04_source_masks_verified":True,
        "Stage36_material_provenance_verified":True,
        "all_filled_polygons_simple":True,
        "candidate_self_intersecting_panels":[],
        "face_left_right_arm_rgb_unchanged":True,
    }
    metrics_path=tmp/"metrics.json"
    metrics_path.write_text(json.dumps(metrics),encoding="utf-8")
    return outer,candidate_path,metrics_path


class Sa1038VectorMaskBrowserTests(unittest.TestCase):
    def test_degenerate_source_hole_must_be_proven_raster_neutral(self):
        valid,report=prove_degenerate_rings_raster_neutral(
            parent_record(),width=64,height=64,
        )
        self.assertEqual(len(valid),2)
        self.assertEqual(report["degenerate_source_ring_count"],1)
        self.assertEqual(report["degenerate_removal_changed_owner_pixels"],0)

    def test_filled_single_pixel_island_cannot_be_silently_omitted(self):
        p=parent_record()
        p["parameters"]["rings"].append({
            "depth":0,"role":"fill","points":[[3,3]]
        })
        with self.assertRaises(ValueError):
            prove_degenerate_rings_raster_neutral(p,width=64,height=64)

    def test_no_source_bitmap_and_every_svg_hole_stroke_counted(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            o,c,m=make_authority(root)
            record=prepare_vector_mask(
                original_outer_scene=o,simplified_apparel_scene=c,
                simplified_apparel_metrics=m,output_dir=root/"out",
            )
            svg=(root/"out"/"source_bound_vector_mask.svg").read_text("utf-8")
            self.assertIn("<mask ",svg)
            self.assertIn('mask-type="luminance"',svg)
            self.assertIn('translate(-0.25 0.5)',svg)
            self.assertEqual(svg.count("<polygon "),5)
            self.assertNotIn("<image",svg)
            self.assertNotIn("base64",svg)
            self.assertEqual(record["svg_apparel_polygon_vertices"],20)
            self.assertEqual(record["svg_mask_hole_boundary_stroke_paths"],1)
            self.assertTrue(record["degenerate_source_rings_proven_raster_neutral"])
            self.assertFalse(record["exact_browser_opencv_pixel_parity"])
            self.assertFalse(record["production_promotion_authorized"])

    def test_without_real_chrome_execution_no_fake_pass(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            o,c,m=make_authority(root)
            prepare_vector_mask(
                original_outer_scene=o,simplified_apparel_scene=c,
                simplified_apparel_metrics=m,output_dir=root/"out",
            )
            out=root/"out"
            ref=cv2.imread(str(out/"authoritative_opencv_material.png"))
            # Even a fabricated byte-identical file must not be considered
            # verified *Chrome execution*.
            cv2.imwrite(str(out/"actual_chrome_headless.png"),ref)
            report=evaluate_real_chrome(output_dir=out)
            self.assertEqual(report["browser_mismatched_rgb_pixels"],0)
            self.assertFalse(report["chrome_execution_provenance_verified"])
            self.assertEqual(report["browser_svg_gate"],"FAIL")
            self.assertFalse(report["production_promotion_authorized"])

    def test_browser_mismatch_is_strict_failure(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            o,c,m=make_authority(root)
            prepare_vector_mask(
                original_outer_scene=o,simplified_apparel_scene=c,
                simplified_apparel_metrics=m,output_dir=root/"out",
            )
            out=root/"out"
            wrong=cv2.imread(str(out/"authoritative_opencv_material.png"))
            wrong[18,13]=[0,0,0]
            cv2.imwrite(str(out/"actual_chrome_headless.png"),wrong)
            report=evaluate_real_chrome(output_dir=out)
            self.assertGreater(report["browser_mismatched_rgb_pixels"],0)
            self.assertEqual(report["browser_svg_gate"],"FAIL")
            self.assertFalse(report["production_promotion_authorized"])

    def test_wrong_source_metrics_sha_and_unsafe_offsets_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            o,c,m=make_authority(root)
            with self.assertRaises(ValueError):
                prepare_vector_mask(
                    original_outer_scene=o,simplified_apparel_scene=c,
                    simplified_apparel_metrics=m,output_dir=root/"out",
                    parent_dx=2.0,
                )
            obj=json.loads(m.read_text("utf-8"))
            obj["candidate_geometry_sha256"]="b"*64
            m.write_text(json.dumps(obj),encoding="utf-8")
            with self.assertRaises(ValueError):
                prepare_vector_mask(
                    original_outer_scene=o,simplified_apparel_scene=c,
                    simplified_apparel_metrics=m,output_dir=root/"out",
                )


if __name__=="__main__":
    unittest.main()
