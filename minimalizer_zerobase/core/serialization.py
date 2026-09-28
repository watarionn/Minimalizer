from __future__ import annotations
import json
from dataclasses import asdict, fields, is_dataclass
from enum import Enum
from typing import Any, TypeVar, Type

T = TypeVar("T", bound="CanonicalModel")

class CanonicalModel:
    def to_dict(self) -> dict[str, Any]:
        def encode(v: Any) -> Any:
            if is_dataclass(v): return {f.name: encode(getattr(v, f.name)) for f in fields(v)}
            if isinstance(v, dict): return {k: encode(v[k]) for k in sorted(v)}
            if isinstance(v, (list, tuple)): return [encode(x) for x in v]
            if isinstance(v, Enum): return v.value
            return v
        return encode(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
