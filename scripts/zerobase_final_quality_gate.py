from __future__ import annotations
import json
import tempfile
import sys
from pathlib import Path
ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))
from minimalizer_zerobase.analyzers.contracts import Evidence, Provenance
from minimalizer_zerobase.core.coordinates import CoordinateSpace
from minimalizer_zerobase.evaluation.quality_gate import FinalQualityGate
from minimalizer_zerobase.production import ProductionPipeline

def production_boundary_clean() -> bool:
    for base in (ROOT / "app", ROOT / "web", ROOT / "minimalize_engine"):
        for path in base.rglob("*.py"):
            if "minimalizer_zerobase" in path.read_text(encoding="utf-8", errors="ignore"):
                return False
    return True

def main() -> int:
    space = CoordinateSpace(100, 100)
    prov = Provenance("phase12-quality-gate", "1")
    records = (
        Evidence("face", "region", space, prov, .9, "face", {"bbox":[10,10,30,30]}, {"base_color":[240,190,160]}),
        Evidence("shirt", "region", space, prov, .9, "shirt", {"bbox":[10,50,50,35]}, {"base_color":[30,80,180]}),
    )
    with tempfile.TemporaryDirectory() as temp:
        capture = Path(temp) / "capture"
        pipeline = ProductionPipeline()
        original = pipeline.run(records, capture)
        replay = pipeline.replay(capture)
        result = FinalQualityGate().evaluate(
            repo_root=ROOT, artifact_root=capture,
            approved78_manifest=ROOT / "docs" / "zerobase" / "approved78_manifest.json",
            production_boundary_clean=production_boundary_clean(),
            renderer_deterministic=original.svg == replay.svg,
            replay_deterministic=(original.vector_scene.to_json() == replay.vector_scene.to_json()
                                  and original.optimization.to_json() == replay.optimization.to_json()),
            notices_present=(ROOT / "docs" / "zerobase" / "THIRD_PARTY_NOTICES.md").is_file(),
        )
    out = ROOT / "docs" / "zerobase" / "FINAL_QUALITY_GATE.json"
    out.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(result.to_json())
    return 0 if result.foundation_ready else 1

if __name__ == "__main__":
    raise SystemExit(main())
