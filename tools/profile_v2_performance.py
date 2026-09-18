from __future__ import annotations
import argparse, json, statistics
from pathlib import Path
from minimalize_engine.io.image_loader import load_image
from minimalize_engine.v2.performance import PERFORMANCE_SCHEMA_VERSION, profile_v2_rgb

def main() -> None:
    parser=argparse.ArgumentParser(description="Profile deterministic Minimalizer V2 phase timings.")
    parser.add_argument("inputs", nargs="+")
    parser.add_argument("--preset", default="minimal")
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--output", required=True)
    args=parser.parse_args(); cases=[]
    for raw in args.inputs:
        path=Path(raw); summary=profile_v2_rgb(load_image(path),preset=args.preset,repeats=args.repeats)
        cases.append({"case":path.stem,"mean_wall_seconds":summary.mean_wall_seconds,"mean_phase_seconds":dict(summary.mean_phase_seconds),"phase_share":dict(summary.phase_share),"algorithm_digest":summary.samples[0].algorithm_digest})
    names=sorted(set().union(*(c["mean_phase_seconds"] for c in cases)))
    mean_wall=statistics.mean(c["mean_wall_seconds"] for c in cases)
    mean_phase={n:statistics.mean(c["mean_phase_seconds"].get(n,0.0) for c in cases) for n in names}
    payload={"schema_version":PERFORMANCE_SCHEMA_VERSION,"preset":args.preset,"repeats":args.repeats,"case_count":len(cases),"mean_wall_seconds":mean_wall,"mean_phase_seconds":mean_phase,"phase_share":{n:v/mean_wall for n,v in mean_phase.items()},"cases":cases}
    Path(args.output).write_text(json.dumps(payload,indent=2),encoding="utf-8")
    print(json.dumps({"case_count":len(cases),"mean_wall_seconds":mean_wall,"top_phases":sorted(mean_phase.items(),key=lambda x:x[1],reverse=True)[:6]},indent=2))

if __name__ == "__main__":
    main()
