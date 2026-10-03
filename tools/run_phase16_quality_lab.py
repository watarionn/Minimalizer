#!/usr/bin/env python3
"""Phase 16 Quality Lab: deterministic evidence + optional Mitsuba semantic critique."""
from __future__ import annotations
import argparse, base64, hashlib, json, mimetypes, urllib.request
from pathlib import Path

PROMPT = """You are a read-only evaluator for Minimalizer. Compare SOURCE and MINIMALIZED.
Do not propose or generate replacement pixels, images, inpainting, or stylistic additions.
Judge only preservation of observed evidence under geometric abstraction.
Return JSON only with this schema:
{"identity_preservation":0.0,"silhouette_preservation":0.0,"semantic_feature_preservation":0.0,
"color_role_preservation":0.0,"abstraction_quality":0.0,
"lost_critical_features":[{"feature":"","severity":"high|medium|low","reason":"","likely_stage":"03|04|05|06|07|08|09|10|11|12"}],
"overpreserved_details":[{"feature":"","reason":""}],"summary":""}
Scores are 0..1. A critical feature is something visibly present in SOURCE whose loss materially harms identity or structure.
Do not reward photorealism or added detail."""

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def data_url(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")

def parse_json_text(text: str) -> dict:
    text=text.strip()
    if text.startswith("```"):
        text=text.split("\n",1)[1].rsplit("```",1)[0].strip()
        if text.startswith("json"): text=text[4:].lstrip()
    return json.loads(text)

def mitsuba_compare(source: Path, output: Path, api: str, timeout: int) -> dict:
    content=[{"type":"text","text":PROMPT+"\nFirst image is SOURCE. Second image is MINIMALIZED."},
             {"type":"image_url","image_url":{"url":data_url(source)}},
             {"type":"image_url","image_url":{"url":data_url(output)}}]
    body=json.dumps({"messages":[{"role":"user","content":content}],"max_tokens":900,
                     "temperature":0.0,"top_p":1.0},ensure_ascii=False).encode("utf-8")
    req=urllib.request.Request(api,data=body,headers={"Content-Type":"application/json; charset=utf-8"})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        payload=json.loads(r.read().decode("utf-8"))
    return parse_json_text(payload["choices"][0]["message"]["content"])

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("source",type=Path); ap.add_argument("minimalized",type=Path)
    ap.add_argument("--report",type=Path,required=True)
    ap.add_argument("--mitsuba-api",default="http://127.0.0.1:18080/v1/chat/completions")
    ap.add_argument("--no-mitsuba",action="store_true"); ap.add_argument("--timeout",type=int,default=240)
    args=ap.parse_args()
    for p in (args.source,args.minimalized):
        if not p.is_file(): raise SystemExit(f"missing image: {p}")
    report={"schema":"minimalizer.phase16.quality-lab.v1","source":{"path":str(args.source),"sha256":sha256(args.source)},
            "minimalized":{"path":str(args.minimalized),"sha256":sha256(args.minimalized)},
            "constraints":{"generative_editing":False,"mitsuba_role":"evaluation-only"},
            "mitsuba":None}
    if not args.no_mitsuba:
        report["mitsuba"]=mitsuba_compare(args.source,args.minimalized,args.mitsuba_api,args.timeout)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False))
    return 0
if __name__=="__main__": raise SystemExit(main())
