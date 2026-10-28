"""Research-only dual-owner class30 extension after a frozen source-only L02 proposal.

SegFormer class30 and independent AnimeSeg generic clothes=10 are observations,
not outerwear truth. Geodesic owner assignment is source-alpha-bound, preserves
all existing owner pixels and forbids 4/8 component merges. Human masks and
coordinates are not inputs. Never release/Golden/Phase4 promotion.
"""
from __future__ import annotations
import numpy as np
from local_l02_guarded_sleeve_geodesic_shadow import _distance_inside
from local_l02_source_palette_sleeve_shadow import _topology_fixed_point
from local_l02_hue_extended_owner_shadow import _assert_component_identity, ExtendedOwnerHold

class DualClass30Hold(ValueError):
    pass

def propose_class30_dual_seed_extension_shadow(*, source_alpha: np.ndarray,
        class_ids: np.ndarray, anime_classes: np.ndarray,
        frozen_owner: np.ndarray) -> tuple[np.ndarray, dict]:
    arrays = (source_alpha, class_ids, anime_classes, frozen_owner)
    if any(type(a) is not np.ndarray or a.dtype != np.uint8 or
           a.ndim != 2 or not a.size for a in arrays):
        raise DualClass30Hold('INVALID_UINT8_INPUT')
    if any(a.shape != source_alpha.shape for a in arrays):
        raise DualClass30Hold('SHAPE_MISMATCH')
    if np.any(class_ids >= 47) or np.any(anime_classes >= 12) or np.any(frozen_owner > 2):
        raise DualClass30Hold('MODEL_OR_OWNER_CLASS_DOMAIN')
    if np.any((frozen_owner > 0) & (source_alpha == 0)):
        raise DualClass30Hold('FROZEN_OWNER_OUTSIDE_SOURCE')
    if (np.any((frozen_owner == 1) & ~np.isin(class_ids,(5,29,30,31,32))) or
        np.any((frozen_owner == 2) & ~np.isin(class_ids,(10,29,30,31,32)))):
        raise DualClass30Hold('FROZEN_OWNER_CLASS_CONFLICT')
    eligible = (frozen_owner == 0) & (source_alpha > 0) & (class_ids == 30) & (anime_classes == 10)
    out = frozen_owner.copy()
    if np.any(eligible):
        # Unlike component-level dual-seed veto, split only on strictly nearer
        # 4-connected geodesic ownership. Equal-distance pixels ABSTAIN.
        dj = _distance_inside(eligible, frozen_owner == 1, 4)
        dc = _distance_inside(eligible, frozen_owner == 2, 4)
        out[(dj > 0) & ((dc < 0) | (dj < dc))] = 1
        out[(dc > 0) & ((dj < 0) | (dc < dj))] = 2
        try:
            out, removed = _topology_fixed_point(frozen_owner, out)
        except Exception as exc:
            raise DualClass30Hold('TOPOLOGY_FIXED_POINT_HOLD') from exc
    else:
        removed = 0
    if (np.any((frozen_owner > 0) & (out != frozen_owner)) or
        np.any((out != frozen_owner) & ~eligible) or
        np.any((out > 0) & (source_alpha == 0))):
        raise DualClass30Hold('FROZEN_OWNER_OR_SOURCE_VIOLATION')
    try:
        for owner_id in (1, 2):
            for connectivity in (4, 8):
                _assert_component_identity(frozen_owner, out, owner_id, connectivity)
    except ExtendedOwnerHold as exc:
        raise DualClass30Hold('OWNER_COMPONENT_IDENTITY_HOLD') from exc
    return out, {
        'schema':'minimalizer/local-l02/class30-dual-seed-shadow/v1',
        'source_only_eligible_px':int(np.count_nonzero(eligible)),
        'source_only_added_px':int(np.count_nonzero(out != frozen_owner)),
        'collision_cut_px':int(removed),
        'source_pixels_generated':0,'original_owner_modified_px':0,
        'human_annotations_used_for_inference':False,
        'independent_generic_clothes_is_outerwear_proof':False,
        'semantic_quality_pass':False,'unseen_character_pass':False,
        'Phase4':'FAIL','L02':'HOLD','L03':'NO_GO',
        'Golden':'HOLD','production':'NO_GO'
    }
