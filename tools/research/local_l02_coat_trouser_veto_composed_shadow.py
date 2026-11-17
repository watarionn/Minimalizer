"""Research-only composition of H06 class32 hue veto and class10 color-mode veto.

Both independently remove frozen owners; their intersection is source-only.
No human mask or coordinates enter inference. 4/8 component identity is a
hard gate. This does not prove the unknown-region trousers/coat semantics.
"""
from __future__ import annotations
import numpy as np
from local_l02_hue_extended_owner_shadow import (
    propose_hue_extended_owner_shadow, _assert_component_identity, ExtendedOwnerHold)
from local_l02_color_owner_coherent_abstain_shadow import propose_coherent_color_owner_shadow

class CoatTrouserVetoHold(ValueError):
    pass


def propose_coat_trouser_veto_shadow(*, source_rgba, class_ids,
                                    independent_outerwear, frozen_owner):
    hue, hue_meta = propose_hue_extended_owner_shadow(
        source_rgba=source_rgba, class_ids=class_ids, frozen_owner=frozen_owner)
    color, color_meta = propose_coherent_color_owner_shadow(
        source_rgba=source_rgba, class_ids=class_ids,
        independent_outerwear=independent_outerwear, frozen_owner=frozen_owner)
    if np.any((hue != 0) & (hue != frozen_owner)) or np.any((color != 0) & (color != frozen_owner)):
        raise CoatTrouserVetoHold('UPSTREAM_OWNER_PROMOTION')
    out = hue.copy()
    out[(frozen_owner > 0) & (color == 0)] = 0
    for owner_id in (1, 2):
        for neighborhood in (4, 8):
            try:
                _assert_component_identity(frozen_owner, out, owner_id, neighborhood)
            except ExtendedOwnerHold as exc:
                raise CoatTrouserVetoHold('COMPOSED_OWNER_TOPOLOGY_CHANGED') from exc
    if (np.any((out != 0) & (out != frozen_owner)) or
            np.any((out > 0) & (source_rgba[..., 3] == 0))):
        raise CoatTrouserVetoHold('SOURCE_OR_OWNER_ESCAPE')
    return out, {
        'schema': 'minimalizer/local-l02/coat-trouser-veto-composed-shadow/v1',
        'hue_abstained_pixels': int(np.count_nonzero((frozen_owner > 0) & (hue == 0))),
        'color_abstained_pixels': int(np.count_nonzero((frozen_owner > 0) & (color == 0))),
        'total_abstained_pixels': int(np.count_nonzero((frozen_owner > 0) & (out == 0))),
        'source_pixels_generated': 0, 'owner_promotions': 0,
        'human_annotations_used_for_inference': False,
        'known_case_explored': True, 'independent_unseen_character_pass': False,
        'semantic_quality_pass': False, 'quality': 'FAIL',
        'L02': 'HOLD', 'L03': 'NO_GO', 'Golden': 'HOLD', 'production': 'NO_GO',
        'hue_stage': hue_meta['schema'], 'color_stage': color_meta['schema'],
    }
