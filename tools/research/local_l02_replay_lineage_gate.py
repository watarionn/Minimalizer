"""Fail-closed exact-PR dependency lineage for dormant L02 signed replay.

This verifies public source blobs, not signed image provenance or semantic
quality. The pinned tree is PR #445's reviewed dependency closure at
2026-10-29; main lacks the staged composition modules. Never treat this as
an exact-main or Phase4 acceptance receipt.
"""
from __future__ import annotations

import ast
import hashlib
from pathlib import Path


class ReplayLineageHold(ValueError):
    """The imported research code does not match the reviewed PR lineage."""


# GitHub contents API Git-blob SHA1, read from exact PR #445 head 2bfbb29a.
# These are code blobs only. No private source, mask, coordinates or weights.
PR_445_REPLAY_BLOBS = {
    'local_l02_no_merge_signed_replay': 'e2097a31c943623018f3483b323dbcaa4785283c',
    'local_l02_sleeve_no_merge_shadow': '422cde9a48c24b03e3a2541c4637d4ab85dd847f',
    'local_l02_guarded_sleeve_geodesic_shadow': '3a29496d6acfdfe62214359c8af8a4ec07803ec4',
    'local_l02_enclosed_class32_shadow': '4205098cf33fe3336b2570484199dde36dd43e34',
    'local_l02_composed_dual_contact_shadow': '2296cbc1607f833a6a91409b0d705561947943d1',
    'local_l02_cross_owner_selective_veto_shadow': '5483df20e05364f3aec9b547275d3c4978eb36c5',
    'local_l02_cross_owner_contact_gate': 'd5c1c99b50acbe94db094675170d6f3689f50b13',
    'local_l02_frozen_owner_transition_audit': 'b284d5699424284d7b9d72cf62be8e7ff2306a5c',
    'local_l02_class32_independent_contact_shadow': '7834468a5ec1d999a8ce8bbcb5fd6f0f09e56e43',
    'local_l02_hue_extended_owner_shadow': '553c1e9142c1c34463bc85964a66a0692614d16d',
    'local_l02_hue_topology_repair_shadow': '664f6bc0769189daff1dca50efbaa1420b0807da',
    'local_l02_hue_seed_contact_shadow': '15ef4c8680f3fe3139176d9dc1d5af77063308b7',
    'local_l02_hue_conflict_abstain': 'b12bb2fc969b42641b39285f3a8ac5a9a8204346',
    'local_l02_source_palette_sleeve_shadow': 'b42ac51a067c3ef60e25f07914edc22c1b425c48',
    'local_l02_class30_dual_seed_extension_shadow': '19d6005c3be3a069ea224b0c8ff41b1d71b250b5',
    'local_l02_composed_p0_shadow': '3e9dc88afcd6e8fd9a65cfb4881622ed7dca0163',
    'local_l02_coat_trouser_veto_composed_shadow': '209c1f7a43ba2cc50a029f21d8049af26e8485fa',
    'local_l02_color_owner_coherent_abstain_shadow': 'bd30b03b29ebafabbbeaca32136f42dd9bce595a',
    'local_l02_color_owner_conflict_shadow': '3407b3dcec493e82312f0e277e0b917edff35635',
    'local_l02_class30_source_extension_shadow': 'c4e6a1d09697fd4b47970f5bea08762159b30772',
    # The signed Run30 dual-owner adapter also executes these three modules.
    # They must be pinned before the runner reads any private source bytes.
    'local_l02_dual_owner_lab_reach_shadow': '1bfe6ef0008784e6b3981e185646a02ffb239124',
    'local_l02_dual_owner_signed_input_adapter': '4ce7b781429d5d87a0983efe344d9bf55b9e39e4',
    'local_l02_signed_shadow_output_gate': '1de4565d35c95bc33e2f25c042ee9892d1973295',
}


def _git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(data)).encode('ascii') + b'\0' + data).hexdigest()


def _local_imports(data: bytes, name: str) -> set[str]:
    """Inspect pinned source for any unpinned local research dependency."""
    try:
        tree = ast.parse(data.decode('utf-8'))
    except (SyntaxError, UnicodeDecodeError) as exc:
        raise ReplayLineageHold('INVALID_PINNED_SOURCE_SYNTAX:' + name) from exc
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            if node.module.startswith('local_l02_'):
                imports.add(node.module)
        elif isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names
                           if alias.name.startswith('local_l02_'))
    return imports


def _verify_lineage(root: Path, pins: dict[str, str]) -> dict:
    """Pure source-only verifier for pinned dependencies and local imports."""
    if (type(pins) is not dict or not pins or any(
            type(k) is not str or not k.startswith('local_l02_') or
            '/' in k or '\\' in k or '..' in k or
            type(v) is not str or len(v) != 40 or
            any(c not in '0123456789abcdef' for c in v)
            for k, v in pins.items())):
        raise ReplayLineageHold('INVALID_EXTERNAL_BLOB_PINS')
    for name, sha in sorted(pins.items()):
        path = root / (name + '.py')
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 1_000_000:
            raise ReplayLineageHold('MISSING_OR_UNSAFE_DEPENDENCY:' + name)
        data = path.read_bytes()
        if _git_blob_sha(data) != sha:
            raise ReplayLineageHold('PR_L02_DEPENDENCY_BLOB_MISMATCH:' + name)
        if _local_imports(data, name) - pins.keys():
            raise ReplayLineageHold('UNPINNED_LOCAL_REPLAY_IMPORT:' + name)
    return {
        'schema': 'minimalizer/local-l02/exact-pr-replay-lineage/v1',
        'verified_dependency_blobs': len(pins),
        'provenance_scope': 'PR_445_ONLY_NOT_MAIN',
        'private_data_read': False,
        'semantic_quality_pass': False,
        'Phase4': 'FAIL', 'L02': 'HOLD', 'L03': 'NO_GO',
        'Golden': 'HOLD', 'production': 'NO_GO',
    }


def verify_pr_replay_lineage() -> dict:
    """Require fixed, externally reviewed PR blob pins before private reads."""
    return _verify_lineage(Path(__file__).parent, PR_445_REPLAY_BLOBS)
