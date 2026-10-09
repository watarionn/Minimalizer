"""Verify frozen SA10.41 source SHA and preserve source alpha for compact color study."""
from pathlib import Path
from PIL import Image
import argparse, hashlib, json

SOURCE={
 "GC001":"75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e",
 "Raden":"d9982c74a2d9a0a8cd3547f3f5cc603a809e942e6dcf62b98e36bfa019903a00",
}
def prepare_alpha(root:Path,out:Path):
 signed=json.loads((out/"verified_inputs.json").read_text(encoding="utf-8"))
 for case,sha in SOURCE.items():
  source=root/"original_inputs"/f"{case}_source.png"
  if hashlib.sha256(source.read_bytes()).hexdigest()!=sha:
   raise ValueError(f"Original source SHA mismatch: {case}")
  if signed[case]["source_sha256"]!=sha:
   raise ValueError(f"Verified manifest mismatch: {case}")
  with Image.open(source) as img:
   rgba=img.convert("RGBA")
   if rgba.size!=(340,340):
    raise ValueError("Signed original size mismatch")
   alpha=rgba.getchannel("A").tobytes()
  for role in ("left_arm","right_arm"):
   mask=out/case/f"{role}_signed.bin"
   if len(mask.read_bytes())!=340*340:
    raise ValueError(f"Missing previously verified signed role: {case}/{role}")
   (out/case/f"{role}_source_alpha.bin").write_bytes(alpha)
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--root",type=Path,required=True)
 p.add_argument("--prepared",type=Path,required=True)
 a=p.parse_args()
 prepare_alpha(a.root,a.prepared)
 print("Frozen signed original alpha bytes verified")
