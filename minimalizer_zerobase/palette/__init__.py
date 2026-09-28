from .engine import MaterialAssignment, MaterialEvidence, PaletteMaterialEngine, PalettePolicy

from .artifacts import (
    phase9_metrics,
    render_palette_preview,
    render_palette_strip,
    write_phase9_artifacts,
)
from .consolidation import (
    CRITICAL_PARTS,
    PaletteAssignment,
    PaletteConsolidationPolicy,
    PaletteConsolidationResult,
    PaletteEntry,
    consolidate_palette,
)

__all__ = [
    "CRITICAL_PARTS",
    "PaletteAssignment",
    "MaterialAssignment",
    "MaterialEvidence",
    "PaletteConsolidationPolicy",
    "PaletteConsolidationResult",
    "PaletteEntry",
    "PaletteMaterialEngine",
    "PalettePolicy",
    "consolidate_palette",
    "phase9_metrics",
    "render_palette_preview",
    "render_palette_strip",
    "write_phase9_artifacts",
]
