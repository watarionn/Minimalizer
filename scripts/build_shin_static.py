from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "web" / "static"
DESTINATION = ROOT / "dist" / "shin"

FORBIDDEN_RUNTIME_MARKERS = (
    "railway.app",
    "Railway fallback",
    'fetch("/api/',
    "fetch('/api/",
    'fetch("/health")',
    "fetch('/health')",
)


def validate_static_runtime() -> None:
    for path in sorted(SOURCE.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".html", ".js", ".css"}:
            continue
        text = path.read_text(encoding="utf-8")
        for marker in FORBIDDEN_RUNTIME_MARKERS:
            if marker in text:
                raise RuntimeError(
                    f"Static runtime still contains hosted-server dependency: "
                    f"{path.relative_to(ROOT)} -> {marker}"
                )


def build() -> Path:
    validate_static_runtime()
    if DESTINATION.exists():
        shutil.rmtree(DESTINATION)

    static_dir = DESTINATION / "static"
    shutil.copytree(SOURCE, static_dir)
    shutil.copy2(SOURCE / "index.html", DESTINATION / "index.html")
    (static_dir / "index.html").unlink()
    (static_dir / ".htaccess").write_text(
        "AddType application/javascript .mjs\n"
        "AddType application/wasm .wasm\n"
        "AddType application/octet-stream .onnx\n",
        encoding="utf-8",
    )

    return DESTINATION


if __name__ == "__main__":
    output = build()
    print(output)
