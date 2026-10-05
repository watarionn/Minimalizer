from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable
from minimalizer_zerobase.production.macro_mass import MacroMassPlan

class HierarchicalBudgetError(RuntimeError):
    pass

@dataclass(frozen=True)
class MassBudget:
    mass_id: str
    role: str
    primitives: int
    tier: str

@dataclass(frozen=True)
class HierarchicalBudget:
    total_budget: int
    allocations: tuple[MassBudget,...]
    unallocated: int

_CORE=("head","torso","lower_body")
_IDENTITY=("hair","accessory")
_SUPPORT=("left_arm","right_arm")

def allocate_hierarchical_macro_budget(plan: MacroMassPlan,total_budget:int) -> HierarchicalBudget:
    if total_budget <= 0:
        raise HierarchicalBudgetError("total budget must be positive")
    by_role={m.role:m for m in plan.masses}
    required=[r for r in _CORE if r in by_role]
    if len(required) < 3:
        raise HierarchicalBudgetError("readable character requires head, torso, and lower_body evidence")
    # Core readability owns the first budget. No decorative feature can starve it.
    alloc={r:1 for r in required}
    remaining=total_budget-len(alloc)
    if remaining < 0:
        raise HierarchicalBudgetError("budget cannot preserve core masses")
    # Hair is a major identity mass when observed, then arms preserve pose/readability,
    # then accessory. Every first allocation precedes any duplicate allocation.
    first=[r for r in ("hair","left_arm","right_arm","accessory") if r in by_role]
    for r in first:
        if remaining<=0: break
        alloc[r]=1; remaining-=1
    # Extra geometry is information-limited: at most one extra for major silhouette masses.
    for r in ("hair","torso","lower_body"):
        if remaining<=0: break
        if r in alloc:
            alloc[r]+=1; remaining-=1
    tiers={r:("core" if r in _CORE else "identity" if r in _IDENTITY else "support") for r in alloc}
    rows=tuple(MassBudget(f"mass:{r}",r,alloc[r],tiers[r]) for r in (*_CORE,"hair",*_SUPPORT,"accessory") if r in alloc)
    return HierarchicalBudget(total_budget,rows,remaining)
