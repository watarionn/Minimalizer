"""Opt-in signed H06/H08 conservative-vs-selective owner replay (A research).

Private archives remain in the user's authorized private Drive. Both owner
arrays are frozen, digested and topology-checked before any postscore reads
human annotations. This tool never emits original pixels or mask coordinates.
The selective mode is never a release/Golden approval and never replaces the
conservative baseline automatically.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from local_l02_no_merge_signed_replay import verify_archives, load_source_only, postscore, components
from local_l02_composed_dual_contact_shadow import propose_composed_dual_contact_shadow
from local_l02_cross_owner_contact_gate import verify_no_new_cross_owner_contacts


def run(private_dir: Path, cases: tuple[str, ...] = ('H06', 'H08')) -> dict:
    if not cases or len(set(cases)) != len(cases) or any(c not in ('H06', 'H08') for c in cases):
        raise ValueError('UNPINNED_OR_DUPLICATED_EXPOSED_CASE')
    verified = verify_archives(private_dir)
    frozen = {}
    for case in cases:
        rgba, cls, owner, anime = load_source_only(private_dir, case)
        outputs = {}
        for mode in ('conservative', 'selective'):
            out, info = propose_composed_dual_contact_shadow(
                source_rgba=rgba, class_ids=cls, anime_classes=anime,
                frozen_owner=owner, contact_repair_mode=mode)
            if np.any((out > 0) & (rgba[..., 3] == 0)):
                raise ValueError('OWNER_OUTSIDE_SIGNED_ALPHA')
            verify_no_new_cross_owner_contacts(before=owner, after=out)
            outputs[mode] = {
                'owner_sha256': hashlib.sha256(out.tobytes()).hexdigest(),
                'source_only_added_px': int(np.count_nonzero((owner == 0) & (out > 0))),
                'component_counts': components(out),
                'repair': info['cross_owner_contact_addition_repair'],
                '_owner_for_postscore': out,
            }
        frozen[case] = outputs
    # No postscore call above this line: no labels influence either proposal.
    for case, outputs in frozen.items():
        for mode in ('conservative', 'selective'):
            row = outputs[mode]
            row['known_only_postscore'] = postscore(private_dir, case, row.pop('_owner_for_postscore'))
        a = outputs['conservative']['known_only_postscore']
        b = outputs['selective']['known_only_postscore']
        outputs['comparison'] = {
            'known_TP_delta': b['TP'] - a['TP'],
            'known_FP_delta': b['known_FP'] - a['known_FP'],
            'known_FN_delta': b['known_FN'] - a['known_FN'],
            'quality_pass': False, 'candidate_auto_promoted': False,
        }
    return {
        'schema': 'minimalizer/local-l02/selective-signed-comparison/v1',
        'private_manifest_counts_verified': verified,
        'signed_source_authenticated_before_inference': True,
        'both_candidates_frozen_before_postscore': True,
        'human_annotations_used_for_inference': False,
        'unknown_pixels_not_treated_as_negative': True,
        'cases': frozen,
        'new_unseen_character_quality': 'PENDING',
        'Phase4': 'FAIL', 'L02': 'HOLD', 'L03': 'NO_GO',
        'Golden': 'HOLD', 'production': 'NO_GO',
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--private-dir', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.private_dir), sort_keys=True, indent=2))
