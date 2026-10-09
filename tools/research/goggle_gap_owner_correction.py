"""Correct source-goggle-gap ownership claims against real masks and verified bangs.

A warm/orange source pixel is NOT automatically a foreground bang. Record
source mask observations separately from semantic owner, and fail closed.
"""
import argparse,json,sys
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from semantic_art_mixer_v1 import load_assets,sha256
from semantic_art_mixer_v3_source_masks import load_observed_masks
from bangs_continuity_source_bridge import extract
from goggle_bangs_occlusion_evidence import analyze

def check(source,mask,original_masks,fringe):
    rgb=np.asarray(source.convert("RGB"),np.uint8)
    _,gaps=analyze(source,mask)
    result=[]
    for gap in gaps:
        p,q=gap["nearest_endpoints"]
        n=gap["sample_count"]
        xs=np.rint(np.linspace(p[0],q[0],n)).astype(int)
        ys=np.rint(np.linspace(p[1],q[1],n)).astype(int)
        pix=rgb[ys,xs];hsv=cv2.cvtColor(pix.reshape(-1,1,3),cv2.COLOR_RGB2HSV).reshape(-1,3)
        orange=(hsv[:,0]<=24)&(hsv[:,1]>=105)
        labels={k:int(np.sum(original_masks[k][ys,xs])) for k in ("hair","face","accessory_or_held_object","subject")}
        on_verified=fringe[ys,xs]
        row={"pair":gap["pair"],"source_endpoints":[p,q],
           "sampled_source_xy":[[int(x),int(y)] for x,y in zip(xs,ys)],
           "source_rgb":[v.tolist() for v in pix],
           "source_orange_sample_count":int(orange.sum()),
           "source_hair_mask_count":labels["hair"],
           "source_face_mask_count":labels["face"],
           "source_accessory_mask_count":labels["accessory_or_held_object"],
           "certified_inter_eye_fringe_count":int(np.sum(on_verified)),
           "candidate_semantic_owner":"unverified_warm_material" if orange.any() else "unverified_pale_material",
           "occlusion_direction_verified":False,"can_bridge":False}
        # A certified central bang is bounded to y>=100. At y<100 a
        # source-orange sample cannot be called that specific strand.
        if any(y<100 for y in ys) and on_verified.any():
            raise AssertionError("Verified inter-eye bang outside reviewed source ROI")
        result.append(row)
    return result

def main():
    ap=argparse.ArgumentParser()
    for key in ("root","source","mask","out"):ap.add_argument("--"+key,type=Path,required=True)
    a=ap.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    src=Image.open(a.source).convert("RGB");rim=Image.open(a.mask).convert("L")
    canonical,_,_=load_assets(a.root)
    if sha256(a.source)!=sha256(a.root/"SA1041_FullCharacterSVG_20261008"/"original_inputs"/"GC001_source.png"):
        raise ValueError("Canonical original source hash mismatch")
    masks,_=load_observed_masks()
    _,fringe=extract(canonical,masks)
    rows=check(src,rim,masks,fringe)
    # Visual diagnostic: three magnified source crops, nearest source pixels
    # and original mask occupancy at each selected segment.
    figure=Image.new("RGB",(1050,420),"#f1f1ef")
    for i,row in enumerate(rows):
        pts=row["sampled_source_xy"];xs=[p[0] for p in pts];ys=[p[1] for p in pts]
        x0=max(0,min(xs)-22);y0=max(0,min(ys)-22);x1=min(340,max(xs)+23);y1=min(340,max(ys)+23)
        crop=src.crop((x0,y0,x1,y1)).resize((320,320),Image.Resampling.NEAREST)
        pen=ImageDraw.Draw(crop)
        for j,(x,y) in enumerate(pts):
            px=int((x-x0)*320/(x1-x0));py=int((y-y0)*320/(y1-y0))
            pen.ellipse((px-3,py-3,px+3,py+3),outline="#00eadb",width=2)
        figure.paste(crop,(i*350+8,10))
        d=ImageDraw.Draw(figure)
        d.text((i*350+8,337),f"PAIR {row['pair']} ORANGE {row['source_orange_sample_count']}/{len(pts)}",fill="#232b27")
        d.text((i*350+8,355),f"HAIR MASK {row['source_hair_mask_count']} / BANG {row['certified_inter_eye_fringe_count']}",fill="#232b27")
        d.text((i*350+8,374),"OWNER UNVERIFIED / NO BRIDGE",fill="#9a3434")
    figure.save(out/"gap_semantic_owner_review.png",optimize=True)
    report={"status":"SEMANTIC_OWNER_NOT_VERIFIED","source_sha256":sha256(a.source),
       "rim_mask_sha256":sha256(a.mask),"gap_samples":rows,
       "corrected_prior_overclaim":"orange at head-goggle gap is not necessarily the verified inter-eye bang",
       "all_occlusion_directions_verified":False,"goggle_bridge_authorized":False,
       "filled_goggle_svg_generated":False,"production_changed":False,
       "artifacts":[{"name":p.name,"sha256":sha256(p)} for p in sorted(out.iterdir()) if p.suffix==".png"]}
    (out/"manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],"gaps":[{k:r[k] for k in ("pair","source_orange_sample_count","source_hair_mask_count","source_face_mask_count","certified_inter_eye_fringe_count")} for r in rows]}))
if __name__=="__main__":main()
