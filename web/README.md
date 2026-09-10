# Minimalizer Web

Minimalizer Web exposes the existing Minimalizer v0.3.0 stable engine through FastAPI and provides a lightweight browser workspace.

## Current web phase

**Web v0.9.0 candidate** extends the completed Rinka Reference / 凛夏手本版 Phase 11 with explicit poster presets while preserving the existing Standard mode and stable engine behavior.

Included:

- drag-and-drop or file-picker image input
- side-by-side source/result preview
- processing, empty, selected, and error states
- segmented `通常 / 凛夏手本版 / Color Strip` mode selector
- Standard mode abstraction level control with advanced settings collapsed by default
- Rinka Reference mode locked to its validated Phase 12 level-4 subject profile
- Rinka-only preset selector: `geometric_poster` (default) or `faceless_subject`
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
- `mode`: `standard`, `rinka_reference`, or `color_strip`, default `standard`
- `level`: abstraction level 1-5, default 4; Rinka Reference requires level 4
- `output_format`: `svg` or `png`, default `svg`
- `rinka_preset`: Rinka-only `geometric_poster` or `faceless_subject`; default `geometric_poster`
- `colors`: optional palette color override, 2-32
- `max_shapes`: optional target shape limit, 5-500
- `background`: optional `source`, `white`, or `transparent`

`colors`, `max_shapes`, and `background` are Standard-mode overrides. Rinka Reference deliberately rejects those overrides so the Phase 12 Rinka profile cannot be silently altered from the Web API. `rinka_preset` is accepted only in Rinka Reference mode.

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/minimalize \
  -F "file=@examples/input.webp;type=image/webp" \
  -F "mode=standard" \
  -F "level=4" \
  -F "output_format=svg" \
  --output minimalized.svg
```

The response includes the selected mode, shape count, analysis size, source size, validated source dimensions, and detected source format in `X-Minimalizer-*` headers.

Rinka Reference example:

```bash
curl -X POST http://127.0.0.1:8000/api/minimalize \
  -F "file=@examples/input.webp;type=image/webp" \
  -F "mode=rinka_reference" \
  -F "level=4" \
  -F "rinka_preset=geometric_poster" \
  -F "output_format=svg" \
  --output minimalized-rinka.svg
```

If both processing slots are occupied, the service returns HTTP `429` with `Retry-After: 2` instead of starting unlimited CPU-heavy jobs.

## Production boundary

The browser UI deliberately keeps the primary flow simple: choose an image, minimalize, compare, download. Production safeguards sit behind that flow and do not alter engine behavior.

The current upload/pixel limits are Web-service safety limits. They do not redefine the capabilities of the desktop/CLI engine.

## Next web phase

After the Phase 12 / Web v0.10.0 candidate is reviewed and explicitly approved for merge, deploy the same build to Railway and verify the public URL end to end in Standard, both Rinka presets, and Color Strip. Keep Standard as the default and confirm the hosted analysis-size cap remains respected before declaring the Phase 12 production rollout complete.
