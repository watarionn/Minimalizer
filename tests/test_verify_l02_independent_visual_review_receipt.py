from pathlib import Path

import pytest

from tools.research.verify_l02_independent_visual_review_receipt import (
    EXPECTED_CANDIDATE_SHA256,
    IndependentReviewHold,
    verify_review_text,
)


def _review_text(*, value: str = "YES", hashes: dict[str, str] | None = None) -> str:
    hashes = hashes or EXPECTED_CANDIDATE_SHA256
    blocks = []
    for case in EXPECTED_CANDIDATE_SHA256:
        blocks.append(
            "\n".join(
                [
                    f"{case} candidate SHA-256:",
                    hashes[case],
                    f"正衣装保持: {value}",
                    f"腕・手の誤ownerなし: {value}",
                    f"下着・別レイヤーの誤ownerなし: {value}",
                    f"袖の回復: {value}",
                    f"遮蔽の前後関係: {value}",
                    f"変更範囲の十分性: {value}",
                    "理由: 全身候補として確認した",
                ]
            )
        )
    return "\n".join(
        [
            "L02 独立視覚レビュー回答",
            "レビュー担当者: reviewer-1",
            "開発側から独立している: YES",
            "推論前に評価ラベルを見ていない: YES",
            "レビュー日時: 2026-11-10T12:00:00+09:00",
            *blocks,
            "総合判定: YES",
            "署名または改変検知可能な記録: reviewer-signature-1",
        ]
    )


def test_plain_text_review_binds_all_frozen_candidates(tmp_path: Path):
    path = tmp_path / "review.txt"
    path.write_text(_review_text(), encoding="utf-8")

    receipt = verify_review_text(path)

    assert receipt["review_gate"] == "PASS"
    assert receipt["Phase4"] == "NOT_PROMOTED"
    assert set(receipt["cases"]) == set(EXPECTED_CANDIDATE_SHA256)


@pytest.mark.parametrize(
    "change",
    [
        lambda text: text.replace(
            EXPECTED_CANDIDATE_SHA256["H06"], "0" * 64, 1
        ),
        lambda text: text.replace("H08 candidate SHA-256:\n" + EXPECTED_CANDIDATE_SHA256["H08"], "H08 candidate SHA-256:\n" + EXPECTED_CANDIDATE_SHA256["H08"] + "x"),
        lambda text: text.replace(
            "H06 candidate SHA-256:\n"
            + EXPECTED_CANDIDATE_SHA256["H06"]
            + "\n正衣装保持: YES",
            "H06 candidate SHA-256:\n"
            + EXPECTED_CANDIDATE_SHA256["H06"]
            + "\n正衣装保持: NO",
        ),
        lambda text: text.replace("開発側から独立している: YES", "開発側から独立している: NO"),
    ],
)
def test_review_must_fail_closed(tmp_path: Path, change):
    path = tmp_path / "review.txt"
    path.write_text(change(_review_text()), encoding="utf-8")

    with pytest.raises(IndependentReviewHold):
        verify_review_text(path)
