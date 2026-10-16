import sys,unittest,io,base64,hashlib,copy
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'/'research'))
from verify_local_l02_manual_intake import validate_reference,rasterize_visible_reference,alignment_audit,AuthorityHold,normalise_user_label,reviewed_h04_overshoot

class Test(unittest.TestCase):
 def setUp(self):
  im=Image.new('RGBA',(60,80),(0,0,0,0))
  for y in range(10,70):
   for x in range(8,52):im.putpixel((x,y),(128,75,34,255))
  buf=io.BytesIO();im.save(buf,format='PNG');self.raw=buf.getvalue()
  self.sha=hashlib.sha256(self.raw).hexdigest()
  self.doc={'schema':'reference-shape-editor/v1','image':{'name':'source.png','dataURL':'data:image/png;base64,'+base64.b64encode(self.raw).decode()},
    'canvas':{'width':60,'height':80},'vertices':{'a':{'x':10,'y':15},'b':{'x':50,'y':15},'c':{'x':50,'y':55},'d':{'x':10,'y':55}},
    'shapes':[{'id':'s1','name':'outerwear/coat','vertexIds':['a','b','c','d'],'fill':'#123456','visible':True}]}
 def test_accepts_labelled(self):self.assertEqual(validate_reference(self.doc,self.raw,self.sha,final=True)['outerwear_shapes'],1)
 def test_blank_project_valid_as_draft(self):
  z=copy.deepcopy(self.doc);z['shapes']=[];z['vertices']={}
  self.assertFalse(validate_reference(z,self.raw,self.sha,final=False)['final_review_ready'])
 def test_blank_not_ready(self):
  z=copy.deepcopy(self.doc);z['shapes']=[]
  with self.assertRaises(AuthorityHold):validate_reference(z,self.raw,self.sha,final=True)
 def test_duplicate_coordinate_refused(self):
  x=copy.deepcopy(self.doc);x['vertices']['d']=dict(x['vertices']['a'])
  with self.assertRaises(AuthorityHold):validate_reference(x,self.raw,self.sha,final=True)
 def test_source_mismatch(self):
  with self.assertRaises(AuthorityHold):validate_reference(self.doc,b'fake',self.sha)
 def test_underlay_mismatch(self):
  x=copy.deepcopy(self.doc);x['image']['dataURL']=x['image']['dataURL'][:-8]+'AAAAAAAA'
  with self.assertRaises(AuthorityHold):validate_reference(x,self.raw,self.sha)
 def test_nonlabelled_not_final(self):
  x=copy.deepcopy(self.doc);x['shapes'][0]['name']='図形 1'
  with self.assertRaises(AuthorityHold):validate_reference(x,self.raw,self.sha,final=True)
 def test_nonlabelled_allowed_draft(self):
  x=copy.deepcopy(self.doc);x['shapes'][0]['name']='図形 1'
  self.assertEqual(validate_reference(x,self.raw,self.sha,final=False)['unlabeled_shapes'],1)
 def test_outside_canvas(self):
  x=copy.deepcopy(self.doc);x['vertices']['c']['x']=80
  with self.assertRaises(AuthorityHold):validate_reference(x,self.raw,self.sha)
 def test_missing_point_ref(self):
  x=copy.deepcopy(self.doc);x['shapes'][0]['vertexIds'][0]='missing'
  with self.assertRaises(AuthorityHold):validate_reference(x,self.raw,self.sha)
 def test_duplicate_shape(self):
  x=copy.deepcopy(self.doc);x['shapes'].append(copy.deepcopy(x['shapes'][0]))
  with self.assertRaises(AuthorityHold):validate_reference(x,self.raw,self.sha)
 def test_wrong_dim(self):
  x=copy.deepcopy(self.doc);x['canvas']['width']=40
  with self.assertRaises(AuthorityHold):validate_reference(x,self.raw,self.sha)
 def test_occlusion_priority(self):
  x=copy.deepcopy(self.doc)
  x['vertices'].update({'e':{'x':20,'y':20},'f':{'x':40,'y':20},'g':{'x':40,'y':35},'h':{'x':20,'y':35}})
  x['shapes'].append({'id':'s2','name':'arm_skin/right_hand','vertexIds':['e','f','g','h'],'fill':'#aacc99','visible':True})
  m=rasterize_visible_reference(x,self.raw,self.sha)
  self.assertFalse(m['outerwear'][27,30]);self.assertTrue(m['arm_skin'][27,30])
  self.assertTrue(m['outerwear'][40,30])
 def test_rasterized_reference_clips_alpha(self):
  m=rasterize_visible_reference(self.doc,self.raw,self.sha)
  self.assertEqual(m['outerwear'].shape,(80,60))
  self.assertEqual(m['outerwear'].dtype.name,'bool')
 def test_extended_fullbody_taxonomy_and_occlusion(self):
  x=copy.deepcopy(self.doc)
  extra=[('face_skin/face',(22,22,36,37),'face'),('neck_skin/neck',(22,38,36,44),'neck'),('lower_body/trousers',(15,56,43,63),'lower')]
  for name,(left,top,right,bottom),stub in extra:
   ids=[stub+q for q in ('a','b','c','d')]
   for vid,pt in zip(ids,((left,top),(right,top),(right,bottom),(left,bottom))):x['vertices'][vid]={'x':pt[0],'y':pt[1]}
   x['shapes'].append({'id':stub,'name':name,'vertexIds':ids,'fill':'#ffccaa','visible':True})
  rep=validate_reference(x,self.raw,self.sha,final=True)
  self.assertEqual(rep['shape_count'],4)
  layers=rasterize_visible_reference(x,self.raw,self.sha)
  for key in ('outerwear','face_skin','neck_skin','lower_body'):self.assertTrue(layers[key].any(),key)
  ids=['outerwear','face_skin','neck_skin','lower_body']
  for i,key in enumerate(ids):
   for other in ids[i+1:]:self.assertFalse((layers[key]&layers[other]).any(),key+' and '+other)
 def test_innerwear_alias(self):
  x=copy.deepcopy(self.doc);x['shapes'][0]['name']='innerwear/leftbody'
  self.assertEqual(validate_reference(x,self.raw,self.sha,final=False)['unlabeled_shapes'],0)
  self.assertEqual(normalise_user_label('innerwear/leftbody'),'underlayer/leftbody')
 def test_body_skin_alias(self):
  x=copy.deepcopy(self.doc);x['shapes'].append({'id':'hand','name':'body_skin/right_hand','vertexIds':['a','b','c','d'],'fill':'#fff','visible':True})
  self.assertEqual(validate_reference(x,self.raw,self.sha,final=True)['shape_count'],2)
  self.assertEqual(normalise_user_label('body_skin/right_hand'),'arm_skin/right_hand')
 def test_h04_exception_does_not_apply_to_unsigned_case(self):
  self.assertFalse(reviewed_h04_overshoot(self.doc,self.sha,'sj'))
 def test_h04_exception_cannot_be_used_by_other_shape(self):
  self.assertFalse(reviewed_h04_overshoot(self.doc,self.sha,'some-new-shape'))
 def test_facial_microdetail_blocked(self):
  x=copy.deepcopy(self.doc);x['shapes'][0]['name']='face_skin/eye'
  with self.assertRaises(AuthorityHold):validate_reference(x,self.raw,self.sha,final=True)
 def test_face_region_only_is_not_a_microdetail(self):
  x=copy.deepcopy(self.doc);x['shapes'].append({'id':'face','name':'face_skin/face','vertexIds':['a','b','c','d'],'fill':'#ffccaa','visible':True})
  self.assertEqual(validate_reference(x,self.raw,self.sha,final=True)['shape_count'],2)
 def test_face_skin_eyelash_rejected_even_if_not_word_token(self):
  x=copy.deepcopy(self.doc);x['shapes'].append({'id':'detail','name':'face_skin/eyelash','vertexIds':['a','b','c','d'],'fill':'#000000','visible':True})
  with self.assertRaises(AuthorityHold):validate_reference(x,self.raw,self.sha,final=True)
 def test_face_microdetails_reject_after_outerwear(self):
  x=copy.deepcopy(self.doc);x['shapes'].append({'id':'iris','name':'face_skin/iris','vertexIds':['a','b','c','d'],'fill':'#000000','visible':True})
  with self.assertRaises(AuthorityHold):validate_reference(x,self.raw,self.sha,final=True)
 def test_alignment_audit_accepts_ordinary_clip(self):
  a=alignment_audit(self.doc,self.raw,self.sha)
  self.assertEqual(a['flagged_shape_count'],0)
  self.assertTrue(a['final_geometry_gate_pass'])
  self.assertFalse(a['human_semantic_label_signature'])
 def test_alignment_audit_identifies_excess_without_mutating_vertices(self):
  x=copy.deepcopy(self.doc)
  before=copy.deepcopy(x['vertices'])
  x['vertices']['a']['x']=1;x['vertices']['b']['x']=59;x['vertices']['c']['x']=59;x['vertices']['d']['x']=1
  deliberately_modified=copy.deepcopy(x['vertices'])
  a=alignment_audit(x,self.raw,self.sha)
  self.assertEqual(a['flagged_shape_count'],1)
  self.assertFalse(a['final_geometry_gate_pass'])
  self.assertEqual(x['vertices'],deliberately_modified)
 def test_alignment_audit_rejects_invalid_threshold(self):
  with self.assertRaises(AuthorityHold):alignment_audit(self.doc,self.raw,self.sha,max_outside_ratio=2)
 def test_bad_schema(self):
  x=copy.deepcopy(self.doc);x['schema']='bad'
  with self.assertRaises(AuthorityHold):validate_reference(x,self.raw,self.sha)
 def test_self_intersection(self):
  x=copy.deepcopy(self.doc);x['shapes'][0]['vertexIds']=['a','c','b','d']
  with self.assertRaises(AuthorityHold):validate_reference(x,self.raw,self.sha)
 def test_not_promoted_automatically(self):
  self.assertFalse(validate_reference(self.doc,self.raw,self.sha,final=True)['semantic_quality_approved'])
 def test_outside_foreground_limit(self):
  x=copy.deepcopy(self.doc);x['vertices']['a']['x']=1;x['vertices']['b']['x']=59;x['vertices']['c']['x']=59;x['vertices']['d']['x']=1
  with self.assertRaises(AuthorityHold):validate_reference(x,self.raw,self.sha,final=True)

if __name__=='__main__':unittest.main()
