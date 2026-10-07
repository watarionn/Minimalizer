import json
from pathlib import Path
from minimalizer_zerobase.evaluation.animeseg_observer import observe

def test_missing_runtime_fails_closed(tmp_path):
    r = observe(Path(__file__), tmp_path, python="definitely-not-a-python")
    assert r["status"] == "observer_unavailable"
    assert r["authority"] is False
    assert r["production_authority"] is False

def test_worker_protocol_records_12_classes():
    text = Path(__file__).parents[2] / "tools" / "animeseg_isolated_worker.py"
    assert "left_eyebrow" in text.read_text(encoding="utf-8")
    assert "accessory" in text.read_text(encoding="utf-8")
