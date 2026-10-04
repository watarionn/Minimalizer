from __future__ import annotations
from dataclasses import asdict, dataclass
import hashlib,json
from pathlib import Path
from typing import Any
from .diffmin import DiffMinDecision,DiffMinEvidence,GuardedDiffMinSwitch

def sha256_file(path:str|Path)->str:
 h=hashlib.sha256()
 with Path(path).open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
 return h.hexdigest()

def _sha(name:str,value:str)->None:
 if len(value)!=64:
  raise ValueError(f"{name} must be SHA-256")
 try:int(value,16)
 except ValueError as e:raise ValueError(f"{name} must be SHA-256") from e

@dataclass(frozen=True)
class DiffMinCandidateArtifact:
 schema_version:str
 candidate_id:str
 source_sha256:str
 baseline_sha256:str
 candidate_sha256:str
 hard_guards_pass:bool
 silhouette_iou:float
 baseline_dino_score:float|None
 candidate_dino_score:float|None
 worker:str="external-worker"
 def __post_init__(self):
  if self.schema_version!="1":raise ValueError("unsupported DiffMin artifact schema")
  if not self.candidate_id:raise ValueError("candidate_id is required")
  for n in ("source_sha256","baseline_sha256","candidate_sha256"):_sha(n,getattr(self,n))
  if not 0<=self.silhouette_iou<=1:raise ValueError("silhouette_iou must be within [0, 1]")
 def to_dict(self)->dict[str,Any]:return asdict(self)
 @classmethod
 def from_dict(cls,x:dict[str,Any])->"DiffMinCandidateArtifact":return cls(**x)

@dataclass(frozen=True)
class DiffMinArtifactDecision:
 artifact:DiffMinCandidateArtifact
 decision:DiffMinDecision
 artifact_integrity_pass:bool
 reason:str
 def to_dict(self)->dict[str,Any]:
  return {"artifact":self.artifact.to_dict(),"decision":self.decision.to_dict(),"artifact_integrity_pass":self.artifact_integrity_pass,"reason":self.reason}

def evaluate_candidate_artifact(*,artifact:DiffMinCandidateArtifact,source_path:str|Path,baseline_path:str|Path,candidate_path:str|Path,switch:GuardedDiffMinSwitch)->DiffMinArtifactDecision:
 checks=(sha256_file(source_path)==artifact.source_sha256,sha256_file(baseline_path)==artifact.baseline_sha256,sha256_file(candidate_path)==artifact.candidate_sha256)
 if not all(checks):
  decision=DiffMinDecision(switch.requested_mode,False,True,"artifact-integrity-failed")
  return DiffMinArtifactDecision(artifact,decision,False,"artifact-integrity-failed")
 evidence=DiffMinEvidence(artifact.hard_guards_pass,artifact.silhouette_iou,artifact.baseline_dino_score,artifact.candidate_dino_score)
 decision=switch.decide(evidence)
 return DiffMinArtifactDecision(artifact,decision,True,decision.reason)

def write_candidate_artifact(path:str|Path,artifact:DiffMinCandidateArtifact)->None:
 Path(path).write_text(json.dumps(artifact.to_dict(),sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")

def load_candidate_artifact(path:str|Path)->DiffMinCandidateArtifact:
 raw=json.loads(Path(path).read_text(encoding="utf-8"))
 if not isinstance(raw,dict):raise ValueError("DiffMin artifact must be a JSON object")
 return DiffMinCandidateArtifact.from_dict(raw)

