"""Research only. Recolor signed SVG rectangles using observed original source RGB.
No new shapes, face detail, raster embedding, change of z-order, or release.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from xml.etree import ElementTree as etree
import numpy as np
from PIL import Image

NS = "{http://www.w3.org/2000/svg}"

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def verify(p, expected):
    if not expected or sha(p) != expected:
        raise ValueError("signed evidence SHA mismatch: " + str(p))

def medoid_l1(rgb, mask):
    pixels = rgb[mask]
    if not len(pixels):
        return None
    colors = np.unique(pixels, axis=0)
    cost = np.zeros(len(colors), dtype=np.int64)
    for k in range(3):
        histogram = np.bincount(pixels[:, k], minlength=256)
        channel = np.abs(np.arange(256)[:, None] - np.arange(256)).dot(histogram)
        cost += channel[colors[:, k]]
    return tuple(map(int, colors[np.argmin(cost)]))

def literal_rgb(text):
    if not text.startswith("rgb(") or not text.endswith(")"):
        raise ValueError("not literal source RGB")
    c = tuple(map(int, text[4:-1].split(",")))
    if len(c) != 3 or not all(0 <= v <= 255 for v in c):
        raise ValueError("invalid RGB triplet")
    return c

def signed_recolor(case, root, manifest, out):
    evidence = manifest[case]
    source = root / "originals" / case / (case + "_source.png")
    svg = root / "baseline" / (case + "_all_signed_owners_budget40.svg")
    verify(source, evidence["signedSourceSha"])
    verify(svg, evidence["signedFull40SvgSha"])
    rgba = np.asarray(Image.open(source).convert("RGBA"))
    if rgba.shape != (340, 340, 4):
        raise ValueError("source 340x340 only")
    rgb = rgba[:, :, :3]
    doc = etree.fromstring(svg.read_bytes())
    if doc.tag != NS + "svg" or any(n.tag.rsplit("}",1)[-1] in ("image","foreignObject","filter") for n in doc.iter()):
        raise ValueError("forbidden markup")
    paths = doc.findall(".//" + NS + "clipPath")
    groups = doc.findall(NS + "g")
    roles = [e.get("id").replace("owner_", "") for e in paths]
    if len(paths) != 10 or len(groups) != 10 or set(roles) != set(evidence["ownerMasksSha"]):
        raise ValueError("invalid source owner taxonomy")
    if any(g.get("clip-path") != "url(#owner_" + role + ")" for g, role in zip(groups, roles)):
        raise ValueError("owner paint z-order changed")
    masks = {}
    for role in roles:
        maskfile = root / "owner_masks" / (case + "_" + role + "_visible.bin")
        verify(maskfile, evidence["ownerMasksSha"][role])
        raw = np.frombuffer(maskfile.read_bytes(), np.uint8).reshape((340, 340))
        if not np.isin(raw, [0, 1]).all() or ((raw != 0) & (rgba[:, :, 3] == 0)).any():
            raise ValueError("invalid source-visible owner")
        masks[role] = raw.astype(bool)
    occupied = np.zeros((340, 340), bool)
    effective = {}
    for role in reversed(roles):
        effective[role] = masks[role] & ~occupied
        occupied |= masks[role]
    before = after = changed = paint = 0
    for role, group in zip(roles, groups):
        rects = group.findall(NS + "rect")
        if not rects or len(rects) != len(group) or role == "face" and len(rects) != 1:
            raise ValueError("face-detail or unapproved geometry")
        owner = np.full((340, 340), -1, np.int16)
        owner[effective[role]] = 0
        for j, r in enumerate(rects[1:], 1):
            x, y, w, h = (int(r.get(k)) for k in ("x", "y", "width", "height"))
            if x < 0 or y < 0 or w < 1 or h < 1 or x + w > 340 or y + h > 340:
                raise ValueError("rectangle bounds")
            owner[y:y+h, x:x+w][effective[role][y:y+h, x:x+w]] = j
        for j, rect in enumerate(rects):
            support = owner == j
            old = literal_rgb(rect.get("fill"))
            new = medoid_l1(rgb, support) or old
            if support.any() and not np.any(np.all(rgb[support] == new, axis=1)):
                raise ValueError("invented RGB")
            before += int(np.abs(rgb[support].astype(np.int16) - old).sum())
            after += int(np.abs(rgb[support].astype(np.int16) - new).sum())
            changed += int(new != old)
            paint += 1
            rect.set("fill", "rgb(" + ",".join(map(str, new)) + ")")
    if paint + len(paths) != 40 or after > before:
        raise ValueError("fixed 40 shape or signed L1 regression")
    rendered = etree.tostring(doc, encoding="utf-8")
    out.mkdir(parents=True, exist_ok=True)
    (out / (case + "_40_refit.svg")).write_bytes(rendered)
    return {"shapeCount": paint + len(paths), "changedColorLayers": changed,
            "visibleSignedColorMAEBefore": before/(3*occupied.sum()),
            "visibleSignedColorMAEAfter": after/(3*occupied.sum()),
            "svgSha256": hashlib.sha256(rendered).hexdigest(),
            "originalMasksUnchanged": True, "faceDetailPaint": False,
            "golden": "HOLD", "production": "UNCHANGED"}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True,
                   help="private folder with originals/, owner_masks/, baseline/")
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    manifest = json.loads(a.manifest.read_text())
    result = {c: signed_recolor(c, a.root, manifest, a.out) for c in ("GC001","Raden")}
    (a.out / "l1_refit_metrics.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
