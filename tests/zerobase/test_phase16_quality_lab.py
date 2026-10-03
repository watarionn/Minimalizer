import importlib.util
import json
from pathlib import Path

MODULE_PATH = Path(__file__).parents[2] / "tools" / "run_phase16_quality_lab.py"
spec = importlib.util.spec_from_file_location("phase16_quality_lab", MODULE_PATH)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

def test_parse_json_text_accepts_plain_and_fenced():
    assert mod.parse_json_text('{"a":1}') == {"a":1}
    assert mod.parse_json_text('```json\n{"a":1}\n```') == {"a":1}

def test_prompt_forbids_generated_pixels():
    assert "Do not propose or generate replacement pixels" in mod.PROMPT
    assert "observed evidence" in mod.PROMPT
