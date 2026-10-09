import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import json
from stage8_lossless_ring_probe import analyze

class ProbeTests(unittest.TestCase):
 def make(self,folder,case,expected):
  roots=[]
  for i in range(11):
   points=[[i*2.0,0.0],[i*2.0+1,0.0]]
   if i==0:points=points+[[i*2.0+2,0.0]]*(expected-22)
   roots.append({"composition_part":str(i),"parameters":{"rings":[{"points":points}],"components":[points]}})
  d=folder/case;d.mkdir()
  (d/"phase8_adaptive_source_contour_research.json").write_text(json.dumps({"no_new_material_or_owner":True,"primitives_back_to_front":roots}))
 def test_both_source_cases_and_no_automatic_promotion(self):
  with TemporaryDirectory() as d:
   root=Path(d);self.make(root,"GC001",3604);self.make(root,"Raden",2370)
   report=analyze(root)
   self.assertEqual(report["cases"]["GC001"]["vertices"],3604)
   self.assertEqual(report["cases"]["Raden"]["vertices"],2370)
   self.assertEqual(report["safePromotions"],0)
 def test_source_owner_drop_rejected(self):
  with TemporaryDirectory() as d:
   root=Path(d);self.make(root,"GC001",3604);self.make(root,"Raden",2370)
   f=root/"GC001"/"phase8_adaptive_source_contour_research.json"
   v=json.loads(f.read_text());v["primitives_back_to_front"].pop();f.write_text(json.dumps(v))
   with self.assertRaises(ValueError):analyze(root)

if __name__=="__main__":unittest.main()
