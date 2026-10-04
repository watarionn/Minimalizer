import shutil
from minimalizer_zerobase.production.diffmin import DIFFMIN_GUARDED,GuardedDiffMinSwitch
from minimalizer_zerobase.production.diffmin_artifact import DiffMinCandidateArtifact,sha256_file,write_candidate_artifact
from minimalizer_zerobase.production.diffmin_handoff import *

def make(root,name="a",delta=.01):
 d=root/name;d.mkdir(parents=True);s=d/"source";b=d/"baseline";c=d/"candidate";s.write_bytes(b"s");b.write_bytes(b"b");c.write_bytes(b"c")
 a=DiffMinCandidateArtifact("1",name,sha256_file(s),sha256_file(b),sha256_file(c),True,.999,.5,.5+delta);write_candidate_artifact(d/"artifact.json",a)
 return DiffMinBundleEntry(name,f"{name}/source",f"{name}/baseline",f"{name}/candidate",f"{name}/artifact.json")

def test_bundle_replays_multiple_candidates_without_worker(tmp_path):
 entries=tuple(sorted((make(tmp_path,"b",-.01),make(tmp_path,"a",.01)),key=lambda x:x.candidate_id));m=DiffMinHandoffManifest("1",entries);h=write_handoff_manifest(tmp_path/"handoff.json",m)
 a=audit_handoff_bundle(tmp_path,GuardedDiffMinSwitch(DIFFMIN_GUARDED));assert a.passed and a.manifest_sha256==h
 assert [x.decision.apply_candidate for x in a.decisions]==[True,False]

def test_bundle_tamper_is_detected(tmp_path):
 e=make(tmp_path);write_handoff_manifest(tmp_path/"handoff.json",DiffMinHandoffManifest("1",(e,)));(tmp_path/"a/candidate").write_bytes(b"x")
 a=audit_handoff_bundle(tmp_path,GuardedDiffMinSwitch(DIFFMIN_GUARDED));assert not a.passed and not a.decisions[0].decision.apply_candidate

def test_bundle_rejects_path_escape(tmp_path):
 e=make(tmp_path);bad=DiffMinBundleEntry(e.candidate_id,"../source",e.baseline_file,e.candidate_file,e.artifact_file);write_handoff_manifest(tmp_path/"handoff.json",DiffMinHandoffManifest("1",(bad,)))
 import pytest
 with pytest.raises(ValueError,match="inside bundle"):audit_handoff_bundle(tmp_path,GuardedDiffMinSwitch(DIFFMIN_GUARDED))

def test_manifest_requires_sorted_unique_entries(tmp_path):
 import pytest
 a=make(tmp_path,"a");b=make(tmp_path,"b")
 with pytest.raises(ValueError,match="unique and sorted"):DiffMinHandoffManifest("1",(b,a))

