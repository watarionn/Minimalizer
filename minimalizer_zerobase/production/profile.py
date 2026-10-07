from __future__ import annotations

import os

CURRENT_PROFILE = "current"
REVIEWED_SA10_PROFILE = "reviewed-sa10"
SUPPORTED_SEMANTIC_PROFILES = (CURRENT_PROFILE, REVIEWED_SA10_PROFILE)


def semantic_profile() -> str:
    value = os.getenv("MINIMALIZER_SEMANTIC_PROFILE", CURRENT_PROFILE).strip().lower()
    if value not in SUPPORTED_SEMANTIC_PROFILES:
        raise ValueError(f"unsupported Minimalizer semantic profile: {value}")
    return value


def reviewed_sa10_enabled() -> bool:
    return semantic_profile() == REVIEWED_SA10_PROFILE
