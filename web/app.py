from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from threading import BoundedSemaphore
from typing import Annotated, Literal

from PIL import Image, UnidentifiedImageError
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from .service import build_config, minimalize_path

APP_VERSION = "0.3.0"
MAX_UPLOAD_BYTES = 20 * 1024 * 1024
UPLOAD_CHUNK_BYTES = 1024 * 1024
MAX_IMAGE_PIXELS = 64_000_000
MAX_IMAGE_SIDE = 16_384
MAX_CONCURRENT_JOBS = 2
SUPPORTED_IMAGE_FORMATS = {"PNG", "JPEG", "WEBP"}
STATIC_DIR = Path(__file__).with_name("static")
_PROCESS_SLOTS = BoundedSemaphore(MAX_CONCURRENT_JOBS)

app = FastAPI(
    title="Minimalizer Web API",
    version=APP_VERSION,
    description="Minimalizer v0.3.0 stable engine with a lightweight browser UI and web API.",
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault(
        "Permissions-Policy",
        "camera=(), microphone=(), geolocation=()",
    )
    if request.url.path.startswith("/api/") or request.url.path == "/health":
        response.headers.setdefault("Cache-Control", "no-store")
    return response


def _engine_version() -> str:
    version_file = Path(__file__).resolve().parents[1] / "VERSION"
    try:
        return version_file.read_text(encoding="utf-8").strip()
    except OSError:
        return "unknown"


@app.get("/", include_in_schema=False)
def root() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html", media_type="text/html")


@app.get("/api/info")
def service_info() -> dict[str, str | int]:
    return {
        "service": "Minimalizer Web",
        "web_version": APP_VERSION,
        "engine_version": _engine_version(),
        "docs": "/docs",
        "max_upload_mb": MAX_UPLOAD_BYTES // (1024 * 1024),
        "max_image_pixels": MAX_IMAGE_PIXELS,
        "max_concurrent_jobs": MAX_CONCURRENT_JOBS,
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "engine_version": _engine_version()}


async def _save_upload(upload: UploadFile, destination: Path) -> int:
    total = 0
    with destination.open("wb") as out:
        while True:
            chunk = await upload.read(UPLOAD_CHUNK_BYTES)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_UPLOAD_BYTES:
                raise HTTPException(
                    status_code=413,
                    detail=f"Upload exceeds {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit.",
                )
            out.write(chunk)
    return total


def _validate_image_file(path: Path) -> tuple[int, int, str]:
    try:
        with Image.open(path) as image:
            image_format = (image.format or "").upper()
            width, height = image.size
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise HTTPException(status_code=400, detail="Uploaded file is not a readable image.") from exc

    if image_format not in SUPPORTED_IMAGE_FORMATS:
        allowed = ", ".join(sorted(SUPPORTED_IMAGE_FORMATS))
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported image format. Use one of: {allowed}.",
        )
    if width <= 0 or height <= 0:
        raise HTTPException(status_code=400, detail="Image dimensions are invalid.")
    if width > MAX_IMAGE_SIDE or height > MAX_IMAGE_SIDE:
        raise HTTPException(
            status_code=413,
            detail=f"Image side exceeds {MAX_IMAGE_SIDE} pixel limit.",
        )
    if width * height > MAX_IMAGE_PIXELS:
        raise HTTPException(
            status_code=413,
            detail=f"Image exceeds {MAX_IMAGE_PIXELS:,} pixel limit.",
        )
    return width, height, image_format


@app.post("/api/minimalize")
async def minimalize_image(
    file: Annotated[UploadFile, File(description="Source image")],
    level: Annotated[int, Form(ge=1, le=5)] = 4,
    output_format: Annotated[Literal["svg", "png"], Form()] = "svg",
    colors: Annotated[int | None, Form(ge=2, le=32)] = None,
    max_shapes: Annotated[int | None, Form(ge=5, le=500)] = None,
    background: Annotated[Literal["source", "white", "transparent"] | None, Form()] = None,
) -> Response:
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="Uploaded file must be an image.")

    config = build_config(
        level,
        colors=colors,
        max_shapes=max_shapes,
        background=background,
    )

    try:
        with TemporaryDirectory(prefix="minimalizer-web-") as temp_dir:
            input_path = Path(temp_dir) / "input.upload"
            size = await _save_upload(file, input_path)
            if size == 0:
                raise HTTPException(status_code=400, detail="Uploaded image is empty.")

            source_width, source_height, source_format = _validate_image_file(input_path)

            if not _PROCESS_SLOTS.acquire(blocking=False):
                raise HTTPException(
                    status_code=429,
                    detail="Minimalizer is busy. Please retry shortly.",
                    headers={"Retry-After": "2"},
                )
            try:
                try:
                    result = await run_in_threadpool(
                        minimalize_path,
                        input_path,
                        config,
                        output_format,
                    )
                except (ValueError, OSError) as exc:
                    raise HTTPException(status_code=400, detail="Could not minimalize the uploaded image.") from exc
            finally:
                _PROCESS_SLOTS.release()
    finally:
        await file.close()

    headers = {
        "Content-Disposition": f'attachment; filename="{result.filename}"',
        "X-Minimalizer-Shape-Count": str(result.shape_count),
        "X-Minimalizer-Analysis-Size": result.analysis_size,
        "X-Minimalizer-Source-Size": result.source_size,
        "X-Minimalizer-Validated-Source-Size": f"{source_width}x{source_height}",
        "X-Minimalizer-Source-Format": source_format,
    }
    return Response(content=result.content, media_type=result.media_type, headers=headers)
