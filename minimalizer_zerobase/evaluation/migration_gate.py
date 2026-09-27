from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping

@dataclass(frozen=True)
class MigrationGateResult:
    replay_cases: int
    source_sha_verified: bool
    reference_sha_verified: bool
    replay_deterministic: bool
    zerobase_mean_silhouette_iou: float
    legacy_mean_silhouette_iou: float
    zerobase_mean_foreground_error: float
    legacy_mean_foreground_error: float
    switch_authorized: bool
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "replay_cases": self.replay_cases,
            "source_sha_verified": self.source_sha_verified,
            "reference_sha_verified": self.reference_sha_verified,
            "replay_deterministic": self.replay_deterministic,
            "zerobase_mean_silhouette_iou": self.zerobase_mean_silhouette_iou,
            "legacy_mean_silhouette_iou": self.legacy_mean_silhouette_iou,
            "zerobase_mean_foreground_error": self.zerobase_mean_foreground_error,
            "legacy_mean_foreground_error": self.legacy_mean_foreground_error,
            "switch_authorized": self.switch_authorized,
            "reasons": list(self.reasons),
        }
class MigrationGate:
    def evaluate(self, capture: Mapping[str, object], comparison: Mapping[str, object]) -> MigrationGateResult:
        aggregate = comparison["aggregate"]
        replay_cases = int(capture.get("case_count", 0))
        source_ok = bool(capture.get("all_source_sha256_verified", False))
        reference_ok = bool(comparison.get("all_reference_sha256_verified", False))
        replay_ok = bool(capture.get("all_replay_deterministic", False))
        z_iou = float(aggregate["zerobase_mean_silhouette_iou"])
        l_iou = float(aggregate["legacy2_mean_silhouette_iou"])
        z_fg = float(aggregate["zerobase_mean_foreground_ratio_error"])
        l_fg = float(aggregate["legacy2_mean_foreground_ratio_error"])
        reasons = []
        if replay_cases != 78:
            reasons.append(f"Approved-78 replay coverage is {replay_cases}/78")
        if not source_ok:
            reasons.append("one or more source SHA-256 bindings are unverified")
        if not reference_ok:
            reasons.append("one or more Approved reference SHA-256 bindings are unverified")
        if not replay_ok:
            reasons.append("one or more saved-Evidence replays are non-deterministic")
        if z_iou < l_iou:
            reasons.append("ZeroBase mean silhouette IoU regresses versus Minimalizer 2.0")
        if z_fg > l_fg:
            reasons.append("ZeroBase mean foreground-ratio error regresses versus Minimalizer 2.0")
        return MigrationGateResult(
            replay_cases, source_ok, reference_ok, replay_ok, z_iou, l_iou, z_fg, l_fg,
            not reasons, tuple(reasons),
        )
