"""H04-specific offline research shadow runner. Does NOT update Minimalizer workers.

Requires signed source PNG/WebP + trusted byte digest and versioned observer NPZ.
Does not accept any human polygons. Can only record candidate masks and HOLD status.
"""
from __future__ import annotations
import argparse,hashlib,json,io
from pathlib import Path
from PIL import Image
import numpy as np
from local_l02_owner_topology_candidate import resolve_owners,Hold,PARTS

def digest(b):return hashlib.sha256(b).hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--source-sha256',required=True)
    p.add_argument('--inherited-soft-npz',type=Path,required=True)
    p.add_argument('--inherited-soft-sha256',required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args()
    if a.output_dir.exists():raise Hold('output path already exists: refuse overwrite')
    source_raw=a.source.read_bytes()
    if digest(source_raw)!=a.source_sha256:raise Hold('signed source hash mismatch')
    source=np.asarray(Image.open(io.BytesIO(source_raw)).convert('RGBA'),dtype=np.uint8)
    owner_bytes=a.inherited_soft_npz.read_bytes()
    if digest(owner_bytes)!=a.inherited_soft_sha256:raise Hold('inherited soft observation hash mismatch')
    with np.load(io.BytesIO(owner_bytes),allow_pickle=False) as z:
        wanted={'owner__'+k for k in PARTS}|{'observation__jacket'}
        if not wanted.issubset(set(z.files)):raise Hold('inherited source owner or 2-observer agreement missing')
        owners={k:z['owner__'+k].astype(bool) for k in PARTS}
        evidence=z['observation__jacket'].astype(bool)
    new,core,report=resolve_owners(source,owners,evidence,source_bytes=source_raw,expected_sha256=a.source_sha256)
    a.output_dir.mkdir(parents=True,exist_ok=False)
    artifact=a.output_dir/'candidate_owner_not_approved.npz'
    np.savez_compressed(artifact,**{'candidate__'+k:new[k].astype(np.uint8) for k in PARTS},observation__jacket_core=core.astype(np.uint8))
    r=report.as_dict()
    r.update(schema='minimalizer-local-l02-exclusive-owner-research/v1',source_sha256=a.source_sha256,
       inherited_soft_observer_npz_sha256=a.inherited_soft_sha256,candidate_npz_sha256=digest(artifact.read_bytes()),
       user_human_annotations_in_inference=False,approved_human_labels_external=0,
       independent_cross_character_jacket_iou=None,quality_gold='HOLD',production_release='NO_GO',
       pinned_phase5_executed_in_this_process=False)
    (a.output_dir/'candidate_metrics_sourcefree.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'artifact_sha256':r['candidate_npz_sha256'],'candidate_head_components':r['repaired_components']['head'],
        'candidate_hair_components':r['repaired_components']['hair'],'candidate_torso_components':r['repaired_components']['torso'],
        'source_union_xor':r['signed_union_xor_pixels'],'protected_xor':r['protected_xor_pixels'],
        'quality':'HOLD','release':'NO_GO'},sort_keys=True))
if __name__=='__main__':main()
