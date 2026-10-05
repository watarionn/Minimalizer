import numpy as np
from minimalizer_zerobase.semantic_abstraction.frozen_observer_bridge import bind_frozen_eyewear_artifact,bind_frozen_records,to_fusion_evidence

def _record(**kw):
 r={"evidence_id":"gsam-goggles","semantic_label":"goggles","confidence":.81,"geometry":{"bbox":[10,8,20,12]},"provenance":{"producer":"phase-e-grounded-sam","model_id":"grounding-dino+sam"},"observer_role":"region","source_sha256":"abc"}
 r.update(kw);return r

def test_binds_bbox_record_with_provenance():
 a=bind_frozen_eyewear_artifact(_record(),shape=(40,50));assert a is not None and a.mask.sum()==240 and a.producer=="phase-e-grounded-sam"
 e=to_fusion_evidence(a);assert e.role=="region" and e.observer_id=="gsam-goggles"

def test_rejects_aggregate_summary_without_geometry():
 r=_record();r.pop("geometry");assert bind_frozen_eyewear_artifact(r,shape=(40,50)) is None

def test_rejects_missing_provenance():
 r=_record();r.pop("provenance");assert bind_frozen_eyewear_artifact(r,shape=(40,50)) is None

def test_rejects_non_eyewear_semantics():
 assert bind_frozen_eyewear_artifact(_record(semantic_label="hair"),shape=(40,50)) is None

def test_rejects_invalid_bbox_instead_of_clipping():
 assert bind_frozen_eyewear_artifact(_record(geometry={"bbox":[45,5,20,10]}),shape=(40,50)) is None

def test_bind_records_is_order_invariant():
 a=_record(evidence_id="b");b=_record(evidence_id="a",observer_role="feature_local")
 x=bind_frozen_records([a,b],shape=(40,50));y=bind_frozen_records([b,a],shape=(40,50));assert [z.observer_id for z in x]==[z.observer_id for z in y]
