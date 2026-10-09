"""v33 deterministic source-owned SVG boundary research (NOT production).

Vectorize the *changed color planes* of exact frozen v32 into integer-pixel
boundary paths. Preserve original Facet as an embedded immutable PNG inside a
standalone SVG. Simplified paths are proposals only until independent browser
raster comparison proves the no-outside-pixel gate.
"""
from __future__ import annotations
import base64
import hashlib
import html
import json
import time
from collections import defaultdict
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

ROOT=Path(r"G:\マイドライブ\chatGPT及びCodex用\Minimalizer\ConnectedSourcePlanesV32_20261009")
RGBS={"Kyoko":((149,211,27),),"Noel":((68,37,36),),"Ririka":()}
MASK_LABEL=(180,0,255)

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()

def rgba(path):
    return np.asarray(Image.open(path).convert("RGBA"),dtype=np.uint8).copy()

def turn(direction):
    (ax,ay),(bx,by)=direction
    dx,dy=bx-ax,by-ay
    dirs={(1,0):0,(0,1):1,(-1,0):2,(0,-1):3}
    return dirs[(dx,dy)]

def boundaries(mask):
    """Trace exact pixel-cell borders as closed oriented edge chains."""
    if mask.dtype!=bool or mask.ndim!=2:raise ValueError("binary mask required")
    h,w=mask.shape
    ys,xs=np.nonzero(mask)
    edges=defaultdict(list)
    for y,x in zip(ys.tolist(),xs.tolist()):
        if y==0 or not mask[y-1,x]:
            edges[(x,y)].append((x+1,y))
        if x+1==w or not mask[y,x+1]:
            edges[(x+1,y)].append((x+1,y+1))
        if y+1==h or not mask[y+1,x]:
            edges[(x+1,y+1)].append((x,y+1))
        if x==0 or not mask[y,x-1]:
            edges[(x,y+1)].append((x,y))
    total=sum(len(v) for v in edges.values())
    contours=[]
    while edges:
        start=min(edges)
        first=edges[start].pop()
        if not edges[start]:del edges[start]
        points=[start]
        prev=start
        current=first
        steps=1
        while current!=start:
            points.append(current)
            options=edges.get(current)
            if not options:raise ValueError(f"open vector contour at {current}")
            if len(options)==1:next_=options.pop()
            else:
                d=turn((prev,current))
                # Prefer the right turn to keep filled pixels to the right.
                ranked=sorted(options,key=lambda n:
                    [((d+1)%4),d,((d+3)%4),((d+2)%4)].index(turn((current,n))))
                next_=ranked[0]
                options.remove(next_)
            if not options:del edges[current]
            prev,current=current,next_
            steps+=1
            if steps>total+2:raise ValueError("vector contour cycle guard")
        # Keep corners only; exact lattice path without stair-step collinear nodes.
        compact=[]
        n=len(points)
        for i,p in enumerate(points):
            a=points[(i-1)%n];b=points[(i+1)%n]
            if (p[0]-a[0])*(b[1]-p[1])-(p[1]-a[1])*(b[0]-p[0]):
                compact.append(p)
        if len(compact)<4:raise ValueError("contour with fewer than 4 orthogonal corners")
        contours.append(compact)
    assert sum(len(loop) for loop in contours)>0 if total else not contours
    return contours

def path_for(loop,epsilon=0.0):
    vertices=loop
    if epsilon>0 and len(loop)>4:
        arr=np.array(loop,dtype=np.float32).reshape(-1,1,2)
        candidate=cv2.approxPolyDP(arr,epsilon,True).reshape(-1,2)
        if len(candidate)>=3:
            vertices=[(float(x),float(y)) for x,y in candidate]
    def fmt(v):
        return str(int(v)) if int(v)==v else f"{v:.3f}".rstrip("0").rstrip(".")
    path="M"+f"{fmt(vertices[0][0])} {fmt(vertices[0][1])}"
    path+="".join(f"L{fmt(x)} {fmt(y)}" for x,y in vertices[1:])+"Z"
    return path,len(vertices)

def class_mask_and_protections(name,source,mask,base):
    supported=np.all(mask[:,:,:3]==MASK_LABEL,axis=2)&(
        source[:,:,3]==255)&(base[:,:,3]!=0)
    protected=np.zeros(supported.shape,dtype=bool)
    for color in RGBS[name]:
        protected|=np.all(base[:,:,:3]==color,axis=2)
    if name=="Kyoko":protected[263:290,90:112]=True
    supported&=~protected
    return supported,protected

def vectorize(name,variant,eps:float,output:Path):
    source_path=ROOT/(name+"_source.png")
    mask_path=ROOT/(name+"_anime_seg_mask.png")
    base_path=ROOT/(name+"_facet.png")
    target_path=ROOT/(name+"_"+variant+".png")
    manifest=json.loads((ROOT/"v32_evidence_manifest.json").read_text(encoding="utf-8"))
    expected={f["name"]:f["sha256"] for f in manifest["files"]}
    for p in (source_path,mask_path,base_path,target_path):
        if sha(p)!=expected[p.name]:raise ValueError("v33 frozen original SHA mismatch: "+p.name)
    src=rgba(source_path);seg=rgba(mask_path)
    base=rgba(base_path);target=rgba(target_path)
    if src.shape!=base.shape or base.shape!=target.shape or base.shape!=(340,340,4):
        raise ValueError("untrusted image shape")
    allowed,protected=class_mask_and_protections(name,src,seg,base)
    delta=np.any(target!=base,axis=2)
    if np.any(delta&~allowed) or not np.array_equal(target[:,:,3],base[:,:,3]):
        raise ValueError("v32 reference itself violates mask/alpha")
    rgb_values=np.unique(target[:,:,:3][delta].reshape(-1,3),axis=0)
    source_colors={tuple(p) for p in src[:,:,:3][allowed]}
    for rgb in rgb_values:
        if tuple(rgb) not in source_colors:raise ValueError("non-source RGB color")
    paths=[]
    exact_vertices=0;svg_vertices=0;loops_count=0
    for rgb in rgb_values:
        points=delta&np.all(target[:,:,:3]==rgb,axis=2)
        subpaths=[]
        for loop in boundaries(points):
            geometry,vertices=path_for(loop,eps)
            svg_vertices+=vertices;exact_vertices+=len(loop);loops_count+=1
            subpaths.append(geometry)
        if subpaths:
            paths.append(f'<path fill="#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}" fill-rule="evenodd" d="{" ".join(subpaths)}"/>')
    b64=base64.b64encode(base_path.read_bytes()).decode("ascii")
    svg=(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
       f'width="340" height="340" viewBox="0 0 340 340">'
       f'<image x="0" y="0" width="340" height="340" '
       f'href="data:image/png;base64,{b64}"/>'
       + "".join(paths)+"</svg>")
    output.write_text(svg,encoding="utf-8")
    return {
        "case":name,"variant":variant,"epsilon":eps,
        "inputSHA":{p.name:expected[p.name] for p in (
            source_path,mask_path,base_path,target_path)},
        "deltaPixels":int(delta.sum()),"pathCount":len(paths),
        "loops":loops_count,"svgVertices":svg_vertices,
        "exactVertices":exact_vertices,
        "svgBytes":output.stat().st_size,"svgSHA256":sha(output),
        "containsRasterFacetAsBackground":True,
        "contiguousSourcePalette":True,"partSemanticAuthority":False,
        "outputAuthority":False,"allowedPixelCount":int(allowed.sum()),
        "protectedPixelCount":int(protected.sum()),
    }

if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--name",required=True,choices=("Kyoko","Noel","Ririka"))
    parser.add_argument("--variant",default="connected_fine",choices=("connected_fine","connected_coarse"))
    parser.add_argument("--epsilon",required=True,type=float)
    parser.add_argument("--out",required=True,type=Path)
    a=parser.parse_args()
    a.out.parent.mkdir(parents=True,exist_ok=True)
    if a.out.exists():raise FileExistsError("will not overwrite existing SVG")
    report=vectorize(a.name,a.variant,a.epsilon,a.out)
    print("V33_VECTOR",json.dumps(report,ensure_ascii=False),flush=True)
