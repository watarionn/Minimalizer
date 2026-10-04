import json
from minimalizer_zerobase.production.diffmin import DIFFMIN_GUARDED,GuardedDiffMinSwitch
from minimalizer_zerobase.production.diffmin_artifact import DiffMinCandidateArtifact,evaluate_candidate_artifact,load_candidate_artifact,sha256_file,write_candidate_artifact

def bundle(tmp_path,delta=.01):
 s=tmp_path/"source.png";b=tmp_path/"baseline.png";c=tmp_path/"candidate.png"
 s.write_bytes(b"source");b.write_bytes(b"baseline");c.write_bytes(b"candidate")
 a=DiffMinCandidateArtifact("1","candidate-1",sha256_file(s),sha256_file(b),sha256_file(c),True,.999,.5,.5+delta)
 return s,b,c,a

def test_portable_artifact_round_trip_is_canonical(tmp_path):
 s,b,c,a=bundle(tmp_path);p=tmp_path/"candidate.json";write_candidate_artifact(p,a)
 assert load_candidate_artifact(p)==a
 assert p.read_text()=="".join([json.dumps(a.to_dict(),sort_keys=True,separators=(",",":")),"\n"])

def test_matching_artifact_can_reach_guarded_decision(tmp_path):
 s,b,c,a=bundle(tmp_path)
 x=evaluate_candidate_artifact(artifact=a,source_path=s,baseline_path=b,candidate_path=c,switch=GuardedDiffMinSwitch(DIFFMIN_GUARDED))
 assert x.artifact_integrity_pass and x.decision.apply_candidate

def test_changed_candidate_fails_integrity_before_observer_decision(tmp_path):
 s,b,c,a=bundle(tmp_path);c.write_bytes(b"tampered")
 x=evaluate_candidate_artifact(artifact=a,source_path=s,baseline_path=b,candidate_path=c,switch=GuardedDiffMinSwitch(DIFFMIN_GUARDED))
 assert not x.artifact_integrity_pass and x.decision.rollback_to_baseline and x.reason=="artifact-integrity-failed"

def test_wrong_baseline_fails_closed(tmp_path):
 s,b,c,a=bundle(tmp_path);b.write_bytes(b"other-baseline")
 x=evaluate_candidate_artifact(artifact=a,source_path=s,baseline_path=b,candidate_path=c,switch=GuardedDiffMinSwitch(DIFFMIN_GUARDED))
 assert not x.decision.apply_candidate and x.reason=="artifact-integrity-failed"

def test_artifact_rejects_unknown_schema(tmp_path):
 s,b,c,a=bundle(tmp_path);d=a.to_dict();d["schema_version"]="99"
 import pytest
 with pytest.raises(ValueError,match="unsupported"):DiffMinCandidateArtifact.from_dict(d)

