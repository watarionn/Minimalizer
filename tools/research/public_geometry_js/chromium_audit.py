"""Source-signed SVG raster audit, real Chromium, candidate-only. No face painting.
Input SVG files and original Stage04 masks must be verified by the preceding signed-source audit.
The browser render is tested at DPR 1/4: pixels with alpha beyond source mask cause HOLD.
"""
from __future__ import annotations
import hashlib, io, json, base64, argparse
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--input-root', type=Path, required=True)
parser.add_argument('--candidate-root', type=Path, required=True)
parser.add_argument('--signed-manifest', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
INPUT = args.input_root.resolve()
CANDIDATES = args.candidate_root.resolve()
OUT = args.out.resolve()
OUT.mkdir(parents=True, exist_ok=True)
spec = json.loads(args.signed_manifest.read_text())
report = {'schema': 'public-js-geometry-chromium-real-v1',
          'quality': 'RESEARCH_ONLY', 'production': 'UNCHANGED',
          'face_policy': 'no_face_features_rendered', 'visualGolden': 'HOLD',
          'signed_source_sha256_verified_again': True, 'cases': {}, 'svg_render_sha256':{}}

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    report['chromium'] = browser.version
    for case in ('GC001', 'Raden'):
        report['cases'][case] = {}
        for role in ('left_arm','right_arm'):
            rec = spec['cases'][case]['signed_roles'][role]
            mask_path = INPUT / case / f'signed_{role}_stage04_mask.png'
            actual_sha = hashlib.sha256(mask_path.read_bytes()).hexdigest()
            if actual_sha != rec['sha256']:
                raise RuntimeError('original Stage04 signed mask SHA mismatch')
            src_mask = (np.asarray(Image.open(mask_path).convert('L')) >= 127)
            svgfile = CANDIDATES / f'{case}_{role}_triangles.svg'
            raw = svgfile.read_bytes()
            if b'<image' in raw.lower() or b'foreignobject' in raw.lower():
                raise RuntimeError('raster embedding prohibited')
            entry = {'svg_sha256': hashlib.sha256(raw).hexdigest(),
                     'source_signed_mask_sha256':actual_sha, 'signed_pixels':int(src_mask.sum()),
                     'rendering':{}}
            for scale in (1,4):
                context=browser.new_context(viewport={'width':340,'height':340},device_scale_factor=scale)
                page=context.new_page()
                page.set_content('<html><head><style>html,body{margin:0;background:transparent}img{display:block;width:340px;height:340px}</style></head><body><img src="data:image/svg+xml;base64,'+base64.b64encode(raw).decode('ascii')+'" /></body></html>', wait_until='load')
                png = page.screenshot(omit_background=True)
                context.close()
                image = Image.open(io.BytesIO(png)).convert('RGBA')
                if image.size != (340*scale,340*scale):
                    raise RuntimeError('unexpected browser pixel dimensions')
                output = OUT / f'{case}_{role}_chromium_{scale}x.png'
                output.write_bytes(png)
                alpha = np.asarray(image)[:,:,3]
                signed=np.repeat(np.repeat(src_mask,scale,axis=0),scale,axis=1)
                outside_opaque=int(((alpha>=128)&~signed).sum())
                outside_any=int(((alpha>0)&~signed).sum())
                missing_opaque=int(((alpha<128)&signed).sum())
                opaque_inside=int(((alpha>=128)&signed).sum())
                entry['rendering'][f'{scale}x']={
                  'outside_opaque_subpixels':outside_opaque,
                  'outside_any_alpha_subpixels':outside_any,
                  'missing_opaque_signed_subpixels':missing_opaque,
                  'opaque_source_coverage':round(opaque_inside/max(1,int(signed.sum())),6),
                  'png_sha256':hashlib.sha256(png).hexdigest(),
                  'pixel_center_only_gate_not_authoritative':False,
                  'browser_mask_strict_zero_extra':outside_any==0,
                }
            entry['release_eligible']=False
            report['cases'][case][role]=entry
    browser.close()

# Human inspection aid: no invented character content, candidate triangle layers shown on blank background.
board=Image.new('RGB',(340*4, 360*2),'#f3f3f3')
paint=ImageDraw.Draw(board)
for ci,case in enumerate(('GC001','Raden')):
    y=ci*360
    src=Image.open(INPUT/case/f'{case}_source.png').convert('RGB')
    board.paste(src,(0,y+20))
    paint.text((4,y+2),f'{case} original',fill='#111111')
    for j,(role,lab) in enumerate([('left_arm','left arm'),('right_arm','right arm')],start=1):
        cand=Image.open(OUT/f'{case}_{role}_chromium_1x.png').convert('RGBA')
        bg=Image.new('RGBA',(340,340),'white')
        bg.alpha_composite(cand)
        board.paste(bg.convert('RGB'),(j*340,y+20))
        paint.text((j*340+4,y+2),f'{case} {lab} candidate',fill='#111111')
    # source-signed reference, no revisions
    ref=Image.open(INPUT/case/'signed_full_opencv_reference.png').convert('RGB')
    board.paste(ref,(3*340,y+20))
    paint.text((3*340+4,y+2),'SA10.41 signed reference',fill='#111111')
boardpath=OUT/'real_two_case_chromium_comparison.png'
board.save(boardpath)
report['comparison_sha256']=hashlib.sha256(boardpath.read_bytes()).hexdigest()
report['all_arm_browser_strict_zero_extra']=all(
  item['rendering']['4x']['outside_any_alpha_subpixels']==0
  for case in report['cases'].values() for item in case.values())
report['release_verdict']='HOLD' if not report['all_arm_browser_strict_zero_extra'] else 'HOLD_PENDING_VISUAL_AND_TOPOLOGY'
(OUT/'chromium_metrics.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
print('Chromium:',report['chromium'])
for case,v in report['cases'].items():
 for role,m in v.items():
  print(case,role,'1x',m['rendering']['1x'],'4x',m['rendering']['4x'])
print('Source candidate release:',report['release_verdict'])
