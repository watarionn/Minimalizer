from __future__ import annotations

from dataclasses import dataclass

from minimalizer_zerobase.core.serialization import CanonicalModel

from .contracts import ArtifactOrigin, ArtifactRecord, RunManifest


@dataclass(frozen=True)
class ProvenanceViolation(CanonicalModel):
    code: str
    artifact_id: str | None
    detail: str


@dataclass(frozen=True)
class ProvenanceGateResult(CanonicalModel):
    passed: bool
    violations: tuple[ProvenanceViolation, ...]


class ProvenancePolicyGate:
    _VISIBLE_ORIGINS = {
        ArtifactOrigin.SOURCE_PIXEL,
        ArtifactOrigin.GEOMETRIC_DERIVATION,
    }
    _FORBIDDEN_LINEAGE_ORIGINS = {
        ArtifactOrigin.SYNTHESIZED,
        ArtifactOrigin.UNKNOWN,
    }

    def evaluate(
        self,
        manifest: RunManifest,
        artifacts: tuple[ArtifactRecord, ...],
    ) -> ProvenanceGateResult:
        violations: list[ProvenanceViolation] = []
        self._audit_run_policy(manifest, violations)

        by_id: dict[str, ArtifactRecord] = {}
        for record in artifacts:
            if record.artifact_id in by_id:
                violations.append(ProvenanceViolation(
                    "duplicate-artifact-id",
                    record.artifact_id,
                    "artifact_id must be unique within one run",
                ))
                continue
            by_id[record.artifact_id] = record

        self._audit_parent_refs(by_id, violations)
        self._audit_artifact_origins(by_id, violations)
        self._audit_cycles(by_id, violations)
        self._audit_visible_lineage(by_id, violations)
        return ProvenanceGateResult(not violations, tuple(violations))

    @staticmethod
    def _audit_run_policy(
        manifest: RunManifest,
        violations: list[ProvenanceViolation],
    ) -> None:
        forbidden = {
            "allow_generative_pixels": manifest.policy.allow_generative_pixels,
            "allow_inpainting": manifest.policy.allow_inpainting,
            "allow_img2img": manifest.policy.allow_img2img,
        }
        for name, enabled in forbidden.items():
            if enabled:
                violations.append(ProvenanceViolation(
                    "run-policy-allows-generated-visible-content",
                    None,
                    f"{name}=true is incompatible with observed-only output",
                ))

    @staticmethod
    def _audit_parent_refs(
        by_id: dict[str, ArtifactRecord],
        violations: list[ProvenanceViolation],
    ) -> None:
        for record in by_id.values():
            for parent_ref in record.parents:
                parent = by_id.get(parent_ref.artifact_id)
                if parent is None:
                    violations.append(ProvenanceViolation(
                        "missing-parent-artifact",
                        record.artifact_id,
                        f"missing parent {parent_ref.artifact_id}",
                    ))
                elif parent.sha256 != parent_ref.sha256:
                    violations.append(ProvenanceViolation(
                        "parent-hash-mismatch",
                        record.artifact_id,
                        f"parent hash mismatch for {parent_ref.artifact_id}",
                    ))

    @classmethod
    def _audit_artifact_origins(
        cls,
        by_id: dict[str, ArtifactRecord],
        violations: list[ProvenanceViolation],
    ) -> None:
        for record in by_id.values():
            if record.origin in cls._FORBIDDEN_LINEAGE_ORIGINS:
                violations.append(ProvenanceViolation(
                    "forbidden-artifact-origin",
                    record.artifact_id,
                    f"artifact origin {record.origin.value} is forbidden by observed-only policy",
                ))

    @staticmethod
    def _audit_cycles(
        by_id: dict[str, ArtifactRecord],
        violations: list[ProvenanceViolation],
    ) -> None:
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(artifact_id: str) -> None:
            if artifact_id in visited:
                return
            if artifact_id in visiting:
                violations.append(ProvenanceViolation(
                    "artifact-lineage-cycle",
                    artifact_id,
                    "artifact provenance graph must be acyclic",
                ))
                return
            visiting.add(artifact_id)
            record = by_id[artifact_id]
            for parent_ref in record.parents:
                if parent_ref.artifact_id in by_id:
                    visit(parent_ref.artifact_id)
            visiting.remove(artifact_id)
            visited.add(artifact_id)

        for artifact_id in sorted(by_id):
            visit(artifact_id)

    def _audit_visible_lineage(
        self,
        by_id: dict[str, ArtifactRecord],
        violations: list[ProvenanceViolation],
    ) -> None:
        for record in by_id.values():
            if not record.visible:
                continue
            if record.origin not in self._VISIBLE_ORIGINS:
                violations.append(ProvenanceViolation(
                    "invalid-visible-origin",
                    record.artifact_id,
                    f"visible origin {record.origin.value} is not permitted",
                ))
            has_source, forbidden = self._trace_lineage(
                record.artifact_id,
                by_id,
                set(),
            )
            if forbidden:
                violations.append(ProvenanceViolation(
                    "forbidden-visible-lineage",
                    record.artifact_id,
                    "visible lineage contains synthesized or unknown provenance",
                ))
            if not has_source:
                violations.append(ProvenanceViolation(
                    "visible-lineage-lacks-source-pixels",
                    record.artifact_id,
                    "visible artifact must trace to a source_pixel artifact",
                ))

    def _trace_lineage(
        self,
        artifact_id: str,
        by_id: dict[str, ArtifactRecord],
        seen: set[str],
    ) -> tuple[bool, bool]:
        if artifact_id in seen or artifact_id not in by_id:
            return False, False
        record = by_id[artifact_id]
        if record.origin in self._FORBIDDEN_LINEAGE_ORIGINS:
            return False, True
        if record.origin == ArtifactOrigin.SOURCE_PIXEL:
            return True, False

        next_seen = seen | {artifact_id}
        has_source = False
        has_forbidden = False
        for parent_ref in record.parents:
            parent_source, parent_forbidden = self._trace_lineage(
                parent_ref.artifact_id,
                by_id,
                next_seen,
            )
            has_source |= parent_source
            has_forbidden |= parent_forbidden
        return has_source, has_forbidden
