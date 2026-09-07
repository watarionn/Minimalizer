# Minimalizer Web hosted pilot runbook

Checked: 2026-09-08

This runbook is for Web Phase 4: the first real hosted Minimalizer pilot.

## 1. Railway service creation

1. Create a new Railway project.
2. Add a service from the GitHub repository `watarionn/Minimalizer`.
3. Deploy the `main` branch.
4. Confirm Railway detects the root `Dockerfile`.
5. Set service variables:

```text
WEB_WORKERS=1
WEB_MAX_CONCURRENT_JOBS=2
```

6. Configure Railway healthcheck path to `/health`.
7. Deploy and wait for a healthy deployment.
8. Enable public HTTP networking and generate the initial Railway domain.

Do not create a new `railway.toml` or `railway.json` for this pilot. Railway Config as Code is deprecated; use the provider-neutral root Dockerfile plus Railway service settings.

## 2. Public endpoint verification

Verify all of the following against the real Railway domain:

- `GET /` returns the Minimalizer browser workspace.
- `GET /health` returns HTTP 200 and `{ "status": "ok", ... }`.
- `GET /api/info` reports Web and engine versions plus current limits.
- `GET /docs` opens the FastAPI Swagger surface.

Record the deployed commit SHA and Railway deployment ID before performance testing.

## 3. Representative image pass

Use at least one representative image from each supported format:

- PNG
- JPEG
- WebP

For each request record:

| Sample | Source size | File size | Level | Output | HTTP | Shapes | Processing ms | Total request ms | Peak memory | Notes |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| PNG small | | | 4 | SVG | | | | | | |
| JPEG medium | | | 4 | SVG | | | | | | |
| WebP corpus | | | 4 | SVG | | | | | | |
| Larger source | | | 4 | SVG | | | | | | |

`X-Minimalizer-Processing-Ms` reports engine-side processing time. `Server-Timing` reports total application request duration. Use Railway metrics for peak memory/CPU.

## 4. Concurrency pass

The initial container should run with one worker and two application processing slots.

1. Start two representative minimalization requests closely enough that both overlap.
2. While both processing slots are occupied, send a third request.
3. Confirm the third request receives HTTP `429` with `Retry-After: 2`.
4. Confirm the two accepted requests complete normally.
5. Check Railway memory and CPU during the overlap.

Do not increase workers or processing slots until memory headroom is measured under this test.

## 5. Limit pass

Verify the hosted service rejects:

- unsupported real image formats;
- fake image content disguised with an image MIME type;
- uploads above the configured byte limit;
- images above the configured pixel limit;
- images above the configured maximum-side limit.

The first pilot should keep the application defaults unless measurements show a clear need to lower them.

## 6. Go / no-go gate

Pilot is ready for wider sharing only when:

- Railway deployment is stable across several redeploys;
- `/health` is consistently healthy;
- representative PNG/JPEG/WebP conversions succeed;
- no representative request causes out-of-memory restart;
- 429 backpressure behaves as designed;
- observed processing time is acceptable for an interactive tool;
- billing/spend controls are configured;
- no uploaded image contents or original filenames appear in application logs.

If memory headroom is small, lower image limits or concurrency before increasing instance size. If request latency is acceptable but CPU is saturated, measure a larger instance before increasing workers.

## 7. After the pilot

Once real measurements exist, update:

- recommended Railway instance size;
- `WEB_MAX_CONCURRENT_JOBS` default or deployment variable;
- public upload/pixel limits if needed;
- `docs/WEB_DEPLOYMENT.md` with measured values;
- `HANDOFF.md` with the public deployment URL and validated deployment settings.

Only after those measurements should Web Phase 5 add features such as accounts, history, queues, or billing if they are actually needed.
