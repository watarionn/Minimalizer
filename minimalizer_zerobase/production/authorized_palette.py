from __future__ import annotations
from typing import Any, Mapping
import numpy as np

class PaletteRoleError(RuntimeError):
    pass

def _hex(rgb: np.ndarray) -> str:
    v=np.clip(np.rint(rgb),0,255).astype(np.uint8)
    return "#%02x%02x%02x"%tuple(int(x) for x in v)

def _topology_pixels(rgb: np.ndarray, mask: Mapping[str, Any]) -> tuple[np.ndarray, np.ndarray]:\n    """Return bbox pixels plus deterministic 4x4 occupancy weights."""\n    H,W,_=rgb.shape; x,y,w,h=[int(round(float(v))) for v in mask["bbox"]]\n    x0,y0=max(0,x),max(0,y); x1,y1=min(W,x+w),min(H,y+h)\n    region=rgb[y0:y1,x0:x1]\n    if region.size==0: return region.reshape(-1,3), np.empty((0,),dtype=float)\n    desc=mask.get("mask_descriptor"); occ=desc.get("occupancy") if isinstance(desc,Mapping) and desc.get("grid")==[4,4] else None\n    if not isinstance(occ,list) or len(occ)!=4: return region.reshape(-1,3), np.ones(region.shape[:2],dtype=float).reshape(-1)\n    weights=np.zeros(region.shape[:2],dtype=float); ys=np.linspace(0,region.shape[0],5,dtype=int); xs=np.linspace(0,region.shape[1],5,dtype=int)\n    for gy in range(4):\n        for gx in range(4):\n            try: v=max(0.0,float(occ[gy][gx]))\n            except (TypeError,ValueError,IndexError): v=0.0\n            weights[ys[gy]:ys[gy+1],xs[gx]:xs[gx+1]]=v\n    flat=region.reshape(-1,3); wf=weights.reshape(-1); keep=wf>0\n    return (flat[keep],wf[keep]) if np.any(keep) else (flat,np.ones(len(flat),dtype=float))\n\ndef extract_authorized_palette(
    image: np.ndarray,
    semantic_masks: Mapping[str, Mapping[str, Any]],
    *,
    bins_per_channel: int = 8,
) -> dict[str,str]:
    """Deterministic dominant-color extraction inside authorized feature regions.

    Semantic ownership comes only from semantic_masks. Color extraction cannot
    add/relabel features and uses no Golden raster or learned model.
    """
    rgb=np.asarray(image)
    if rgb.ndim!=3 or rgb.shape[2]!=3 or rgb.dtype!=np.uint8:
        raise PaletteRoleError("image must be uint8 RGB")
    if bins_per_channel < 2 or bins_per_channel > 16:
        raise PaletteRoleError("bins_per_channel must be in [2,16]")
    out={}
    H,W,_=rgb.shape
    for fid in sorted(semantic_masks):
        mask=semantic_masks[fid]
        if mask.get("authorized") is not True:
            raise PaletteRoleError(f"semantic mask is not authorized: {fid}")
        box=mask.get("bbox")
        if not isinstance(box,(list,tuple)) or len(box)!=4:
            raise PaletteRoleError(f"authorized semantic mask requires bbox: {fid}")
        x,y,w,h=[int(round(float(v))) for v in box]
        x0,y0=max(0,x),max(0,y);x1,y1=min(W,x+w),min(H,y+h)
        pixels=rgb[y0:y1,x0:x1].reshape(-1,3)
        if pixels.size==0:
            raise PaletteRoleError(f"empty authorized region: {fid}")
        q=np.minimum((pixels.astype(np.int32)*bins_per_channel)//256,bins_per_channel-1)
        keys=q[:,0]*bins_per_channel*bins_per_channel+q[:,1]*bins_per_channel+q[:,2]
        counts=np.bincount(keys,weights=weights,minlength=bins_per_channel**3)
        winner=int(np.flatnonzero(counts==counts.max())[0])
        chosen=pixels[keys==winner]
        out[fid]=_hex(np.median(chosen,axis=0))
    return out


def extract_authorized_palette_roles(
    image: np.ndarray,
    semantic_masks: Mapping[str, Mapping[str, Any]],
    *,
    bins_per_channel: int = 8,
) -> dict[str, dict[str, str | None]]:
    """Return dominant plus deterministic local accent for each authorized feature.

    Accent is selected from quantized bins by chroma * sqrt(population), excluding
    the dominant bin. It is evidence about color only and cannot create features.
    """
    rgb=np.asarray(image)
    dominant=extract_authorized_palette(rgb,semantic_masks,bins_per_channel=bins_per_channel)
    H,W,_=rgb.shape; out={}
    for fid in sorted(semantic_masks):
        x,y,w,h=[int(round(float(v))) for v in semantic_masks[fid]["bbox"]]
        pixels, weights = _topology_pixels(rgb, semantic_masks[fid])
        q=np.minimum((pixels.astype(np.int32)*bins_per_channel)//256,bins_per_channel-1)
        keys=q[:,0]*bins_per_channel*bins_per_channel+q[:,1]*bins_per_channel+q[:,2]
        candidates=[]
        for key in np.unique(keys):
            chosen=pixels[keys==key]
            med=np.median(chosen,axis=0)
            chroma=float(med.max()-med.min())
            population=float(weights[keys==key].sum())\n            score=chroma*np.sqrt(population)
            hx=_hex(med)
            if hx != dominant[fid]:
                candidates.append((score,int(len(chosen)),-int(key),hx))
        candidates.sort(reverse=True)
        accent=candidates[0][3] if candidates and candidates[0][0] > 0 else None
        out[fid]={"dominant":dominant[fid],"accent":accent}
    return out
