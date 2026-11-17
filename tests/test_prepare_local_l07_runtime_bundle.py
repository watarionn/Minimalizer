from pathlib import Path

import pytest

from tools.research.prepare_local_l07_runtime_bundle import prepare


ROOT = Path(__file__).parents[1]


def test_prepare_is_non_mutating_and_binds_generation(tmp_path):
    output = tmp_path / "bundle"
    manifest = prepare(ROOT, output)

    assert manifest["status"] == "STAGING_READY"
    assert manifest["runtime_mutation"] is False
    assert manifest["release_authorized"] is False
    assert manifest["owner_apply_required"] is True
    assert manifest["generation"] == "minimalizer-local-20261117-2"
    assert (output / "local_worker/frontend/sw.js").is_file()
    assert (output / "local_worker/frontend/local-route.js").is_file()
    assert (output / "runtime-staging-manifest.json").is_file()


def test_prepare_rejects_existing_nonempty_output(tmp_path):
    output = tmp_path / "bundle"
    output.mkdir()
    (output / "sentinel.txt").write_text("keep", encoding="utf-8")

    with pytest.raises(ValueError, match="new empty directory"):
        prepare(ROOT, output)


def test_prepare_rejects_generation_mismatch(tmp_path):
    source = tmp_path / "source"
    for relative in (
        Path("local_worker/frontend/sw.js"),
        Path("local_worker/frontend/local-route.js"),
    ):
        target = source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text((ROOT / relative).read_text(encoding="utf-8"), encoding="utf-8")
    route = source / "local_worker/frontend/local-route.js"
    route.write_text(
        route.read_text(encoding="utf-8").replace(
            "minimalizer-local-20261117-2", "minimalizer-local-20261118-1"
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="generations differ"):
        prepare(source, tmp_path / "bundle")


def test_prepare_rejects_unsafe_service_worker(tmp_path):
    source = tmp_path / "source"
    for relative in (
        Path("local_worker/frontend/sw.js"),
        Path("local_worker/frontend/local-route.js"),
    ):
        target = source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text((ROOT / relative).read_text(encoding="utf-8"), encoding="utf-8")
    sw = source / "local_worker/frontend/sw.js"
    sw.write_text(sw.read_text(encoding="utf-8") + "\ncaches.delete('old');\n", encoding="utf-8")

    with pytest.raises(ValueError, match="forbidden Service Worker operation"):
        prepare(source, tmp_path / "bundle")
