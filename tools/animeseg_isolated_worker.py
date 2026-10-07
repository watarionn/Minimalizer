"""Isolated AnimeSeg Mask2Former worker.

JSON-lines protocol: one request on stdin, one response on stdout.  The
worker is deliberately independent from Minimalizer's interpreter so a torch
or native-extension failure cannot take down the parent process.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

CLASS_NAMES = ("background", "skin", "face", "hair_main", "left_eye",
               "right_eye", "left_eyebrow", "right_eyebrow", "nose", "mouth",
               "clothes", "accessory")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main(req: dict) -> dict:
    source = Path(req["source"]).resolve()
    out = Path(req["mask_png"]).resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    import torch
    from PIL import Image
    from anime_seg import AnimeSegPipeline

    device = req.get("device", "cuda" if torch.cuda.is_available() else "cpu")
    pipe = AnimeSegPipeline.from_mask2former(
        repo_id=req.get("repo_id", "suzukimain/AnimeSeg"),
        filename=req.get("filename", "models/anime_seg_mask2former_v3.safetensors"),
    ).to(device)
    result = pipe(str(source), width=req.get("width"), height=req.get("height"))
    out.parent.mkdir(parents=True, exist_ok=True)
    result.save(out)
    im = Image.open(out).convert("RGB")
    pixels = list(im.getdata())
    colors = {(0, 0, 0): 0}
    counts = [0] * len(CLASS_NAMES)
    # AnimeSeg's documented visualization colors are stable enough for an
    # observer artifact; unknown colors remain explicit and never authorize.
    palette = [(0,0,0),(255,220,180),(100,150,255),(255,0,0),(0,255,255),
               (255,255,0),(150,255,0),(0,255,100),(255,140,0),(255,0,150),
               (180,0,255),(128,128,0)]
    lookup = {c: i for i, c in enumerate(palette)}
    unknown = 0
    for p in pixels:
        i = lookup.get(p)
        if i is None:
            unknown += 1
        else:
            counts[i] += 1
    return {"status": "ok", "class_names": CLASS_NAMES,
            "pixel_counts": dict(zip(CLASS_NAMES, counts)),
            "unknown_pixel_count": unknown, "mask_sha256": _sha256(out),
            "model": {"repo_id": req.get("repo_id", "suzukimain/AnimeSeg"),
                      "filename": req.get("filename", "models/anime_seg_mask2former_v3.safetensors"),
                      "device": device}, "authority": False}


if __name__ == "__main__":
    try:
        print(json.dumps(main(json.loads(sys.stdin.readline())), sort_keys=True), flush=True)
    except Exception as exc:  # child errors are data, never parent exceptions
        print(json.dumps({"status": "observer_unavailable", "error": type(exc).__name__ + ": " + str(exc),
                          "authority": False}, sort_keys=True), flush=True)
        sys.exit(2)
