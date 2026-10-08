#!/usr/bin/env python3
"""Package V20 read-only golden-image evidence, optional Drive mirror with SHA verification."""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

CASES = ("Kyoko", "Noel", "Ririka")
REPORT_FILES = (
    "v20_candidate_rows.csv",
    "v20_distribution_metrics.json",
    "v20_distribution_report.md",
    "v20_distribution_chart.png",
    "v20_candidate_locations.png",
)
ARCHIVE = "v20_golden_original_and_probe_outputs.zip"
MANIFEST = "v20_evidence_manifest.json"


def checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def label_candidate_locations(output: Path, source_dirs: dict[str, Path]):
    from PIL import Image, ImageDraw, ImageFont
    report = json.loads((output / "v20_distribution_metrics.json").read_text(encoding="utf-8"))
    pad, label_space, gap = 18, 56, 15
    image_width, image_height = 340, 340
    total_width = pad * 3 + 2 * image_width
    total_height = pad * 2 + 3 * (image_height + label_space) + 2 * gap
    canvas = Image.new("RGB", (total_width, total_height), (248, 248, 248))
    drawer = ImageDraw.Draw(canvas)
    font_path = Path("C:/Windows/Fonts/arial.ttf")
    font = ImageFont.truetype(str(font_path), 16) if font_path.exists() else ImageFont.load_default()
    for index, name in enumerate(CASES):
        file_root = source_dirs[name]
        donor_cases = report["samples"][name]["areaOnlyCandidatePairs"]
        unique = {item["donorId"]: item for item in donor_cases}
        top = pad + index * (image_height + label_space + gap)
        for col, (filename, title) in enumerate((("source.png", "Source"),("facet.png", "Facet baseline"))):
            left = pad + col * (image_width + pad)
            image = Image.open(file_root / filename).convert("RGB")
            if image.size != (image_width,image_height):
                raise ValueError(f"{name} source not 340x340: {image.size}")
            canvas.paste(image, (left,top + label_space))
            drawer.text((left,top + 5),f"{name} / {title}",fill=(24,28,34),font=font)
            drawer.text((left,top + 27),
                f"{len(donor_cases)} area-only pairs; {len(unique)} distinct donors",
                fill=(69,76,83),font=font)
            for n, (id_value, record) in enumerate(unique.items()):
                x0,y0,x1,y1=record["donorBox"]
                rect=(left+x0,top+label_space+y0,left+x1,top+label_space+y1)
                color=(206,44,54) if n==0 else (211,110,31)
                drawer.rectangle(rect,outline=color,width=3)
                tx=min(left+image_width-130,left+x0+5)
                ty=max(top+label_space+5,top+label_space+y0+5)
                drawer.text((tx,ty),f"donor {id_value}, {record['donorPixels']}px",fill=color,font=font,
                            stroke_width=2,stroke_fill=(249,249,249))
    canvas.save(output/"v20_candidate_locations.png",optimize=True)


def package(report_dir: Path, input_dir: Path, repo_root: Path, drive_dir: Path | None):
    folders={name:input_dir/f"browser-donor-v20-{name}-20261008" for name in CASES}
    for name,folder in folders.items():
        if not (folder/"metrics.json").is_file():
            raise FileNotFoundError(f"Missing Chrome case {name}: {folder}")
    label_candidate_locations(report_dir,folders)

    with zipfile.ZipFile(report_dir/ARCHIVE,"w",compression=zipfile.ZIP_DEFLATED,
                         compresslevel=7) as archive:
        for filename in REPORT_FILES:
            archive.write(report_dir/filename,filename)
        for case,root in folders.items():
            for filename in ("source.png","facet.png","near.png","metrics.json"):
                archive.write(root/filename,f"{case}/{filename}")

    artifact_names=list(REPORT_FILES)+[ARCHIVE]
    scripts=[
        repo_root/"tools/run_browser_donor_v20_chrome.py",
        repo_root/"tools/analyze_browser_donor_v20.py",
        repo_root/"tools/package_browser_donor_v20_evidence.py",
    ]
    artifact_files=[report_dir/n for n in artifact_names]+scripts
    manifest={
        "status":"HOLD_NO_GEOMETRY_GAIN",
        "mode":"READ_ONLY_V20_DONOR_DISTRIBUTION",
        "goldenSourceCases":list(CASES),
        "archiveContains":"3 original source PNGs + corresponding Facet/Near PNGs and Chrome metadata",
        "files":{file.name:{"size":file.stat().st_size,"sha256":checksum(file)}
                 for file in artifact_files},
    }
    (report_dir/MANIFEST).write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",
                                      encoding="utf-8")
    artifact_files.append(report_dir/MANIFEST)
    if drive_dir:
        if not drive_dir.is_dir():
            raise FileNotFoundError("Drive directory not visible; no replacement location chosen: "+str(drive_dir))
        for file in artifact_files:
            target=drive_dir/file.name
            if target.exists() and checksum(target)!=checksum(file):
                raise FileExistsError("Drive target exists with different checksum: "+str(target))
            if not target.exists():
                shutil.copy2(file,target)
            if checksum(target)!=checksum(file):
                raise IOError("Drive checksum mismatch: "+str(target))
        print("V20_DRIVE_SHA256_VERIFIED",len(artifact_files),
              "bytes",sum(f.stat().st_size for f in artifact_files),flush=True)
    print("V20_EVIDENCE_FILES",
          [(file.name,file.stat().st_size,checksum(file)[:16]) for file in artifact_files],
          flush=True)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--report",type=Path,required=True)
    p.add_argument("--inputs",type=Path,required=True)
    p.add_argument("--repo",type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument("--drive",type=Path)
    a=p.parse_args()
    package(a.report,a.inputs,a.repo,a.drive)

if __name__=="__main__":
    main()
