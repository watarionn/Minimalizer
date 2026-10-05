from __future__ import annotations
import numpy as np

def _area(r):
 return abs(sum(r[i][0]*r[(i+1)%len(r)][1]-r[(i+1)%len(r)][0]*r[i][1] for i in range(len(r)))/2)
def _dist(p,a,b):
 ax,ay=a;bx,by=b;px,py=p;dx=bx-ax;dy=by-ay
 if dx==dy==0:return ((px-ax)**2+(py-ay)**2)**.5
 t=max(0,min(1,((px-ax)*dx+(py-ay)*dy)/(dx*dx+dy*dy)))
 return ((px-(ax+t*dx))**2+(py-(ay+t*dy))**2)**.5
def _simplify_open(p,e):
 if len(p)<=2:return p[:]
 ds=[_dist(p[i],p[0],p[-1]) for i in range(1,len(p)-1)]
 if not ds or max(ds)<=e:return [p[0],p[-1]]
 j=1+max(range(len(ds)),key=ds.__getitem__)
 return _simplify_open(p[:j+1],e)[:-1]+_simplify_open(p[j:],e)
def simplify_closed(p,e):
 if len(p)<=4:return p[:]
 j=max(range(1,len(p)),key=lambda i:(p[i][0]-p[0][0])**2+(p[i][1]-p[0][1])**2)
 q=_simplify_open(p[:j+1],e)[:-1]+_simplify_open(p[j:]+[p[0]],e)[:-1]
 return q if len(q)>=3 else p[:]

def boundary_ring(mask):
 m=np.asarray(mask,bool);h,w=m.shape; edges=[]
 for y,x in zip(*np.where(m)):
  if y==0 or not m[y-1,x]:edges.append(((x,y),(x+1,y)))
  if x==w-1 or not m[y,x+1]:edges.append(((x+1,y),(x+1,y+1)))
  if y==h-1 or not m[y+1,x]:edges.append(((x+1,y+1),(x,y+1)))
  if x==0 or not m[y,x-1]:edges.append(((x,y+1),(x,y)))
 if not edges:return []
 out={}
 for a,b in edges:out.setdefault(a,[]).append(b)
 rings=[];unused=set(edges)
 while unused:
  a,b=min(unused);ring=[a];cur=(a,b)
  for _ in range(len(edges)+1):
   if cur not in unused:break
   unused.remove(cur);ring.append(cur[1])
   if cur[1]==ring[0]:break
   cand=[(cur[1],z) for z in out.get(cur[1],[]) if (cur[1],z) in unused]
   if not cand:break
   cur=min(cand)
  if len(ring)>=4 and ring[-1]==ring[0]:rings.append(ring[:-1])
 return max(rings,key=_area) if rings else []

def semantic_contour(mask,max_vertices=18):
 ring=boundary_ring(mask)
 if not ring:return []
 lo,hi=0.0,max(np.asarray(mask).shape)
 best=ring
 # largest epsilon that respects a compact vertex budget
 for _ in range(18):
  mid=(lo+hi)/2;q=simplify_closed(ring,mid)
  if len(q)>max_vertices:lo=mid
  else:best=q;hi=mid
 return best
