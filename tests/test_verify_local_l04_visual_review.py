from pathlib import Path

import json

from tools.research.verify_local_l04_visual_review import readback_review


def _package(tmp_path: Path) -> Path:
    package = tmp_path / "package"
    package.mkdir()
    (package / "L04_CANDIDATE_TRIPLE_AUDIT.json").write_text(
        json.dumps({"numerical_handoff_eligible": True, "failures": [], "schema": "candidate"}),
        encoding="utf-8",
    )
    (package / "B_L04_DELIVERY_AUDIT.json").write_text(
        json.dumps({"B_L04_delivery": "PASS", "failures": [], "schema": "delivery"}),
        encoding="utf-8",
    )
    return package


def _review(tmp_path: Path, h04: str = "はい") -> Path:
    lines = [
        "確認者名: reviewer",
        "所属・立場（開発側との関係）: なし",
        "開発側から独立している: はい",
        "確認日時（JST）: 2026-11-13 10:00",
        "使用端末・ブラウザ: Chrome",
    ]
    for case in ("H04", "H06", "H08"):
        lines += [f"## {case}"] + [f"回答: {h04 if case == 'H04' else 'はい'}"] * 6
    lines += [
        "## 全体回答",
        "三例すべてを視覚的に受入できる: はい",
        "数値来歴と実物表示を照合した: はい",
        "独立性を確認した: はい",
    ]
    path = tmp_path / "review.txt"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def test_review_readback_holds_on_one_case_failure(tmp_path: Path):
    result = readback_review(_review(tmp_path, h04="いいえ"), _package(tmp_path))
    assert result["review_gate"] == "HOLD"
    assert result["L04_formal"] == "HOLD"
    assert result["failure_reasons"] == {"H04": [1, 2, 3, 4, 5, 6]}
    assert result["release_authorized"] is False


def test_review_readback_passes_only_when_all_cases_are_yes(tmp_path: Path):
    result = readback_review(_review(tmp_path), _package(tmp_path))
    assert result["review_gate"] == "PASS"
    assert result["Golden"] == "PASS"
    assert result["production"] == "NO_GO"
