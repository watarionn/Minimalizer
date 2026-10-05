from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping
import numpy as np
from minimalizer_zerobase.production.part_color_regions import extract_part_color_regions, PartColorRegion

@dataclass(frozen=True)
class RegionNode:
 id:str
 part:str
 mask:np.ndarray
 rgb:tuple[int,int,int]
 area:int

@dataclass(frozen=True)
class RegionEdge:
 a:str
 b:str
 shared_boundary:int
 color_distance:float

@dataclass(frozen=True)
class CrossPartRegionGraph:
 nodes:tuple[RegionNode,...]
 edges:tuple[RegionEdge,...]
 major_ids:tuple[str,...]

def _touch(a,b):
 a=np.asarray(a,bool);b=np.asarray(b,bool)
 return int(((a[1:]&b[:-1])|(b[1:]&a[:-1])).sum()+((a[:,1:]&b[:,:-1])|(b[:,1:]&a[:,:-1])).sum())

def _cd(a,b):
 return float(sum((int(x)-int(y))**2 for x,y in zip(a,b))**.5)

def build_cross_part_region_graph(rgb:np.ndarray,part_masks:Mapping[str,np.ndarray],*,max_regions_per_part:int=3,major_ratio:float=.025)->CrossPartRegionGraph:
 nodes=[]
 for part in sorted(part_masks):
  for i,r in enumerate(extract_part_color_regions(rgb,part_masks[part],max_regions=max_regions_per_part)):
   nodes.append(RegionNode(f"{part}:{i}",part,r.mask,r.rgb,r.area))
 edges=[]
 for i,a in enumerate(nodes):
  for b in nodes[i+1:]:
   if a.part==b.part: continue
   t=_touch(a.mask,b.mask)
   if t: edges.append(RegionEdge(a.id,b.id,t,_cd(a.rgb,b.rgb)))
 subject=max(1,int(np.logical_or.reduce([np.asarray(m,bool) for m in part_masks.values()]).sum())) if part_masks else 1
 major=tuple(n.id for n in nodes if n.area/subject>=major_ratio)
 return CrossPartRegionGraph(tuple(nodes),tuple(edges),major)

def composed_regions(graph:CrossPartRegionGraph,*,merge_color_distance:float=42.0):
 """Merge only touching cross-part regions with close colors. Major regions survive."""
 parent={n.id:n.id for n in graph.nodes}
 def find(x):
  while parent[x]!=x: parent[x]=parent[parent[x]];x=parent[x]
  return x
 def union(a,b):
  a=find(a);b=find(b)
  if a!=b: parent[max(a,b)]=min(a,b)
 for e in sorted(graph.edges,key=lambda e:(e.color_distance,-e.shared_boundary,e.a,e.b)):
  if e.color_distance<=merge_color_distance: union(e.a,e.b)
 groups={}
 for n in graph.nodes: groups.setdefault(find(n.id),[]).append(n)
 out=[]
 for key,ns in sorted(groups.items()):
  mask=np.logical_or.reduce([n.mask for n in ns]);area=int(mask.sum())
  weights=np.array([n.area for n in ns],float);cols=np.array([n.rgb for n in ns],float)
  rgb=tuple(int(round(x)) for x in np.average(cols,axis=0,weights=weights))
  out.append((key,mask,rgb,area,tuple(n.id for n in ns)))
 return tuple(out)
