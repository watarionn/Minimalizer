import unittest
from unified_release_gate import evaluate

def case(name,stage,render,mae,champ):
 return {"sourceSha256":"a"*64,"maskManifestSha256":"b"*64,"candidateSha256":"c"*64,
  "stage8OriginalVertices":stage,"renderedVertices":render,"shapeCount":40,
  "alphaOutsideDpr4":0,"alphaMissingDpr4":0,"nonfaceRgbMAE":mae,
  "champion":{"nonfaceRgbMAE":champ},"faceFeaturesHidden":True,
  "chromiumValidated":True,"safariValidated":False,"humanGoldenApproved":False}

class Gates(unittest.TestCase):
 def test_signed_real_current_data_cannot_promote(self):
  cases={"GC001":case("GC001",3604,5353,42.012781,40.318419),
         "Raden":case("Raden",2370,3586,21.575139,24.297144)}
  result=evaluate({"cases":cases})
  self.assertEqual(result["release"],"HOLD")
  self.assertFalse(result["cases"]["GC001"]["checks"]["champion_nonregression"])
  for c in result["cases"].values():
   self.assertFalse(c["checks"]["stage8_budget"])
   self.assertFalse(c["checks"]["rendered_vertex_budget"])
   self.assertFalse(c["checks"]["human_golden"])
 def test_even_every_pass_is_manual_release(self):
  data={"cases":{"GC001":case("GC001",100,100,1,2),"Raden":case("Raden",100,100,1,2)}}
  for x in data["cases"].values():
   x["safariValidated"]=True;x["humanGoldenApproved"]=True
  got=evaluate(data)
  self.assertTrue(got["allNumericAndReviewChecksPass"])
  self.assertEqual(got["release"],"HOLD")
 def test_missing_source_data_fails_closed(self):
  with self.assertRaises(ValueError):evaluate({"cases":{"GC001":case("GC001",1,1,1,2)}})
  data={"cases":{"GC001":case("GC001",1,1,1,2),"Raden":case("Raden",1,1,1,2)}}
  data["cases"]["GC001"]["candidateSha256"]="unverified"
  with self.assertRaises(ValueError):evaluate(data)
 def test_negative_leakage_and_faked_boolean_budget_rejected(self):
  data={"cases":{"GC001":case("GC001",1,1,1,2),"Raden":case("Raden",1,1,1,2)}}
  data["cases"]["GC001"]["stage8OriginalVertices"]=True
  with self.assertRaises(ValueError):evaluate(data)
if __name__=="__main__":unittest.main()
