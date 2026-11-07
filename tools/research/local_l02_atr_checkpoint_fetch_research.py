"""Research-only, source-free ATR18 checkpoint acquisition with exact SHA pin.

Downloads a public model, never any private signed image. This is not a
licence clearance, model execution, owner change, or quality acceptance.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import tempfile
from urllib.request import urlopen

REVISION = 'a54fa65e7e4f27f21011f652ffc0053ebb24b292'
FILENAME = 'schp-atr-18-int8-static.onnx'
SHA256 = '4420d8db8c1f266967c89485786b01209f6d405f320fc0f87e8ced49392cefb5'
SIZE = 69_141_996
URL = (f'https://huggingface.co/pirocheto/schp-atr-18/resolve/{REVISION}'
       f'/onnx/{FILENAME}')
CHUNK = 1024 * 1024


class CheckpointHold(RuntimeError):
    """No checkpoint is released if the provenance or local path is unsafe."""


def _is_private_destination(folder: Path) -> bool:
    """Refuse checkout descendants, including linked worktrees with .git files."""
    current = folder
    while True:
        if (current / '.git').exists():
            return False
        if current.parent == current:
            return True
        current = current.parent


def _verify_file(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size != SIZE:
        return False
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(CHUNK), b''):
            digest.update(chunk)
    return digest.hexdigest() == SHA256


def fetch_pinned_atr_checkpoint(destination_dir: Path) -> Path:
    """Return verified local model; fail closed on mismatch or unsafe destination.

    A complete model is created atomically and never replaces an existing file.
    The HTTPS endpoint is pinned to an immutable upstream commit; all bytes are
    verified independently against the upstream SHA-256 before publication.
    """
    if not isinstance(destination_dir, Path):
        raise CheckpointHold('PRIVATE_DESTINATION_PATH_REQUIRED')
    folder = destination_dir.resolve(strict=True)
    if not folder.is_dir() or not _is_private_destination(folder):
        raise CheckpointHold('PRIVATE_DESTINATION_OUTSIDE_GIT_REQUIRED')
    target = folder / FILENAME
    if target.exists():
        if not _verify_file(target):
            raise CheckpointHold('EXISTING_CHECKPOINT_MISMATCH')
        return target
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(prefix='.atr18-', suffix='.part',
                                         dir=folder, delete=False) as tmp:
            temp_name = tmp.name
            os.chmod(temp_name, 0o600)
            digest = hashlib.sha256()
            count = 0
            with urlopen(URL, timeout=30) as response:
                while True:
                    chunk = response.read(CHUNK)
                    if not chunk:
                        break
                    count += len(chunk)
                    if count > SIZE:
                        raise CheckpointHold('CHECKPOINT_OVERSIZE')
                    digest.update(chunk)
                    tmp.write(chunk)
            tmp.flush()
            os.fsync(tmp.fileno())
        if count != SIZE or digest.hexdigest() != SHA256:
            raise CheckpointHold('CHECKPOINT_SHA_OR_SIZE_MISMATCH')
        # Exclusive hard-link creation: never overwrite an existing destination.
        try:
            os.link(temp_name, target)
        except FileExistsError:
            if not _verify_file(target):
                raise CheckpointHold('CONCURRENT_CHECKPOINT_MISMATCH')
        if not _verify_file(target):
            raise CheckpointHold('CHECKPOINT_READBACK_MISMATCH')
        return target
    finally:
        if temp_name is not None:
            try:
                os.unlink(temp_name)
            except FileNotFoundError:
                pass
