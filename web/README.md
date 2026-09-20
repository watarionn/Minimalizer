# Minimalizer Web

Minimalizer Web exposes the Minimalizer engine through FastAPI and provides a lightweight browser workspace.

## Current browser experience

The browser UI exposes one canonical minimalization path: **Minimalizer 2.0 high-accuracy V2**. Users no longer choose between Standard and Rinka Reference. Color Strip remains separate because it produces a different kind of output.

Browser behavior:

- drag-and-drop or file-picker image input
- side-by-side source/result preview
- `ミニマル化 / Color Strip` tool selector
- browser minimalization always calls `POST /api/v2/minimalize`
- V2 uses the production `minimal` preset with facets enabled and returns PNG
- legacy level/color/max-shape/background controls are not exposed in the browser
- Rinka Reference is not exposed in the browser
- Color Strip keeps its color-selection and layout controls
- PNG download for the canonical V2 minimalization result
- SVG and PNG download for Color Strip
- responsive mobile layout
- FastAPI Swagger UI retained at `/docs`
- accepted source formats limited to PNG, JPEG, and WebP
- 20 MB upload limit
- 64,000,000 pixel total-image limit
- 16,384 pixel maximum side limit
- one concurrent image-processing job per application process
- immediate HTTP 429 + `Retry-After` when the processing slot is busy
- basic security response headers and no-store API responses
- production Docker image with the hosted rembg model baked in

The legacy `standard` and `rinka_reference` API modes remain available for backward compatibility and evaluation tooling. Removing them from the browser does not remove those API contracts.

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
- V2 API information: `http://127.0.0.1:8000/api/v2/info`
- Health check: `http://127.0.0.1:8000/health`
- Swagger UI: `http://127.0.0.1:8000/docs`

## Run with Docker

```bash
docker build -t minimalizer-web .
docker run --rm -p 8000:8000 minimalizer-web
```

The container reads `PORT`, `WEB_WORKERS`, and the Web safety-limit variables. Production uses one Uvicorn worker and one image-processing slot.

See `docs/WEB_DEPLOYMENT.md` for production sizing and hosting notes.

## Canonical V2 minimalization API

`POST /api/v2/minimalize` accepts multipart form data.

Fields:

- `file`: PNG, JPEG, or WebP source image, required
- `preset`: `minimal`, `balanced`, `detailed`, or `ultra_minimal`; browser uses `minimal`
- `include_facets`: boolean; browser uses `true`

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/v2/minimalize \
  -F "file=@examples/input.webp;type=image/webp" \
  -F "preset=minimal" \
  -F "include_facets=true" \
  --output minimalized.png
```

## Compatibility API

`POST /api/minimalize` remains available for historical and specialist modes.

Supported modes:

- `standard`
- `rinka_reference`
- `color_strip`

This route still supports legacy Standard settings, Rinka Reference presets, and Color Strip settings. The browser only uses it for Color Strip.

Rinka Reference is retained for compatibility and evaluation. It is not presented as a competing browser button against the canonical V2 path.

## Production boundary

The browser intentionally exposes only the current canonical V2 minimalization path. Historical and specialist engines remain available through the API for compatibility, testing, and comparison, but users do not need to understand or choose between those internal generations.

The current upload, pixel, analysis-size, and concurrency limits are Web-service safety limits. They do not redefine the capabilities of the desktop/CLI engine.
