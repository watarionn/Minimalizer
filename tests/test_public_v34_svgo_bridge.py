"""MinimalizerPublic-only safety contract for the frozen v34 SVGO research gate."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "public_v34_svgo_candidate.mjs"
GATE = ROOT / "scripts" / "verify_public_v34_svgo_chrome.py"

def test_bridge_is_research_only_and_sha_gated():
    js = CLI.read_text(encoding="utf-8")
    py = GATE.read_text(encoding="utf-8")
    assert '../web/static/vendor/svgo/svgo.browser.js' in js
    assert "preset-default" not in js or "no preset-default" in js
    assert 'writeFileSync(output, candidate, {flag: "wx"})' in js
    assert "appliedToProduction: false" in js
    assert 'check_sha(v34, "v34_evidence_manifest.json"' in py
    assert 'check_sha(v32, "v32_evidence_manifest.json"' in py
    assert py.index('check_sha(v34,') < py.index('out.mkdir(parents=True)')
    assert "negativeControlDifferentPixels" in py
    assert '"productionPromoted": False' in py
    assert '"semanticSourceOwnershipApproved": False' in py
    ast.parse(py)

def test_no_local_or_live_public_route_hooks():
    public = (ROOT / "web/static/public-route.js").read_text(encoding="utf-8")
    local = (ROOT / "local_worker/frontend/local-route.js").read_text(encoding="utf-8")
    assert "public_v34_svgo_candidate" not in public + local
    assert "verify_public_v34_svgo_chrome" not in public + local

def test_negative_rgba_pixel_and_alpha_controls():
    import importlib.util
    spec = importlib.util.spec_from_file_location("v34gate", GATE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    base = bytes([10, 20, 30, 255, 40, 50, 60, 0])
    assert module.mismatched_pixels(base, base) == 0
    assert module.mismatched_pixels(base, bytes([10, 20, 30, 0, 40, 50, 60, 0])) == 1
    assert module.mismatched_pixels(base, bytes([10, 20, 31, 255, 40, 50, 60, 0])) == 1
