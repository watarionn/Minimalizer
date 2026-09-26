from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock
from time import perf_counter
import logging
import os

import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from minimalize_engine.io.image_loader import load_image_bundle
from minimalize_engine.v2 import (
    PipelineConfig,
    RembgGuidanceConfig,
    ShadingFlattenConfig,
    ShadingFlattenGuardConfig,
    RtmlibStructuralConfig,
    attach_rtmlib_structure,
    build_rembg_guidance,
    create_rembg_session,
    create_rtmlib_wholebody,
    export_png,
    minimalize_v2,
)
from minimalize_engine.v2.pipeline import LayeredPersonConfig
logger = logging.getLogger(__name__)

HOST = "127.0.0.1"
PORT = int(os.getenv("MINIMALIZER_LOCAL_WORKER_PORT", "28765"))
ANALYSIS_MAX_SIDE = int(os.getenv("MINIMALIZER_LOCAL_ANALYSIS_MAX_SIDE", "400"))
REMBG_MODEL = os.getenv("MINIMALIZER_LOCAL_REMBG_MODEL", "u2netp")
RTMLIB_MODE = os.getenv("MINIMALIZER_LOCAL_RTMLIB_MODE", "balanced")
RTMLIB_DEVICE = os.getenv("MINIMALIZER_LOCAL_RTMLIB_DEVICE", "cpu")
SHADING_FLATTEN_ENABLED = os.getenv(
    "MINIMALIZER_LOCAL_SHADING_FLATTEN", "1"
).strip().lower() not in {"0", "false", "no", "off"}
SHADING_FLATTEN_SR = int(os.getenv("MINIMALIZER_LOCAL_SHADING_FLATTEN_SR", "45"))
SHADING_FLATTEN_GUARD = os.getenv(
    "MINIMALIZER_LOCAL_SHADING_FLATTEN_GUARD", "1"
).strip().lower() not in {"0", "false", "no", "off"}
GEOMETRIC_MASS_ENABLED = os.getenv(
    "MINIMALIZER_LOCAL_GEOMETRIC_MASS", "1"
).strip().lower() not in {"0", "false", "no", "off"}

DEFAULT_ORIGINS = (
    "https://minimalizer-web-production-a2bc.up.railway.app",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
)
_extra_origins = tuple(
    origin.strip()
    for origin in os.getenv("MINIMALIZER_LOCAL_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
)
ALLOWED_ORIGINS = tuple(dict.fromkeys((*DEFAULT_ORIGINS, *_extra_origins)))

_runtime_lock = Lock()
_process_lock = Lock()
_rembg_session = None
_rtmlib_model = None
_runtime_error: str | None = None
def _rembg_session_options():
    import onnxruntime as ort

    options = ort.SessionOptions()
    options.enable_cpu_mem_arena = True
    options.enable_mem_pattern = True
    options.intra_op_num_threads = max(1, min(4, (os.cpu_count() or 4) // 2))
    options.inter_op_num_threads = 1
    options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    return options


def _ensure_runtime() -> tuple[object, object]:
    global _rembg_session, _rtmlib_model, _runtime_error
    with _runtime_lock:
        try:
            if _rembg_session is None:
                rembg_config = RembgGuidanceConfig(model=REMBG_MODEL)
                _rembg_session = create_rembg_session(
                    rembg_config,
                    sess_opts=_rembg_session_options(),
                )
            if _rtmlib_model is None:
                rtmlib_config = RtmlibStructuralConfig(
                    mode=RTMLIB_MODE,
                    device=RTMLIB_DEVICE,
                )
                _rtmlib_model = create_rtmlib_wholebody(rtmlib_config)
            _runtime_error = None
            return _rembg_session, _rtmlib_model
        except Exception as exc:
            _runtime_error = f"{type(exc).__name__}: {exc}"
            raise
def _build_guidance(input_path: Path):
    rembg_session, rtmlib_model = _ensure_runtime()
    loaded = load_image_bundle(input_path)
    source_rgb = loaded.rgb
    rembg_config = RembgGuidanceConfig(model=REMBG_MODEL)
    base = build_rembg_guidance(
        source_rgb,
        config=rembg_config,
        session=rembg_session,
    )
    if loaded.has_transparency:
        source_alpha = loaded.alpha.astype(np.float32) / 255.0
        constrained_subject = np.where(
            source_alpha > 0.0,
            np.maximum(base.subject_prob, source_alpha),
            0.0,
        ).astype(np.float32)
        base = replace(
            base,
            subject_prob=constrained_subject,
            alpha=source_alpha,
        )
    structural_config = RtmlibStructuralConfig(
        mode=RTMLIB_MODE,
        device=RTMLIB_DEVICE,
    )
    guided, selection = attach_rtmlib_structure(
        source_rgb,
        config=structural_config,
        base_guidance=base,
        model=rtmlib_model,
    )
    return source_rgb, guided, selection


def _run_high_quality(
    input_path: Path,
    *,
    preset: str,
    include_facets: bool,
):
    source_rgb, guidance, selection = _build_guidance(input_path)
    config = PipelineConfig(
        analysis_max_side=ANALYSIS_MAX_SIDE,
        shading_flatten=ShadingFlattenConfig(
            enabled=SHADING_FLATTEN_ENABLED,
            sr=SHADING_FLATTEN_SR,
            hierarchical_parts=True,
        ),
        shading_flatten_guard=ShadingFlattenGuardConfig(
            enabled=SHADING_FLATTEN_GUARD,
        ),
        layered_person=LayeredPersonConfig(
            enabled=True,
            semantic_geometric_mass=GEOMETRIC_MASS_ENABLED,
        ),
    )
    result = minimalize_v2(
        source_rgb,
        presets=(preset,),
        config=config,
        guidance=guidance,
    )
    return export_png(
        result,
        preset=preset,
        include_facets=include_facets,
        preserve_source_alpha=True,
    ), selection
@asynccontextmanager
async def lifespan(_: FastAPI):
    if os.getenv("MINIMALIZER_LOCAL_WORKER_EAGER", "1") != "0":
        try:
            _ensure_runtime()
        except Exception:
            logger.exception("Local worker runtime warmup failed")
    yield


app = FastAPI(
    title="Minimalizer Local Compute Worker",
    version="1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(ALLOWED_ORIGINS),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.middleware("http")
async def guard_browser_origin(request: Request, call_next):
    origin = request.headers.get("origin")
    if origin and origin not in ALLOWED_ORIGINS:
        return JSONResponse(status_code=403, content={"detail": "Origin is not allowed."})
    return await call_next(request)
@app.get("/health")
def health():
    ready = _rembg_session is not None and _rtmlib_model is not None
    status = "ready" if ready else ("degraded" if _runtime_error else "cold")
    return {
        "status": status,
        "worker": "local-compute-v1",
        "ready": ready,
        "analysis_max_side": ANALYSIS_MAX_SIDE,
        "rembg_model": REMBG_MODEL,
        "rtmlib_mode": RTMLIB_MODE,
        "rtmlib_device": RTMLIB_DEVICE,
        "layered_person": True,
        "shading_flatten_candidate": SHADING_FLATTEN_ENABLED,
        "shading_flatten_sr": SHADING_FLATTEN_SR,
        "shading_flatten_guard": SHADING_FLATTEN_GUARD,
        "semantic_geometric_mass": GEOMETRIC_MASS_ENABLED,
        "runtime_error": _runtime_error,
    }


@app.post("/api/local-worker/warmup")
def warmup():
    started = perf_counter()
    try:
        _ensure_runtime()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Local worker runtime could not initialize.") from exc
    return {
        "status": "ready",
        "worker": "local-compute-v1",
        "warmup_ms": round((perf_counter() - started) * 1000.0, 1),
    }


@app.post("/api/v2/minimalize")
async def minimalize_local(
    file: UploadFile = File(...),
    preset: str = Form("minimal"),
    include_facets: bool = Form(True),
):
    if preset not in {"minimal", "balanced", "detailed", "ultra_minimal"}:
        raise HTTPException(status_code=400, detail="Unsupported preset.")
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="Uploaded file must be an image.")
    if not _process_lock.acquire(blocking=False):
        raise HTTPException(
            status_code=429,
            detail="Local Minimalizer worker is busy.",
            headers={"Retry-After": "2"},
        )

    started = perf_counter()
    try:
        with TemporaryDirectory(prefix="minimalizer-local-worker-") as temp_dir:
            input_path = Path(temp_dir) / "input.upload"
            content = await file.read()
            if not content:
                raise HTTPException(status_code=400, detail="Uploaded image is empty.")
            input_path.write_bytes(content)
            try:
                result, selection = _run_high_quality(
                    input_path,
                    preset=preset,
                    include_facets=include_facets,
                )
            except HTTPException:
                raise
            except Exception as exc:
                logger.exception("Local high-quality minimalization failed")
                raise HTTPException(
                    status_code=503,
                    detail="Local high-quality Minimalizer failed.",
                ) from exc
    finally:
        _process_lock.release()
        await file.close()
    metadata = result.metadata
    actual_shading_flatten = (
        metadata.shading_flatten_accepted
        if metadata.shading_flatten_evaluated
        else SHADING_FLATTEN_ENABLED
    )
    elapsed_ms = (perf_counter() - started) * 1000.0
    headers = {
        "Content-Disposition": f'attachment; filename="{result.filename}"',
        "X-Minimalizer-Mode": "v2-local-worker",
        "X-Minimalizer-Compute": "local-worker",
        "X-Minimalizer-Analysis": "rembg+rtmlib",
        "X-Minimalizer-Layered-Person": "true",
        "X-Minimalizer-Geometry-Mass": str(
            GEOMETRIC_MASS_ENABLED
        ).lower(),
        "X-Minimalizer-Shading-Flatten": str(actual_shading_flatten).lower(),
        "X-Minimalizer-Shading-Flatten-Candidate": str(
            SHADING_FLATTEN_ENABLED
        ).lower(),
        "X-Minimalizer-Shading-Flatten-Guard": str(
            SHADING_FLATTEN_GUARD
        ).lower(),
        "X-Minimalizer-Shading-Flatten-Evaluated": str(
            metadata.shading_flatten_evaluated
        ).lower(),
        "X-Minimalizer-Shading-Flatten-SR": str(SHADING_FLATTEN_SR),
        "X-Minimalizer-Shading-Flatten-Reasons": ",".join(
            metadata.shading_flatten_reasons
        ),
        "X-Minimalizer-RTMLib-Selected": "true" if selection is not None else "false",
        "X-Minimalizer-V2-Contract-Version": metadata.contract_version,
        "X-Minimalizer-V2-Preset": metadata.preset,
        "X-Minimalizer-V2-Include-Facets": str(metadata.include_facets).lower(),
        "X-Minimalizer-V2-Pixel-SHA256": metadata.pixel_sha256,
        "X-Minimalizer-V2-PNG-SHA256": metadata.png_sha256,
        "X-Minimalizer-Preserves-Source-Alpha": str(
            metadata.preserves_source_alpha
        ).lower(),
        "X-Minimalizer-Shape-Count": str(metadata.visible_shape_count),
        "X-Minimalizer-Analysis-Size": f"{metadata.width}x{metadata.height}",
        "X-Minimalizer-Source-Size": f"{metadata.source_width}x{metadata.source_height}",
        "X-Minimalizer-Processing-Ms": f"{elapsed_ms:.1f}",
    }
    return Response(content=result.content, media_type=result.media_type, headers=headers)
