"""Private L02 human annotation verification; does not infer or approve production release.
Source imagery and polygon vertices are never logged or written to public outputs.
"""
import io,json,base64,hashlib,re,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np,cv2
from PIL import Image,ImageDraw,ImageFont
from verify_local_l02_manual_intake import check_polygon,AuthorityHold

PINS={
 'H04':'7d5a62251326e7b2c6ab058fb6bc76af12a8c0b442444344044a79a97ebae0d3',
 'H06':'c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8',
 'H08':'759b4ed81a49b0e9fce31e6134189a7169ec3c134c3fc97d22d4d0fd6a344a9e'}
NAMES={'H04':'H04_original_signed_trace (1).json','H06':'H06_trace.json','H08':'H08_trace.json'}
SVG={'H06':'H06_trace.svg','H08':'H08_trace.svg'}
ALIASES={'outerwear':'outerwear','innerwear':'underlayer','underlayer':'underlayer','arm_skin':'arm_skin','body_skin':'arm_skin','neck_skin':'neck_skin','lower_body':'lower_body','face_skin':'face_skin','hair':'hair','accessory':'accessory'}
COLORS={'outerwear':(242,184,53),'underlayer':(76,170,246),'arm_skin':(217,115,151),'neck_skin':(203,129,159),'lower_body':(93,153,222),'face_skin':(223,130,153),'hair':(158,97,186),'accessory':(111,185,124)}

class ReviewError(Exception):pass

def inspect(path,case,svg_path=None):
    d=json.loads(Path(path).read_text(encoding='utf-8'))
    assert d['schema']=='reference-shape-editor/v1' and d.get('appVersion')=='1.1.0'
    embedded=d['image']['dataURL']
    if not re.fullmatch(r'data:image/(?:png|webp);base64,[A-Za-z0-9+/=]+',embedded):raise ReviewError('Unsupported underlay')
    raw=base64.b64decode(embedded.split(',',1)[1],validate=True)
    if hashlib.sha256(raw).hexdigest()!=PINS[case]:raise ReviewError('SIGNED_SOURCE_MISMATCH '+case)
    src=np.asarray(Image.open(io.BytesIO(raw)).convert('RGBA'),np.uint8)
    h,w=src.shape[:2]
    if d['canvas']!={'width':w,'height':h}:raise ReviewError('dimension mismatch')
    alpha=src[:,:,3]>0
    labels={name:np.zeros((h,w),bool) for name in COLORS}
    top=np.zeros((h,w),bool)
    records=[];claimed=[]
    if svg_path:
        svgroot=ET.parse(svg_path).getroot()
        poly_nodes=svgroot.findall('{http://www.w3.org/2000/svg}polygon')
        if len(poly_nodes)!=len(d['shapes']):raise ReviewError('SVG polygon count mismatch')
    else:poly_nodes=[None]*len(d['shapes'])
    polygons=[]
    for i,(shape,node) in enumerate(zip(d['shapes'],poly_nodes)):
        if shape.get('visible',True) is False:continue
        pts=np.array([[d['vertices'][v]['x'],d['vertices'][v]['y']] for v in shape['vertexIds']],dtype=np.float64)
        if len(pts)<3 or np.any(~np.isfinite(pts)) or np.any(pts[:,0]<0) or np.any(pts[:,0]>w) or np.any(pts[:,1]<0) or np.any(pts[:,1]>h):raise ReviewError('Invalid polygon coords')
        try:check_polygon([tuple(map(float,point)) for point in pts])
        except AuthorityHold as exc:raise ReviewError('self-intersection or degenerate polygon '+shape['id']) from exc
        label=shape['name'];kind=label.split('/')[0]
        if kind=='face_skin' and label not in ('face_skin/face','face_skin/skin'):
            raise ReviewError('facial microdetails not permitted in Minimalizer default reference')
        if kind not in ALIASES:raise ReviewError('Unknown human label '+label)
        if node is not None:
            svg_name=node.get('data-shape-name');svgpts=np.array([list(map(float,xy.split(','))) for xy in node.get('points').split()])
            if svg_name!=label or svgpts.shape!=pts.shape or float(np.max(np.abs(svgpts-pts)))>.011:raise ReviewError('SVG/JSON mismatch')
        m=np.zeros((h,w),np.uint8)
        cv2.fillPoly(m,[np.rint(pts).astype(np.int32)],1)
        m=m>0
        outside=int(np.count_nonzero(m&~alpha));fraction=outside/max(1,int(m.sum()))
        records.append({'shape_index':i+1,'shape_id':shape['id'],'label':label,'canonical':ALIASES[kind], 'pixels':int(m.sum()),'outside_alpha_px':outside,'outside_fraction':round(fraction,6)})
        polygons.append(m)
    # last polygon drawn is visually on top. Source underlay is accepted signed bytes.
    for shape,m in zip(reversed([s for s in d['shapes'] if s.get('visible',True)]),reversed(polygons)):
        cat=ALIASES[shape['name'].split('/')[0]]
        visibility=m&alpha&~top
        labels[cat]|=visibility
        top|=m&alpha
    if np.any(sum(x.astype('uint8') for x in labels.values())>1):raise ReviewError('visible labels overlap')
    if np.any(top&~alpha):raise ReviewError('outside signed alpha')
    score={'case':case,'source_sha256':PINS[case],'annotation_json_sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),
      'annotation_svg_sha256':hashlib.sha256(Path(svg_path).read_bytes()).hexdigest() if svg_path else None,
      'canvas':[w,h],'polygon_count':len(records),'vertex_count':len(d['vertices']),
      'source_opaque_px':int(alpha.sum()),'visible_manually_labelled_px':int(top.sum()),'labelled_fraction_of_alpha':round(float(top.sum()/alpha.sum()),6),
      'visible_outerwear_px':int(labels['outerwear'].sum()),'visible_underlayer_px':int(labels['underlayer'].sum()),
      'visible_arm_skin_px':int(labels['arm_skin'].sum()),'unlabelled_px':int((alpha&~top).sum()),
      'outside_alpha_shapes_gt_1p5pct':sum(x['outside_fraction']>.015 for x in records),
      'source_alpha_clipped':True,'layer_order':'last-listed foreground',
      'human_right_left_convention':'anatomical_character_right_left',
      'shape_audit':records}
    return score,src,alpha,labels,top

def render(case,src,labels,top,out):
    h,w=src.shape[:2]
    orig=Image.fromarray(src).convert('RGBA')
    original_composite=Image.new('RGBA',(w,h),(240,239,237,255));original_composite.alpha_composite(orig)
    maskarr=np.full((h,w,3),235,dtype=np.uint8)
    for key,color in COLORS.items():maskarr[labels[key]]=color
    # put original underneath labels in 40% opacity
    image_arr=np.asarray(original_composite.convert('RGB'),np.uint8)
    mix=np.rint(np.where(top[:,:,None],maskarr*.72+image_arr*.28,image_arr)).astype(np.uint8)
    rgb=Image.fromarray(mix,'RGB')
    maximum=660
    scale=min(1.,maximum/max(w,h))
    size=(round(w*scale),round(h*scale))
    p=Image.new('RGB',(size[0]*2,size[1]+40),(250,249,247))
    p.paste(original_composite.convert('RGB').resize(size),(0,40))
    p.paste(rgb.resize(size),(size[0],40))
    ctx=ImageDraw.Draw(p)
    ctx.text((9,11),f'{case} original (signed source)',fill=(20,20,20))
    ctx.text((size[0]+9,11),'HUMAN visible labels (not model predictions)',fill=(20,20,20))
    p.save(out,optimize=True)

if __name__=='__main__':
    import sys
    base=Path(sys.argv[1]);output=Path(sys.argv[2]);output.mkdir(parents=True,exist_ok=True)
    scores={}
    for case in PINS:
        f=base/NAMES[case];svg=base/SVG[case] if case in SVG else None
        score,src,alpha,labels,top=inspect(f,case,svg)
        scores[case]=score
        render(case,src,labels,top,output/(case+'_HUMAN_LABELS_PRIVATE.png'))
        np.savez_compressed(output/(case+'_HUMAN_VISIBLE_MASKS_PRIVATE.npz'),**{k:arr.astype('uint8') for k,arr in labels.items()},opaque=alpha.astype('uint8'),labelled=top.astype('uint8'))
        print(case,{k:v for k,v in score.items() if k not in ('shape_audit',)})
    (output/'H04_H06_H08_REVIEWED_ANNOTATION_AUDIT_PRIVATE.json').write_text(json.dumps(scores,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
