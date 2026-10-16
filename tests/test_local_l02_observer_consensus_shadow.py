"""Deterministic source-only agreement and adversarial unknown-label tests."""
from __future__ import annotations
import hashlib,io,inspect,json,sys,unittest,zipfile
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
from local_l02_observer_consensus_shadow import (
 ResearchHold,sha,CASES,assert_binary,decompose,known_only,diagnose,load_pred,run)

def setup():
 alpha=np.ones((20,25),dtype=bool);alpha[:2,:]=False
 first=np.zeros_like(alpha);first[4:14,5:15]=True
 second=np.zeros_like(alpha);second[7:17,8:18]=True
 pos=np.zeros_like(alpha);pos[6:15,7:17]=True
 neg=np.zeros_like(alpha);neg[3:5,20:23]=True
 hair=np.zeros_like(alpha);hair[4:6,5:7]=True
 arm=np.zeros_like(alpha);arm[10:12,5:7]=True
 return alpha,first,second,pos,neg,hair,arm

class ConsensusChecks(unittest.TestCase):
 def test_three_distinct_signed_character_cases(self):
  self.assertEqual(set(CASES),{"H04","H06","H08"})
 def test_partition_is_exhaustive_disjoint(self):
  a,s,d,*_=setup()
  p=decompose(a,s,d)
  self.assertTrue(np.array_equal(np.logical_or.reduce(list(p.values())),a))
  self.assertTrue(all(not np.any(p[x]&p[y]) for x in p for y in p if x!=y))
 def test_pair_requires_signed_source_alpha(self):
  a,s,d,*_=setup();s[0,0]=True
  with self.assertRaisesRegex(ResearchHold,"OUTSIDE_SOURCE"):decompose(a,s,d)
 def test_mismatched_mask_dtype_fail_closed(self):
  a,s,d,*_=setup()
  with self.assertRaisesRegex(ResearchHold,"INVALID_BINARY_MASK"):decompose(a,s.astype(np.uint8),d)
 def test_mismatched_geometry_fail_closed(self):
  a,s,d,*_=setup()
  with self.assertRaisesRegex(ResearchHold,"INVALID_BINARY_MASK"):decompose(a,s[:-1],d)
 def test_human_label_conflict_rejected(self):
  a,s,d,p,n,h,arm=setup();n|=p
  with self.assertRaisesRegex(ResearchHold,"HUMAN_CONFLICT"):
   diagnose(a,s,d,positive=p,negative=n,hair=h,arms=arm)
 def test_unknown_is_not_negative(self):
  a,s,d,p,n,h,arm=setup()
  q=known_only(a,s,p,n)
  self.assertEqual(q["known_negative_fp_rate"],0)
  self.assertGreater(q["unknown_predicted_px"],0)
 def test_research_agreement_never_promotes(self):
  a,s,d,p,n,h,arm=setup()
  q=diagnose(a,s,d,positive=p,negative=n,hair=h,arms=arm)
  self.assertEqual(q["decision"],"SHADOW_AGREEMENT_NOT_OWNER_AUTHORITY")
  self.assertFalse(q["owner_promotion_authorized"])
 def test_empty_second_observer_requires_abstain(self):
  a,s,d,p,n,h,arm=setup();d[:]=False
  q=diagnose(a,s,d,positive=p,negative=n,hair=h,arms=arm)
  self.assertEqual(q["decision"],"ABSTAIN_EMPTY_INDEPENDENT_AGREEMENT")
  self.assertEqual(q["shared_source_px"],0)
 def test_labels_are_diagnostic_only(self):
  self.assertEqual(list(inspect.signature(decompose).parameters),["alpha","segformer","deepfashion"])
 def test_protected_arm_evidence_only_at_evaluation(self):
  a,s,d,p,n,h,arm=setup()
  arm[8:11,9:12]=True
  q=diagnose(a,s,d,positive=p,negative=n,hair=h,arms=arm)
  self.assertGreater(q["regions"]["shared"]["human_arm_px"],0)
  self.assertFalse(q["owner_promotion_authorized"])
 def test_array_signature_tamper_abstains(self):
  a,s,d,*_=setup()
  u=s.astype("uint8");blob=io.BytesIO();np.savez_compressed(blob,prediction=u)
  zbytes=io.BytesIO()
  with zipfile.ZipFile(zbytes,"w") as w:w.writestr("test.npz",blob.getvalue())
  zbytes.seek(0)
  with zipfile.ZipFile(zbytes) as z:
   valid=load_pred(z,"test.npz",sha(s.tobytes()),a)
   self.assertTrue(np.array_equal(valid,s))
   with self.assertRaisesRegex(ResearchHold,"SHA_MISMATCH"):
    load_pred(z,"test.npz","0"*64,a)
 def test_reject_multifile_or_extra_npz_schema(self):
  a,s,d,*_=setup();b=io.BytesIO()
  np.savez_compressed(b,prediction=s.astype("uint8"),human_labels=s.astype("uint8"))
  zbytes=io.BytesIO()
  with zipfile.ZipFile(zbytes,"w") as w:w.writestr("test.npz",b.getvalue())
  zbytes.seek(0)
  with zipfile.ZipFile(zbytes) as z:
   with self.assertRaisesRegex(ResearchHold,"SCHEMA_MISMATCH"):
    load_pred(z,"test.npz",sha(s.tobytes()),a)
 def test_nonbinary_array_rejected(self):
  a,s,d,*_=setup();u=s.astype("uint8");u[3,3]=2
  b=io.BytesIO();np.savez_compressed(b,prediction=u)
  zbytes=io.BytesIO()
  with zipfile.ZipFile(zbytes,"w") as w:w.writestr("test.npz",b.getvalue())
  zbytes.seek(0)
  with zipfile.ZipFile(zbytes) as z:
   with self.assertRaisesRegex(ResearchHold,"NOT_BINARY_SOURCE_FRAME"):
    load_pred(z,"test.npz",sha(s.tobytes()),a)
 def test_preserve_existing_evidence(self):
  # Never clobber an already-existing private proof artifact.
  import tempfile
  with tempfile.TemporaryDirectory() as d:
   target=Path(d)/"existing.zip";target.write_bytes(b"preserve")
   with self.assertRaisesRegex(ResearchHold,"REFUSE_OVERWRITE"):
    run(Path(d)/"in.zip",Path(d)/"seg.zip",Path(d)/"deep.zip",target)
   self.assertEqual(target.read_bytes(),b"preserve")

if __name__=="__main__":unittest.main(verbosity=2)
