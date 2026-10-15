"""Verify a ReferenceShapeEditor v1 annotation against a pinned signed image.

No manual polygons, source image, or derived full-resolution masks are ever printed
or intended for public Git. This module provides only an intake gate and metrics.
"""
from __future__ import annotations
import base64,hashlib,io,json,re
from typing import Mapping
import numpy as np, cv2
from PIL import Image

class AuthorityHold(ValueError):pass
LABELS={'outerwear','arm_skin','hair','underlayer','accessory','unknown'}
PREFIXES=tuple(l+'/' for l in sorted(LABELS))

def check_polygon(points):
    if len(points)<3 or len(set(points))!=len(points):raise AuthorityHold('missing or duplicate polygon vertices')
    area=0.
    for i,(x,y) in enumerate(points):
        a,b=points[(i+1)%len(points)];area+=x*b-a*y
    if abs(area)<.5:raise AuthorityHold('zero-area polygon')
    # Fail closed on any strict proper segment intersection.
    def orient(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    for i in range(len(points)):
        for j in range(i+1,len(points)):
            if abs(i-j)==1 or {i,j}=={0,len(points)-1}:continue
            a,b=points[i],points[(i+1)%len(points)];c,d=points[j],points[(j+1)%len(points)]
            o1,o2=orient(a,b,c),orient(a,b,d)
            o3,o4=orient(c,d,a),orient(c,d,b)
            if o1*o2<0 and o3*o4<0:raise AuthorityHold('self intersecting polygon')

def validate_reference(doc:dict,source_bytes:bytes,expected_sha:str,*,final:bool=False)->dict:
    if doc.get('schema')!='reference-shape-editor/v1':raise AuthorityHold('invalid source editor schema')
    if not isinstance(expected_sha,str) or len(expected_sha)!=64 or hashlib.sha256(source_bytes).hexdigest()!=expected_sha:
        raise AuthorityHold('signed source SHA mismatch')
    im=doc.get('image') or {}
    data=im.get('dataURL','')
    if not re.fullmatch(r'data:image/(?:webp|png|jpeg|gif);base64,[A-Za-z0-9+/=]+',data):
        raise AuthorityHold('missing or unsupported embedded signed image')
    try:embedded=base64.b64decode(data.split(',',1)[1],validate=True)
    except Exception as e:raise AuthorityHold('malformed source embedding') from e
    if hashlib.sha256(embedded).digest()!=hashlib.sha256(source_bytes).digest():
        raise AuthorityHold('embedded original does not match pinned signed bytes')
    rgba=np.asarray(Image.open(io.BytesIO(embedded)).convert('RGBA'),dtype=np.uint8)
    h,w=rgba.shape[:2]
    if doc.get('canvas')!={'width':w,'height':h}:raise AuthorityHold('wrong canvas dimensions')
    verts=doc.get('vertices');shapes=doc.get('shapes')
    if not isinstance(verts,dict) or not isinstance(shapes,list):raise AuthorityHold('vertices/shapes required')
    if len(verts)>100000 or len(shapes)>20000:raise AuthorityHold('excess input')
    for vid,p in verts.items():
        if not isinstance(vid,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,50}',vid):raise AuthorityHold('invalid vertex id')
        if not isinstance(p,dict) or not all(isinstance(p.get(k),(int,float)) and np.isfinite(p[k]) for k in ('x','y')):
            raise AuthorityHold('nonfinite vertex')
        if not(0<=p['x']<=w and 0<=p['y']<=h):raise AuthorityHold('vertex outside source rectangle')
    ids=set();names=[];wrong=[];drawn_masks=[];alpha=rgba[:,:,3]>0
    for shape in shapes:
        sid=shape.get('id','')
        if not isinstance(sid,str) or not sid or sid in ids:raise AuthorityHold('duplicate or blank shape id')
        ids.add(sid)
        label=shape.get('name','')
        if final and not any(label.startswith(prefix) for prefix in PREFIXES):raise AuthorityHold('unlabeled user polygon '+sid)
        verts0=shape.get('vertexIds')
        if not isinstance(verts0,list) or len(verts0)<3 or len(verts0)>20000 or any(k not in verts for k in verts0):
            raise AuthorityHold('invalid polygon vertex lookup')
        points=[(float(verts[k]['x']),float(verts[k]['y'])) for k in verts0]
        check_polygon(points)
        if shape.get('visible',True) is False:continue
        poly=np.zeros((h,w),np.uint8)
        cv2.fillPoly(poly,[np.rint(np.array(points)).astype(np.int32)],1)
        count=int(poly.sum());outside=int(((poly>0)&~alpha).sum())
        wrong.append({'shape_id':sid,'name':label,'polygon_pixels':count,
                      'outside_source_pixels':outside,
                      'outside_source_ratio':round(outside/max(count,1),5)})
        if final and outside/max(1,count)>.015:
            raise AuthorityHold('polygon extends too far outside signed source foreground: '+sid)
        drawn_masks.append(poly.astype(bool));names.append(label)
    if final and (not names or not any(n.startswith('outerwear/') for n in names)):
        raise AuthorityHold('no authenticated outerwear polygon in final user review')
    # Human-drawn polygon is not itself an immutable Stage4 mask or a Golden signoff.
    return {'case_original_sha256':expected_sha,'width':w,'height':h,'shape_count':len(shapes),
            'visible_count':len(names),'outerwear_shapes':sum(n.startswith('outerwear/') for n in names),
            'unlabeled_shapes':sum(not any(n.startswith(prefix) for prefix in PREFIXES) for n in names),
            'final_review_ready':bool(final and names),'semantic_quality_approved':False,
            'source_pixels_generated':0,'shape_integrity':wrong}


def rasterize_visible_reference(doc:dict,source_bytes:bytes,expected_sha:str):
    """Create PRIVATE signed-source-coordinate visible part-label masks from human polygons.

    Layer order matches ReferenceShapeEditor SVG: last visible polygon is foremost.
    All manually rasterized pixels are clipped to ORIGINAL image alpha. The
    returned arrays are human reference observations, not Phase4 owner masks.
    """
    validate_reference(doc,source_bytes,expected_sha,final=True)
    alpha=np.asarray(Image.open(io.BytesIO(source_bytes)).convert('RGBA'))[:,:,3]>0
    h,w=alpha.shape
    results={x:np.zeros((h,w),bool) for x in LABELS}
    above=np.zeros((h,w),bool)
    for sh in reversed(doc['shapes']):
        if sh.get('visible',True) is False:continue
        label=sh['name'].split('/',1)[0]
        points=np.rint(np.array([[doc['vertices'][i]['x'],doc['vertices'][i]['y']] for i in sh['vertexIds']])).astype('int32')
        filled=np.zeros((h,w),np.uint8)
        cv2.fillPoly(filled,[points],1)
        visible=(filled>0)&alpha&~above
        results[label]|=visible
        above|=(filled>0)&alpha
    if sum(x.sum() for x in results.values())>int(alpha.sum()):raise AuthorityHold('visible reference exceeds signed source')
    return results
