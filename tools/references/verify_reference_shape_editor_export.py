#!/usr/bin/env python3
"""Validate a private Reference Shape Editor v1 JSON/SVG pair without publishing pixels.

Only reports geometry summary, hashes and source binding. Does not modify files.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import sys
import xml.etree.ElementTree as ET

PNG_SIG = b'\x89PNG\r\n\x1a\n'
HEX = re.compile(r'^#[0-9a-fA-F]{6}$')

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def as_point(item: dict, width: int, height: int) -> tuple[float, float]:
    x, y = item['x'], item['y']
    if not isinstance(x, (float, int)) or not isinstance(y, (float, int)):
        raise ValueError('vertex coordinate must be numeric')
    if not math.isfinite(x) or not math.isfinite(y) or not (0 <= x <= width and 0 <= y <= height):
        raise ValueError('nonfinite/out-of-canvas vertex')
    return float(x), float(y)


def cross(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])


def segments_cross(a, b, c, d):
    """Closed segment crossing for non-adjacent polygon edges."""
    eps = 1e-8
    o1,o2,o3,o4=(cross(a,b,c),cross(a,b,d),cross(c,d,a),cross(c,d,b))
    def on(p,q,r):
        return min(p[0],q[0])-eps <= r[0] <= max(p[0],q[0])+eps and min(p[1],q[1])-eps <= r[1] <= max(p[1],q[1])+eps
    if o1 * o2 < -eps and o3 * o4 < -eps:
        return True
    return ((abs(o1)<eps and on(a,b,c)) or (abs(o2)<eps and on(a,b,d)) or
            (abs(o3)<eps and on(c,d,a)) or (abs(o4)<eps and on(c,d,b)))


def check_polygon(points):
    n = len(points)
    if n < 3 or len(set(points)) != n:
        raise ValueError('polygon has under 3 distinct vertices or repeats')
    area2 = sum(points[i][0]*points[(i+1)%n][1] - points[(i+1)%n][0]*points[i][1] for i in range(n))
    if abs(area2) <= 1e-6:
        raise ValueError('zero-area polygon')
    for i in range(n):
        a,b=points[i],points[(i+1)%n]
        if a==b:raise ValueError('zero-length edge')
        for j in range(i+1,n):
            if (i+1)%n == j or (j+1)%n == i:
                continue
            if segments_cross(a,b,points[j],points[(j+1)%n]):
                raise ValueError('self-intersecting polygon')


def validate(json_path: Path, svg_path: Path):
    jb=json_path.read_bytes();sb=svg_path.read_bytes()
    doc=json.loads(jb)
    if doc.get('schema')!='reference-shape-editor/v1':
        raise ValueError('unsupported schema')
    canvas=doc['canvas'];w=canvas['width'];h=canvas['height']
    if not isinstance(w,int) or not isinstance(h,int) or not (1<=w<=8192 and 1<=h<=8192):
        raise ValueError('bad canvas dimensions')
    im=doc.get('image') or {}
    dataurl=im.get('dataURL')
    if not isinstance(dataurl,str) or not dataurl.startswith('data:image/png;base64,'):
        raise ValueError('embedded private source PNG absent or unsupported')
    payload=base64.b64decode(dataurl.split(',',1)[1], validate=True)
    if len(payload)<24 or not payload.startswith(PNG_SIG):
        raise ValueError('embedded PNG signature missing')
    pw,ph=struct.unpack('>II',payload[16:24])
    if (pw,ph)!=(w,h):
        raise ValueError('embedded PNG size does not match canvas')
    verts=doc['vertices']
    if not isinstance(verts,dict) or not verts:
        raise ValueError('vertex list missing')
    points={}
    for vid, coord in verts.items():
        if not isinstance(vid,str) or not isinstance(coord,dict):
            raise ValueError('bad vertex entry')
        points[vid]=as_point(coord,w,h)
    shapes=doc['shapes']
    if not isinstance(shapes,list) or not shapes:
        raise ValueError('shapes missing')
    used={k:0 for k in points}; ids=set()
    svgroot=ET.fromstring(sb)
    if svgroot.tag!='{http://www.w3.org/2000/svg}svg':
        raise ValueError('not an SVG root')
    if svgroot.attrib.get('viewBox')!=f'0 0 {w} {h}':
        raise ValueError('SVG viewBox does not match')
    nodes=list(svgroot.iter())
    if len(nodes)!=len(shapes)+1 or any(node.tag!='{http://www.w3.org/2000/svg}polygon' for node in nodes[1:]):
        raise ValueError('SVG contains extra/missing elements: no source images/scripts allowed')
    for index,(shape,node) in enumerate(zip(shapes,nodes[1:])):
        if shape.get('id') in ids:
            raise ValueError('duplicate shape ID')
        ids.add(shape.get('id'))
        vids=shape['vertexIds']
        if len(vids)!=len(set(vids)):
            raise ValueError(f'repeated shape vertex ID at {index}')
        poly=[]
        for vid in vids:
            if vid not in points:raise ValueError(f'unknown vertex ID at {index}')
            used[vid]+=1;poly.append(points[vid])
        check_polygon(poly)
        if not HEX.fullmatch(shape['fill']):
            raise ValueError('invalid hex fill')
        if shape.get('visible') is False:
            raise ValueError('exported SVG cannot contain hidden shape')
        if node.attrib.get('fill','').lower()!=shape['fill'].lower() or node.attrib.get('data-shape-name')!=shape['name']:
            raise ValueError(f'SVG color/name mismatch at {index}')
        coords=[]
        for pair in node.attrib['points'].split():
            xy=pair.split(',')
            if len(xy)!=2:raise ValueError('malformed SVG point')
            coords.append((float(xy[0]),float(xy[1])))
        if len(coords)!=len(poly) or any(abs(a-b)>0.006 for c,p in zip(coords,poly) for a,b in zip(c,p)):
            raise ValueError(f'SVG/JSON vertex mismatch at {index}')
    if not all(used.values()):
        raise ValueError('unused vertex entries')
    report={
        'schema':'kyoko-manual-reference-validation/v1',
        'editor_schema':doc['schema'], 'canvas':{'width':w,'height':h},
        'source_image_sha256':sha256(payload),'source_image_bytes':len(payload),
        'project_json_sha256':sha256(jb), 'render_svg_sha256':sha256(sb),
        'polygon_count':len(shapes),'vertex_count':len(points),
        'shared_vertex_count':sum(x>1 for x in used.values()),
        'visible_shape_count':sum(x.get('visible',True) for x in shapes),
        'svg_matches_json':True,'has_source_raster_in_svg':False,
        'topology_pass':True,
    }
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('json_path',type=Path)
    p.add_argument('svg_path',type=Path)
    p.add_argument('--report',type=Path)
    args=p.parse_args()
    try:
        report=validate(args.json_path,args.svg_path)
        result=json.dumps(report,ensure_ascii=False,indent=2)+'\n'
        if args.report:
            args.report.parent.mkdir(parents=True,exist_ok=True)
            args.report.write_text(result,encoding='utf-8')
        print(result,end='')
        return 0
    except (ValueError, KeyError, TypeError, ET.ParseError, UnicodeDecodeError, OSError, base64.binascii.Error) as exc:
        print('FAIL: '+str(exc),file=sys.stderr)
        return 1

if __name__=='__main__':
    raise SystemExit(main())
