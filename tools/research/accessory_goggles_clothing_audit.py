"""Research-only spatial diagnosis: accessory mask vs actual visible goggles,
and clothing source-mask RGB/pixel-cell outline gaps. No generative edits.
"""
import argparse,json,os,sys
from pathlib import Path
import numpy as np,cv2
from PIL import Image,ImageDraw
from xml.etree import ElementTree as ET
from semantic_art_mixer_v1 import load_assets,sha256
from semantic_art_mixer_v3_source_masks import load_observed_masks
from remove_subject_skin_underlay import NS
from bangs_cell_vertex_reduction import polygons
def stats(mask):
    n,l,s,c=cv2.connectedComponentsWithStats(mask.astype(np.uint8),8)
    return [{"pixels":int(s[i,cv2.CC_STAT_AREA]),"xywh":s[i,:4].astype(int).tolist()} for i in range(1,n) if s[i,cv2.CC_STAT_AREA]>=3]
def main():
    p=argparse.ArgumentParser()
    for name in ("root","prior","out"):p.add_argument("--"+name,type=Path,required=True)
    a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    src,_,_=load_assets(a.root);masks,_=load_observed_masks()
    acc=masks["accessory_or_held_object"]&masks["subject"]
    clothing=masks["major_clothing"]&masks["subject"]
    lower=masks["lower_body"]&masks["subject"]
    # Human-observable goggles region, a rectangular diagnostic, NOT a
    # claimed ground-truth segment. Report original-mask intersections only.
    roi=np.zeros(acc.shape,bool);roi[38:104,104:241]=True
    goggles_acc=acc&roi
    scene=ET.parse(a.prior/"part_owned_tonal_hair_scene.svg").getroot()
    report={"accessory_mask_pixels":int(acc.sum()),
       "accessory_connected_components":stats(acc),
       "goggles_roi_xyxy":[104,38,241,104],
       "goggles_roi_accessory_mask_pixels":int(goggles_acc.sum()),
       "goggles_roi_is_NOT_ground_truth":True,"clothing":[]}
    canvas=Image.new("RGB",(1020,720),"#eee")
    original=src.convert("RGB")
    for i,mask in enumerate([acc,clothing,lower]):
        over=original.copy()
        rgb=np.asarray(over).copy()
        rgb[mask]=(0.55*rgb[mask]+0.45*np.array((50,215,95))).astype(np.uint8)
        panel=Image.fromarray(rgb)
        canvas.paste(panel,(i*340,0))
        ImageDraw.Draw(canvas).text((i*340+8,345),["ACCESSORY MASK","MAJOR CLOTHING MASK","LOWER BODY MASK"][i],fill="#222")
    for i,part in enumerate(("major_clothing","lower_body")):
        mask=clothing if i==0 else lower
        data,n,verts=polygons(mask,0.35)
        r=ET.Element("{%s}svg"%NS,{"viewBox":"0 0 340 340","width":"340","height":"340"})
        ET.SubElement(r,"{%s}path"%NS,{"d":data,"fill":"#4d81a0","fill-rule":"evenodd","data-part":part})
        path=out/(part+"_mask_fidelity.svg");ET.ElementTree(r).write(path,encoding="utf-8",xml_declaration=True)
        renderdir=Path(os.environ.get("LOCALAPPDATA",""))/"Minimalizer/research/resvg-py-0.5.0"
        sys.path.insert(0,str(renderdir));import resvg_py
        png=out/(part+"_mask_fidelity.png");png.write_bytes(resvg_py.svg_to_bytes(svg_path=str(path),width=340,height=340))
        rendered=np.asarray(Image.open(png).convert("RGBA").getchannel("A"))>=128
        entry={"part":part,"mask_pixels":int(mask.sum()),"pixel_cell_covered":int((mask&rendered).sum()),
              "pixel_cell_missing":int((mask&~rendered).sum()),"pixel_cell_extra":int((~mask&rendered).sum()),"vertices":verts,"contours":n}
        report["clothing"].append(entry)
        white=Image.new("RGBA",(340,340),"#f5eee4");white.alpha_composite(Image.open(png).convert("RGBA"))
        canvas.paste(white.convert("RGB"),(i*340,370))
    draw=ImageDraw.Draw(canvas)
    draw.rectangle((104,38,241,104),outline="#ffef15",width=2)
    visual=out/"compare_accessory_clothing_masks.png";canvas.save(visual,optimize=True)
    report["not_production"]=True
    report["artifacts"]=[{"name":q.name,"sha256":sha256(q)} for q in sorted(out.iterdir()) if q.is_file()]
    (out/"manifest.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({k:report[k] for k in ("accessory_mask_pixels","accessory_connected_components","goggles_roi_accessory_mask_pixels","clothing")}))
if __name__=="__main__":main()
