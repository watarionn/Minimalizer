from .config import MinimalizeConfig
from .pipeline import minimalize
from .target_style import (
    apply_rinka_reference_style,
    minimalize_rinka_reference,
    rinka_reference_config,
)

__all__ = [
    "MinimalizeConfig",
    "minimalize",
    "rinka_reference_config",
    "apply_rinka_reference_style",
    "minimalize_rinka_reference",
]
