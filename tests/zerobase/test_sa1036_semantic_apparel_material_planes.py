import unittest

import cv2
import numpy as np

from minimalizer_zerobase.reviewed_sa10.semantic_apparel_material_planes import (
    MAX_NECKTIE_EXPANSION, material_polygon_mask,
    propose_source_uniform_panels, render_source_uniform_panels,
)


def test_case() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rgb = np.full((120, 120, 3), [238, 238, 238], np.uint8)
    parent = np.zeros((120, 120), bool)
    parent[20:110, 5:95] = True
    rgb[parent] = [25, 32, 65]
    rgb[26:73, 22:43] = [237, 240, 243]
    rgb[26:73, 60:83] = [237, 240, 243]
    rgb[20:110, 46:57] = [111, 210, 18]
    protected = np.zeros(parent.shape, bool)
    protected[104:109, 8:12] = True
    return rgb, parent, protected


class SemanticUniformMaterialTests(unittest.TestCase):
    def test_shirt_and_dark_panels_and_tie_are_geometry(self):
        source, parent, protected = test_case()
        result = propose_source_uniform_panels(
            source_rgb=source, parent_visible=parent,
            protected=protected, parent_primitive_id="original-lowerbody",
        )
        self.assertIsNotNone(result)
        panels, report = result
        self.assertEqual(len(panels), 5)
        self.assertEqual(
            [p["material"] for p in panels],
            ["dark_uniform", "dark_uniform", "white_shirt",
             "white_shirt", "green_necktie"],
        )
        self.assertTrue(all(p["polygon_vertex_count"] <= 16 for p in panels))
        for p in panels:
            self.assertTrue(p["additional_filled_geometric_subpath"])
            self.assertTrue(p["material_class_precision"] >= 0.60)
            mask = material_polygon_mask(p, parent_visible=parent, protected=protected)
            self.assertFalse(np.any(mask & ~parent))
            self.assertFalse(np.any(mask & protected))
            self.assertIn(
                tuple(p["color_rgb_observed"]),
                set(map(tuple, source.reshape(-1, 3))),
            )
        tie = panels[-1]
        self.assertLessEqual(tie["panel_area_pixels"], MAX_NECKTIE_EXPANSION*tie["source_class_pixels"])
        self.assertLessEqual(report["necktie_area_ratio"], MAX_NECKTIE_EXPANSION)
        original = np.full(source.shape, [104, 91, 86], np.uint8)
        new, coverage = render_source_uniform_panels(
            base_rgb=original, panels=panels, parent_visible=parent,
            protected=protected,
        )
        self.assertFalse(np.any(coverage & ~parent))
        self.assertFalse(np.any(coverage & protected))
        self.assertTrue(np.array_equal(new[~parent], original[~parent]))
        self.assertTrue(np.array_equal(new[protected], original[protected]))
        self.assertTrue(np.any(new != original))

    def test_skip_when_no_green_tie(self):
        source, parent, protected = test_case()
        source[20:110, 46:57] = [25, 32, 65]
        self.assertIsNone(propose_source_uniform_panels(
            source_rgb=source, parent_visible=parent,
            protected=protected, parent_primitive_id="lowerbody",
        ))

    def test_skip_when_no_white_shirt_panels(self):
        source, parent, protected = test_case()
        source[26:73, 22:43] = [25, 32, 65]
        source[26:73, 60:83] = [25, 32, 65]
        self.assertIsNone(propose_source_uniform_panels(
            source_rgb=source, parent_visible=parent,
            protected=protected, parent_primitive_id="lowerbody",
        ))

    def test_invalid_polygon_material_cannot_render(self):
        source, parent, protected = test_case()
        panels,_ = propose_source_uniform_panels(
            source_rgb=source, parent_visible=parent,
            protected=protected, parent_primitive_id="lowerbody",
        )
        wrong = dict(panels[0])
        wrong["owner"] = "face"
        with self.assertRaises(ValueError):
            material_polygon_mask(wrong, parent_visible=parent, protected=protected)
        wrong = dict(panels[0])
        wrong["points"] = [[0, 0], [1, 1]]
        with self.assertRaises(ValueError):
            material_polygon_mask(wrong, parent_visible=parent, protected=protected)

    def test_wrong_material_layers_rejected(self):
        source,parent,protected = test_case()
        panels,_ = propose_source_uniform_panels(
            source_rgb=source,parent_visible=parent,
            protected=protected,parent_primitive_id="lowerbody",
        )
        baseline = np.zeros(source.shape,np.uint8)
        with self.assertRaises(ValueError):
            render_source_uniform_panels(
                base_rgb=baseline,panels=panels[::-1],
                parent_visible=parent,protected=protected,
            )
        with self.assertRaises(ValueError):
            render_source_uniform_panels(
                base_rgb=baseline,panels=panels[:3],
                parent_visible=parent,protected=protected,
            )

    def test_deterministic_source_derived_plan(self):
        source,parent,protected = test_case()
        a=propose_source_uniform_panels(
            source_rgb=source,parent_visible=parent,
            protected=protected,parent_primitive_id="lowerbody",
        )
        b=propose_source_uniform_panels(
            source_rgb=source,parent_visible=parent,
            protected=protected,parent_primitive_id="lowerbody",
        )
        self.assertEqual(a,b)


if __name__=="__main__":
    unittest.main()
