"""C02b3 source-bound appearance probe; never a release candidate."""
import hashlib, json, zipfile
from pathlib import Path
from io import BytesIO
import cv2, numpy as np
from PIL import Image
SOURCE='75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e'
SNAP='89286cb1e8cf2003f02ec2dbab2a80dcf3da26b902123255a9cc17767855e434'
ARM='8829b6865a50abee2fac820cfe250c35e3089a8f5eb4c3754b633a7d1327ac58'

def digest(b): return hashlib.sha256(b).hexdigest()
def binary(b):
    a=np.asarray(Image.open(BytesIO(b)).convert('L'))
    if a.shape!=(340,340) or not np.isin(a,(0,255)).all(): raise ValueError('MASK_SHAPE_OR_VALUES')
    return a>0

def probe(source:Path,snapshot:Path):
    if digest(source.read_bytes())!=SOURCE: raise ValueError('SOURCE_PIN_FAIL')
    if digest(snapshot.read_bytes())!=SNAP: raise ValueError('SNAPSHOT_PIN_FAIL')
    rgb=np.asarray(Image.open(source).convert('RGBA'))
    if rgb.shape!=(340,340,4): raise ValueError('SOURCE_CANVAS_FAIL')
    rgb=rgb[:,:,:3]
    with zipfile.ZipFile(snapshot) as z:
        if digest(z.read('phase_04/part_masks/right_arm.png'))!=ARM: raise ValueError('ARM_PIN_FAIL')
        manifest=json.loads(z.read('PRIVATE_SHA_MANIFEST.json'))
        if manifest['source_sha256']!=SOURCE or manifest['promotion_authorized'] is not False: raise ValueError('MANIFEST_FAIL')
        for n,h in manifest['files'].items():
            if digest(z.read(n))!=h: raise ValueError('MEMBER_PIN_FAIL')
        subject=binary(z.read('phase_03/03_subject_mask.png'))
        arm=binary(z.read('phase_04/part_masks/right_arm.png'))
        seed=np.logical_or.reduce([binary(z.read(f'phase_04/part_masks/{k}.png')) for k in ('face','torso','major_clothing')])
    edges=cv2.Canny(cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY),50,120)>0
    metrics={}; variants=[]
    for radius in (2,4,6):
        init=np.full((340,340),cv2.GC_PR_BGD,np.uint8)
        init[subject]=cv2.GC_PR_FGD
        init[:3]=cv2.GC_BGD;init[-3:]=cv2.GC_BGD
        init[:,:3]=cv2.GC_BGD;init[:,-3:]=cv2.GC_BGD
        eroded=cv2.erode(seed.astype('uint8'),np.ones((2*radius+1,)*2,np.uint8))>0
        eroded &= subject
        eroded[:3]=False;eroded[-3:]=False;eroded[:,:3]=False;eroded[:,-3:]=False
        if eroded.sum()<100: raise ValueError('SEED_FAIL')
        init[eroded]=cv2.GC_FGD
        cv2.setRNGSeed(0)
        cv2.grabCut(np.ascontiguousarray(rgb),init,None,np.zeros((1,65)),np.zeros((1,65)),5,cv2.GC_INIT_WITH_MASK)
        keep=arm & ((init==cv2.GC_FGD)|(init==cv2.GC_PR_FGD))
        drop=arm & ~keep
        metrics[str(radius)]={'retained':int(keep.sum()),'removed':int(drop.sum()),'removed_source_edges':int((drop&edges).sum()),'components':cv2.connectedComponents(keep.astype('uint8'))[0]-1,'added_pixels':int((keep&~arm).sum())}
        variants.append(keep)
    union=np.logical_or.reduce(variants);inter=np.logical_and.reduce(variants)
    return {'stage':'C02b3','status':'RESEARCH_HOLD','source_pinned':True,'snapshot_pinned':True,'original_arm_pixels':int(arm.sum()),'original_arm_edges':int((arm&edges).sum()),'disputed_pixels':int((union&~inter).sum()),'variants':metrics,'anatomy_ground_truth':False,'human_golden':'PENDING','raden_owner_control':'NOT_RUN','chromium':'NOT_RUN','stage8':'HOLD','release_authorized':False,'production_changed':False}
