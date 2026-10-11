# Stage46 CI exact verification, 2026-10-12

- GitHub repository: `watarionn/Minimalizer`
- Draft PR #390, branch `research/public-structural-recovery-p0-part-preservation-20261011`.
- CI-triggering source/test head: `d7d905a4675b83e4b93d2df9f186cf1e070344ed`.
- GitHub Actions run: https://github.com/watarionn/Minimalizer/actions/runs/38164224872
- GitHub job `114543306311`, `conclusion=success`.
- Readback of job logs: **246 tests; 246 passed; 0 failed; 0 skipped**. Previous Stage1–41 count 212, new Stage42–44 count 34 (24 viewport/session + 10 source-probe).
- CI adapter is the already listed `tests/js/test_public_annotation_stage36_p0.mjs`, now importing both new test suites. The workflow itself remains source-only research regression; no deployment occurs.
- Independent original-image anatomy review **0 accepted** for GC001/Raden. Source SHA-only test passage does **not** authorize painting, final Golden, release, or merge. This test suite does not exercise private Chrome HTML or native iPhone Safari.
- Validating the code commit does not prove any subsequent docs-only HEAD; keep the exact triggering SHA when reporting.
