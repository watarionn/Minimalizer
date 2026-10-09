"""Optional pyclipper topology diagnostics for source-owned Stage8 rings.

Never changes official OpenCV raster semantics. This is an independent geometric
check which must NOT authorize a production candidate without full raster parity.
"""
from __future__ import annotations

def inspect_clip_geometry(rings: list[dict]) -> dict:
    try:
        import pyclipper
    except ImportError as exc:
        raise RuntimeError("Install research dependency pyclipper==1.4.0") from exc
    paths = []
    skipped = 0
    for ring in rings:
        pts = ring.get("points", [])
        if len(pts) < 3:
            skipped += 1
            continue
        path = [(int(round(x)), int(round(y))) for x, y in pts]
        path = list(dict.fromkeys(path))
        if len(path) < 3:
            skipped += 1
            continue
        paths.append(path)
    if not paths:
        return {"library": "pyclipper", "validPaths": 0, "skippedDegenerateRings": skipped,
                "unionPathCount": 0, "netArea": 0.0}
    pc = pyclipper.Pyclipper()
    pc.AddPaths(paths, pyclipper.PT_SUBJECT, True)
    solution = pc.Execute(pyclipper.CT_UNION, pyclipper.PFT_EVENODD, pyclipper.PFT_EVENODD)
    # The area of the EVENODD union is a geometric diagnostic only.
    return {"library": "pyclipper", "validPaths": len(paths), "skippedDegenerateRings": skipped,
            "unionPathCount": len(solution),
            "netArea": float(sum(pyclipper.Area(poly) for poly in solution))}


def inspect_stage8_scene(scene: dict) -> dict:
    return {p["composition_part"]: inspect_clip_geometry(p["parameters"]["rings"])
            for p in scene["primitives_back_to_front"]}
