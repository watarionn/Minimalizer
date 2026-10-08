"""SA10.41 full-character renderer positive and negative geometry regressions."""
import unittest
import numpy as np

from minimalizer_zerobase.reviewed_sa10.full_character_svg import (
    compile_full_character_svg,_contour_mask_svg,_binary_mask_svg,
)


def stage_scene(with_apparel=True):
    owners=[
        "hair","lower_body","right_arm","face","torso",
        "major_clothing","unknown","left_arm","neck","head",
        "accessory_or_held_object",
    ]
    records=[]
    for i,owner in enumerate(owners):
        rings=[
            {"depth":0,"role":"fill",
             "points":[[float(i),4.],[float(i+12),4.],[float(i+12),25.],[float(i),25.]]},
        ]
        if i==0:
            rings.extend([
                {"depth":0,"role":"fill","points":[[45.,45.]]},
                {"depth":0,"role":"fill","points":[[42.,42.],[43.,43.]]},
                {"depth":1,"role":"hole","points":[[8.,8.],[11.,8.],[11.,11.],[8.,11.]]},
            ])
        records.append({
            "primitive_id":f"source-p{i}",
            "primitive_type":"polygon",
            "source_mask_owner":owner,
            "source_mask_replay":True,
            "semantic_part_id":None if owner=="unknown" else owner,
            "structural_support_only":i==9,
            "palette_color_rgb":[25+i,70+i,120+i],
            "parameters":{"rings":rings,"components":[rings[0]["points"]]},
        })
    plane={
        "parent_primitive_id":"source-p4",
        "owner":"torso",
        "points":[[8.,8.],[11.,8.],[11.,12.],[8.,12.]],
        "observed_rgb":[238,236,237],
    }
    panels=[]
    if with_apparel:
        for i,material in enumerate(
            ["dark_uniform","dark_uniform","white_shirt","white_shirt","green_necktie"]
        ):
            panels.append({
                "parent_primitive_id":"source-p1",
                "owner":"lower_body",
                "material":material,
                "points":[[5.+i,8.],[8.+i,8.],[8.+i,15.],[5.+i,15.]],
                "color_rgb_observed":[45+i,70+i,95+i],
            })
    masks={
        "face":np.zeros((64,64),bool),
        "left_arm":np.zeros((64,64),bool),
        "right_arm":np.zeros((64,64),bool),
    }
    masks["face"][13:24,13:25]=True
    masks["left_arm"][22:30,25:34]=True
    masks["right_arm"][24:28,8:12]=True
    return records,[plane],panels,masks


class FullCharacterSvgResearchTests(unittest.TestCase):
    def test_entire_owner_z_order_hair_face_arms_and_all_colors(self):
        records,planes,panels,masks=stage_scene()
        svg,audit=compile_full_character_svg(
            records=records,stage9_planes=planes,
            garment_panels=panels,stage04_masks=masks,
            face_guard_rgb=(251,225,218),width=64,height=64,
        )
        self.assertEqual(audit["original_source_primitive_records"],11)
        self.assertEqual(audit["source_owner_rendered_count"],10)
        self.assertEqual(audit["phase9_interior_filled_subpaths"],1)
        self.assertEqual(audit["phase37_apparel_filled_subpaths"],5)
        self.assertEqual(audit["phase37_apparel_polygon_vertices"],20)
        self.assertEqual(audit["source_topological_singleton_ring_count"],1)
        self.assertEqual(audit["source_topological_two_point_ring_count"],1)
        self.assertEqual(audit["svg_explicit_degenerate_rect_line_elements"],2)
        self.assertEqual(svg.count("<mask "),13)
        self.assertEqual(svg.count("data-owner-index="),10)
        self.assertEqual(svg.count("<polygon "),6)
        self.assertNotIn('data-owner-index="9"',svg)
        self.assertIn('mask="url(#sa1041-original-face-guard)"',svg)
        self.assertLess(svg.index('data-owner-index="3"'),svg.index('data-owner-index="4"'))
        self.assertLess(svg.index('data-owner-index="4"'),svg.index('data-owner-index="7"'))
        self.assertNotIn("<image",svg)
        self.assertNotIn("base64",svg)
        self.assertNotIn("<foreignObject",svg)
        self.assertFalse(audit["production_promotion_authorized"])
        self.assertFalse(audit["whole_scene_chrome_pixel_parity_proven"])
        self.assertTrue(audit["svg_flat_face_guard_original_stage04_mask_counted"])

    def test_source_degenerate_one_and_two_point_contours_are_not_discarded(self):
        rings=[
            {"depth":0,"role":"fill","points":[[3.,4.]]},
            {"depth":0,"role":"fill","points":[[6.,7.],[8.,7.]]},
            {"depth":0,"role":"fill","points":[[0.,0.],[15.,0.],[15.,15.]]},
            {"depth":1,"role":"hole","points":[[8.,8.]]},
        ]
        text,counts=_contour_mask_svg(name="signed-short-rings",
                                       rings=rings,width=64,height=64)
        self.assertEqual(counts["source_small_ring_count"],3)
        self.assertEqual(counts["source_ring_vertices"],7)
        self.assertEqual(counts["svg_degenerate_rect_or_line_elements"],3)
        self.assertIn('<line ',text)
        self.assertIn('<rect x="3" y="4" width="1" height="1"',text)
        self.assertIn('<rect x="8" y="8" width="1" height="1" fill="#000000"',text)

    def test_second_independent_image_no_matching_apparel_is_noop(self):
        records,planes,_,masks=stage_scene(with_apparel=False)
        svg,audit=compile_full_character_svg(
            records=records,stage9_planes=planes,garment_panels=[],
            stage04_masks=masks,face_guard_rgb=(251,225,218),width=64,height=64,
        )
        self.assertEqual(audit["phase37_apparel_filled_subpaths"],0)
        self.assertNotIn("#2d465f",svg)
        self.assertFalse(audit["production_promotion_authorized"])

    def test_protected_face_and_arm_color_planes_cannot_be_fabricated(self):
        records,planes,panels,masks=stage_scene()
        fake={**planes[0],"owner":"face","parent_primitive_id":"source-p3"}
        with self.assertRaises(ValueError):
            compile_full_character_svg(
                records=records,stage9_planes=[fake],garment_panels=panels,
                stage04_masks=masks,face_guard_rgb=(251,225,218),width=64,height=64,
            )
        with self.assertRaises(ValueError):
            compile_full_character_svg(
                records=records,stage9_planes=planes,
                garment_panels=[{**p,"material":"green_necktie"} for p in panels],
                stage04_masks=masks,face_guard_rgb=(251,225,218),width=64,height=64,
            )

    def test_unknown_owner_and_missing_source_signed_rings_fail_closed(self):
        records,planes,panels,masks=stage_scene()
        corrupted=[dict(p) for p in records]
        corrupted[2]["source_mask_replay"]=False
        with self.assertRaises(ValueError):
            compile_full_character_svg(
                records=corrupted,stage9_planes=planes,garment_panels=panels,
                stage04_masks=masks,face_guard_rgb=(251,225,218),width=64,height=64,
            )
        corrupted=[dict(p) for p in records]
        corrupted[3]["primitive_id"]=corrupted[4]["primitive_id"]
        with self.assertRaises(ValueError):
            compile_full_character_svg(
                records=corrupted,stage9_planes=planes,garment_panels=panels,
                stage04_masks=masks,face_guard_rgb=(251,225,218),width=64,height=64,
            )

    def test_stage04_protection_mask_vectorizes_without_embedded_pixels(self):
        _,_,_,masks=stage_scene()
        protection=masks["face"]|masks["left_arm"]|masks["right_arm"]
        svg,counts=_binary_mask_svg(
            name="protected-mask",mask=protection,width=64,height=64,invert=True,
        )
        self.assertGreater(counts["source_ring_vertices"],0)
        self.assertIn('mask-type="luminance"',svg)
        self.assertIn('fill="#ffffff"',svg)
        self.assertIn('fill="#000000" fill-rule="evenodd"',svg)
        self.assertNotIn("<image",svg)


if __name__=="__main__":
    unittest.main()
