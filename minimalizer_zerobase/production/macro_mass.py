from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping

class MacroMassPlanError(RuntimeError):
    pass

@dataclass(frozen=True)
class MacroMass:
    mass_id: str
    role: str
    parent_id: str | None
    required: bool
    confidence: float
    bbox: tuple[float,float,float,float]
    primitive_families: tuple[str,...]
    provenance: str

@dataclass(frozen=True)
class MacroMassPlan:
    masses: tuple[MacroMass,...]

_ROLE_ORDER=("head","hair","torso","left_arm","right_arm","lower_body","accessory")
_FAMILIES={
 "head":("ellipse","polygon"),"hair":("bezier_silhouette","polygon"),
 "torso":("trapezoid","polygon"),"left_arm":("ribbon","polygon"),
 "right_arm":("ribbon","polygon"),"lower_body":("trapezoid","polygon"),
 "accessory":("polygon","ellipse","ribbon"),
}
_PARENT={"hair":"head","left_arm":"torso","right_arm":"torso","lower_body":"torso","accessory":"torso"}

def build_macro_mass_plan(parts: Mapping[str,Mapping[str,Any]]) -> MacroMassPlan:
    """Promote authorized semantic-part evidence into structural masses, never raw observer roles."""
    unknown=set(parts)-set(_ROLE_ORDER)
    if unknown:
        raise MacroMassPlanError("unknown semantic part: "+", ".join(sorted(unknown)))
    masses=[]
    for role in _ROLE_ORDER:
        row=parts.get(role)
        if not row or row.get("authorized") is not True:
            continue
        box=row.get("bbox")
        if not isinstance(box,(list,tuple)) or len(box)!=4 or float(box[2])<=0 or float(box[3])<=0:
            raise MacroMassPlanError(f"invalid bbox for {role}")
        confidence=float(row.get("confidence",0.0))
        if not 0<=confidence<=1:
            raise MacroMassPlanError(f"invalid confidence for {role}")
        parent=_PARENT.get(role)
        if parent and parent not in parts:
            parent=None
        masses.append(MacroMass(
            mass_id=f"mass:{role}",role=role,parent_id=f"mass:{parent}" if parent else None,
            required=role in {"head","torso","lower_body"},confidence=confidence,
            bbox=tuple(float(v) for v in box),primitive_families=_FAMILIES[role],
            provenance=str(row.get("provenance","semantic_part_evidence")),
        ))
    supported={m.role for m in masses}
    if {"head","torso","lower_body"}.issubset(set(parts)) and not {"head","torso","lower_body"}.issubset(supported):
        raise MacroMassPlanError("supported core masses must remain authorized")
    return MacroMassPlan(tuple(masses))
