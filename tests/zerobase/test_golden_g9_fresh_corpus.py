from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CORPUS=ROOT/"benchmarks"/"golden"/"blind"/"GBLIND_G9_FRESH_20261005.json"

def _c(): return json.loads(CORPUS.read_text(encoding="utf-8"))

def test_g9_fresh_suite_is_sealed_before_observer_run():
    c=_c()
    assert c["status"]=="SEALED_BEFORE_FIRST_OBSERVER_RUN"
    assert c["first_observer_run_performed"] is False
    assert c["selection_rule"]["visual_inspection_used"] is False
    assert c["observer"]["configuration_changes_after_selection"] is False

def test_g9_fresh_suite_uses_prefrozen_template_and_no_goldens():
    c=_c()
    assert c["evaluation_template"]["sha256"]=="8933fbcda7d7723f7ce21ba8d1aed118b0c8a0295297368359a2ad9554e1ccc0"
    assert c["evaluation_template"]["frozen_on_main_before_selection"]=="f2a991be7a107d8a5a2b351ef9a56c8cc26938e3"
    assert c["golden_images"] is False
    assert all(x["has_golden"] is False for x in c["cases"])

def test_g9_fresh_suite_is_distinct_and_deterministically_ordered():
    c=_c()
    old={"AZKi_list_thumb.png","IRyS_list_thumb.png","Gawr-Gura_list_thumb.png","Ceres-Fauna_list_thumb.png","Nanashi-Mumei_list_thumb.png"}
    assert len(c["cases"])==5
    assert len({x["case_id"] for x in c["cases"]})==5
    assert all(x["source_path"].rsplit("/",1)[-1] not in old for x in c["cases"])
    hashes=[x["sha256"] for x in c["cases"]]
    assert hashes==sorted(hashes)
