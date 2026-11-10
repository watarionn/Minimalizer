"""Research-only class32 color-conflict abstention.

All decisions use frozen model classes/owner and original RGB/alpha only.
No human masks, annotations, or learned per-character thresholds are inputs.
This is a hypothesis, not a semantic-quality or release approval.
"""
from __future__ import annotations
import numpy as np
from scipy import ndimage

class ColorConflictHold(ValueError):
    pass

def _rgb_to_hsv_numpy(rgb):
    rgb = rgb.astype(np.float32) / 255.0
    maximum = rgb.max(axis=-1)
    minimum = rgb.min(axis=-1)
    delta = maximum - minimum
    saturation = np.divide(delta, maximum, out=np.zeros_like(maximum), where=maximum>0)
    h = np.zeros_like(maximum)
    r,g,b = rgb[...,0],rgb[...,1],rgb[...,2]
    positive = delta > 1e-8
    m = positive & (maximum == r)
    h[m] = ((g[m]-b[m])/delta[m])%6
    m = positive & (maximum == g)
    h[m] = (b[m]-r[m])/delta[m]+2
    m = positive & (maximum == b)
    h[m] = (r[m]-g[m])/delta[m]+4
    return h/6, saturation, maximum

def propose_class32_hue_conflict_abstention(source_rgba, class_ids, frozen_owner, *, min_region=64):
    """Conservatively abstain on saturated, strongly seed-hue-conflicting class32.

    Requires dominant saturated class5/10 seed hue and leaves all non-class32
    owner unchanged. Rejects any proposal that splits an original owner island.
    90-degree angular hue gap, 30% saturation, 5x5 consensus are fixed a priori.
    """
    if not isinstance(source_rgba,np.ndarray) or source_rgba.dtype != np.uint8 or source_rgba.ndim != 3 or source_rgba.shape[2] != 4:
        raise ColorConflictHold('RGBA_CONTRACT')
    shape = source_rgba.shape[:2]
    if (class_ids.shape != shape or frozen_owner.shape != shape or
        class_ids.dtype != np.uint8 or frozen_owner.dtype != np.uint8 or
        min_region != 64):
        raise ColorConflictHold('INPUT_CONTRACT')
    if np.any(~np.isin(frozen_owner,[0,1,2])):
        raise ColorConflictHold('OWNER_DOMAIN')
    if (np.any((frozen_owner==1)&(~np.isin(class_ids,[5,32]))) or
        np.any((frozen_owner==2)&(~np.isin(class_ids,[10,32])))):
        raise ColorConflictHold('OWNER_CLASS_CONFLICT')
    if np.any((frozen_owner>0)&(source_rgba[:,:,3]==0)):
        raise ColorConflictHold('SOURCE_ALPHA')
    hue,sat,value = _rgb_to_hsv_numpy(source_rgba[:,:,:3])
    seed = (frozen_owner>0)&np.isin(class_ids,[5,10])&(sat>=0.30)
    if seed.sum()<64:
        raise ColorConflictHold('NO_SATURATED_SEED')
    # A dominant seed hue is selected without assuming all class10 pixels are
    # semantically correct (a second color mode may be trousers or accessory).
    histogram, _ = np.histogram(hue[seed], bins=18, range=(0,1))
    dominant = int(np.argmax(histogram))
    fraction = float(histogram[dominant] / seed.sum())
    if fraction < 0.55:
        raise ColorConflictHold('NO_DOMINANT_SEED_HUE')
    anchor = 2*np.pi*((dominant+0.5)/18)
    gap = np.abs(np.angle(np.exp(1j*(2*np.pi*hue-anchor))))
    saturated_conflict=(sat>=0.30)&(gap>=np.pi/2)
    # Neutral-white cloth can be a distinct underlayer despite hue undefined.
    # Only a strong-saturation seed allows this independent color conflict.
    achromatic_conflict=(sat<0.15)&(value>0.50)&(np.median(sat[seed])>0.30)
    conflict=(frozen_owner>0)&(class_ids==32)&(saturated_conflict|achromatic_conflict)
    # Require 5x5 local consensus to avoid fine edge/texture edits.
    local=ndimage.uniform_filter(conflict.astype(np.float32),size=5,mode='constant')
    conflict &= (local>=0.60)
    labels,n=ndimage.label(conflict,structure=np.ones((3,3),dtype=np.uint8))
    sizes=np.bincount(labels.ravel())
    # Admit complete conflict regions only when they preserve owner topology.
    # Avoid the failure mode of a blanket pixelwise veto splitting coat panels.
    proposal=frozen_owner.copy()
    structure=np.ones((3,3),dtype=np.uint8)
    accepted=0
    skipped=0
    orphan_abstained=0
    for label in sorted(range(1,n+1),key=lambda i:(-sizes[i],i)):
        if sizes[label]<min_region:continue
        region=(labels==label)
        trial=proposal.copy()
        trial[region]=0
        # Only original components that had a trusted model class5/10 seed
        # may lose newly isolated non-seed class32 fragments. Do not split any
        # seed-bearing component into two or erase seed pixels.
        okay=True
        orphan=0
        for oid in np.unique(proposal[region]):
            if oid==0:continue
            orig_labels,_=ndimage.label(proposal==oid,structure=structure)
            for orig_id in np.unique(orig_labels[region]):
                if orig_id==0:continue
                original=(orig_labels==orig_id)
                seed_in=original & np.isin(class_ids,[5,10])
                if not seed_in.any():
                    okay=False
                    break
                remain_labels,_=ndimage.label(original&(trial==oid),structure=structure)
                seed_parts=np.unique(remain_labels[seed_in]);seed_parts=seed_parts[seed_parts>0]
                if len(seed_parts)!=1:
                    okay=False
                    break
                stray=(original&(trial==oid)&(remain_labels!=seed_parts[0]))
                if np.any(stray & np.isin(class_ids,[5,10])):
                    okay=False
                    break
                orphan+=int(stray.sum())
                trial[stray]=0
            if not okay:break
        if not okay:
            skipped+=1
            continue
        proposal=trial
        accepted+=1
        orphan_abstained+=orphan
    conflict=(proposal!=frozen_owner)
    return proposal, {'abstained_pixels':int(conflict.sum()),'dominant_seed_fraction':fraction,'accepted_regions':accepted,'skipped_regions':skipped,'orphan_abstained':orphan_abstained,
                      'semantic_quality_pass':False,'release_authorized':False}
