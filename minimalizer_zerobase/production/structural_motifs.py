from __future__ import annotations
import numpy as np

def principal_axis(mask:np.ndarray)->tuple[np.ndarray,np.ndarray]:
 m=np.asarray(mask,bool);y,x=np.where(m)
 if len(x)<2:return np.array([0.,0.]),np.array([0.,1.])
 pts=np.column_stack([x,y]).astype(float);c=pts.mean(0);z=pts-c
 _,_,vh=np.linalg.svd(z,full_matrices=False);v=vh[0]
 if v[1]<0:v=-v
 return c,v

def arm_axis_band(mask:np.ndarray,*,width_ratio:float=.42)->np.ndarray:
 """Keep a connected arm-readable band along the mask's dominant axis, clipped to authority."""
 m=np.asarray(mask,bool)
 if not np.any(m):return m.copy()
 c,v=principal_axis(m);y,x=np.indices(m.shape);dx=x-c[0];dy=y-c[1]
 perp=np.abs(-v[1]*dx+v[0]*dy);proj=v[0]*dx+v[1]*dy
 ys,xs=np.where(m);span=max(xs.max()-xs.min()+1,ys.max()-ys.min()+1)
 band=(perp<=max(2.,span*width_ratio*.5))&m
 # Never erase most of a narrow/curved arm.
 return band if band.sum()>=m.sum()*.38 else m.copy()

def clothing_major_regions(rgb:np.ndarray,mask:np.ndarray,*,max_regions:int=4)->tuple[tuple[np.ndarray,tuple[int,int,int]],...]:
 """Large connected color masses for readable garment construction."""
 a=np.asarray(rgb,np.uint8);m=np.asarray(mask,bool);total=max(1,int(m.sum()))
 q=(a//48).astype(np.int16);keys=q[:,:,0]*36+q[:,:,1]*6+q[:,:,2]
 seen=np.zeros(m.shape,bool);rows=[];h,w=m.shape
 for sy,sx in zip(*np.where(m)):
  if seen[sy,sx]:continue
  key=keys[sy,sx];st=[(sy,sx)];seen[sy,sx]=1;pts=[]
  while st:
   y,x=st.pop();pts.append((y,x))
   for ny,nx in ((y-1,x),(y,x-1),(y,x+1),(y+1,x)):
    if 0<=ny<h and 0<=nx<w and m[ny,nx] and not seen[ny,nx] and keys[ny,nx]==key:
     seen[ny,nx]=1;st.append((ny,nx))
  if len(pts)<max(8,int(total*.045)):continue
  mm=np.zeros_like(m);yy,xx=zip(*pts);mm[yy,xx]=1
  col=tuple(int(v) for v in np.median(a[mm],axis=0));rows.append((len(pts),mm,col))
 rows.sort(key=lambda z:(-z[0],z[2]))
 return tuple((mm,col) for _,mm,col in rows[:max_regions])

def two_segment_arm_masks(mask:np.ndarray,torso_mask:np.ndarray)->tuple[np.ndarray,np.ndarray]:
 """Split an arm into shoulder-side and distal masses using the torso attachment as orientation."""
 m=np.asarray(mask,bool);torso=np.asarray(torso_mask,bool)
 if not np.any(m):return m.copy(),m.copy()
 c,v=principal_axis(m);ys,xs=np.where(m);pts=np.column_stack([xs,ys]).astype(float)
 # Orient axis so negative projection is nearer the torso centroid.
 ty,tx=np.where(torso)
 tc=np.array([tx.mean(),ty.mean()]) if len(tx) else c
 if np.dot(tc-c,v)>0:v=-v
 proj=(pts-c)@v;cut=float(np.median(proj))
 near=np.zeros_like(m);far=np.zeros_like(m)
 near[ys[proj<=cut],xs[proj<=cut]]=1;far[ys[proj>cut],xs[proj>cut]]=1
 # Preserve real mass rather than reducing either half to a centerline.
 if near.sum()<m.sum()*.18 or far.sum()<m.sum()*.18:return m.copy(),np.zeros_like(m)
 return near,far

def clothing_authority(torso:np.ndarray,major_clothing:np.ndarray|None)->np.ndarray:
 """Union clothing evidence while retaining semantic ownership boundaries upstream."""
 t=np.asarray(torso,bool)
 return t.copy() if major_clothing is None else (t|np.asarray(major_clothing,bool))

def boundary_band(a:np.ndarray,b:np.ndarray,*,radius:int=2)->np.ndarray:
 """Pixels of a touching semantic boundary, expanded only inside their union."""
 aa=np.asarray(a,bool);bb=np.asarray(b,bool);h,w=aa.shape
 def dilate(m):
  p=np.pad(m,1);o=m.copy()
  for dy,dx in ((0,1),(1,0),(1,2),(2,1)):o|=p[dy:dy+h,dx:dx+w]
  return o
 da,db=aa.copy(),bb.copy()
 for _ in range(max(1,radius)):da=dilate(da);db=dilate(db)
 return (da&db)&(aa|bb)

def collar_motif(mask:np.ndarray,head_mask:np.ndarray)->np.ndarray:
 """Upper-central garment structure nearest the head/neck attachment."""
 m=np.asarray(mask,bool);head=np.asarray(head_mask,bool)
 if not np.any(m) or not np.any(head):return np.zeros_like(m)
 band=boundary_band(m,head,radius=4)&m
 if not np.any(band):
  ys,xs=np.where(m);cut=np.quantile(ys,.28);band=m&(np.indices(m.shape)[0]<=cut)
 # Keep central upper structure rather than shoulder-wide noise.
 ys,xs=np.where(m);cx=float(xs.mean());span=max(1.,float(xs.max()-xs.min()+1))
 xgrid=np.indices(m.shape)[1]
 return band&(np.abs(xgrid-cx)<=span*.28)

def sleeve_boundary_motifs(torso:np.ndarray,left_arm:np.ndarray|None,right_arm:np.ndarray|None)->tuple[np.ndarray,...]:
 """Return sparse garment/arm attachment bands for sleeve readability."""
 t=np.asarray(torso,bool);out=[]
 for arm in (left_arm,right_arm):
  if arm is None:continue
  b=boundary_band(t,np.asarray(arm,bool),radius=3)
  if np.any(b):out.append(b)
 return tuple(out)

def sleeve_forearm_masses(rgb:np.ndarray,arm:np.ndarray,torso:np.ndarray)->tuple[np.ndarray,np.ndarray]:
 """Split an arm into torso-side sleeve and distal forearm using geometry plus dominant color change."""
 a=np.asarray(rgb,np.uint8);m=np.asarray(arm,bool);t=np.asarray(torso,bool)
 if not np.any(m):return m.copy(),m.copy()
 c,v=principal_axis(m);ty,tx=np.where(t);tc=np.array([tx.mean(),ty.mean()]) if len(tx) else c
 if np.dot(tc-c,v)>0:v=-v
 y,x=np.where(m);pts=np.column_stack([x,y]).astype(float);proj=(pts-c)@v
 order=np.argsort(proj);p=proj[order];cols=a[y[order],x[order]].astype(float)
 # Search central cuts only. Score combines color separation and balanced support.
 best=None
 for q in np.linspace(.28,.62,8):
  cut=np.quantile(p,q);lo=cols[p<=cut];hi=cols[p>cut]
  if len(lo)<4 or len(hi)<4:continue
  contrast=float(np.linalg.norm(np.median(lo,axis=0)-np.median(hi,axis=0)))
  balance=min(len(lo),len(hi))/len(cols);score=contrast*(.5+balance)
  if best is None or score>best[0]:best=(score,cut)
 cut=float(np.median(p)) if best is None or best[0]<18 else best[1]
 sleeve=np.zeros_like(m);fore=np.zeros_like(m);s=proj<=cut
 sleeve[y[s],x[s]]=1;fore[y[~s],x[~s]]=1
 if sleeve.sum()<m.sum()*.18 or fore.sum()<m.sum()*.18:return two_segment_arm_masks(m,t)
 return sleeve,fore

def collar_shape_segments(rgb:np.ndarray,garment:np.ndarray,head:np.ndarray,*,max_segments:int=2)->tuple[np.ndarray,...]:
 """Extract at most two coherent upper-garment collar strokes from source evidence."""
 a=np.asarray(rgb,np.uint8);g=np.asarray(garment,bool);h=np.asarray(head,bool)
 if not np.any(g):return ()
 base=collar_motif(g,h)
 ys,xs=np.where(g);cx=float(xs.mean());span=max(1.,float(xs.max()-xs.min()+1))
 yy,xx=np.indices(g.shape)
 upper=g&(yy<=np.quantile(ys,.42))&(np.abs(xx-cx)<=span*.38)
 # Prefer color contrast against the garment median, but remain inside upper garment authority.
 med=np.median(a[g],axis=0).astype(float)
 dist=np.linalg.norm(a.astype(float)-med,axis=2)
 cand=upper&(dist>=max(18.,float(np.quantile(dist[g],.68))))
 cand|=base
 # Split left/right around garment center. This naturally represents V/Y collars with <=2 masses.
 out=[]
 for side in (cand&(xx<=cx),cand&(xx>cx)):
  if side.sum()<max(4,int(g.sum()*.004)):continue
  # Keep component nearest upper center.
  seen=np.zeros_like(side);comps=[];H,W=side.shape
  for sy,sx in zip(*np.where(side)):
   if seen[sy,sx]:continue
   st=[(sy,sx)];seen[sy,sx]=1;pts=[]
   while st:
    y,x=st.pop();pts.append((y,x))
    for ny,nx in ((y-1,x),(y,x-1),(y,x+1),(y+1,x)):
     if 0<=ny<H and 0<=nx<W and side[ny,nx] and not seen[ny,nx]:
      seen[ny,nx]=1;st.append((ny,nx))
   if len(pts)>=4:comps.append(pts)
  if not comps:continue
  comps.sort(key=lambda p:(np.mean([q[0] for q in p]),-len(p)))
  m=np.zeros_like(g);py,px=zip(*comps[0]);m[py,px]=1;out.append(m)
 return tuple(out[:max_segments])

def major_color_masses(rgb:np.ndarray,mask:np.ndarray,*,max_masses:int=3,min_ratio:float=.10)->tuple[tuple[np.ndarray,tuple[int,int,int]],...]:
 """Reserve dominant connected color masses before detail regions consume the primitive budget."""
 a=np.asarray(rgb,np.uint8);m=np.asarray(mask,bool)
 if not np.any(m):return ()
 total=int(m.sum());q=(a//48).astype(np.int16);keys=q[:,:,0]*36+q[:,:,1]*6+q[:,:,2]
 seen=np.zeros_like(m);rows=[];H,W=m.shape
 for sy,sx in zip(*np.where(m)):
  if seen[sy,sx]:continue
  key=keys[sy,sx];st=[(sy,sx)];seen[sy,sx]=1;pts=[]
  while st:
   y,x=st.pop();pts.append((y,x))
   for ny,nx in ((y-1,x),(y,x-1),(y,x+1),(y+1,x)):
    if 0<=ny<H and 0<=nx<W and m[ny,nx] and not seen[ny,nx] and keys[ny,nx]==key:
     seen[ny,nx]=1;st.append((ny,nx))
  if len(pts)<max(8,int(total*min_ratio)):continue
  mm=np.zeros_like(m);yy,xx=zip(*pts);mm[yy,xx]=1
  col=tuple(int(v) for v in np.median(a[mm],axis=0));rows.append((len(pts),mm,col))
 rows.sort(key=lambda z:(-z[0],z[2]))
 return tuple((mm,col) for _,mm,col in rows[:max_masses])

def garment_panels(rgb:np.ndarray,garment:np.ndarray,*,max_panels:int=4,min_ratio:float=.07)->tuple[tuple[np.ndarray,tuple[int,int,int]],...]:
 """Build a few large garment panels from connected quantized source color masses."""
 a=np.asarray(rgb,np.uint8);g=np.asarray(garment,bool)
 if not np.any(g):return ()
 # Coarser than detail proposals: panels represent clothing construction, not trim.
 q=(a//56).astype(np.int16);key=q[:,:,0]*25+q[:,:,1]*5+q[:,:,2]
 H,W=g.shape;seen=np.zeros_like(g);total=int(g.sum());rows=[]
 for sy,sx in zip(*np.where(g)):
  if seen[sy,sx]:continue
  k=key[sy,sx];st=[(sy,sx)];seen[sy,sx]=1;pts=[]
  while st:
   y,x=st.pop();pts.append((y,x))
   for ny,nx in ((y-1,x),(y,x-1),(y,x+1),(y+1,x)):
    if 0<=ny<H and 0<=nx<W and g[ny,nx] and not seen[ny,nx] and key[ny,nx]==k:
     seen[ny,nx]=1;st.append((ny,nx))
  if len(pts)<max(8,int(total*min_ratio)):continue
  m=np.zeros_like(g);yy,xx=zip(*pts);m[yy,xx]=1
  col=tuple(int(v) for v in np.median(a[m],axis=0))
  rows.append((len(pts),float(np.mean(yy)),m,col))
 rows.sort(key=lambda z:(-z[0],z[1],z[3]))
 chosen=[]
 occupied=np.zeros_like(g)
 for _,_,m,col in rows:
  novel=m&~occupied
  if novel.sum()<total*min_ratio:continue
  chosen.append((novel,col));occupied|=novel
  if len(chosen)>=max_panels:break
 return tuple(chosen)

def global_mass_regions(rgb:np.ndarray,parts:dict[str,np.ndarray],*,min_subject_ratio:float=.025,max_regions:int=10)->tuple[tuple[str,np.ndarray,tuple[int,int,int]],...]:
 """Select visually dominant source-derived masses across the whole subject, not per-detail budgets."""
 a=np.asarray(rgb,np.uint8);subject=np.zeros(a.shape[:2],bool)
 for m in parts.values():subject|=np.asarray(m,bool)
 total=max(1,int(subject.sum()));rows=[]
 for role,m0 in parts.items():
  m=np.asarray(m0,bool)
  if not np.any(m):continue
  # Broad quantization deliberately favors silhouette-scale color blocks.
  q=(a//64).astype(np.int16);keys=q[:,:,0]*16+q[:,:,1]*4+q[:,:,2]
  H,W=m.shape;seen=np.zeros_like(m)
  for sy,sx in zip(*np.where(m)):
   if seen[sy,sx]:continue
   k=keys[sy,sx];st=[(sy,sx)];seen[sy,sx]=1;pts=[]
   while st:
    y,x=st.pop();pts.append((y,x))
    for ny,nx in ((y-1,x),(y,x-1),(y,x+1),(y+1,x)):
     if 0<=ny<H and 0<=nx<W and m[ny,nx] and not seen[ny,nx] and keys[ny,nx]==k:
      seen[ny,nx]=1;st.append((ny,nx))
   ratio=len(pts)/total
   if ratio<min_subject_ratio:continue
   mm=np.zeros_like(m);yy,xx=zip(*pts);mm[yy,xx]=1
   col=tuple(int(v) for v in np.median(a[mm],axis=0))
   # Area dominates, with chroma as a mild identity cue.
   chroma=(max(col)-min(col))/255.;score=ratio*(1.+.25*chroma)
   rows.append((score,role,mm,col))
 rows.sort(key=lambda z:(-z[0],z[1],z[3]))
 return tuple((role,m,col) for _,role,m,col in rows[:max_regions])

def reserve_identity_accents(rgb:np.ndarray,authority:np.ndarray,*,max_accents:int=3,min_ratio:float=.003,max_ratio:float=.09)->tuple[tuple[np.ndarray,tuple[int,int,int]],...]:
 """Reserve compact, high-contrast connected accents before perceptual-budget competition."""
 a=np.asarray(rgb,np.uint8);m=np.asarray(authority,bool)
 if not np.any(m):return ()
 total=int(m.sum());base=np.median(a[m],axis=0).astype(float)
 q=(a//40).astype(np.int16);keys=q[:,:,0]*49+q[:,:,1]*7+q[:,:,2]
 H,W=m.shape;seen=np.zeros_like(m);rows=[]
 for sy,sx in zip(*np.where(m)):
  if seen[sy,sx]:continue
  k=keys[sy,sx];st=[(sy,sx)];seen[sy,sx]=1;pts=[]
  while st:
   y,x=st.pop();pts.append((y,x))
   for ny,nx in ((y-1,x),(y,x-1),(y,x+1),(y+1,x)):
    if 0<=ny<H and 0<=nx<W and m[ny,nx] and not seen[ny,nx] and keys[ny,nx]==k:
     seen[ny,nx]=1;st.append((ny,nx))
  ratio=len(pts)/total
  if not(min_ratio<=ratio<=max_ratio):continue
  yy,xx=zip(*pts);col=np.median(a[yy,xx],axis=0).astype(float)
  contrast=float(np.linalg.norm(col-base));chroma=float(col.max()-col.min())
  if contrast<52 or chroma<28:continue
  mm=np.zeros_like(m);mm[yy,xx]=1
  score=contrast*(.7+.3*chroma/255.)*np.sqrt(ratio)
  rows.append((score,mm,tuple(int(v) for v in col)))
 rows.sort(key=lambda z:(-z[0],z[2]))
 return tuple((mm,col) for _,mm,col in rows[:max_accents])

def silhouette_mass(mask:np.ndarray,*,bands:int=5)->np.ndarray:
 """Recompose a semantic silhouette into broad horizontal masses while staying inside authority."""
 m=np.asarray(mask,bool)
 if not np.any(m):return m.copy()
 y,x=np.where(m);y0,y1=int(y.min()),int(y.max())+1
 out=np.zeros_like(m)
 edges=np.linspace(y0,y1,bands+1).astype(int)
 for a,b in zip(edges[:-1],edges[1:]):
  yy,xx=np.where(m[a:b])
  if not len(xx):continue
  lo=int(np.quantile(xx,.08));hi=int(np.quantile(xx,.92))
  band=np.zeros_like(m);band[a:b,lo:hi+1]=1
  out|=band&m
 return out

def hierarchical_shape_mass(mask:np.ndarray,*,bands:int=4)->np.ndarray:
 m=np.asarray(mask,bool)
 if not np.any(m):return m.copy()
 y,x=np.where(m);out=np.zeros_like(m)
 edges=np.linspace(y.min(),y.max()+1,bands+1).astype(int)
 for a,b in zip(edges[:-1],edges[1:]):
  yy,xx=np.where(m[a:b])
  if len(xx)<3:continue
  lo=int(np.quantile(xx,.12));hi=int(np.quantile(xx,.88))
  core=np.zeros_like(m);core[a:b,lo:hi+1]=1
  out|=core&m
 return out
