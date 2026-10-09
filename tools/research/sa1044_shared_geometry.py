"""SA10.44 source-exact SVG path reuse, expanded accounting, real Chromium.

Research only. Every signed source/Stage08/Stage04 artifact is frozen by SA10.43.
Never redefine a material owner, repair anatomy by inventing geometry, or
count href duplication as free rendered geometric complexity.
"""
from __future__ import annotations
import argparse
import copy
from hashlib import sha256
import json
from pathlib import Path
from xml.etree import ElementTree as ET
import numpy as np
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
import sa1043_boundary_compaction as prev

NS=prev.NS
BUDGET=prev.BUDGET
SIZE=prev.SIZE
EXTRAS=prev.EXTRAS
SHARED_ID={
    'face':'sa1044-source-face',
    'left_arm':'sa1044-source-left-arm',
    'right_arm_signed':'sa1044-source-right-arm-signed',
    'right_arm_owner':'sa1044-source-right-arm-owner',
}


def original_masks(root:Path):
    prev.frozen(root)
    scene=json.loads((root/'phase8_adaptive_source_contour_research.json').read_text('utf-8'))
    if scene.get('original_source_sha256')!=prev.SHA['Raden_source.png']:
        raise ValueError('Different source digest')
    owners=scene['primitives_back_to_front']
    if tuple(p['source_mask_owner'] for p in owners)!=prev.ORDER:
        raise ValueError('Owner order changed')
    masks={f'sa1041-owner-{i}':prev.source_ring_mask(record['parameters']['rings'])
           for i,record in enumerate(owners)}
    signed={name:np.asarray(Image.open(root/f'signed_{name}_stage04_mask.png').convert('L'))>0
           for name in ('face','left_arm','right_arm')}
    masks['sa1041-original-face-guard']=signed['face']
    masks['sa1041-protected-clear']=signed['face']|signed['left_arm']|signed['right_arm']
    if not np.array_equal(masks['sa1041-owner-5'],signed['face']):
        raise ValueError('Face owner/source signed mask differs, cannot alias')
    if not np.array_equal(masks['sa1041-owner-3'],signed['left_arm']):
        raise ValueError('Left-arm owner/source signed mask differs, cannot alias')
    right_delta=int(np.count_nonzero(masks['sa1041-owner-2']!=signed['right_arm']))
    if right_delta != 2:
        raise ValueError('Frozen right-arm owner/signed discrepancy unexpectedly changed')
    if np.any(signed['face']&signed['left_arm']) or np.any(signed['face']&signed['right_arm']) or np.any(signed['left_arm']&signed['right_arm']):
        raise ValueError('Protection semantic roles overlap, no union reuse authority')
    return masks,signed,right_delta


def path_vertices(d:str)->int:
    # The deterministic Stage10.43 path emits one explicit M/L per vertex.
    # Fail closed on SVG shorthand or curves: those require other accounting.
    import re
    clean=re.sub(r'-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?','',d)
    if re.sub(r'[MLZ\s]','',clean):
        raise ValueError('Unexpected path geometry command')
    return len(re.findall(r'[ML]',clean))


def write_mask(mask:ET.Element, vertices:int, path:str|None=None,
               references:list[str]|None=None, inverse=False)->None:
    if (path is None)==(references is None):
        raise ValueError('Must give path or explicit geometry references')
    for elem in list(mask): mask.remove(elem)
    ET.SubElement(mask,NS+'rect',{'width':'340','height':'340',
        'fill':'#ffffff' if inverse else '#000000'})
    if path is not None:
        if path_vertices(path)!=vertices:raise ValueError('Geometry/path vertex mismatch')
        ET.SubElement(mask,NS+'path',{'d':path,'fill-rule':'evenodd',
            'shape-rendering':'crispEdges','fill':'#000000' if inverse else '#ffffff'})
    else:
        for ref in references:
            if not ref.startswith('#sa1044-source-'):
                raise ValueError('Nonlocal SVG reference not allowed')
            ET.SubElement(mask,NS+'use',{'href':ref,
               'fill':'#000000' if inverse else '#ffffff',
               'fill-rule':'evenodd','shape-rendering':'crispEdges'})


def count_expanded_and_stored(svg:ET.Element)->dict:
    defs=svg.find(NS+'defs')
    if defs is None:raise ValueError('SVG must have defs')
    paths={}
    for e in defs:
        if e.tag==NS+'path' and (name:=e.get('id')):
            if name in paths or not name.startswith('sa1044-source-'):
                raise ValueError('Duplicate or unknown shared path')
            paths[name]=path_vertices(e.get('d',''))
    if not paths:raise ValueError('No shared source geometry')
    all_references=[]
    expanded=0
    stored=sum(paths.values())
    mask_count=0
    for node in defs:
        if node.tag!=NS+'mask':continue
        mask_count+=1
        for part in node:
            if part.tag==NS+'path':
                verts=path_vertices(part.get('d',''))
                expanded+=verts
                stored+=verts
            elif part.tag==NS+'use':
                href=part.get('href')
                if not href or not href.startswith('#') or href[1:] not in paths:
                    raise ValueError('Broken, external, or cyclic SVG use reference')
                if list(part):raise ValueError('Nested use reference forbidden')
                all_references.append(href[1:])
                expanded+=paths[href[1:]]
            elif part.tag!=NS+'rect':
                raise ValueError('Uncounted geometric element in signed mask')
    if mask_count!=13:
        raise ValueError('Must account for all 11 owners and 2 protection masks')
    if len(all_references)!=7:
        raise ValueError('Expected exactly seven source-geometry occurrences from uses')
    # Original eleven owner masks, face guard, inverse protection, plus stage9.
    return {'unique_mask_path_vertices':stored,
            'painted_mask_vertices_expanded':expanded,
            'unique_plus_stage9':stored+EXTRAS,
            'expanded_plus_stage9':expanded+EXTRAS,
            'stage9_vertices':EXTRAS,'mask_count':mask_count,
            'uses_expanded':len(all_references),
            'shared_ids_and_vertices':paths,
            'reference_usages':{ref:all_references.count(ref) for ref in sorted(set(all_references))},
            'unique_under_budget':stored+EXTRAS<=BUDGET,
            'expanded_under_budget':expanded+EXTRAS<=BUDGET}


def compile_candidate(source_svg:ET.Element,masks:dict,signed:dict,
                      epsilon_nonprotected:float)->tuple[ET.Element,dict]:
    # Four exact, individually source-verified paths. The signed right arm
    # differs from its Stage8 owner by 2px and MUST NOT be replaced by it.
    root=copy.deepcopy(source_svg)
    defs=root.find(NS+'defs')
    if defs is None:raise ValueError('Expected original SVG defs')
    shared_masks={
       'face':signed['face'],
       'left_arm':signed['left_arm'],
       'right_arm_signed':signed['right_arm'],
       'right_arm_owner':masks['sa1041-owner-2'],
    }
    for name,pixels in shared_masks.items():
        path,verts=prev.boundary_path(prev.pixel_edge_loops(pixels),0.5)
        if path_vertices(path)!=verts:raise AssertionError('Uncounted path tokens')
        ET.SubElement(defs,NS+'path',{'id':SHARED_ID[name], 'd':path,
            'fill-rule':'evenodd','shape-rendering':'crispEdges'})
    # Current product owner order is never changed; only clip/luminance mask data.
    replacement={
        'sa1041-owner-2':['right_arm_owner'],
        'sa1041-owner-3':['left_arm'],
        'sa1041-owner-5':['face'],
        'sa1041-original-face-guard':['face'],
        'sa1041-protected-clear':['face','left_arm','right_arm_signed'],
    }
    for ident,pixels in masks.items():
        nodes=[x for x in defs if x.tag==NS+'mask' and x.get('id')==ident]
        if len(nodes)!=1:raise ValueError('Missing source mask: '+ident)
        inverse=ident=='sa1041-protected-clear'
        if ident in replacement:
            refs=['#'+SHARED_ID[n] for n in replacement[ident]]
            write_mask(nodes[0],0,references=refs,inverse=inverse)
        else:
            path,verts=prev.boundary_path(prev.pixel_edge_loops(pixels),epsilon_nonprotected)
            write_mask(nodes[0],verts,path=path,inverse=inverse)
    for node in root.iter():
        if node.tag in (NS+'image',NS+'foreignObject'):
            raise ValueError('Raster embedding and foreign objects forbidden')
    result=count_expanded_and_stored(root)
    result['source_owner_right_vs_signed_pixels']=2
    result['nonprotected_epsilon']=epsilon_nonprotected
    return root,result


def svg_string(root:ET.Element)->str:
    return ET.tostring(root,encoding='unicode')


def compare(reference:np.ndarray, image:np.ndarray, signed:dict)->dict:
    d=np.any(reference!=image,axis=2)
    return {'full_rgb_mismatch':int(d.sum()),
            'protected':{name:int(np.count_nonzero(d&signed[name]))
                         for name in ('face','left_arm','right_arm')},
            'mean_absolute_rgb':round(float(np.abs(reference.astype(np.int16)-image.astype(np.int16)).mean()),6)}


def test_all_browser_masks(page,svg:ET.Element,masks:dict)->dict:
    result={}
    for ident,original in masks.items():
        image=prev.chromium_rgb(page,prev.isolated_svg(svg,ident))
        binary=image[...,0]<128
        target=~original if ident=='sa1041-protected-clear' else original
        result[ident]=int(np.count_nonzero(binary!=target))
    return result


def evaluate(root:Path,out:Path,chromium='/usr/bin/chromium')->dict:
    root,out=root.resolve(),out.resolve()
    if root==out or root in out.parents or out in root.parents:
        raise ValueError('Signed input/output cannot overlap')
    masks,signed,right_delta=original_masks(root)
    authority=ET.parse(root/'full_character_vector.svg').getroot()
    reference=np.asarray(Image.open(root/'signed_full_opencv_reference.png').convert('RGB'))
    if reference.shape!=(340,340,3):raise ValueError('Invalid signed baseline size')
    candidates={
        'shared_exact':compile_candidate(authority,masks,signed,0.5),
        'shared_unique_budget':compile_candidate(authority,masks,signed,1.5),
    }
    out.mkdir(parents=True,exist_ok=True)
    reports={}
    frames=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path=chromium,
            args=['--no-sandbox','--disable-gpu'])
        try:
            page=browser.new_page(viewport={'width':340,'height':340},device_scale_factor=1)
            old=prev.chromium_rgb(page,svg_string(authority))
            Image.fromarray(old).save(out/'source_svg_baseline.png')
            frames.extend([('ORIGINAL OPENCV',reference),('OLD CHROME SVG',old)])
            for ident,(svg,counts) in candidates.items():
                content=svg_string(svg)
                (out/f'{ident}.svg').write_text(content,'utf-8')
                rendered=prev.chromium_rgb(page,content)
                Image.fromarray(rendered).save(out/f'{ident}.png')
                mask_errors=test_all_browser_masks(page,svg,masks)
                reports[ident]={**counts,'metrics':compare(reference,rendered,signed),
                                'mask_binary_errors':mask_errors,
                                'all_13_masks_exact':not any(mask_errors.values()),
                                'source_svg_embedded_raster':False}
                frames.append((ident.upper(),rendered))
            chromium_version=browser.version
        finally:
            browser.close()
    if any(reports['shared_exact']['mask_binary_errors'].values()):
        raise AssertionError('Shared source-exact geometry changed pixel ownership')
    if any(reports['shared_exact']['metrics']['protected'].values()):
        raise AssertionError('Shared references broke face or arms')
    if reports['shared_exact']['metrics']['full_rgb_mismatch']!=148:
        raise AssertionError('Shared source-exact full Chrome result changed relative to SA10.43')
    if not reports['shared_unique_budget']['unique_under_budget'] or reports['shared_unique_budget']['expanded_under_budget']:
        raise AssertionError('Expected misleading unique-only budgeting case was not reproduced')
    sheet=Image.new('RGB',(340*len(frames),380),(246,246,244))
    draw=ImageDraw.Draw(sheet)
    for i,(name,frame) in enumerate(frames):
        sheet.paste(Image.fromarray(frame),(i*340,40))
        draw.text((i*340+10,12),name,fill=(35,35,35))
    sheet.save(out/'sa1044_four_way.png')
    report={'stage':'SA10.44','case':'Juufuutei-Raden_stylecal_source',
        'schema':'sa1044-shared-source-mask-references-expanded-budget-v1',
        'chromium_version':chromium_version,'source_original_sha256':prev.SHA,
        'source_owner_signed_right_arm_delta_pixels':right_delta,
        'original_budget_limit':BUDGET,
        'source_svg_baseline':compare(reference,old,signed),
        'variants':reports,
        'deduplicated_svg_byte_size_research_only':True,
        'expanded_geometry_budget_is_authoritative':True,
        'no_production_changes':True,'full_character_golden_pass':False,
        'release_decision':'REFERENCES_PARITY_PASS_EXPANDED_VERTEX_BUDGET_NO_GO',
        'next':'Seek semantic source-owner compression and cross-case accuracy without waiving expanded budget or protected anatomy'}
    report['output_sha256']={f.name:sha256(f.read_bytes()).hexdigest() for f in sorted(out.iterdir())
                if f.suffix.lower() in ('.svg','.png')}
    (out/'sa1044_metrics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    return report


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--chromium',default='/usr/bin/chromium')
    a=p.parse_args()
    r=evaluate(a.root,a.out,a.chromium)
    print(json.dumps({'gate':r['release_decision'],
      'variants':{k:{'unique':v['unique_plus_stage9'],'expanded':v['expanded_plus_stage9'],
            'rgb_errors':v['metrics']['full_rgb_mismatch'],
            'protected':v['metrics']['protected'],'mask_errors':sum(v['mask_binary_errors'].values())}
            for k,v in r['variants'].items()}},ensure_ascii=False,indent=2))

if __name__=='__main__':main()