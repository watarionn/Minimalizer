from minimalizer_zerobase.production.diffmin import DIFFMIN_GUARDED, DIFFMIN_OFF
from minimalizer_zerobase.production.diffmin_artifact import DiffMinCandidateArtifact, sha256_file, write_candidate_artifact
from minimalizer_zerobase.production.diffmin_handoff import DiffMinBundleEntry, DiffMinHandoffManifest, write_handoff_manifest
from minimalizer_zerobase.production.diffmin_release import DIFFMIN_KILL_ENV, run_release_gate

def bundle(root):
    d=root/"a";d.mkdir();s=d/"s";b=d/"b";c=d/"c"
    s.write_bytes(b"s");b.write_bytes(b"b");c.write_bytes(b"c")
    a=DiffMinCandidateArtifact("1","a",sha256_file(s),sha256_file(b),sha256_file(c),True,.999,.5,.51)
    write_candidate_artifact(d/"a.json",a)
    e=DiffMinBundleEntry("a","a/s","a/b","a/c","a/a.json")
    write_handoff_manifest(root/"handoff.json",DiffMinHandoffManifest("1",(e,)))

def test_release_is_off_without_explicit_opt_in(tmp_path,monkeypatch):
    bundle(tmp_path);monkeypatch.delenv(DIFFMIN_KILL_ENV,raising=False)
    x=run_release_gate(tmp_path,audit_dir=tmp_path/"audit")
    assert x.effective_mode==DIFFMIN_OFF and not x.audit.decisions[0].decision.apply_candidate

def test_guarded_release_requires_audit_retention(tmp_path,monkeypatch):
    bundle(tmp_path);monkeypatch.delenv(DIFFMIN_KILL_ENV,raising=False)
    x=run_release_gate(tmp_path,requested_mode=DIFFMIN_GUARDED)
    assert x.effective_mode==DIFFMIN_OFF and x.audit_file is None

def test_explicit_guarded_release_writes_audit(tmp_path,monkeypatch):
    bundle(tmp_path);monkeypatch.delenv(DIFFMIN_KILL_ENV,raising=False)
    x=run_release_gate(tmp_path,requested_mode=DIFFMIN_GUARDED,audit_dir=tmp_path/"audit")
    assert x.effective_mode==DIFFMIN_GUARDED and x.audit.decisions[0].decision.apply_candidate and x.audit_file

def test_kill_switch_overrides_explicit_guarded_mode(tmp_path,monkeypatch):
    bundle(tmp_path);monkeypatch.setenv(DIFFMIN_KILL_ENV,"1")
    x=run_release_gate(tmp_path,requested_mode=DIFFMIN_GUARDED,audit_dir=tmp_path/"audit")
    assert x.kill_switch and x.effective_mode==DIFFMIN_OFF and not x.audit.decisions[0].decision.apply_candidate
