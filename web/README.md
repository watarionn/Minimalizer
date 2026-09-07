# Minimalizer Web Phase 1

Phase 1 exposes the existing Minimalizer v0.3.0 stable engine through FastAPI. It intentionally contains no account system, database, billing, or browser UI yet.

## Install

```bash
python -m pip install -r requirements-web.txt
```

## Run

```bash
python -m uvicorn web.app:app --host 127.0.0.1 --port 8000
```

Open:

- API information: `http://127.0.0.1:8000/`
- Health check: `http://127.0.0.1:8000/health`
- Swagger UI: `http://127.0.0.1:8000/docs`

## Minimalize an image

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

## Phase boundary

Phase 1 is API-only. Browser drag-and-drop, before/after preview, progress UI, and download controls belong to Web Phase 2 and later.
