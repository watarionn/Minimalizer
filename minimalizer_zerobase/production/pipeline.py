from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from minimalizer_zerobase.analyzers.contracts import Evidence, Provenance
from minimalizer_zerobase.compose import SemanticComposer, VectorScene
from minimalizer_zerobase.core.coordinates import CoordinateSpace
from minimalizer_zerobase.geometry import PrimitiveGenerator
from minimalizer_zerobase.importance import ImportanceEngine
from minimalizer_zerobase.optimize import GeometryOptimizer, GeometryOptimizationResult
from minimalizer_zerobase.palette import MaterialEvidence, PaletteMaterialEngine
from minimalizer_zerobase.regions import RegionReconstructor
from minimalizer_zerobase.render import SvgRenderer
from minimalizer_zerobase.scene.fusion import EvidenceFusion

@dataclass(frozen=True)
class ProductionPipelinePolicy:
    require_material_evidence: bool = True
    artifact_version: str = "1"

@dataclass(frozen=True)
class PipelineArtifacts:
    vector_scene: VectorScene
    optimization: GeometryOptimizationResult
    svg: str
    artifact_dir: Path | None = None

class ProductionPipeline:
    producer = "ProductionPipeline"
    producer_version = "1.0"
    def __init__(self, policy: ProductionPipelinePolicy | None = None):
        self.policy = policy or ProductionPipelinePolicy()
        self.fusion = EvidenceFusion()
        self.reconstructor = RegionReconstructor()
        self.importance = ImportanceEngine()
        self.palette = PaletteMaterialEngine()
        self.generator = PrimitiveGenerator()
        self.optimizer = GeometryOptimizer()
        self.composer = SemanticComposer()
        self.renderer = SvgRenderer()

    def run(self, evidence: Iterable[Evidence], artifact_dir: str | Path | None = None) -> PipelineArtifacts:
        records = tuple(sorted(evidence, key=lambda x: x.evidence_id))
        scene = self.fusion.fuse(records)
        self._write(artifact_dir, "01_evidence.json", [x.to_dict() for x in records])
        self._write(artifact_dir, "02_fused_scene.json", scene.to_dict())
        scene = self.reconstructor.reconstruct(scene)
        self._write(artifact_dir, "03_reconstructed_scene.json", scene.to_dict())
        scene = self.importance.apply(scene)
        self._write(artifact_dir, "04_importance_scene.json", scene.to_dict())
        materials = self._materials(scene, records)
        scene = self.palette.apply(scene, materials)
        assignments = self.palette.assign(scene, materials)
        self._write(artifact_dir, "05_palette_scene.json", scene.to_dict())
        candidates = self.generator.generate(scene)
        self._write(artifact_dir, "06_candidates.json", [x.to_dict() for x in candidates])
        optimization = self.optimizer.optimize(scene, candidates)
        self._write(artifact_dir, "07_optimization.json", optimization.to_dict())
        vector = self.composer.compose(scene, candidates, optimization.selections, assignments)
        self._write(artifact_dir, "08_vector_scene.json", vector.to_dict())
        svg = self.renderer.render(vector)
        self._write_text(artifact_dir, "09_vector_scene.svg", svg)
        manifest = {
            "producer": self.producer,
            "producer_version": self.producer_version,
            "artifact_version": self.policy.artifact_version,
            "stages": [
                "01_evidence.json", "02_fused_scene.json", "03_reconstructed_scene.json",
                "04_importance_scene.json", "05_palette_scene.json", "06_candidates.json",
                "07_optimization.json", "08_vector_scene.json", "09_vector_scene.svg",
            ],
        }
        self._write(artifact_dir, "manifest.json", manifest)
        return PipelineArtifacts(vector, optimization, svg, Path(artifact_dir) if artifact_dir else None)

    def replay(self, artifact_dir: str | Path) -> PipelineArtifacts:
        root = Path(artifact_dir)
        raw = json.loads((root / "01_evidence.json").read_text(encoding="utf-8"))
        return self.run((self._evidence(x) for x in raw), root)

    def _materials(self, scene, evidence: tuple[Evidence, ...]) -> tuple[MaterialEvidence, ...]:
        by_id = {x.evidence_id: x for x in evidence}
        out = []
        for region in sorted(scene.regions, key=lambda x: x.region_id):
            colors = []
            for evidence_id in region.evidence_ids:
                raw = by_id[evidence_id].normalization.get("base_color")
                if isinstance(raw, (list, tuple)) and len(raw) == 3:
                    colors.append(tuple(int(v) for v in raw))
            if not colors:
                if self.policy.require_material_evidence:
                    raise ValueError(f"region lacks normalized base_color evidence: {region.region_id}")
                colors = [(128, 128, 128)]
            color = sorted(colors)[0]
            out.append(MaterialEvidence(region.region_id, color, source="normalized_evidence"))
        return tuple(out)

    @staticmethod
    def _write(root: str | Path | None, name: str, value) -> None:
        if root is None:
            return
        path = Path(root)
        path.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        (path / name).write_text(payload + "\n", encoding="utf-8")

    @staticmethod
    def _write_text(root: str | Path | None, name: str, value: str) -> None:
        if root is None:
            return
        path = Path(root)
        path.mkdir(parents=True, exist_ok=True)
        (path / name).write_text(value, encoding="utf-8")

    @staticmethod
    def _evidence(data: dict) -> Evidence:
        space = data["coordinate_space"]
        provenance = data["provenance"]
        return Evidence(
            evidence_id=data["evidence_id"], evidence_type=data["evidence_type"],
            coordinate_space=CoordinateSpace(**space),
            provenance=Provenance(**provenance), confidence=data.get("confidence"),
            semantic_label=data.get("semantic_label"), geometry=data.get("geometry", {}),
            normalization=data.get("normalization", {}),
            schema_version=data.get("schema_version", "1.0"),
        )
