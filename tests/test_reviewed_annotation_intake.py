"""Synthetic fail-closed controls without real/private assets."""
import io,sys,json,base64,hashlib,copy,unittest,tempfile,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'/'research'))
import verify_reviewed_annotations as m
class Tests(unittest.TestCase):
 def setUp(self):
  im=Image.new('RGBA',(90,90),(0,0,0,0))
  for y in range(10,80):
   for x in range(10,80):im.putpixel((x,y),(240,80,120,255))
  z=io.BytesIO();im.save(z,format='PNG');self.raw=z.getvalue();self.sha=hashlib.sha256(self.raw).hexdigest()
  self.d={'schema':'reference-shape-editor/v1','appVersion':'1.1.0','canvas':{'width':90,'height':90},
  'image':{'dataURL':'data:image/png;base64,'+base64.b64encode(self.raw).decode()},
  'vertices':{'a':{'x':20,'y':20},'b':{'x':70,'y':20},'c':{'x':70,'y':70},'d':{'x':20,'y':70}},
  'shapes':[{'id':'s1','name':'outerwear/jacket_right','vertexIds':['a','b','c','d'],'visible':True}]}
  self.keep=m.PINS.copy();m.PINS['X']=self.sha
 def tearDown(self):m.PINS.clear();m.PINS.update(self.keep)
 def evaluate(self,d=None,svg=None):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'trace.json';p.write_text(json.dumps(d or self.d));
   if svg:
    s=Path(td)/'trace.svg';s.write_text(svg);return m.inspect(p,'X',s)
   return m.inspect(p,'X')
 def test_accepts_good(self):self.assertEqual(self.evaluate()[0]['polygon_count'],1)
 def test_reject_bad_underlay(self):
  z=copy.deepcopy(self.d);z['image']['dataURL']=z['image']['dataURL'][:-2]+'AA'
  with self.assertRaises((m.ReviewError,ValueError)):self.evaluate(z)
 def test_wrong_sha_fails(self):
  m.PINS['X']='f'*64
  with self.assertRaises(m.ReviewError):self.evaluate()
 def test_incorrect_dimensions(self):
  d=copy.deepcopy(self.d);d['canvas']['height']=89
  with self.assertRaises(m.ReviewError):self.evaluate(d)
 def test_outside_canvas(self):
  d=copy.deepcopy(self.d);d['vertices']['a']['x']=-1
  with self.assertRaises(m.ReviewError):self.evaluate(d)
 def test_self_intersection(self):
  d=copy.deepcopy(self.d);d['shapes'][0]['vertexIds']=['a','c','b','d']
  with self.assertRaises(m.ReviewError):self.evaluate(d)
 def test_alias_innerwear(self):
  d=copy.deepcopy(self.d);d['shapes'][0]['name']='innerwear/sleeve'
  self.assertEqual(self.evaluate(d)[0]['visible_underlayer_px'],2601)
 def test_alias_body_skin(self):
  d=copy.deepcopy(self.d);d['shapes'][0]['name']='body_skin/left_hand'
  self.assertEqual(self.evaluate(d)[0]['visible_arm_skin_px'],2601)
 def test_anatomical_name_preserved(self):
  self.assertEqual(self.evaluate()[0]['shape_audit'][0]['label'],'outerwear/jacket_right')
 def test_unknown_label_refused(self):
  d=copy.deepcopy(self.d);d['shapes'][0]['name']='arbitrary/thing'
  with self.assertRaises(m.ReviewError):self.evaluate(d)
 def test_alpha_clip(self):
  d=copy.deepcopy(self.d);d['vertices']['a']['x']=2;d['vertices']['d']['x']=2
  _,src,alpha,labels,top=self.evaluate(d)
  self.assertFalse((top&~alpha).any())
 def test_occlusion_last_on_top(self):
  d=copy.deepcopy(self.d);d['shapes'].append({'id':'top','name':'arm_skin/right_hand','vertexIds':['a','b','c','d'],'visible':True})
  _,_,_,labels,_=self.evaluate(d)
  self.assertEqual(int(labels['outerwear'].sum()),0)
  self.assertGreater(int(labels['arm_skin'].sum()),0)
 def test_no_overlap(self):
  d=copy.deepcopy(self.d);d['shapes'].append({'id':'top','name':'underlayer/shirt','vertexIds':['a','b','c','d'],'visible':True})
  _,_,_,labels,_=self.evaluate(d)
  self.assertTrue((sum(v.astype('uint8') for v in labels.values())<=1).all())
 def test_svg_parity_good(self):
  s='<svg xmlns="http://www.w3.org/2000/svg"><polygon points="20,20 70,20 70,70 20,70" data-shape-name="outerwear/jacket_right"/></svg>'
  self.assertEqual(self.evaluate(svg=s)[0]['polygon_count'],1)
 def test_svg_parity_wrong(self):
  s='<svg xmlns="http://www.w3.org/2000/svg"><polygon points="21,20 70,20 70,70 20,70" data-shape-name="outerwear/jacket_right"/></svg>'
  with self.assertRaises(m.ReviewError):self.evaluate(svg=s)
 def test_svg_wrong_name(self):
  s='<svg xmlns="http://www.w3.org/2000/svg"><polygon points="20,20 70,20 70,70 20,70" data-shape-name="outerwear/jacket_left"/></svg>'
  with self.assertRaises(m.ReviewError):self.evaluate(svg=s)
if __name__=='__main__':unittest.main(verbosity=2)
