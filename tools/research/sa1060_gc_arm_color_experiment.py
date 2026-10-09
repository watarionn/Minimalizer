"""Non-promoting signed-source GC001 arm paint plane feasibility research.

Do not infer artistic correctness from RGB gains. Original pixels, source masks,
face primitives, SVG owner masks, and historical Stage8 policy are immutable.
Only additional source-observed SVG polygons (no images/filters/generated fill).
"""
from __future__ import annotations
import argparse,copy,hashlib,io,json
from pathlib import Path
from xml.etree import ElementTree as ET
import cv2,numpy as np
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright

SVG_NS='http://www.w3.org/2000/svg'; NS='{'+SVG_NS+'}'
ET.register_namespace('',SVG_NS)
PIN={
 'GC001_source.png':'75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e',
 'gc001_structure_guarded.svg':'bdea6fc36a953c01fe115032c10cb9313ecc900377f63954ff84bcb0392b2939',
 'gc001_left.png':'49986981c02f472a888e1717205799c254b16c1bca7ef96beba2dc6b4f696b5f',
 'gc001_right.png':'4900beccaf0ca4a9ca33600339df77976a4500f1db932fcb240a41907b935b91',
 'gc001_face.png':'b4812364eaec7da9930a18ae85270d6612555d3fb3d80283efcf69b03aa6a72f'}
BASELINE_PNG_SHA='c51c8bac13f68802b1a7d0022eccd1eff66ae2e4b2f601a7e9b881b936eb4445'
BUDGET=1887; BASE_COST=1873; OWNER={'left':7,'right':2}


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def png_sha(pix):
    b=io.BytesIO();Image.fromarray(pix).save(b,format='PNG');return hashlib.sha256(b.getvalue()).hexdigest()
def render(page,root):
    xml=ET.tostring(root,encoding='unicode')
    if any(tag in xml for tag in ('<image','data:image','base64,','foreignObject')):raise ValueError('RASTER_OR_FOREIGN_CONTENT_FORBIDDEN')
    page.set_content('<style>html,body{margin:0;padding:0}svg{display:block}</style>'+xml)
    return np.asarray(Image.open(io.BytesIO(page.locator('svg').screenshot())).convert('RGB')).copy()
def mae(im,src,m):return float(np.abs(im[m].astype('int16')-src[m].astype('int16')).mean())
def pin_load(folder):
    folder=Path(folder)
    for name,digest in PIN.items():
        if not (folder/name).is_file() or sha(folder/name)!=digest:raise ValueError('SIGNED_PIN_MISMATCH '+name)
    svg=ET.parse(folder/'gc001_structure_guarded.svg').getroot()
    if svg.get('data-minimalizer-face-features')!='off':raise ValueError('FACELESS_OFF_REQUIRED')
    photo=np.asarray(Image.open(folder/'GC001_source.png').convert('RGB'))
    masks={k:np.asarray(Image.open(folder/f'gc001_{k}.png').convert('L'))>127 for k in ('left','right','face')}
    groups={int(n.get('data-owner-index')):n for n in svg if n.get('data-owner-index') is not None}
    if set(OWNER.values())-set(groups):raise ValueError('ARM_OWNER_GROUPS_MISSING')
    for arm,idx in OWNER.items():
        if groups[idx].get('mask')!=f'url(#sa1041-owner-{idx})':raise ValueError('OWNER_MASK_CHANGED')
    if (masks['face'] & (masks['left']|masks['right'])).any():raise ValueError('FACE_ARM_PROTECTED_MASK_OVERLAP')
    return svg,photo,masks,groups


def polygon_mask(poly,shape):
    out=np.zeros(shape,dtype=np.uint8);cv2.fillPoly(out,[poly.reshape(-1,1,2).astype(np.int32)],1)
    return out.astype(bool)

def candidates(photo,arm_mask,base_color,role):
    """Deterministic source RGB clustering, source-boundary contour simplification.

    A proposal is a real-color polygon from the actual source ROI. Signed owner SVG
    mask clips it; no pixel array is exported to the SVG.
    """
    yy,xx=np.where(arm_mask)
    pix=photo[arm_mask].astype(np.float32)
    if len(pix)<250:raise ValueError('SIGNED_ARM_EMPTY')
    options=[]; seen=set()
    for k in (4,6,8):
        cv2.setRNGSeed(1060+k)
        _,labels,centers=cv2.kmeans(pix,k,None,(cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER,60,.15),3,cv2.KMEANS_PP_CENTERS)
        ids=np.full(photo.shape[:2],-1,np.int16);ids[yy,xx]=labels.reshape(-1)
        for label in range(k):
            matching=ids==label
            # Medoid must be an EXACT source pixel, not an RGB average or synthesized color.
            colors,nums=np.unique(photo[matching],axis=0,return_counts=True)
            if not len(colors):continue
            # Choose source pixel closest to observed cluster center, with stable tie.
            ix=np.argmin(np.sum((colors.astype(np.float32)-centers[label])**2,axis=1))
            rgb=tuple(map(int,colors[ix]))
            if rgb==tuple(base_color):continue
            count, components, stats,_=cv2.connectedComponentsWithStats(matching.astype(np.uint8),8)
            for cc in range(1,count):
                area=int(stats[cc,cv2.CC_STAT_AREA])
                if area<60:continue
                blob=(components==cc).astype(np.uint8)
                contours,_=cv2.findContours(blob,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
                if not contours:continue
                outline=max(contours,key=cv2.contourArea)
                for eps in (1.5,3.,5.,8.):
                    poly=cv2.approxPolyDP(outline,eps,True).reshape(-1,2)
                    if not 3<=len(poly)<=7:continue
                    pm=polygon_mask(poly,arm_mask.shape)&arm_mask
                    if int(pm.sum())<40:continue
                    gain=(np.abs(photo[pm].astype('int16')-np.array(base_color,dtype=np.int16)).sum()
                          -np.abs(photo[pm].astype('int16')-np.array(rgb,dtype=np.int16)).sum())
                    if gain<=10:continue
                    key=(rgb,tuple(map(tuple,poly)))
                    if key in seen:continue
                    seen.add(key)
                    options.append({'arm':role,'rgb':rgb,'points':poly.tolist(),'vertices':len(poly),
                                    'estimated_rgb_error_gain_sum':int(gain),'source_cluster_pixels':int(area)})
    return sorted(options,key=lambda v:(-v['estimated_rgb_error_gain_sum'],v['vertices'],v['points']))

def add_plane(group,opt):
    attrs={'points':' '.join(','.join(map(str,p)) for p in opt['points']),
           'fill':'#%02x%02x%02x'%tuple(opt['rgb']), 'shape-rendering':'crispEdges',
           'data-sa1060-source-arm-color':opt['arm']}
    return ET.SubElement(group,NS+'polygon',attrs)


def border_background_overlap(photo,mask):
    """Conservative exact RGB flood from a known opaque source background edge.

    This is diagnostic evidence only, never a semantic truth classifier.
    """
    # Choose the dominant exact opaque RGB touching the entire scene border,
    # ignoring (0,0,0) transparent-corner RGB values. No guessed character colors.
    border=np.concatenate((photo[0],photo[-1],photo[:,0],photo[:,-1]),axis=0)
    colors,counts=np.unique(border,axis=0,return_counts=True)
    choices=[(int(n), tuple(map(int,c))) for c,n in zip(colors,counts) if tuple(c)!=(0,0,0)]
    if not choices or max(n for n,c in choices)<200:
        raise ValueError('SIGNED_BORDER_ANCHOR_AMBIGUOUS')
    _,rgb=max(choices,key=lambda item:(item[0],item[1]))
    same=np.all(photo==np.asarray(rgb,dtype=np.uint8),axis=2).astype(np.uint8)
    count, labels, _, _ =cv2.connectedComponentsWithStats(same,4)
    edge=np.unique(np.concatenate((labels[0],labels[-1],labels[:,0],labels[:,-1])))
    touching=[int(i) for i in edge if i!=0]
    boundary=np.isin(labels,touching)
    return {'background_exact_rgb':list(rgb),'border_connected_pixels':int(boundary.sum()),
            'overlap_with_signed_arm_pixels':int(np.count_nonzero(boundary&mask)),
            'arm_mask_pixels':int(mask.sum())}


def evaluate(source,out,chromium='/usr/bin/chromium'):
    source=Path(source).resolve();out=Path(out).resolve()
    if out==source or out in source.parents or source in out.parents:raise ValueError('PRIVATE_INPUT_OUTPUT_OVERLAP')
    root,photo,masks,groups=pin_load(source)
    allarms=masks['left']|masks['right']; outside=~allarms
    if out.exists() and any(out.iterdir()):raise ValueError('OUTPUT_MUST_BE_EMPTY')
    out.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as pl:
        browser=pl.chromium.launch(executable_path=chromium,headless=True,args=['--no-sandbox','--disable-gpu'])
        try:
            page=browser.new_page(viewport={'width':340,'height':340},device_scale_factor=1)
            baseline=render(page,root)
            if png_sha(baseline)!=BASELINE_PNG_SHA:raise AssertionError('SIGNED_CHROMIUM_BASELINE_MISMATCH')
            starting={arm:mae(baseline,photo,masks[arm]) for arm in OWNER}
            proposals={}
            for arm,index in OWNER.items():
                rect=next(x for x in groups[index] if x.tag==NS+'rect')
                base=tuple(bytes.fromhex(rect.get('fill').lstrip('#')))
                proposals[arm]=candidates(photo,masks[arm],base,arm)
            accepted=[]; frame=baseline; used=BASE_COST; tries=0
            # Each first step is isolated and optional. No baseline regression accepted.
            for role in ('left','right'):
                first=proposals[role][:24]
                choices=[]
                for opt in first:
                    if used+opt['vertices']>BUDGET:continue
                    n=add_plane(groups[OWNER[role]],opt)
                    shot=render(page,root);tries+=1
                    groups[OWNER[role]].remove(n)
                    if not np.array_equal(shot[outside],baseline[outside]):continue
                    if not np.array_equal(shot[masks['face']],baseline[masks['face']]):continue
                    a=mae(shot,photo,masks[role]); baseline_arm=mae(frame,photo,masks[role])
                    other=next(x for x in OWNER if x!=role)
                    if a>=baseline_arm-0.005 or mae(shot,photo,masks[other])>mae(frame,photo,masks[other])+1e-6:continue
                    choices.append((a,opt))
                if choices:
                    new_error,opt=min(choices,key=lambda x:(x[0],x[1]['vertices'],x[1]['points']))
                    add_plane(groups[OWNER[role]],opt)
                    frame=render(page,root)
                    used+=opt['vertices']
                    accepted.append({'arm':role,'source_rgb':opt['rgb'],'points_kept_private':True,
                                     'vertices':opt['vertices'],'source_cluster_pixels':opt['source_cluster_pixels'],
                                     'signed_arm_mae_after':round(new_error,6)})
            final=render(page,root)
            if not np.array_equal(final,frame):raise AssertionError('NONDETERMINISTIC_RENDER')
            if not np.array_equal(final[outside],baseline[outside]):raise AssertionError('PIXELS_OUTSIDE_SIGNED_ARMS_CHANGED')
            if not np.array_equal(final[masks['face']],baseline[masks['face']]):raise AssertionError('SIGNED_FACE_CHANGED')
            if used>BUDGET:raise AssertionError('COMPACT_VERTEX_BUDGET')
            if not accepted:raise AssertionError('NO_SOURCE_OBSERVED_SAFE_ARM_IMPROVEMENT')
            version=browser.version
        finally:browser.close()
    report={'stage':'SA10.60-ARM','status':'RESEARCH_ONLY_HOLD','signed_source_sha256':PIN['GC001_source.png'],
            'signed_sa1057_svg_sha256':PIN['gc001_structure_guarded.svg'],
            'signed_mask_pins_valid':True,
            'background_owner_contamination_diagnostic':{k:border_background_overlap(photo,masks[k]) for k in OWNER},
            'trial_candidate_visual_gate':'HOLD', 'trial_candidate_promotion_allowed':False,
            'chromium':version,'starting_svg_vertices':BASE_COST,
            'expanded_svg_vertices':used,'deployed_vertex_cap':BUDGET,
            'candidate_chromium_renders':tries,'candidate_source_regions':{k:len(v) for k,v in proposals.items()},
            'signed_arm_mae_before':{k:round(x,6) for k,x in starting.items()},
            'signed_arm_mae_after':{k:round(mae(final,photo,masks[k]),6) for k in OWNER},
            'signed_face_pixel_changes':0,'pixels_outside_signed_arms_changed':0,
            'signed_arm_changed_pixels':{k:int(np.count_nonzero(np.any(final!=baseline,axis=2)&masks[k])) for k in OWNER},
            'default_face_microfeatures_visible':False,
            'numerically_selected_unapproved_arm_planes':accepted,'historical_stage8_source_ring_gate':'HOLD',
            'human_visual_golden':'PENDING','production':'UNCHANGED',
            'first_bad_stage_hypothesis':'PHASE4_SIGNED_ARM_MASK_BACKGROUND_OVERLAP_REQUIRES_REVIEW',
            'note':'Numerical RGB gain does NOT establish arm semantics or artistic quality. Trial polygons remain private and REJECTED for promotion until source mask contamination and identity are resolved.'}
    (out/'gc001_sa1060_arm_candidate.svg').write_text(ET.tostring(root,encoding='unicode'),'utf-8')
    Image.fromarray(baseline).save(out/'gc001_sa1057_frozen_baseline.png')
    Image.fromarray(final).save(out/'gc001_sa1060_arm_candidate.png')
    board=Image.new('RGB',(1020,380),(242,242,240));pen=ImageDraw.Draw(board)
    for j,(im,title) in enumerate(((photo,'SIGNED SOURCE'),(baseline,'SA10.57 BASE'),(final,'SA10.60-ARM CANDIDATE'))):
        board.paste(Image.fromarray(im),(j*340,40));pen.text((j*340+7,10),title,fill=(20,20,20))
    board.save(out/'gc001_sa1060_private_review_board.png')
    report['artifact_sha256']={p.name:sha(p) for p in out.iterdir() if p.is_file()}
    (out/'sa1060_arm_private_metrics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    return report

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();print(json.dumps(evaluate(a.source,a.out),indent=2))
