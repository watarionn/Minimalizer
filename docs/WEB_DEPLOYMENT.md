# Minimalizer Web deployment

Checked: 2026-09-07

Minimalizer Web is a stateless FastAPI service. It does not require a database or persistent disk for the current feature set. Uploaded images are written only to a per-request temporary directory, processed synchronously, and removed when the request ends.

## Container contract

The repository includes a production-oriented `Dockerfile`.

Runtime defaults:

- listen address: `0.0.0.0`
- port: `PORT` environment variable, default `8000`
- Uvicorn workers: `WEB_WORKERS`, default `1`
- application-level image-processing concurrency: 2 jobs per process
- health endpoint: `GET /health`
- accepted source formats: PNG, JPEG, WebP
- upload byte limit: 20 MB
- image pixel limit: 64,000,000 pixels
- maximum image side: 16,384 pixels

Build and run locally:

```bash
docker build -t minimalizer-web .
docker run --rm -p 8000:8000 minimalizer-web
```

Then open `http://127.0.0.1:8000/`.

## Sizing guidance

Minimalizer is CPU-bound and decodes the source image before the analysis resize step. Large source images can therefore cause short memory and CPU spikes even though the analysis canvas is much smaller.

For a public service:

- do not assume a 512 MB instance is sufficient for the configured maximum image size;
- start with one Uvicorn worker;
- monitor peak RSS and request duration with real uploads before increasing concurrency;
- scale by increasing instance resources first, then replicas/workers only after measuring;
- keep the application-level concurrency guard enabled so bursts do not start unlimited image jobs.

The existing 52.21 MP engine stress result demonstrates engine capability on the development machine, not a guarantee that a small cloud instance can process the same image safely.

## Hosting evaluation

### Railway

Current pricing documentation describes a usage-based model with a Free tier for experimentation and a Hobby plan with a $5/month base commitment that counts toward resource usage. This fits an early, low-traffic pilot where request volume is uncertain.

Reference: https://docs.railway.com/pricing

Suggested use: first live pilot, with billing/spend controls enabled and memory usage observed before increasing the public image limits.

### Render

Render supports Docker web services directly. Current docs list a free web-service compute option with 0.1 CPU / 512 MB and paid compute plans including 1 CPU / 2 GB. The free compute size is useful for route/UI smoke testing but is not the preferred target for large image processing. A 2 GB class service is more realistic if predictable always-on capacity is preferred.

References:

- https://render.com/docs/web-services
- https://render.com/docs/compute-plans
- https://render.com/pricing

### Fly.io

Fly.io uses pay-as-you-go infrastructure pricing and supports flexible machine sizing. It is a good option when lower-level control, regional placement, or machine-level tuning becomes useful, but it introduces more infrastructure decisions than the initial Minimalizer pilot needs.

References:

- https://fly.io/pricing/
- https://fly.io/docs/about/pricing/

## Initial recommendation

Use the generic Docker image and start with Railway for the first external pilot. Keep hosting-specific configuration outside the core application until real traffic and memory measurements are available.

If predictable always-on resources become more important than usage-based cost, reevaluate Render with a 2 GB class compute plan.

## Before public launch

- set a cost/spend alert or hard usage limit where the provider supports it;
- verify the deployed `/health`, `/`, and `/api/info` endpoints;
- upload representative PNG, JPEG, and WebP images;
- test a near-limit source image and observe peak memory;
- verify that the 429 busy response is surfaced cleanly under concurrent load;
- keep one worker until memory headroom is measured;
- do not add persistent storage unless a future feature actually needs it.
