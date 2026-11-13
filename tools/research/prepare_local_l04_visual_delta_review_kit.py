"""Prepare a focused visual delta-review kit for a changed L04 candidate.

The previous independent review remains bound to its own candidate receipt.
This kit carries that review forward and asks only about the visual findings
that changed in the new candidate.  It never promotes a candidate or creates
a Golden receipt.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


CASES = ("H04", "H06", "H08")
EXPECTED_BASELINE_FAILURES = {"H04": [3], "H06": [1, 6], "H08": []}


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _receipt(source: Path) -> tuple[dict[str, object], str]:
    path = source / "L04_CANDIDATE_TRIPLE_RECEIPT.json"
    value = _read_json(path)
    if value.get("schema") != "minimalizer/local-l04/candidate-triple-receipt/v1":
        raise ValueError("候補三点セットreceiptのschemaが不正です")
    cases = value.get("cases", [])
    if tuple(item.get("case") for item in cases) != CASES:
        raise ValueError("H04/H06/H08の三例が揃っていません")
    return value, hashlib.sha256(path.read_bytes()).hexdigest()


def _baseline_manifest(receipt_path: Path, review_path: Path) -> dict[str, object]:
    receipt, receipt_sha = _receipt(receipt_path.parent)
    review = _read_json(review_path)
    if review.get("schema") != "minimalizer/local-l04/independent-visual-review-readback/v1":
        raise ValueError("v5独立視覚レビューreadbackのschemaが不正です")
    cases = review.get("cases", {})
    failures = {
        case: list(cases.get(case, {}).get("failed_question_numbers", []))
        for case in CASES
    }
    if failures != EXPECTED_BASELINE_FAILURES:
        raise ValueError("指定されたv5レビューは既知の差分対象と一致しません")
    if review.get("review_gate") != "HOLD" or review.get("L04_formal") != "HOLD":
        raise ValueError("v5レビューはHOLDのまま引き継ぐ必要があります")
    return {
        "schema": "minimalizer/local-l04/visual-delta-baseline-binding/v1",
        "baseline_label": "v5",
        "baseline_receipt_sha256": receipt_sha,
        "baseline_review_file_sha256": review.get("review_file_sha256"),
        "baseline_review_readback_sha256": hashlib.sha256(review_path.read_bytes()).hexdigest(),
        "baseline_review_gate": review.get("review_gate"),
        "baseline_cases": cases,
        "baseline_receipt_cases": receipt.get("cases"),
        "carried_forward_accepted_case": "H08",
        "delta_required_cases": ["H04", "H06", "H08"],
    }


def _write_readme(destination: Path, current_sha: str, baseline_sha: str) -> None:
    lines = [
        "# Minimalizer L04 差分視覚確認キット",
        "",
        "v5候補の独立評価結果は、v5のreceipt SHAに対する正式な回答として保持しています。",
        "今回は候補のowner修復と署名済み元画像由来paletteが変わったため、同じ全問を繰り返さず、v5で不合格だった表示点と新規の無回帰だけを確認します。",
        "",
        "## 確認手順",
        "",
        "1. `sources/`の署名済み元画像と、各ケースの`expanded_stage8.svg`をブラウザで開く。",
        "2. v5の回答を先に読み直さず、今回の元画像とSVGを見て、差分票の4項目だけを確認する。",
        "3. `はい`・`いいえ`・`保留`を記入する。保留やいいえにはケースと理由を書く。",
        "4. 確認票だけを返す。JSONを手書きする必要はありません。",
        "",
        "## 今回見ないもの",
        "",
        "- 推論前の人手ラベル、正解マスク、旧cap、GitHub実装差分。",
        "- v5で既に受入済みだったH08の旧質問を、同じ内容で再回答すること。",
        "",
        f"今回の候補receipt SHA-256: `{current_sha}`",
        f"引継ぐv5 receipt SHA-256: `{baseline_sha}`",
        "",
        "三点照合とBレーンのブラウザ表示監査は機械検証済みですが、差分視覚確認が終わるまでL04 formalとGoldenはHOLDです。",
        "",
    ]
    (destination / "README_日本語.md").write_text("\n".join(lines), encoding="utf-8")


def _write_form(destination: Path, current_sha: str, baseline_sha: str) -> None:
    lines = [
        "Minimalizer L04 差分視覚確認票",
        "この票はJSONではありません。回答後、このテキストをそのまま返してください。",
        "",
        f"今回レビュー対象三点セットreceipt SHA-256（書き換え禁止）: {current_sha}",
        f"前回v5レビュー対象receipt SHA-256（固定）: {baseline_sha}",
        "",
        "確認者名: ",
        "所属・立場（開発側との関係）: ",
        "開発側から独立している: [ ] はい  [ ] いいえ",
        "確認日時（JST）: ",
        "使用端末・ブラウザ: ",
        "",
        "回答方法: 各項目の`回答:`に、はい／いいえ／保留のいずれかを書いてください。",
        "",
        "## 差分確認",
        "",
        "1. H04: v5で不合格だった腕・袖・下着相当の境界が、今回のSVGでは衣装の誤ownerとして見えない",
        "回答: ",
        "備考: ",
        "",
        "2. H06: v5で不合格だった人物・衣装・腕・遮蔽の意味保持が、今回のSVGでは受入可能になった",
        "回答: ",
        "備考: ",
        "",
        "3. H06: v5で不合格だったブラウザ表示が、今回のSVGでは候補として受入可能になった",
        "回答: ",
        "備考: ",
        "",
        "4. H08: v5で受入済みだった品質を壊す新しい視覚欠陥が、今回の候補に追加されていない",
        "回答: ",
        "備考: ",
        "",
        "## 全体回答",
        "",
        "差分4項目をすべて視覚的に受入できる: [ ] はい  [ ] いいえ  [ ] 保留",
        "今回のreceiptの数値来歴と実物表示を照合した: [ ] はい  [ ] いいえ",
        "独立性を確認した: [ ] はい  [ ] いいえ",
        "総合コメント: ",
        "",
        "注意: この確認票だけでは本人承認・本番反映・Golden公開を自動で許可しません。",
    ]
    (destination / "L04差分独立視覚確認票.txt").write_text("\n".join(lines), encoding="utf-8")


def prepare(
    source: Path,
    destination: Path,
    baseline_receipt: Path,
    baseline_review: Path,
) -> dict[str, object]:
    source = source.resolve()
    destination = destination.resolve()
    current, current_sha = _receipt(source)
    baseline = _baseline_manifest(baseline_receipt.resolve(), baseline_review.resolve())
    baseline_sha = str(baseline["baseline_receipt_sha256"])
    if current_sha == baseline_sha:
        raise ValueError("差分確認にはv5と異なる候補receiptが必要です")
    if destination.exists():
        raise FileExistsError(f"出力先が既に存在します: {destination}")
    shutil.copytree(source, destination)
    (destination / "BASELINE_REVIEW_BINDING.json").write_text(
        json.dumps(baseline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    _write_readme(destination, current_sha, baseline_sha)
    _write_form(destination, current_sha, baseline_sha)
    return {
        "status": "READY_FOR_INDEPENDENT_VISUAL_DELTA_REVIEW",
        "destination": str(destination),
        "current_receipt_sha256": current_sha,
        "baseline_receipt_sha256": baseline_sha,
        "baseline_review_carried_forward": True,
        "delta_questions": 4,
        "receipt_created": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="L04差分視覚確認キットを準備する")
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--baseline-receipt", required=True, type=Path)
    parser.add_argument("--baseline-review", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.destination, args.baseline_receipt, args.baseline_review), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
