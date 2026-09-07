from dataclasses import dataclass
import colorsys,numpy as np
from ..models import PaletteColor,Region
@dataclass
class DesignPaletteEntry:
    palette_id:int; role:str; source_rgb:tuple[int,int,int]; output_rgb:tuple[int,int,int]
def _blend(a,b,t):return tuple(int(round(a[i]*(1-t)+b[i]*t)) for i in range(3))
def build_design_palette(palette,harmony_strength=.20,has_background=True):
    if not palette:return [],{}
    dom=max(palette,key=lambda p:p.ratio); raw=[]
    for p in palette:
        _,s,v=colorsys.rgb_to_hsv(*(x/255 for x in p.rgb))
        role=("background" if has_background and p.id==dom.id and p.ratio>=.20 else "accent" if s>=.58 and p.ratio<=.18 else "dark" if v<=.34 else "light" if v>=.78 and s<=.38 else "mid")
        raw.append((p,role))
    anchors={}
    for role in {"background","accent","dark","light","mid"}:
        g=[(p,r) for p,r in raw if r==role]
        if g:
            total=sum(max(p.ratio,.001) for p,_ in g)
            anchors[role]=tuple(int(round(sum(p.rgb[k]*max(p.ratio,.001) for p,_ in g)/total)) for k in range(3))
    entries=[];mapping={}
    for p,role in raw:
        t=harmony_strength*(.55 if role=="accent" else 1)
        out=_blend(p.rgb,anchors.get(role,p.rgb),t);mapping[p.id]=out;entries.append(DesignPaletteEntry(p.id,role,p.rgb,out))
    return entries,mapping
def apply_design_palette(regions,mapping):
    for r in regions:
        if r.palette_id in mapping:r.color_rgb=mapping[r.palette_id]
    return regions
