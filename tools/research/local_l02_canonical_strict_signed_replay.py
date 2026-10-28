"""Reconstruct signed H06/H08 L02 owner without a transient cached-best NPZ.

Guarded conservative staged overlay only (2026-10-23 22:53), not main.
Research-only, source-only inference first; human masks loaded only after owner
and SHA are frozen. The private archives stay outside the public repository.
This cannot approve Phase4, L03, Golden, or production.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
from zipfile import ZipFile
import numpy as np
from local_l02_no_merge_signed_replay import (
    REVIEW, verify_archives, load_source_only, postscore, components,
)
from local_l02_composed_dual_contact_shadow import propose_composed_dual_contact_shadow
from local_l02_enclosed_class32_shadow import propose_enclosed_class32_shadow

PINNED_GUARDED_WRAPPER_SHA256 = 'b49d3c0744c838715e44b7405ec0b621c8b356c1de710eff7b803ed71bc196a7'

PINNED_COMPOSED = {
    'H06': 'ceaae1199d673d07411bf120aca46f3415df69c0c5dee1395a2536d414b2602c',
    'H08': '3e46769428946d54f0cc441ead77699a81839cd8e372ca39212e5b7825ee4a1a',
}
PINNED_STRICT = {
    'H06': 'ceaae1199d673d07411bf120aca46f3415df69c0c5dee1395a2536d414b2602c',
    'H08': '32bb5266a479ce64571f190ffebe90b50c01329598408019b363c5ab0c9f0778',
}

def replay(private_dir: Path, case: str) -> dict:
    if case not in PINNED_COMPOSED:
        raise ValueError('ONLY_PINNED_EXPOSED_CASES')
    actual_wrapper_sha = hashlib.sha256(
        (Path(__file__).parent / 'local_l02_composed_dual_contact_shadow.py').read_bytes()
    ).hexdigest()
    if actual_wrapper_sha != PINNED_GUARDED_WRAPPER_SHA256:
        raise ValueError('GUARDED_STAGING_WRAPPER_SHA_MISMATCH')
    verified = verify_archives(private_dir)
    rgba, class_ids, frozen, anime = load_source_only(private_dir, case)
    # IMPORTANT: do not open human labels or use any annotation coordinates here.
    composed, meta1 = propose_composed_dual_contact_shadow(
        source_rgba=rgba, class_ids=class_ids,
        anime_classes=anime, frozen_owner=frozen)
    composed_sha = hashlib.sha256(composed.tobytes()).hexdigest()
    if composed_sha != PINNED_COMPOSED[case]:
        raise ValueError('COMPOSED_BASELINE_SHA_MISMATCH')
    strict, meta2 = propose_enclosed_class32_shadow(
        source_alpha=rgba[..., 3], class_ids=class_ids,
        original_owner=frozen, baseline_owner=composed)
    strict_sha = hashlib.sha256(strict.tobytes()).hexdigest()
    if strict_sha != PINNED_STRICT[case]:
        raise ValueError('STRICT_OWNER_SHA_MISMATCH')
    if (np.any((composed > 0) & (strict != composed)) or
            np.any((strict > 0) & (rgba[..., 3] == 0)) or
            np.any((strict != composed) & (class_ids != 32))):
        raise ValueError('OWNER_SOURCE_OR_CLASS_REGRESSION')
    if components(composed) != components(strict):
        raise ValueError('OWNER_COMPONENT_REGRESSION')
    # Evaluation only after both candidate SHA pins and all source-only gates.
    before = postscore(private_dir, case, composed)
    after = postscore(private_dir, case, strict)
    if (after['known_FP'] > before['known_FP'] or
            after['TP'] < before['TP'] or
            after['known_arm_FP'] > before['known_arm_FP'] or
            after['known_underlayer_FP'] > before['known_underlayer_FP']):
        raise ValueError('SIGNED_KNOWN_P0_REGRESSION')
    # Explicitly-known labels only. Unknown is not a negative.
    with ZipFile(private_dir / REVIEW) as archive:
        with np.load(io.BytesIO(archive.read(
                f'reviews/{case}_HUMAN_VISIBLE_MASKS_PRIVATE.npz')),
                allow_pickle=False) as human:
            missing = (human['outerwear'] > 0) & (strict == 0)
            by_class = {str(int(cid)): int(np.count_nonzero(missing & (class_ids == cid)))
                        for cid in np.unique(class_ids[missing])}
            known = np.zeros(strict.shape, bool)
            for key in ('outerwear', 'underlayer', 'arm_skin', 'neck_skin',
                        'lower_body', 'face_skin', 'hair', 'accessory'):
                known |= human[key] > 0
            new = (strict > 0) & (composed == 0)
            new_true = int(np.count_nonzero(new & (human['outerwear'] > 0)))
            new_false = int(np.count_nonzero(new & known & (human['outerwear'] == 0)))
            new_unknown = int(np.count_nonzero(new & ~known))
    if (int(np.count_nonzero(strict != composed)) !=
            new_true + new_false + new_unknown):
        raise ValueError('ADDITIVE_PIXEL_ACCOUNTING_MISMATCH')
    return {
        'schema': 'minimalizer/local-l02/guarded-canonical-composed-strict-signed-replay/v2',
        'case': case, 'known_case_only': True,
        'guarded_wrapper_sha256': actual_wrapper_sha,
        'staged_overlay_only_not_main': True,
        'archive_manifest_checks': verified,
        'source_only_composed_sha256': composed_sha,
        'source_only_strict_sha256': strict_sha,
        'composed_stage': meta1['schema'],
        'strict_stage': meta2['schema'],
        'composed': before, 'strict': after,
        'strict_additive_true_px': new_true,
        'strict_additive_known_false_px': new_false,
        'strict_additive_unknown_px': new_unknown,
        'remaining_known_fn_by_frozen_class': by_class,
        'private_arrays_or_coordinates_emitted': False,
        'human_labels_used_for_inference': False,
        'unknown_treated_as_negative': False,
        'unseen_blind_pass': False,
        'Phase4': 'FAIL', 'L02': 'HOLD', 'L03': 'NO_GO',
        'Golden': 'HOLD', 'production': 'NO_GO',
    }

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--private-dir', type=Path, required=True)
    p.add_argument('--case', choices=('H06', 'H08'), required=True)
    args = p.parse_args()
    print(json.dumps(replay(args.private_dir, args.case), indent=2, sort_keys=True))
