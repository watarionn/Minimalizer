"""Source-exact fixed-round campaign starting from private multi-point Stage8 candidates.
Every accepted change requires official full owner mask equality; source originals unchanged.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from stage8_official_polygon_replay import official_mirror
from stage8_multi_point_exact import optimize

def run(root,out,rounds,trials):
 out.mkdir(parents=True,exist_ok=True)
 results={}
 for case,cap in [("Raden",1412),("GC001",1887)]:
  inp=root/f"{case}_multi_point_candidate_PRIVATE.json"
  payload=inp.read_bytes(); scene=json.loads(payload)
  log=[];prev=sum(len(r["points"]) for p in scene["primitives_back_to_front"] for r in p["parameters"]["rings"])
  for step in range(1,rounds+1):
   changed=0
   for part in scene["primitives_back_to_front"]:
    initial=official_mirror(part)
    stats,rings=optimize(part,max_trials=trials,max_span=14)
    proposal=dict(part,parameters=dict(part["parameters"],rings=rings))
    if not np.array_equal(initial,official_mirror(proposal)):raise ValueError("owner changed")
    part["parameters"]["rings"]=rings
    changed+=stats["removedVertices"]
   final=sum(len(r["points"]) for p in scene["primitives_back_to_front"] for r in p["parameters"]["rings"])
   if final!=prev-changed:raise ValueError("count drift")
   log.append({"round":step,"vertices":final,"removedThisRound":changed})
   prev=final
   if changed==0:break
  f=out/f"{case}_campaign_PRIVATE.json"
  f.write_text(json.dumps(scene,ensure_ascii=False,separators=(",",":")))
  results[case]={"inputSha256":hashlib.sha256(payload).hexdigest(),
     "outputSha256":hashlib.sha256(f.read_bytes()).hexdigest(),
     "initialVertices":log[0]["vertices"]+log[0]["removedThisRound"],
     "finalVertices":prev,"historicalCap":cap,"remainingGap":max(0,prev-cap),
     "rounds":log,"productionAuthorized":False}
 (out/"campaign_metrics.json").write_text(json.dumps(results,indent=2)+"\n")
 print(json.dumps({k:{"final":v["finalVertices"],"gap":v["remainingGap"],"rounds":v["rounds"]} for k,v in results.items()}))
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--input",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
 p.add_argument("--rounds",type=int,default=4);p.add_argument("--trials",type=int,default=30000)
 a=p.parse_args();run(a.input,a.output,a.rounds,a.trials)
