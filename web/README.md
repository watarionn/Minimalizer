# Minimalizer Web

Minimalizer Web exposes the existing Minimalizer v0.3.0 stable engine through FastAPI and provides a lightweight browser workspace.

## Current web phase

**Web Phase 2** adds the first user-facing browser UI on top of the Phase 1 API.

Included:

- drag-and-drop or file-picker image input
- side-by-side source/result preview
- processing, empty, selected, and error states
- abstraction level control with advanced settings collapsed by default
- SVG preview and download
- PNG download
- responsive mobile layout
- FastAPI Swagger UI retained at `/docs`

No account system, database, billing, or production deployment provider is introduced yet.

## Install

```bash
python -m pip install -r requirements-web.txt
```

## Run

```bash
python -m uvicorn web.app:app --host 127.0.0.1 --port 8000
```

Open:

- Browser UI: `http://127.0.0.1:8000/`
- API information: `http://127.0.0.1:8000/api/info`
- Health check: `http://127.0.0.1:8000/health`
- Swagger UI: `http://127.0.0.1:8000/docs`

## Minimalize API

`POST /api/minimalize` accepts `multipart/form-data`.

Fields:

- `file`: source image, required
- `level`: abstraction level 1-5, default 4
- `output_format`: `svg` or `png`, default `svg`
- `colors`: optional palette color override, 2-32
- `max_shapes`: optional target shape limit, 5-500
- `background`: optional `source`, `white`, or `transparent`

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/minimalize \
  -F "file=@examples/input.webp" \
  -F "level=4" \
  -F "output_format=svg" \
  --output minimalized.svg
```

The response also includes shape count, analysis size, and source size in `X-Minimalizer-*` headers.

## Phase 2 design boundary

The browser UI deliberately keeps the primary flow simple: choose an image, minimalize, compare, download. Secondary controls stay inside the collapsed detail section so optional settings do not compete with the core product goal.

## Next web phase

Web Phase 3 should focus on production-readiness around the browser experience: stronger upload validation, request limits/concurrency behavior, deployment packaging, and end-to-end browser verification before selecting a production hosting provider.
