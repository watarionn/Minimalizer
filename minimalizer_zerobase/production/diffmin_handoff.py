from __future__ import annotations
from dataclasses import asdict,dataclass
import hashlib,json
from pathlib import Path
from typing import Any
from .diffmin import GuardedDiffMinSwitch
from .diffmin_artifact import DiffMinArtifactDecision,DiffMinCandidateArtifact,evaluate_candidate_artifact,load_candidate_artifact,sha256_file

BUNDLE_SCHEMA="1"

@dataclass(frozen=True)
class DiffMinBundleEntry:
 candidate_id:str
 source_file:str
 baseline_file:str
 candidate_file:str
 artifact_file:str

@dataclass(frozen=True)
class DiffMinHandoffManifest:
 schema_version:str
 entries:tuple[DiffMinBundleEntry,...]
 def __post_init__(self):
  if self.schema_version!=BUNDLE_SCHEMA:raise ValueError("unsupported DiffMin handoff schema")
  ids=[x.candidate_id for x in self.entries]
  if ids!=sorted(ids) or len(ids)!=len(set(ids)):raise ValueError("handoff entries must be unique and sorted")
 def to_dict(self)->dict[str,Any]:return {"schema_version":self.schema_version,"entries":[asdict(x) for x in self.entries]}
 @classmethod
 def from_dict(cls,x:dict[str,Any])->"DiffMinHandoffManifest":
  return cls(x["schema_version"],tuple(DiffMinBundleEntry(**e) for e in x["entries"]))

@dataclass(frozen=True)
class DiffMinBundleAudit:
 manifest_sha256:str
 passed:bool
 decisions:tuple[DiffMinArtifactDecision,...]
 def to_dict(self)->dict[str,Any]:return {"manifest_sha256":self.manifest_sha256,"passed":self.passed,"decisions":[x.to_dict() for x in self.decisions]}

def write_handoff_manifest(path:str|Path,manifest:DiffMinHandoffManifest)->str:
 p=Path(path);payload=(json.dumps(manifest.to_dict(),sort_keys=True,separators=(",",":"))+"\n").encode();p.write_bytes(payload);return hashlib.sha256(payload).hexdigest()

def load_handoff_manifest(path:str|Path)->DiffMinHandoffManifest:
 x=json.loads(Path(path).read_text(encoding="utf8"))
 if not isinstance(x,dict):raise ValueError("handoff manifest must be an object")
 return DiffMinHandoffManifest.from_dict(x)

def audit_handoff_bundle(root:str|Path,switch:GuardedDiffMinSwitch)->DiffMinBundleAudit:
 root=Path(root);mp=root/"handoff.json";manifest=load_handoff_manifest(mp);decisions=[]
 for e in manifest.entries:
  # Relative-only paths keep the bundle portable and prevent path escape.
  paths=[Path(x) for x in (e.source_file,e.baseline_file,e.candidate_file,e.artifact_file)]
  if any(p.is_absolute() or ".." in p.parts for p in paths):raise ValueError("handoff paths must stay inside bundle")
  artifact=load_candidate_artifact(root/e.artifact_file)
  if artifact.candidate_id!=e.candidate_id:raise ValueError("candidate id mismatch")
  decisions.append(evaluate_candidate_artifact(artifact=artifact,source_path=root/e.source_file,baseline_path=root/e.baseline_file,candidate_path=root/e.candidate_file,switch=switch))
 return DiffMinBundleAudit(sha256_file(mp),all(x.artifact_integrity_pass for x in decisions),tuple(decisions))

