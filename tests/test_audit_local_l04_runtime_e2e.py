from __future__ import annotations

import hashlib
import json

from tools.research.audit_local_l04_runtime_e2e import audit_runtime_e2e


def _headers(path, *, status="HTTP/1.1 200 OK", source=True, candidate=True,
             svg_case="H04", content_type="image/png"):
    lines = [status, f"Content-Type: {content_type}", "X-Minimalizer-Processing-Ms: 12.5",
             "X-Minimalizer-L04-Svg-Available: true"]
    if source:
        lines.append("X-Minimalizer-Input-Sha256: " + "a" * 64)
    if candidate:
        lines.extend([
            "X-Minimalizer-L04-Candidate-Receipt-Sha256: " + "381b0b5a6b52c25472c063c5ca55b65755f3602ab451f569fd6d6a27a20b775a",
            f"X-Minimalizer-L04-Case: {svg_case}",
            "X-Minimalizer-L04-Release: GO",
        ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_current_e2e_receipt_passes_without_publishing_bodies(tmp_path):
    manifest_cases = {}
    files = {}
    for case in ("H04", "H06", "H08"):
        suffix = "" if case == "H04" else "-webp"
        png_body = tmp_path / f"{case}-png{suffix}.body"
        svg_body = tmp_path / f"{case}-svg{suffix}.body"
        png_body.write_bytes(f"png-{case}".encode())
        svg_body.write_bytes(f"svg-{case}".encode())
        svg_sha = hashlib.sha256(svg_body.read_bytes()).hexdigest()
        png_headers = tmp_path / f"{case}-png{suffix}.headers.txt"
        svg_headers = tmp_path / f"{case}-svg{suffix}.headers.txt"
        _headers(png_headers)
        _headers(svg_headers, svg_case=case, content_type="image/svg+xml")
        files[case] = {"png_headers": png_headers, "png_body": png_body,
                       "svg_headers": svg_headers, "svg_body": svg_body}
        manifest_cases[case] = {"source": {"sha256": "a" * 64},
                                "expanded_svg": {"sha256": svg_sha}}
    result = audit_runtime_e2e(
        manifest={"candidate_receipt_sha256": "381b0b5a6b52c25472c063c5ca55b65755f3602ab451f569fd6d6a27a20b775a",
                  "L04_formal": "PASS", "production": "GO", "cases": manifest_cases},
        case_files=files,
    )
    assert result["status"] == "PASS"
    assert result["source_free"] is True
    assert result["release_authorized"] is False


def test_bad_source_or_svg_binding_holds(tmp_path):
    files = {}
    cases = {}
    for case in ("H04", "H06", "H08"):
        suffix = "" if case == "H04" else "-webp"
        for kind in ("png", "svg"):
            body = tmp_path / f"{case}-{kind}{suffix}.body"
            body.write_bytes(b"body")
            headers = tmp_path / f"{case}-{kind}{suffix}.headers.txt"
            _headers(
                headers,
                svg_case=case,
                content_type="image/svg+xml" if kind == "svg" else "image/png",
            )
            files.setdefault(case, {})[f"{kind}_headers"] = headers
            files[case][f"{kind}_body"] = body
        cases[case] = {"source": {"sha256": "b" * 64},
                       "expanded_svg": {"sha256": hashlib.sha256(b"body").hexdigest()}}
    result = audit_runtime_e2e(
        manifest={"candidate_receipt_sha256": "381b0b5a6b52c25472c063c5ca55b65755f3602ab451f569fd6d6a27a20b775a",
                  "L04_formal": "PASS", "production": "GO", "cases": cases},
        case_files=files,
    )
    assert result["status"] == "HOLD"
    assert any("source_sha_bound" in failure for failure in result["failures"])
