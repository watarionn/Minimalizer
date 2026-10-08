# Minimalizer Local Worker × Rinka Resource Manager

**Stage:** source integrated; activation occurs only when the Local Worker
process safely restarts. Never restart while handling an image request.

The CPU-heavy processing section of both `/api/zerobase2/minimalize` and
`/api/v2/minimalize` obtains the RRM single-heavy-job reservation.
The resident FastAPI server itself stays online; warmup/health calls do not
request heavyweight admission. Admission failures return HTTP 429 and a
`Retry-After: 10` hint. Existing quality-gate semantics are unchanged.

On Windows, a newly started worker uses RRM by default.
Required local installation:
- `C:\Work\Projects\RinkaLocalOperator` on the same host (override with
  `MINIMALIZER_RRM_ROOT`).
- Project ID `minimalizer` registered as `heavy`, state `ready`.
- No ongoing uncoordinated Qwen/Minimalizer processing at switchover.

If a gate cannot be read, compute requests fail closed rather than bypassing
the shared queue. For an explicit emergency rollback set
`MINIMALIZER_RRM_MODE=off` **before the next safe worker restart**. Non-Windows
environments default to off unless explicitly set to `enforce`.

The request guard occupies the same SQLite slot as
`rrm.cmd heavy-run` and Qwen's guarded benchmark entrypoint. The presence
of a running worker does not occupy the slot when no image is being processed.

**Limitations:** this does not retroactively guard workers already in memory,
other Minimalizer servers/processes, or Qwen producers launched outside RRM.
The RRM slot is cooperative, not GPU-wide OS scheduling. No running worker
is killed and no model is automatically unloaded by this change.

## Validation

```powershell
python -m unittest discover -s tests -p test_rrm_admission.py -v
python -m py_compile local_worker/app.py local_worker/rrm_admission.py
```
