# Minimalizer Web deployment

Checked: 2026-09-08

Minimalizer Web is a stateless FastAPI service. It does not require a database or persistent disk for the current feature set. Uploaded images are written only to a per-request temporary directory, processed synchronously, and removed when the request ends.

## Container contract

The repository includes a production-oriented root `Dockerfile`.

Runtime defaults:

- listen address: `0.0.0.0`
- port: `PORT` environment variable, default `8000`
- Uvicorn workers: `WEB_WORKERS`, default `1`
- application-level image-processing concurrency: `WEB_MAX_CONCURRENT_JOBS`, default `2` per process
- health endpoint: `GET /health`
- accepted source formats: PNG, JPEG, WebP
- upload limit: `WEB_MAX_UPLOAD_MB`, default `20`
- image pixel limit: `WEB_MAX_IMAGE_PIXELS`, default `64,000,000`
- maximum image side: `WEB_MAX_IMAGE_SIDE`, default `16,384`

The application clamps environment-based limits to safe implementation ranges rather than accepting arbitrary values.

Build and run locally:

```bash
docker build -t minimalizer-web .
docker run --rm -p 8000:8000 minimalizer-web
```

Then open `http://127.0.0.1:8000/`.

## Pilot observability

Successful minimalization responses expose:

- `X-Request-ID`: generated request identifier
- `X-Minimalizer-Processing-Ms`: engine-side processing duration
- `X-Minimalizer-Shape-Count`: result shape count
- `X-Minimalizer-Source-Format`: validated source format
- `X-Minimalizer-Validated-Source-Size`: validated source dimensions
- `Server-Timing`: total application request duration

Application logs record request ID, source format, source dimensions, output format, processing duration, and shape count. They intentionally do not record uploaded image contents or original filenames.

## Sizing guidance

Minimalizer is CPU-bound and decodes the source image before the analysis resize step. Large source images can therefore cause short memory and CPU spikes even though the analysis canvas is much smaller.

For a public service:

- do not assume a 512 MB instance is sufficient for the configured maximum image size;
- start with `WEB_WORKERS=1`;
- start with `WEB_MAX_CONCURRENT_JOBS=2`;
- monitor peak RSS and request duration with real uploads before increasing concurrency;
- scale by increasing instance resources first, then replicas/workers only after measuring;
- remember that each Uvicorn worker owns its own concurrency semaphore, so total possible image jobs are approximately `WEB_WORKERS * WEB_MAX_CONCURRENT_JOBS` per container.

The existing 52.21 MP engine stress result demonstrates engine capability on the development machine, not a guarantee that a small cloud instance can process the same image safely.

## Railway pilot

Railway is the preferred first hosted pilot target.

Current Railway behavior relevant to this repository:

- a root file named `Dockerfile` is automatically detected and used for the build;
- a GitHub repository can be connected directly as the service source;
- the service should bind to `0.0.0.0` and Railway's `PORT`, which the Dockerfile already does;
- configure Railway's deployment healthcheck path as `/health`;
- enable public networking after the first healthy deployment to obtain a public domain.

Do **not** introduce a new `railway.toml` or `railway.json` for this pilot. Railway's Config as Code feature is deprecated, and its documentation states that legacy Config as Code files remain supported only until 2026-12-01. Keep the current provider-neutral Dockerfile as the source of runtime behavior and use Railway service settings for the small amount of provider-specific configuration.

Railway references:

- https://docs.railway.com/builds/dockerfiles
- https://docs.railway.com/services
- https://docs.railway.com/deployments/healthchecks
- https://docs.railway.com/config-as-code/reference
- https://docs.railway.com/pricing

Recommended initial Railway variables:

```text
WEB_WORKERS=1
WEB_MAX_CONCURRENT_JOBS=2
```

Leave the image/upload limits at application defaults for the first measurement pass.

## Other hosting candidates

### Render

Render supports Docker web services directly. A small free compute option is useful for route/UI smoke testing, but large image processing should be sized from measured memory use rather than assumed to fit a minimal instance.

References:

- https://render.com/docs/web-services
- https://render.com/docs/compute-plans
- https://render.com/pricing

### Fly.io

Fly.io supports flexible machine sizing and regional placement. It remains a strong option if machine-level tuning becomes useful, but it adds more infrastructure decisions than the first Minimalizer pilot needs.

References:

- https://fly.io/pricing/
- https://fly.io/docs/about/pricing/

## Before widening public access

- enable Railway billing/spend controls appropriate to the account;
- verify deployed `/health`, `/`, `/api/info`, and `/docs`;
- upload representative PNG, JPEG, and WebP images;
- record `X-Minimalizer-Processing-Ms` and Railway peak memory for each sample;
- exercise two concurrent conversions, then verify an additional overlapping request receives HTTP 429 when both local processing slots are occupied;
- test a larger source image only after checking memory headroom;
- keep one worker until memory headroom is measured;
- do not add persistent storage unless a future feature actually needs it.

See `docs/WEB_PILOT_RUNBOOK.md` for the first-deployment checklist and measurement table.
