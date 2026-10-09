"""Signed read-only Stage8 budget lower-bound audit. Research only, never a simplifier.

This program reports arithmetic counterfactuals (not allowed modifications) to
show whether removing small/degenerate rings could even satisfy the historical
source-ring cap. It does not alter original scenes, policies, or owner geometry.
"""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

SIGNED = {
    'GC001': {
        'scene_sha256': '7eed624b31c9a117b6d7e6e5fe9788067f00b3fc3e8889fd250c14adaaac8f08',
        'metrics_sha256': 'a3ca4f09a033603692e775f2587052c5e9e0112dd3b1868039c655ee1e4c085c',
        'source_sha256': '75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e',
        'ring_vertices': 3604, 'cap': 1887, 'ring_count': 203,
    },
    'Raden': {
        'scene_sha256': 'be6001f3607466617a4c2db92cdc92ad81296a403cdeeef009ac0628dc149b5f',
        'metrics_sha256': 'ea9415e172b17c6a52fb668c5183809af11d33afec809a308e90c1e58ecd501f',
        'source_sha256': 'd9982c74a2d9a0a8cd3547f3f5cc603a809e942e6dcf62b98e36bfa019903a00',
        'ring_vertices': 2370, 'cap': 1412, 'ring_count': 61,
    },
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def counterfactual_bounds(counts, cap, hole_vertices):
    if cap <= 0 or not counts or any(n < 1 for n in counts):
        raise ValueError('INVALID_BUDGET_OR_RINGS')
    total = sum(counts)
    scenarios = {}
    for cutoff in (2, 4, 8, 16):
        deleted = sum(n for n in counts if n <= cutoff)
        remaining = total - deleted
        scenarios[f'all_rings_le_{cutoff}'] = {
            'hypothetically_removed_vertices': deleted,
            'remaining_vertices': remaining,
            'still_over_cap': max(0, remaining - cap),
            'meets_cap_by_count_only': remaining <= cap,
            'legally_removable': False,
        }
    if hole_vertices < 0 or hole_vertices > total:
        raise ValueError('INVALID_HOLE_COUNT')
    remaining = total - hole_vertices
    scenarios['all_holes'] = {
        'hypothetically_removed_vertices': hole_vertices,
        'remaining_vertices': remaining,
        'still_over_cap': max(0, remaining - cap),
        'meets_cap_by_count_only': remaining <= cap,
        'legally_removable': False,
    }
    return scenarios


def inspect_case(case, scene_file, metrics_file):
    if case not in SIGNED:
        raise ValueError('UNKNOWN_CASE')
    pinned = SIGNED[case]
    original_bytes = Path(scene_file).read_bytes()
    if sha(original_bytes) != pinned['scene_sha256']:
        raise ValueError('SCENE_PIN_FAIL')
    scene = json.loads(original_bytes)
    metrics_bytes = Path(metrics_file).read_bytes()
    if sha(metrics_bytes) != pinned['metrics_sha256']:
        raise ValueError('METRICS_PIN_FAIL')
    metrics = json.loads(metrics_bytes)
    if metrics.get('adaptive_vector_sha256') != pinned['scene_sha256']:
        raise ValueError('METRICS_SCENE_PIN_FAIL')
    if scene.get('original_source_sha256') != pinned['source_sha256'] or metrics.get('original_source_sha256') != pinned['source_sha256']:
        raise ValueError('SOURCE_PIN_FAIL')
    if scene.get('production_authorized') is not False or scene.get('research_only') is not True or metrics.get('promotion_authorized') is not False:
        raise ValueError('PROMOTION_GUARD_FAIL')
    if metrics.get('candidate_vertices', {}).get('ring_vertices') != pinned['ring_vertices']:
        raise ValueError('VERTEX_PIN_FAIL')
    if metrics.get('original_budget', {}).get('ring_vertices') != pinned['cap']:
        raise ValueError('CAP_PIN_FAIL')

    counts = []
    owners = defaultdict(int)
    roles = defaultdict(int)
    owner_ring_count = defaultdict(int)
    for primitive in scene['primitives_back_to_front']:
        owner = primitive['composition_part']
        for ring in primitive['parameters']['rings']:
            n = len(ring['points'])
            if n < 1 or ring.get('role') not in ('fill', 'hole'):
                raise ValueError('RING_SCHEMA_FAIL')
            counts.append(n)
            owners[owner] += n
            roles[ring['role']] += n
            owner_ring_count[owner] += 1
    total = sum(counts)
    if total != pinned['ring_vertices'] or len(counts) != pinned['ring_count']:
        raise ValueError('RING_COUNT_FAIL')
    if roles['fill'] != metrics['candidate_vertices']['component_vertices']:
        raise ValueError('COMPONENT_COUNT_FAIL')

    cap = pinned['cap']
    excess = total - cap
    if excess <= 0:
        raise ValueError('EXPECTED_HISTORICAL_FAIL')
    scenarios = counterfactual_bounds(counts, cap, roles['hole'])
    # Even if every 1- or 2-point ring vanished, nondegenerate rings must
    # still lose this many vertices. This is an optimistic arithmetic bound,
    # not a topology-preserving removal proposal.
    degenerate_vertices = scenarios['all_rings_le_2']['hypothetically_removed_vertices']
    return {
        'case': case,
        'status': 'RESEARCH_ONLY_HOLD',
        'scene_sha256': pinned['scene_sha256'],
        'metrics_sha256': pinned['metrics_sha256'],
        'source_sha256': pinned['source_sha256'],
        'ring_vertices': total,
        'immutable_ring_cap': cap,
        'over_cap': excess,
        'required_total_reduction_pct': round(excess / total * 100, 4),
        'ring_count': len(counts),
        'fill_vertices': roles['fill'],
        'hole_vertices': roles['hole'],
        'degenerate_vertices': degenerate_vertices,
        'minimum_reduction_from_non_degenerate_if_all_degenerates_removed': max(0, excess - degenerate_vertices),
        'owner_vertices': dict(sorted(owners.items())),
        'owner_ring_counts': dict(sorted(owner_ring_count.items())),
        'scenarios': scenarios,
        'scene_mutated': False,
        'original_budget_redefined': False,
        'human_golden': 'PENDING',
        'real_chromium': 'NOT_RUN',
        'release_authorized': False,
        'production_changed': False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--gc-scene', type=Path, required=True)
    parser.add_argument('--gc-metrics', type=Path, required=True)
    parser.add_argument('--raden-scene', type=Path, required=True)
    parser.add_argument('--raden-metrics', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    results = [inspect_case('GC001', args.gc_scene, args.gc_metrics),
               inspect_case('Raden', args.raden_scene, args.raden_metrics)]
    args.output.write_text(json.dumps({'schema': 'c03-stage8-budget-bounds-v1', 'results': results,
       'source_owner_visual_parity': 'NOT_PROVEN', 'stage8_policy': 'UNCHANGED_HOLD',
       'release_authorized': False}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

if __name__ == '__main__':
    main()
