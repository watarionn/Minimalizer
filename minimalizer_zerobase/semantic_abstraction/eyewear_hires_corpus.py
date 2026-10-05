from __future__ import annotations
from dataclasses import dataclass
import hashlib,json
from pathlib import Path

@dataclass(frozen=True)
class HiresCorpusEntry:
 name:str
 source_sha256:str
 role:str
 label_basis:str

def freeze_hires_corpus(entries:tuple[HiresCorpusEntry,...])->dict:
 if not entries:raise ValueError("corpus required")
 rows=[]
 for e in sorted(entries,key=lambda x:x.name):
  if e.role not in {"positive","negative"}:raise ValueError("invalid role")
  if len(e.source_sha256)!=64:raise ValueError("source sha256 required")
  if e.label_basis!="manual_visual_hires":raise ValueError("high-resolution visual verification required")
  rows.append({"name":e.name,"source_sha256":e.source_sha256,"role":e.role,"label_basis":e.label_basis})
 if not any(x["role"]=="positive" for x in rows) or not any(x["role"]=="negative" for x in rows):raise ValueError("both roles required")
 raw=json.dumps(rows,sort_keys=True,separators=(",",":")).encode()
 return {"version":"sa7.16-v1","entries":rows,"corpus_sha256":hashlib.sha256(raw).hexdigest()}
