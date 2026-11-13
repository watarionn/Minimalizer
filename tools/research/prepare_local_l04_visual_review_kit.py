"""Prepare a human-first review folder for the frozen Local L04 candidate triple.

The tool copies the already-frozen private artifacts and creates Japanese
instructions/form fields.  It never changes source, SVG, Stage8 JSON, or gate
results, and it never creates a Golden receipt from incomplete answers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


CASES = ("H04", "H06", "H08")


def _load_receipt(source: Path) -> dict[str, object]:
    receipt = json.loads((source / "L04_CANDIDATE_TRIPLE_RECEIPT.json").read_text(encoding="utf-8"))
    if receipt.get("schema") != "minimalizer/local-l04/candidate-triple-receipt/v1":
        raise ValueError("候補三点セットreceiptのschemaが不正です")
    cases = receipt.get("cases", [])
    if tuple(item.get("case") for item in cases) != CASES:
        raise ValueError("H04/H06/H08の三例が揃っていません")
    receipt["results"] = {item["case"]: item for item in cases}
    return receipt


def _write_instructions(destination: Path, receipt: dict[str, object]) -> None:
    lines = [
        "# Minimalizer L04 独立視覚Golden確認キット",
        "",
        "これは凍結済み候補を人間が確認するためのフォルダです。",
        "確認者は開発側の推論実装や候補マスクを見ず、各ケースの元画像と展開SVGを見比べてください。",
        "この確認で見るのは、表示事故ではなく、元画像の意味と最終SVGの見た目が受入可能かです。",
        "",
        "## やること",
        "",
        "1. `sources/H04.png`、`sources/H06.webp`、`sources/H08.webp`を100%表示する。",
        "2. 同じケースの`expanded_stage8.svg`をブラウザで開き、元画像と見比べる。",
        "3. 下の確認票で、各項目を`はい`または`いいえ`で回答する。分からない場合は`いいえ`にせず、理由を備考へ書いて保留にする。",
        "4. 確認者名、独立性、確認日時、使用環境を記入して、確認票だけを返す。JSONを新規作成する必要はありません。",
        "",
        "## 確認してはいけないもの",
        "",
        "- 推論前に作られた人手ラベルや正解マスク（このフォルダには含めていません）。",
        "- 別候補、旧Stage8、旧SVG、旧capの比較結果。",
        "- GitHub上の実装差分を見て、画像の見た目を推測すること。",
        "",
        "## 数値来歴（確認者は書き換えない）",
    ]
    for case in CASES:
        item = receipt["results"][case]
        lines.extend(
            [
                f"- {case}: source SHA `{item['source_sha256']}`, Stage8 SHA `{item['stage8_json_sha256']}`, SVG SHA `{item['expanded_svg_sha256']}`",
            ]
        )
    lines.extend(
        [
            "",
            "正式判定は、数値ゲートPASSだけでは行いません。三例の視覚確認が完了するまでL04 formalはHOLDです。",
            "",
        ]
    )
    (destination / "README_日本語.md").write_text("\n".join(lines), encoding="utf-8")


def _write_form(destination: Path, receipt: dict[str, object]) -> None:
    receipt_sha = hashlib.sha256(
        (destination / "L04_CANDIDATE_TRIPLE_RECEIPT.json").read_bytes()
    ).hexdigest()
    lines = [
        "Minimalizer L04 独立視覚Golden確認票",
        "この票はJSONではありません。テキストで回答し、回答後にそのまま返してください。",
        "",
        f"レビュー対象三点セットreceipt SHA-256（書き換え禁止）: {receipt_sha}",
        "このSHAが一致しない確認票は、別候補の回答として扱い正式receiptにしません。",
        "",
        "確認者名: ",
        "所属・立場（開発側との関係）: ",
        "開発側から独立している: [ ] はい  [ ] いいえ",
        "確認日時（JST）: ",
        "使用端末・ブラウザ: ",
        "",
        "回答方法: 各項目の`回答:`に、はい／いいえ／保留のいずれかを書いてください。",
        "保留またはいいえの場合は、ケース名と理由を必ず備考へ書いてください。",
        "",
    ]
    questions = (
        "元画像の人物・衣装・腕・遮蔽の意味が、出力SVGでも受入可能に保たれている",
        "出力SVGに元画像にはない人物外の大きな形状・穴・欠落がない",
        "腕、袖、下着相当の境界が、衣装の誤ownerとして見えていない",
        "遮蔽された部分を、見えていないことを理由に誤って塗りつぶしていない",
        "頭部・顔・髪・首・アクセサリなど、正しい保護対象が壊れていない",
        "SVGをブラウザで開いた表示が、候補として受入可能である",
    )
    for case in CASES:
        lines.extend([f"## {case}", "", f"元画像: `sources/{case}.png` または `sources/{case}.webp`", f"出力: `{case}/expanded_stage8.svg`", ""])
        for index, question in enumerate(questions, start=1):
            lines.extend([f"{index}. {question}", "回答: ", ""])
        lines.extend(["備考: ", "", ""])
    lines.extend(
        [
            "## 全体回答",
            "",
            "三例すべてを視覚的に受入できる: [ ] はい  [ ] いいえ  [ ] 保留",
            "数値来歴と実物表示を照合した: [ ] はい  [ ] いいえ",
            "独立性を確認した: [ ] はい  [ ] いいえ",
            "総合コメント: ",
            "",
            "注意: この確認票の回答だけでは、本人承認・本番反映・Golden公開を自動で許可しません。",
        ]
    )
    (destination / "L04独立視覚Golden確認票.txt").write_text("\n".join(lines), encoding="utf-8")


def prepare(source: Path, destination: Path) -> dict[str, object]:
    source = source.resolve()
    destination = destination.resolve()
    receipt = _load_receipt(source)
    sources = source / "sources"
    if not sources.is_dir():
        raise FileNotFoundError("レビューキットのsourcesフォルダがありません")
    for case in CASES:
        matches = sorted(sources.glob(f"{case}.*"))
        if len(matches) != 1:
            raise FileNotFoundError(f"署名済み元画像が一意ではありません: {case}")
        expanded_svg = source / case / "expanded_stage8.svg"
        if not expanded_svg.is_file():
            raise FileNotFoundError(f"展開SVGがありません: {case}")
    if destination.exists():
        raise FileExistsError(f"出力先が既に存在します: {destination}")
    shutil.copytree(source, destination)
    _write_instructions(destination, receipt)
    _write_form(destination, receipt)
    return {
        "status": "READY_FOR_INDEPENDENT_VISUAL_REVIEW",
        "source": str(source),
        "destination": str(destination),
        "cases": list(CASES),
        "receipt_created": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="L04独立視覚Golden確認キットを準備する")
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.destination), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
