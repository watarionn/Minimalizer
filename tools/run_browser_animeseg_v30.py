from pathlib import Path
import hashlib, zipfile, json, subprocess, sys, time
ROOT=Path(r"C:\Temp\minimalizer-v30-evidence")
ROOT.mkdir(parents=True,exist_ok=True)
ARCHIVE=Path(r"G:\マイドライブ\chatGPT及びCodex用\Minimalizer\PartEvidenceV27_20261009\v27_stages_metrics.zip")
assert hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()=="91b9f3851622feb55169bbf301b9dbb52d81036c260ea7e8f88fd7814423bd39"
PY=Path(r"C:\Work\Temp\Minimalizer-AnimeSeg\.venv\Scripts\python.exe")
WORKER=Path(__file__).resolve().with_name("animeseg_isolated_worker.py")
assert PY.exists()
print("V30_START",PY,flush=True)
with zipfile.ZipFile(ARCHIVE) as z:
 for name in ("Noel","Ririka"):
  folder=ROOT/name;folder.mkdir(exist_ok=True)
  source=folder/"source.png";source.write_bytes(z.read(name+"/source.png"))
  assert hashlib.sha256(source.read_bytes()).hexdigest()=={"Noel":"f0dceadc5af23eaa914d3fece271186aca428ce176d76bd91c05686b1f44ef26","Ririka":"6da229380c2673611b57bada10b77d03b9b831770070d594137f2062ca302914"}[name]
  print("V30_SOURCE_VERIFIED",name,flush=True)
  req={"source":str(source),"mask_png":str(folder/"animeseg_mask.png"),"device":"cpu","width":340,"height":340}
  proc=subprocess.Popen([str(PY),str(WORKER)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
  try:
   stdout,stderr=proc.communicate(json.dumps(req)+"\n",timeout=540)
  except subprocess.TimeoutExpired:
   proc.kill();stdout,stderr=proc.communicate()
   raise RuntimeError("V30_TIMEOUT "+name)
  (folder/"worker_stdout.txt").write_text(stdout,encoding="utf-8")
  (folder/"worker_stderr.txt").write_text(stderr,encoding="utf-8")
  print("V30_WORKER_RESULT",name,"code",proc.returncode,"stdout",stdout[-1200:],"stderr_tail",stderr[-500:],flush=True)
  if proc.returncode!=0:raise RuntimeError("v30 worker failed "+name)
