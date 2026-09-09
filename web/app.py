from __future__ import annotations

import logging
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import BoundedSemaphore
from time import perf_counter
from typing import Annotated, Literal
from uuid import uuid4

from PIL import Image, UnidentifiedImageError
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from minimalize_engine.color_strip import (
    ANALYSIS_MAX_SIDE as COLOR_STRIP_ANALYSIS_MAX_SIDE,
    COLOR_STRIP_VERSION,
    DEFAULT_COLOR_COUNT as COLOR_STRIP_DEFAULT_COLOR_COUNT,
    DEFAULT_SIMILARITY as COLOR_STRIP_DEFAULT_SIMILARITY,
    MAX_COLOR_COUNT as COLOR_STRIP_MAX_COLOR_COUNT,
    MAX_SIMILARITY as COLOR_STRIP_MAX_SIMILARITY,
    MIN_COLOR_COUNT as COLOR_STRIP_MIN_COLOR_COUNT,
    MIN_SIMILARITY as COLOR_STRIP_MIN_SIMILARITY,
)
from minimalize_engine.target_style import RINKA_REFERENCE_VERSION

from .service import (
    build_config,
    build_rinka_config,
    color_strip_path,
    minimalize_path,
    minimalize_rinka_path,
)

APP_VERSION = "0.6.0"
UPLOAD_CHUNK_BYTES = 1024 * 1024
SUPPORTED_IMAGE_FORMATS = {"PNG", "JPEG", "WEBP"}
STATIC_DIR = Path(__file__).with_name("static")
logger = logging.getLogger("minimalizer.web")


def _env_int(name: str, default: int, *, minimum: int, maximum: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        logger.warning("Ignoring invalid integer environment value for %s", name)
        return default
    if value < minimum or value > maximum:
        logger.warning("Clamping %s to allowed range %s..%s", name, minimum, maximum)
    return max(minimum, min(maximum, value))


MAX_UPLOAD_MB = _env_int("WEB_MAX_UPLOAD_MB", 20, minimum=1, maximum=100)
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
MAX_IMAGE_PIXELS = _env_int(
    "WEB_MAX_IMAGE_PIXELS",
    64_000_000,
    minimum=1_000_000,
    maximum=200_000_000,
)
MAX_IMAGE_SIDE = _env_int("WEB_MAX_IMAGE_SIDE", 16_384, minimum=512, maximum=65_535)
MAX_ANALYSIS_SIDE = _env_int("WEB_MAX_ANALYSIS_SIDE", 640, minimum=256, maximum=2_048)
MAX_CONCURRENT_JOBS = _env_int("WEB_MAX_CONCURRENT_JOBS", 2, minimum=1, maximum=8)
_PROCESS_SLOTS = BoundedSemaphore(MAX_CONCURRENT_JOBS)

app = FastAPI(
    title="Minimalizer Web API",
    version=APP_VERSION,
    description="Minimalizer v0.3.0 stable engine with Standard, Rinka Reference, and Color Strip browser modes.",
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.middleware("http")
async def add_request_metadata_and_security_headers(request: Request, call_next):
    request_id = uuid4().hex
    request.state.request_id = request_id
    started = perf_counter()
    response = await call_next(request)
    total_ms = (perf_counter() - started) * 1000.0

    response.headers.setdefault("X-Request-ID", request_id)
    response.headers.setdefault("Server-Timing", f"app;dur={total_ms:.1f}")
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
def service_info() -> dict[str, object]:
    return {
        "service": "Minimalizer Web",
        "web_version": APP_VERSION,
        "engine_version": _engine_version(),
        "docs": "/docs",
        "max_upload_mb": MAX_UPLOAD_MB,
        "max_image_pixels": MAX_IMAGE_PIXELS,
        "max_image_side": MAX_IMAGE_SIDE,
        "max_analysis_side": MAX_ANALYSIS_SIDE,
        "max_concurrent_jobs": MAX_CONCURRENT_JOBS,
        "supported_modes": ["standard", "rinka_reference", "color_strip"],
        "rinka_reference_version": RINKA_REFERENCE_VERSION,
        "color_strip_version": COLOR_STRIP_VERSION,
        "color_strip_default_colors": COLOR_STRIP_DEFAULT_COLOR_COUNT,
        "color_strip_default_similarity": COLOR_STRIP_DEFAULT_SIMILARITY,
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
                    detail=f"Upload exceeds {MAX_UPLOAD_MB} MB limit.",
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
    request: Request,
    file: Annotated[UploadFile, File(description="Source image")],
    level: Annotated[int, Form(ge=1, le=5)] = 4,
    output_format: Annotated[Literal["svg", "png"], Form()] = "svg",
    mode: Annotated[Literal["standard", "rinka_reference", "color_strip"], Form()] = "standard",
    colors: Annotated[int | None, Form(ge=2, le=32)] = None,
    color_similarity: Annotated[
        float | None,
        Form(ge=COLOR_STRIP_MIN_SIMILARITY, le=COLOR_STRIP_MAX_SIMILARITY),
    ] = None,
    max_shapes: Annotated[int | None, Form(ge=5, le=500)] = None,
    background: Annotated[Literal["source", "white", "transparent"] | None, Form()] = None,
) -> Response:
    request_id = request.state.request_id
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="Uploaded file must be an image.")

    strip_color_count = COLOR_STRIP_DEFAULT_COLOR_COUNT
    strip_similarity = COLOR_STRIP_DEFAULT_SIMILARITY

    if mode == "rinka_reference":
        if (
            level != 4
            or colors is not None
            or color_similarity is not None
            or max_shapes is not None
            or background is not None
        ):
            raise HTTPException(
                status_code=400,
                detail="Rinka Reference uses its frozen level-4 profile; custom detail settings are not supported.",
            )
        config = build_rinka_config(analysis_max_side_cap=MAX_ANALYSIS_SIDE)
        configured_analysis_max_side = config.analysis_max_side
        response_level = "4"
    elif mode == "color_strip":
        if max_shapes is not None or background is not None:
            raise HTTPException(
                status_code=400,
                detail="Color Strip only supports color count and color similarity settings.",
            )
        strip_color_count = colors if colors is not None else COLOR_STRIP_DEFAULT_COLOR_COUNT
        if not COLOR_STRIP_MIN_COLOR_COUNT <= strip_color_count <= COLOR_STRIP_MAX_COLOR_COUNT:
            raise HTTPException(
                status_code=400,
                detail="Color Strip color count must be between 3 and 5.",
            )
        strip_similarity = (
            color_similarity if color_similarity is not None else COLOR_STRIP_DEFAULT_SIMILARITY
        )
        configured_analysis_max_side = min(COLOR_STRIP_ANALYSIS_MAX_SIDE, MAX_ANALYSIS_SIDE)
        response_level = "n/a"
        config = None
    else:
        if color_similarity is not None:
            raise HTTPException(
                status_code=400,
                detail="Color similarity is only available in Color Strip mode.",
            )
        config = build_config(
            level,
            colors=colors,
            max_shapes=max_shapes,
            background=background,
            analysis_max_side_cap=MAX_ANALYSIS_SIDE,
        )
        configured_analysis_max_side = config.analysis_max_side
        response_level = str(level)

    try:
        with TemporaryDirectory(prefix="minimalizer-web-") as temp_dir:
            input_path = Path(temp_dir) / "input.upload"
            size = await _save_upload(file, input_path)
            if size == 0:
                raise HTTPException(status_code=400, detail="Uploaded image is empty.")

            source_width, source_height, source_format = _validate_image_file(input_path)

            if not _PROCESS_SLOTS.acquire(blocking=False):
                logger.info(
                    "minimalize_busy request_id=%s mode=%s format=%s width=%s height=%s level=%s analysis_max_side=%s",
                    request_id,
                    mode,
                    source_format,
                    source_width,
                    source_height,
                    response_level,
                    configured_analysis_max_side,
                )
                raise HTTPException(
                    status_code=429,
                    detail="Minimalizer is busy. Please retry shortly.",
                    headers={"Retry-After": "2"},
                )

            processing_started = perf_counter()
            try:
                try:
                    if mode == "rinka_reference":
                        result = await run_in_threadpool(
                            minimalize_rinka_path,
                            input_path,
                            output_format,
                            analysis_max_side_cap=MAX_ANALYSIS_SIDE,
                        )
                    elif mode == "color_strip":
                        result = await run_in_threadpool(
                            color_strip_path,
                            input_path,
                            output_format,
                            color_count=strip_color_count,
                            similarity=strip_similarity,
                            analysis_max_side_cap=MAX_ANALYSIS_SIDE,
                        )
                    else:
                        result = await run_in_threadpool(
                            minimalize_path,
                            input_path,
                            config,
                            output_format,
                        )
                except (ValueError, OSError) as exc:
                    raise HTTPException(status_code=400, detail="Could not minimalize the uploaded image.") from exc
            finally:
                processing_ms = (perf_counter() - processing_started) * 1000.0
                _PROCESS_SLOTS.release()
    finally:
        await file.close()

    logger.info(
        "minimalize_success request_id=%s mode=%s format=%s width=%s height=%s level=%s analysis_max_side=%s output=%s processing_ms=%.1f shapes=%s",
        request_id,
        mode,
        source_format,
        source_width,
        source_height,
        response_level,
        configured_analysis_max_side,
        output_format,
        processing_ms,
        result.shape_count,
    )

    headers = {
        "Content-Disposition": f'attachment; filename="{result.filename}"',
        "X-Minimalizer-Mode": mode,
        "X-Minimalizer-Level": response_level,
        "X-Minimalizer-Configured-Analysis-Max-Side": str(configured_analysis_max_side),
        "X-Minimalizer-Shape-Count": str(result.shape_count),
        "X-Minimalizer-Analysis-Size": result.analysis_size,
        "X-Minimalizer-Source-Size": result.source_size,
        "X-Minimalizer-Validated-Source-Size": f"{source_width}x{source_height}",
        "X-Minimalizer-Source-Format": source_format,
        "X-Minimalizer-Processing-Ms": f"{processing_ms:.1f}",
    }
    if result.color_count is not None:
        headers["X-Minimalizer-Color-Count"] = str(result.color_count)
    if result.color_similarity is not None:
        headers["X-Minimalizer-Color-Similarity"] = f"{result.color_similarity:g}"

    return Response(content=result.content, media_type=result.media_type, headers=headers)
