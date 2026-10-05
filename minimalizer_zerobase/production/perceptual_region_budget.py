from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping, Sequence
import numpy as np
from minimalizer_zerobase.production.semantic_edge_regions import EdgeRegion

@dataclass(frozen=True)
class BudgetedRegion:
 part:str
 region:EdgeRegion
 score:float
 major:bool
 accent:bool

_DEFAULT_IMPORTANCE={"torso":1.30,"hair":1.25,"head":1.15,"accessory":1.20,"lower_body":1.0,"left_arm":.90,"right_arm":.90}

def _contrast(rgb:tuple[int,int,int],base:tuple[int,int,int])->float:
 return float(sum((int(a)-int(b))**2 for a,b in zip(rgb,base))**.5)/(255.0*(3.0**.5))

def select_perceptual_regions(regions:Mapping[str,Sequence[EdgeRegion]],part_masks:Mapping[str,np.ndarray],base_colors:Mapping[str,tuple[int,int,int]],*,budget:int=12,importance:Mapping[str,float]|None=None,major_ratio:float=.055)->tuple[BudgetedRegion,...]:
 """Allocate a global primitive budget to salient region evidence.
 Major regions are guaranteed first; remaining slots use deterministic perceptual score.
 """
 imp=dict(_DEFAULT_IMPORTANCE);imp.update(importance or {})
 subject=int(np.logical_or.reduce([np.asarray(m,bool) for m in part_masks.values()]).sum()) if part_masks else 1
 subject=max(subject,1);rows=[]
 for part in sorted(regions):
  base=base_colors.get(part,(128,128,128))
  parea=max(1,int(np.asarray(part_masks[part],bool).sum()))
  for r in regions[part]:
   subject_ratio=r.area/subject;part_ratio=r.area/parea
   major=subject_ratio>=major_ratio or part_ratio>=.34
   contrast=_contrast(r.rgb,base)
   # Generic identity-accent rescue: compact, strongly contrasting, edge-supported evidence.
   accent=(.008<=subject_ratio<=.085 and contrast>=.24 and r.edge_boundary>=.12)
   # Area establishes mass; contrast/edge rescue identity accents without letting tiny fragments dominate.
   score=imp.get(part,1.0)*(1.8*np.sqrt(subject_ratio)+.75*np.sqrt(part_ratio)+.65*contrast+.20*min(1.0,r.edge_boundary))
   rows.append(BudgetedRegion(part,r,float(score),major,accent))
 majors=sorted((x for x in rows if x.major),key=lambda x:(-x.score,x.part,-x.region.area,x.region.rgb))
 accents=sorted((x for x in rows if x.accent and not x.major),key=lambda x:(-x.score,x.part,-x.region.area,x.region.rgb))
 minors=sorted((x for x in rows if not x.major and not x.accent),key=lambda x:(-x.score,x.part,-x.region.area,x.region.rgb))
 # Preserve at most one guaranteed major per part before global competition.
 guaranteed=[];seen=set()
 for x in majors:
  if x.part not in seen: guaranteed.append(x);seen.add(x.part)
 # Reserve a bounded accent lane without allowing tiny details to dominate the composition.
 accent_slots=min(max(1,budget//4),len(accents)) if budget>=4 else 0
 chosen=guaranteed[:max(0,budget-accent_slots)]
 for x in accents[:accent_slots]:
  if len(chosen)<budget: chosen.append(x)
 chosen_ids={(x.part,id(x.region)) for x in chosen}
 for x in majors+accents+minors:
  if len(chosen)>=budget:break
  key=(x.part,id(x.region))
  if key not in chosen_ids:chosen.append(x);chosen_ids.add(key)
 return tuple(chosen)
