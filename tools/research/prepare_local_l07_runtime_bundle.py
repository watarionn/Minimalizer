"""Prepare a fail-closed, non-mutating Local L07 runtime staging bundle.

This tool never edits the production checkout.  It copies only the two files
that carry the generation-pinned browser contract into a new, empty staging
directory and emits a source-free manifest for the owner-controlled apply and
readback step.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path


SCHEMA = "minimalizer/local-l07/runtime-staging/v1"
FILES = (
    Path("local_worker/app.py"),
    Path("tools/research/local_l04_production_bundle.py"),
    Path("local_worker/frontend/sw.js"),
    Path("local_worker/frontend/local-route.js"),
)
GENERATION_RE = re.compile(r'minimalizer-local-[0-9]{8}-[0-9]+')
FORBIDDEN = (
    "caches.delete",
    "skipWaiting",
    "clients.claim",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_head(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def validate_source(root: Path) -> tuple[str, dict[str, str]]:
    contents: dict[str, str] = {}
    for relative in FILES:
        path = root / relative
        if not path.is_file():
            raise ValueError(f"missing required source file: {relative}")
        contents[str(relative).replace("\\", "/")] = path.read_text(encoding="utf-8")

    sw = contents["local_worker/frontend/sw.js"]
    route = contents["local_worker/frontend/local-route.js"]
    worker = contents["local_worker/app.py"]
    bundle_loader = contents["tools/research/local_l04_production_bundle.py"]
    for token in FORBIDDEN:
        if token in sw:
            raise ValueError(f"forbidden Service Worker operation: {token}")
    for token in ("output_format: str = Form(\"png\")", "_formal_l04_case_for_source"):
        if token not in worker:
            raise ValueError(f"formal L04 runtime path is missing: {token}")
    if "MINIMALIZER_LOCAL_L04_RECEIPT_SHA256" not in bundle_loader:
        raise ValueError("formal L04 bundle loader is not candidate-bound")

    sw_generations = GENERATION_RE.findall(sw)
    route_generations = GENERATION_RE.findall(route)
    if len(set(sw_generations)) != 1 or len(set(route_generations)) != 1:
        raise ValueError("each source file must contain exactly one generation")
    if sw_generations[0] != route_generations[0]:
        raise ValueError("Service Worker and local route generations differ")
    return sw_generations[0], contents


def prepare(source: Path, output: Path) -> dict[str, object]:
    source = source.resolve()
    output = output.resolve()
    if output.exists():
        if any(output.iterdir()) if output.is_dir() else True:
            raise ValueError(f"output must be a new empty directory: {output}")
    else:
        output.mkdir(parents=True)

    generation, _ = validate_source(source)
    file_records: list[dict[str, str]] = []
    for relative in FILES:
        source_file = source / relative
        target_file = output / relative
        target_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, target_file)
        file_records.append(
            {
                "path": str(relative).replace("\\", "/"),
                "sha256": sha256(target_file),
            }
        )

    manifest = {
        "schema": SCHEMA,
        "status": "STAGING_READY",
        "runtime_mutation": False,
        "release_authorized": False,
        "generation": generation,
        "source_commit": git_head(source),
        "files": file_records,
        "owner_apply_required": True,
        "owner_readback_required": True,
    }
    (output / "runtime-staging-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        manifest = prepare(args.source, args.output)
    except (OSError, ValueError) as error:
        print(json.dumps({"schema": SCHEMA, "status": "HOLD", "error": str(error)}, ensure_ascii=False))
        return 2
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
