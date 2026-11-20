"""Audit a real LocalWorker L04 PNG/SVG replay without storing source bytes.

The caller supplies response headers and private response bodies captured from
the current Worker.  This adapter hashes only the response bodies and compares
the source identity and SVG output against the source-free L04 manifest.  It
does not copy or publish images, SVGs, or coordinates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping


EXPECTED_CANDIDATE = "381b0b5a6b52c25472c063c5ca55b65755f3602ab451f569fd6d6a27a20b775a"
CASES = ("H04", "H06", "H08")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class RuntimeE2EHold(ValueError):
    """Raised when an E2E replay cannot be bound to the formal L04 bundle."""


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _headers(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        result[key.strip().lower()] = value.strip()
    status = next(
        (line.strip() for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
         if line.startswith("HTTP/")),
        "",
    )
    result[":status"] = status
    return result


def _object(value: object, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise RuntimeE2EHold(f"INVALID_OBJECT:{field}")
    return value


def audit_runtime_e2e(
    *,
    manifest: Mapping[str, Any],
    case_files: Mapping[str, Mapping[str, Path]],
) -> dict[str, object]:
    if manifest.get("candidate_receipt_sha256") != EXPECTED_CANDIDATE:
        raise RuntimeE2EHold("MANIFEST_CANDIDATE_MISMATCH")
    if manifest.get("L04_formal") != "PASS" or manifest.get("production") != "GO":
        raise RuntimeE2EHold("MANIFEST_NOT_FORMAL_GO")

    cases = _object(manifest.get("cases"), "manifest.cases")
    audited: dict[str, object] = {}
    failures: list[str] = []
    for case in CASES:
        paths = case_files.get(case)
        if paths is None:
            failures.append(f"MISSING_CASE:{case}")
            continue
        expected = _object(cases.get(case), f"manifest.cases.{case}")
        source = _object(expected.get("source"), f"manifest.cases.{case}.source")
        svg = _object(expected.get("expanded_svg"), f"manifest.cases.{case}.expanded_svg")
        png_headers = _headers(paths["png_headers"])
        svg_headers = _headers(paths["svg_headers"])
        png_sha = _sha(paths["png_body"])
        svg_sha = _sha(paths["svg_body"])

        checks = {
            "png_http_200": png_headers.get(":status") == "HTTP/1.1 200 OK",
            "png_content_type": png_headers.get("content-type") == "image/png",
            "svg_http_200": svg_headers.get(":status") == "HTTP/1.1 200 OK",
            "svg_content_type": svg_headers.get("content-type") == "image/svg+xml",
            "source_sha_bound": png_headers.get("x-minimalizer-input-sha256") == source.get("sha256"),
            "svg_candidate_bound": svg_headers.get("x-minimalizer-l04-candidate-receipt-sha256") == EXPECTED_CANDIDATE,
            "svg_case_bound": svg_headers.get("x-minimalizer-l04-case") == case,
            "svg_release_go": svg_headers.get("x-minimalizer-l04-release") == "GO",
            "svg_sha_matches_manifest": svg_sha == svg.get("sha256"),
            "svg_available_on_png_route": png_headers.get("x-minimalizer-l04-svg-available") == "true",
            "processing_ms_recorded": bool(re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", png_headers.get("x-minimalizer-processing-ms", ""))),
        }
        if not all(checks.values()):
            failures.extend(f"{case}:{name}" for name, passed in checks.items() if not passed)
        audited[case] = {
            "checks": checks,
            "source_sha256": source.get("sha256"),
            "png_sha256": png_sha,
            "svg_sha256": svg_sha,
            "processing_ms": float(png_headers["x-minimalizer-processing-ms"]),
            "shape_count": png_headers.get("x-minimalizer-shape-count"),
            "input_size": png_headers.get("x-minimalizer-input-size"),
        }

    return {
        "schema": "minimalizer/local-l04/runtime-e2e-audit/v1",
        "status": "PASS" if not failures else "HOLD",
        "candidate_receipt_sha256": EXPECTED_CANDIDATE,
        "cases": audited,
        "failures": failures,
        "source_free": True,
        "private_response_bodies_read_for_hash_only": True,
        "release_authorized": False,
    }


def _load(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return _object(value, path.name)


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Audit current Worker L04 PNG/SVG E2E")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    case_files = {
        case: {
            "png_headers": args.root / f"{case}-png{'' if case == 'H04' else '-webp'}.headers.txt",
            "png_body": args.root / f"{case}-png{'' if case == 'H04' else '-webp'}.body",
            "svg_headers": args.root / f"{case}-svg{'' if case == 'H04' else '-webp'}.headers.txt",
            "svg_body": args.root / f"{case}-svg{'' if case == 'H04' else '-webp'}.body",
        }
        for case in CASES
    }
    try:
        result = audit_runtime_e2e(manifest=_load(args.manifest), case_files=case_files)
        code = 0 if result["status"] == "PASS" else 2
    except (OSError, KeyError, RuntimeE2EHold, json.JSONDecodeError) as exc:
        result = {
            "schema": "minimalizer/local-l04/runtime-e2e-audit/v1",
            "status": "HOLD",
            "failures": [str(exc)],
            "source_free": True,
            "release_authorized": False,
        }
        code = 2
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(_cli())
