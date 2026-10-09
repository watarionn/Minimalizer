"""R6 release gate must remain NO_GO without real external signoffs."""
from __future__ import annotations
import ast
import importlib.util
import sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/verify_public_r6_release_admission.py"
sys.path.insert(0,str(ROOT/"scripts"))
spec=importlib.util.spec_from_file_location("r6_release",SCRIPT)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def test_release_gate_refuses_missing_or_forged_records():
    with pytest.raises(ValueError):
        m.evaluate({}, {})
    assert 'humanGoldenSigned":False' in SCRIPT.read_text(encoding="utf-8")
    assert '"releaseAuthorized":False' in SCRIPT.read_text(encoding="utf-8")

def test_frozen_evidence_read_preflight_fails_missing_folder(tmp_path):
    with pytest.raises(FileNotFoundError):
        m.execute(tmp_path,tmp_path/"out")
    assert not (tmp_path/"out").exists()
    assert not any(tmp_path.iterdir())

def test_no_overwrite_existing_decision(tmp_path):
    (tmp_path/"already").mkdir()
    with pytest.raises(FileExistsError):
        m.execute(tmp_path,tmp_path/"already")

def test_gate_has_no_merge_or_deploy_execution_path():
    source=SCRIPT.read_text(encoding="utf-8")
    ast.parse(source)
    assert "mergeOrDeployPerformed" in source
    for forbidden in ("git push","git merge","railway deploy",
                      "GenUI.openUrl","subprocess.run","start_process"):
        assert forbidden not in source
    for name in ("web/static/public-route.js",
                 "web/static/browser-fallback.js",
                 "local_worker/frontend/local-route.js"):
        assert "verify_public_r6_release_admission" not in (ROOT/name).read_text(encoding="utf-8")
