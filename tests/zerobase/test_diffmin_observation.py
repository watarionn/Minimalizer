import json
from minimalizer_zerobase.production.diffmin_observation import observations_from_release_audit,summarize_observations,write_observation_log

def payload():
 return {"effective_mode":"guarded","kill_switch":False,"audit":{"decisions":[
  {"artifact":{"candidate_id":"a","silhouette_iou":.999,"baseline_dino_score":.5,"candidate_dino_score":.51},"decision":{"apply_candidate":True,"reason":"guarded-candidate-improved"}},
  {"artifact":{"candidate_id":"b","silhouette_iou":.998,"baseline_dino_score":.5,"candidate_dino_score":.49},"decision":{"apply_candidate":False,"reason":"observer-not-improved"}}]}}

def test_release_audit_becomes_observation_records(tmp_path):
 x=observations_from_release_audit(payload(),run_id="r1");assert len(x)==2 and x[0].dino_delta==.01 and not x[1].apply_candidate
 p=tmp_path/"obs.jsonl";write_observation_log(p,x);assert len(p.read_text().splitlines())==2

def test_summary_tracks_adoption_and_rollback_reason():
 s=summarize_observations(observations_from_release_audit(payload(),run_id="r1"))
 assert s["candidates"]==2 and s["adopted"]==1 and s["rolled_back"]==1 and s["adoption_rate"]==.5
 assert s["rollback_reasons"]=={"observer-not-improved":1}
