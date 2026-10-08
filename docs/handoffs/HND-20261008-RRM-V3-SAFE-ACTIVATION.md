# RRM v3 Minimalizer production rollout handoff (2026-10-08 JST)

## Verified and already completed
- `watarionn/rinka-local-operator` main includes PR #67, shared `resource_request_guard.py`.
- `watarionn/Minimalizer` main includes PR #233, guarded `local_worker/app.py` compute endpoints and `local_worker/rrm_admission.py`.
- Local RLO checkout at `C:\Work\Projects\RinkaLocalOperator` was fast-forwarded to `0bb941ca63ceb419607f72d93e9b99d068574107`; 43 RRM/RLO tests passed.
- Actual Local Worker deployment checkout `C:\Work\Projects\MinimalizerProductionWorker` was clean and fast-forwarded to `6a9edf6c0448ad5bafb2c9e85690b0ff881409ca`.
- Local production checkout: 5 RRM adapter tests passed; `python -m py_compile local_worker/app.py local_worker/rrm_admission.py` passed.
- Real shared SQLite smoke, **no image inference**: `compute_slot('v2')` with `MINIMALIZER_RRM_MODE=enforce` was rejected with `low_ram` while RAM was constrained. Before/after heavy queue showed no active or queued ticket, confirming clean rejection.
- `Reference3DStudio` remains registered `paused`.

## Runtime activation intentionally NOT performed
- Existing Minimalizer Uvicorn parent PID `38048` and child PID `41072` were launched 2026-10-08 12:48:50 JST, **before** source changes. They remained running and returned `status=ready` from the existing /health route.
- Current process modules are the old in-memory image-processing code. Fast-forwarding source files on disk does **not** activate request admission in the already-running worker.
- Qwen scripts PIDs `4332` and `34468` were running; ComfyUI `GET http://127.0.0.1:8212/queue` showed **one running prompt, zero pending**. Duplicate inference was not established, and processes were not modified.
- Host free physical RAM fluctuated around `0.1–0.33 GiB`; NVIDIA VRAM was almost full. Restarting a production worker or launching a model smoke test under this pressure is unsafe.
- No process was killed, no worker restarted, no models unloaded, no new heavy job submitted.

## Safe activation gate (all are mandatory)
1. Verify Qwen generation is complete or explicitly checkpointed: `/queue` shows no running/pending jobs **and** Qwen producer processes are no longer performing work. Do not infer idleness from queue alone.
2. Confirm the Minimalizer worker has no in-flight upload/compute request; coordinate any planned restart with active clients and its auto-restart controller. Current /health alone does not prove idleness.
3. Require comfortably available RAM for safe startup (RRM heavy default: at least 6 GiB free physical RAM). Inspect GPU pressure separately when applicable. Do not bypass a low-memory gate merely to activate integration.
4. Ensure RLO's shared heavy queue is empty, project `minimalizer` is `ready`, `Reference3DStudio` is still `paused`, and there are no orphaned leases.
5. Only then restart the existing managed Minimalizer service through its documented supervisor/maintenance path; never spawn a duplicate on the same port. Re-check /health and run a **non-inference** admission rejection check. Verify that the new worker process imported `local_worker.rrm_admission` before describing rollout as active.

## Cautions
- The new Windows worker default is `MINIMALIZER_RRM_MODE=enforce`. A missing SQLite gate or constrained RAM causes a fail-closed 429 with Retry-After on compute requests, not automatic Qwen preemption.
- The Qwen benchmark script was modified for **subsequent launches** only. Existing active Python interpreters are not retroactively guarded. Other direct ComfyUI routes can still bypass RRM.
- No automatic background restart, polling trigger, or OS-wide scheduling is enabled. Continue only after re-evaluating live state.
- If a running lease survives a crash, inspect its owner and child processes before considering manual recovery.
