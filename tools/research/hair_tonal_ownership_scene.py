"""Research-only source-owned whole-hair colored Pixel-Cell integration.

Do not append a single large orange hair plate above accessories. Replace
the original hair layers in-place (same z-order), then preserve the separately
certified 694px central fringe overlay from the prior composite. Never draw a
face/subject underlay or infer unobserved skin.
"""
import argparse,json,os,sys,copy
from pathlib import Path
from xml.etree import ElementTree as ET
import numpy as np,cv2
from PIL import Image,ImageDraw
from semantic_art_mixer_v1 import load_assets,sha256
from semantic_art_mixer_v3_source_masks import load_observed_masks
from bangs_continuity_source_bridge import extract
from remove_subject_skin_underlay import NS,region_colormasks,CAP
from bangs_cell_vertex_reduction import polygons

def layers_from_source(source,masks):
    observed=masks["hair"]&masks["subject"]
    missing,_=extract(source,masks)
    corrected=observed|missing
    # The verified forelock is kept independently on top from the prior
    # certified scene: exclude its 390 face-misclassified pixels from
    # wide-hair tonal paths to prevent flattening its three existing tones.
    tone_layers=region_colormasks(source,observed,CAP["hair"])
    return observed,missing,corrected,tone_layers

def replace_hair(original_tree,tonal_layers):
    root=original_tree.getroot()
    existing=[node for node in list(root) if node.tag=="{%s}path"%NS and node.get("data-part")=="hair" and node.get("data-layer")!="source-bang-cell-verified"]
    if not existing:raise ValueError("No prior hair nodes at expected original scene layer")
    positions=[list(root).index(el) for el in existing]
    index=min(positions)
    for el in existing:root.remove(el)
    generated=[]
    for mask,color,kind in tonal_layers:
        d,n,v=polygons(mask,0.35)
        if not d:continue
        element=ET.Element("{%s}path"%NS,{"d":d,"fill":"#%02x%02x%02x"%color,
            "fill-rule":"evenodd","data-part":"hair",
            "data-layer":"source-owned-cell-"+kind})
        root.insert(index+len(generated),element);generated.append((n,v))
    if not generated:raise ValueError("Source-tonal hair geometry lost")
    forbidden=(root.findall(".//{%s}path[@data-part='face']"%NS) or
               root.findall(".//{%s}path[@data-part='subject']"%NS) or
               root.findall(".//{%s}image"%NS))
    if forbidden:raise AssertionError("Face plate/subject skin/raster forbidden")
    preserved=[node for node in root if node.get("data-layer")=="source-bang-cell-verified"]
    if len(preserved)!=3:raise AssertionError("Three verified fringe tone layers not preserved")
    return generated

def main():
    p=argparse.ArgumentParser()
    for key in ("root","prior","out"):p.add_argument("--"+key,type=Path,required=True)
    a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    source,_,_=load_assets(a.root);masks,_=load_observed_masks()
    observed,missing,corrected,tones=layers_from_source(source,masks)
    prior=a.prior/"subject_with_verified_bangs.svg"
    tree=ET.parse(prior)
    generated=replace_hair(tree,tones)
    svg=out/"part_owned_tonal_hair_scene.svg";tree.write(svg,encoding="utf-8",xml_declaration=True)
    folder=Path(os.environ.get("LOCALAPPDATA",""))/"Minimalizer/research/resvg-py-0.5.0"
    sys.path.insert(0,str(folder));import resvg_py
    before=out/"scene_before.png";after=out/"scene_tonal_hair.png"
    before.write_bytes(resvg_py.svg_to_bytes(svg_path=str(prior),width=340,height=340))
    after.write_bytes(resvg_py.svg_to_bytes(svg_path=str(svg),width=340,height=340))
    old=np.asarray(Image.open(before).convert("RGB"))
    new=np.asarray(Image.open(after).convert("RGB"))
    delta=np.any(old!=new,axis=2)
    guard=cv2.dilate(observed.astype(np.uint8),np.ones((5,5),np.uint8))>0
    outside=int((delta&~guard).sum())
    if outside:raise AssertionError(f"Hair replacement affected {outside} pixels outside original hair mask")
    # Compare topologies and color source provenance independently, not
    # conflate full RGB scenery with a semantic source hair mask.
    palette=[color for _,color,_ in tones]
    rgb=np.asarray(source.convert("RGB"))
    actual={tuple(x) for x in rgb[observed]}
    if not all(tuple(c) in actual for c in palette):
        raise AssertionError("Hair palette contains unobserved RGB")
    gallery=Image.new("RGB",(1040,400),"#f0efec")
    for i,im in enumerate((source,Image.fromarray(old),Image.fromarray(new))):
        gallery.paste(im.convert("RGB"),(10+i*345,15))
    d=ImageDraw.Draw(gallery)
    for i,s in enumerate(("ORIGINAL","PRIOR / VERIFIED FRINGE","SOURCE-TONAL PIXEL-CELL HAIR")):
        d.text((12+i*345,363),s,fill="#26342c")
    compare=out/"compare_tonal_hair_scene.png";gallery.save(compare,optimize=True)
    manifest={"status":"RESEARCH_HOLD","source_hair_pixels":int(observed.sum()),
      "derived_hair_pixels":int(corrected.sum()),
      "prior_fringe_misclassified_pixels":int(missing.sum()),
      "tonal_layers":len(generated),"contours":sum(x[0] for x in generated),
      "vertices":sum(x[1] for x in generated),
      "scene_changed_pixels":int(delta.sum()),"changed_outside_observed_hair":outside,
      "preserved_verified_fringe_layers":3,
      "hair_palette_original_RGB":[list(c) for c in palette],
      "full_character_golden_pass":False,"face_unresolved":True,
      "files":[{"name":q.name,"sha256":sha256(q)} for q in (svg,before,after,compare)]}
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({k:manifest[k] for k in ("status","tonal_layers","contours","vertices","scene_changed_pixels","changed_outside_observed_hair","preserved_verified_fringe_layers")}))
if __name__=="__main__":main()
