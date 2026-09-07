# Minimalizer Web

Minimalizer Web exposes the existing Minimalizer v0.3.0 stable engine through FastAPI and provides a lightweight browser workspace.

## Current web phase

**Web Phase 3** hardens the Phase 2 browser experience for an initial hosted pilot without changing the stable engine algorithms.

Included:

- drag-and-drop or file-picker image input
- side-by-side source/result preview
- processing, empty, selected, and error states
- abstraction level control with advanced settings collapsed by default
- SVG preview and download
- PNG download
- responsive mobile layout
- FastAPI Swagger UI retained at `/docs`
- server-side actual-image validation with Pillow
- accepted source formats limited to PNG, JPEG, and WebP
- 20 MB upload limit
- 64,000,000 pixel total-image limit
- 16,384 pixel maximum side limit
- two concurrent image-processing jobs per application process
- immediate HTTP 429 + `Retry-After` when all processing slots are busy
- basic security response headers and no-store API responses
- generic production Docker image
- CI cancellation for superseded PR runs
- real-Uvicorn server smoke coverage in CI

No account system, database, billing, or persistent storage is required for the current product.

## Install

```bash
python -m pip install -r requirements-web.txt
```

## Run locally

```bash
python -m uvicorn web.app:app --host 127.0.0.1 --port 8000
```

Open:

- Browser UI: `http://127.0.0.1:8000/`
- API information: `http://127.0.0.1:8000/api/info`
- Health check: `http://127.0.0.1:8000/health`
- Swagger UI: `http://127.0.0.1:8000/docs`

## Run with Docker

```bash
docker build -t minimalizer-web .
docker run --rm -p 8000:8000 minimalizer-web
```

The container reads `PORT` and `WEB_WORKERS`. Defaults are port `8000` and one Uvicorn worker.

See `docs/WEB_DEPLOYMENT.md` for production sizing and hosting notes.

## Minimalize API

`POST /api/minimalize` accepts `multipart/form-data`.

Fields:

- `file`: PNG, JPEG, or WebP source image, required
- `level`: abstraction level 1-5, default 4
- `output_format`: `svg` or `png`, default `svg`
- `colors`: optional palette color override, 2-32
- `max_shapes`: optional target shape limit, 5-500
- `background`: optional `source`, `white`, or `transparent`

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/minimalize \
  -F "file=@examples/input.webp;type=image/webp" \
  -F "level=4" \
  -F "output_format=svg" \
  --output minimalized.svg
```

The response includes shape count, analysis size, source size, validated source dimensions, and detected source format in `X-Minimalizer-*` headers.

If both processing slots are occupied, the service returns HTTP `429` with `Retry-After: 2` instead of starting unlimited CPU-heavy jobs.

## Production boundary

The browser UI deliberately keeps the primary flow simple: choose an image, minimalize, compare, download. Production safeguards sit behind that flow and do not alter engine behavior.

The current upload/pixel limits are Web-service safety limits. They do not redefine the capabilities of the desktop/CLI engine.

## Next web phase

Web Phase 4 should be the first hosted pilot:

1. deploy the Docker image to the selected provider;
2. verify the real public URL end to end;
3. measure peak memory and request duration with representative images;
4. test the 429 busy path under real concurrent requests;
5. tune instance size and Web limits from measurements rather than guesses;
6. only then decide whether accounts, job history, async queues, or billing are actually needed.
