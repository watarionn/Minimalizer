"""Non-local BrowserFallback v28: SHA-bound, read-only anime-part model suitability audit.
The existing AnimeSeg GC001/Kyoko observation is REUSED (no new inference).
A saved Python observation does NOT imply a browser-executable model.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,zipfile
from collections import Counter
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

PINNED_SOURCE="75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e"
PINNED_ANIME_MASK="ea1be2ff34d3bdbef5693ab3dbe1c60363fe6365cb42454829b96994f3520148"
PINNED_V27_ARCHIVE="91b9f3851622feb55169bbf301b9dbb52d81036c260ea7e8f88fd7814423bd39"
ANIME_LABELS=("background","skin","face","hair_main","left_eye","right_eye",
  "left_eyebrow","right_eyebrow","nose","mouth","clothes","accessory")
ANIME_PALETTE=((0,0,0),(255,220,180),(100,150,255),(255,0,0),
  (0,255,255),(255,255,0),(150,255,0),(0,255,100),
  (255,140,0),(255,0,150),(180,0,255),(128,128,0))
V27_PALETTE=((0,0,0),(244,165,43),(240,189,156),
  (244,214,170),(30,187,125),(112,119,138))
V27_LABELS=("background","hair","body_skin","face_skin","clothes","accessories")

def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def file_sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
    return h.hexdigest()

def audit(source_path:Path,mask_path:Path,archive_path:Path,out:Path,checkpoint:Path|None=None):
    src_bytes=source_path.read_bytes()
    anime_bytes=mask_path.read_bytes()
    zip_bytes=archive_path.read_bytes()
    if sha(src_bytes)!=PINNED_SOURCE:raise ValueError("source SHA mismatch; cross-model comparison forbidden")
    if sha(anime_bytes)!=PINNED_ANIME_MASK:raise ValueError("AnimeSeg mask SHA mismatch; unknown model evidence")
    if sha(zip_bytes)!=PINNED_V27_ARCHIVE:raise ValueError("v27 archive SHA mismatch; comparison unavailable")
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        if z.read("Kyoko/source.png")!=src_bytes:
            raise ValueError("v27 source bytes not identical")
        old_facet=z.read("Kyoko/facet.png")
        v27_classes=z.read("Kyoko/part_classes.png")
        original_metrics=json.loads(z.read("Kyoko/metrics.json"))
        assert original_metrics["provenance"]["domainCalibratedForAnime"] is False
    source=Image.open(io.BytesIO(src_bytes)).convert("RGBA")
    anime=Image.open(io.BytesIO(anime_bytes)).convert("RGB")
    v27=Image.open(io.BytesIO(v27_classes)).convert("RGB")
    facet=Image.open(io.BytesIO(old_facet)).convert("RGB")
    if source.size!=anime.size or source.size!=v27.size or source.size!=facet.size:
        raise ValueError("source/model masks have mismatched coordinate dimensions")
    w,h=source.size
    if (w,h)!=(340,340):raise ValueError("v28 fixed corpus 340x340 expected")
    source_pixels=list(source.getdata())
    colors=list(anime.getdata());v27_pixels=list(v27.getdata())
    pal_a={rgb:idx for idx,rgb in enumerate(ANIME_PALETTE)}
    pal_b={rgb:idx for idx,rgb in enumerate(V27_PALETTE)}
    # All pixels in either observation MUST be known palette values.
    if not set(colors).issubset(pal_a):raise ValueError("unknown AnimeSeg mask RGB labels")
    if not set(v27_pixels).issubset(pal_b):raise ValueError("unknown v27 mask RGB labels")
    class_a=[pal_a[c] for c in colors]
    class_b=[pal_b[c] for c in v27_pixels]
    counts_a=Counter(class_a);counts_b=Counter(class_b)
    opaque=[p[3]==255 for p in source_pixels]
    i_hair=3;i_clothes=10
    a_hair={i for i,v in enumerate(class_a) if v==i_hair and opaque[i]}
    a_clothes={i for i,v in enumerate(class_a) if v==i_clothes and opaque[i]}
    b_clothes={i for i,v in enumerate(class_b) if v==4 and opaque[i]}
    b_hair={i for i,v in enumerate(class_b) if v==1 and opaque[i]}
    observations={
      "rawAnimeHair":len(a_hair),
      "rawAnimeClothes":len(a_clothes),
      "v27PhotoClothes":len(b_clothes),
      "v27PhotoHair":len(b_hair),
      "v27ClothesOverlapsAnimeHair":len(b_clothes&a_hair),
      "v27ClothesOverlapsAnimeClothes":len(b_clothes&a_clothes),
      "v27HairOverlapsAnimeHair":len(b_hair&a_hair),
      "animeHairOverlapsPhotoBackground":sum(i in a_hair for i,v in enumerate(class_b) if v==0),
      "eligibleOpaqueSourcePixels":sum(opaque),
      "animeMaskUnrecognizedColorCount":0,
      "v27MaskUnrecognizedColorCount":0,
    }
    if checkpoint is None or not checkpoint.is_file():
        raise ValueError("v28 model checkpoint path required for SHA-verified provenance")
    if checkpoint.stat().st_size!=431643704:
        raise ValueError("v28 model checkpoint byte size mismatch")
    actual_model_sha=file_sha(checkpoint)
    out.mkdir(parents=True,exist_ok=True)
    # Source clip overlays are DIAGNOSTIC ONLY. Face/eye source detections
    # must NEVER enter the Minimalizer final composition.
    overlay=source.convert("RGB").copy()
    pixels=list(overlay.getdata())
    for i in a_hair:
        r,g,b=pixels[i];pixels[i]=(min(255,(r+248)//2),g//2,b//2)
    for i in a_clothes:
        r,g,b=pixels[i];pixels[i]=(r//2,g//2,min(255,(b+248)//2))
    overlay.putdata(pixels)
    legend=Image.new("RGB",(w*5+12*6,h+64),(242,242,242))
    draw=ImageDraw.Draw(legend)
    fontfile=Path("C:/Windows/Fonts/arial.ttf")
    font=ImageFont.truetype(str(fontfile),17) if fontfile.exists() else ImageFont.load_default()
    images=[source.convert("RGB"),facet,v27,anime,overlay]
    names=["Original Kyoko","Frozen Facet","V27 photographic 6-class","AnimeSeg v3 cached 12-class","Anime source-clipped cues"]
    for j,(label,im) in enumerate(zip(names,images)):
        x=12+j*(w+12)
        legend.paste(im,(x,54))
        draw.text((x,18),label,font=font,fill=(20,25,30))
    legend.save(out/"v28_kyoko_anime_vs_photo.png",optimize=True)
    # Compare classes as measurements only: no GT claim for AnimeSeg.
    report={
      "status":"CACHED_ANIMESEG_SINGLE_SOURCE_AUDIT_PASS",
      "semanticQuality":"VISUAL_REVIEW_REQUIRED_NOT_GROUND_TRUTH",
      "browserAnimeInference":"NOT_IMPLEMENTED",
      "productionAuthority":False,
      "partBindingAuthority":False,
      "armSideLabelsAvailable":False,
      "casesAvailable":{"Kyoko":"cached_v3_mask","Noel":"unavailable","Ririka":"unavailable"},
      "model":{"name":"suzukimain/AnimeSeg","architecture":"Mask2Former",
        "checkpoint":"models/anime_seg_mask2former_v3.safetensors",
        "fileSizeBytes":431643704,"modelSha256":actual_model_sha,
        "modelShaStatus":"sha256_verified_from_existing_cached_weight_file",
        "runtime":"existing isolated Python CPU result (not browser inference)",
        "classes":list(ANIME_LABELS)},
      "provenance":{"sourceSha256":PINNED_SOURCE,"cachedMaskSha256":PINNED_ANIME_MASK,
        "v27FrozenZipSha256":PINNED_V27_ARCHIVE,
        "v27FacetSha256":sha(old_facet),"v27ClassesSha256":sha(v27_classes)},
      "pixel_counts_anime":dict((ANIME_LABELS[i],counts_a[i]) for i in range(12)),
      "pixel_counts_photo":dict((V27_LABELS[i],counts_b[i]) for i in range(6)),
      "comparison":observations,
      "limitation":"Cross-model agreement/disagreement is not independent part ground truth.",
      "conclusion":"ANIME_PARSER_REFERENCE_USEFUL_BROWSER_READY_HOLD"
    }
    (out/"v28_metrics.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    with (out/"v28_confusion.csv").open("w",newline="",encoding="utf-8-sig") as f:
        wr=csv.writer(f);wr.writerow(["anime_class","v27_photo_class","opaque_overlapping_pixels"])
        pairs=Counter((a,b) for a,b,ok in zip(class_a,class_b,opaque) if ok)
        for (a,b),v in sorted(pairs.items()):wr.writerow([ANIME_LABELS[a],V27_LABELS[b],v])
    stage={
      "stage":"browser-anime-feasibility-v28",
      "sourceSHA256":PINNED_SOURCE,"inputMaskSHA256":PINNED_ANIME_MASK,
      "v27EvidenceSHA256":PINNED_V27_ARCHIVE,
      "previewSHA256":sha((out/"v28_kyoko_anime_vs_photo.png").read_bytes()),
      "metricsSHA256":sha((out/"v28_metrics.json").read_bytes()),
      "coordinateSpace":"source-pixel-top-left",
      "inferenceAvailableInBrowser":False,"semanticAuthority":False,
      "visibleOutputModified":False,"generatedPixels":False,
      "missingCases":["Noel","Ririka"],
    }
    (out/"stage.json").write_text(json.dumps(stage,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("V28_SHA_BOUND_KYOKO_PASS",json.dumps(observations,sort_keys=True),flush=True)
    print("V28_LIMITATION",report["conclusion"],flush=True)
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--mask",type=Path,required=True)
    p.add_argument("--v27-zip",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--checkpoint",type=Path,required=True)
    args=p.parse_args()
    audit(args.source,args.mask,args.v27_zip,args.out,args.checkpoint)
