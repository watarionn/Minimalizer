"""Fixture-only validation tests; does not contain private/reference source images."""
import base64
import json
from pathlib import Path
import tempfile
import unittest

from verify_reference_shape_editor_export import validate

# Transparent 1x1 public test fixture. PNG chunks are only structural input to the
# verifier, which reads the IHDR; this fixture is unrelated to user art.
TEST_PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+XhmYAAAAASUVORK5CYII=')


def fixture():
    project = {
        'schema':'reference-shape-editor/v1',
        'canvas': {'width':1,'height':1},
        'image': {'name':'fixture.png','dataURL':'data:image/png;base64,'+base64.b64encode(TEST_PNG).decode()},
        'vertices':{'v1':{'x':0,'y':0},'v2':{'x':1,'y':0},'v3':{'x':1,'y':1},'v4':{'x':0,'y':1}},
        'shapes':[{'id':'a','name':'one','vertexIds':['v1','v2','v3'],'fill':'#ffffff','visible':True},
                  {'id':'b','name':'two','vertexIds':['v1','v3','v4'],'fill':'#000000','visible':True}]
    }
    svg = '<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1" viewBox="0 0 1 1">\n' \
          '<polygon points="0,0 1,0 1,1" fill="#ffffff" data-shape-name="one"/>\n' \
          '<polygon points="0,0 1,1 0,1" fill="#000000" data-shape-name="two"/>\n</svg>'
    return project,svg


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.ctx = tempfile.TemporaryDirectory()
        self.addCleanup(self.ctx.cleanup)
        self.j = Path(self.ctx.name)/'project.json'
        self.s = Path(self.ctx.name)/'shape.svg'
        self.project,self.svg=fixture()

    def check(self):
        self.j.write_text(json.dumps(self.project))
        self.s.write_text(self.svg)
        return validate(self.j,self.s)

    def test_valid_pair_and_shared_vertices(self):
        report=self.check()
        self.assertEqual((report['polygon_count'],report['vertex_count'],report['shared_vertex_count']),(2,4,2))
        self.assertTrue(report['svg_matches_json'])
        self.assertFalse(report['has_source_raster_in_svg'])

    def test_svg_geometry_mismatch_rejected(self):
        self.svg=self.svg.replace('0,0 1,0 1,1','0,0 0,0 1,1')
        with self.assertRaisesRegex(ValueError,'mismatch'):self.check()

    def test_external_svg_image_rejected(self):
        self.svg=self.svg.replace('</svg>','<image href="https://example.invalid/secret.png"/></svg>')
        with self.assertRaisesRegex(ValueError,'extra/missing'):self.check()

    def test_bad_geometry_rejected(self):
        self.project['shapes'][0]['vertexIds']=['v1','v2','v2']
        with self.assertRaisesRegex(ValueError,'repeated'):self.check()

    def test_missing_vertex_rejected(self):
        self.project['shapes'][0]['vertexIds']=['v1','v2','unknown']
        with self.assertRaisesRegex(ValueError,'unknown'):self.check()

    def test_bad_source_dimensions_rejected(self):
        self.project['canvas']['width']=2
        with self.assertRaisesRegex(ValueError,'size does not match'):self.check()

    def test_bad_color_rejected(self):
        self.project['shapes'][0]['fill']='javascript:bad'
        with self.assertRaisesRegex(ValueError,'invalid hex'):self.check()


if __name__=='__main__':unittest.main()
