"""GC001: inspect 2 missing strand pixels and stitch verified hair-only paths.

Research-only. No face or subject plate, no raster embeds, no new skin,
no generated content. Base scene has an unresolved face and remains NO-GO.
"""
import argparse,json,os,sys
from pathlib import Path
from xml.etree import ElementTree as ET
import numpy as np,cv2
from PIL import Image,ImageDraw
from semantic_art_mixer_v1 import load_assets,sha256
from semantic_art_mixer_v3_source_masks import load_observed_masks
from bangs_continuity_source_bridge import extract
from remove_subject_skin_underlay import NS

def alpha(path):
    return np.asarray(Image.open(path).convert("RGBA").getchannel("A"))>=128

def inspect(source_mask,output_mask):
    missing=np.argwhere(source_mask&~output_mask)
    excess=np.argwhere(output_mask&~source_mask)
    return {"missing_yx":missing.astype(int).tolist(),
            "excess_yx":excess.astype(int).tolist(),
            "source_total":int(source_mask.sum()),
            "covered":int((source_mask&output_mask).sum())}

def stitch(base,fringe,out):
    tree=ET.parse(base);root=tree.getroot()
    src=ET.parse(fringe).getroot()
    pieces=src.findall(".//{%s}path"%NS)
    if not pieces:raise ValueError("No verified fringe paths")
    if root.findall(".//{%s}path[@data-part='subject']"%NS) or root.findall(".//{%s}path[@data-part='face']"%NS):
        raise AssertionError("Implicit face plate detected")
    for p in pieces:
        if p.get("data-part")!="hair" or p.get("d") is None:
            raise AssertionError("Unexpected fringe provenance")
        ET.SubElement(root,"{%s}path"%NS,{
          "d":p.get("d"),"fill":p.get("fill"),
          "fill-rule":"evenodd","data-part":"hair",
          "data-layer":"source-bang-cell-verified",
          "data-provenance":"GC001-694px-epsilon-0.35"})
    ET.ElementTree(root).write(out,encoding="utf-8",xml_declaration=True)
    result=ET.parse(out).getroot()
    if result.findall(".//{%s}image"%NS) or result.findall(".//{%s}path[@data-part='subject']"%NS):
        raise AssertionError("Raster or face plate inserted")
    return len(pieces)

def main():
    p=argparse.ArgumentParser()
    for k in ("root","fringe","prior","out"):p.add_argument("--"+k,type=Path,required=True)
    a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    src,_,_=load_assets(a.root);masks,_=load_observed_masks()
    _,source=extract(src,masks)
    source_svg=a.fringe/"eps_0p35.svg"
    manifest=json.loads((a.fringe/"manifest.json").read_text(encoding="utf-8"))
    saved=[r for r in manifest["candidates"] if r["epsilon"]==0.35]
    if len(saved)!=1 or saved[0]["svg_sha"]!=sha256(source_svg):
        raise ValueError("Selected bang SVG SHA mismatch")
    rootrender=Path(os.environ.get("LOCALAPPDATA",""))/"Minimalizer/research/resvg-py-0.5.0"
    if not rootrender.is_dir():raise RuntimeError("No isolated resvg renderer")
    sys.path.insert(0,str(rootrender));import resvg_py
    solo=out/"verified_fringe.png"
    solo.write_bytes(resvg_py.svg_to_bytes(svg_path=str(source_svg),width=340,height=340))
    evidence=inspect(source,alpha(solo))
    if evidence["covered"]!=692 or len(evidence["excess_yx"])!=0:
        raise AssertionError("Historical isolated hair footprint changed")
    # The full scene is deliberately incomplete; only repair original hair pixels.
    combined=out/"subject_with_verified_bangs.svg"
    count=stitch(a.prior/"character_part_vector.svg",source_svg,combined)
    if count>4:raise ValueError("Unexpected number of color layers")
    png=out/"subject_with_verified_bangs.png"
    png.write_bytes(resvg_py.svg_to_bytes(svg_path=str(combined),width=340,height=340))
    oldsvg=a.prior/"character_part_vector.svg"
    original_render=out/"subject_before_bangs.png"
    original_render.write_bytes(resvg_py.svg_to_bytes(svg_path=str(oldsvg),width=340,height=340))
    base=np.asarray(Image.open(original_render).convert("RGB"))
    revised=np.asarray(Image.open(png).convert("RGB"))
    diff=np.any(base!=revised,axis=2)
    within=cv2.dilate(source.astype(np.uint8),np.ones((5,5),np.uint8))>0
    far=int((diff&~within).sum())
    if far:raise AssertionError("Unrelated painting outside observed hair ROI")
    canvas=Image.new("RGB",(1040,405),"#f2f1ee");draw=ImageDraw.Draw(canvas)
    for i,im in enumerate([src,Image.fromarray(base),Image.fromarray(revised)]):
        canvas.paste(im.convert("RGB"),(10+345*i,14))
    for i,label in enumerate(("ORIGINAL","PART SVG BEFORE","PART SVG + VERIFIED HAIR")):
        draw.text((12+345*i,363),label,fill="#203027")
    comparison=out/"compare_integrated_bangs.png"
    canvas.save(comparison,optimize=True)
    result={"stage":"Two Pixel Fringe Audit + Full Scene Integration",
      "fringe_source_pixels":694,"missing_pixel_yx":evidence["missing_yx"],
      "remaining_missing_count":len(evidence["missing_yx"]),
      "rendered_fringe_covered":evidence["covered"],"rendered_fringe_extra":len(evidence["excess_yx"]),
      "composite_svg_added_hair_layers":count,"full_scene_changed_pixels":int(diff.sum()),
      "changed_outside_2px_source_neighborhood":far,
      "no_face_or_subject_opaque_plate":True,"full_character_golden_pass":False,
      "face_still_unresolved":True,
      "artifacts":[{"name":f.name,"sha256":sha256(f)} for f in sorted(out.iterdir()) if f.suffix in (".svg",".png")]}
    (out/"manifest.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({k:result[k] for k in ("missing_pixel_yx","rendered_fringe_covered","rendered_fringe_extra","composite_svg_added_hair_layers","full_scene_changed_pixels","changed_outside_2px_source_neighborhood")}))
if __name__=="__main__":main()
