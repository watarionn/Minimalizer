# Minimalizer browser process residue prevention (2026-10-08)

## Outcome and scope

This phase addressed process/RAM hygiene, not the SA10.42 image-quality pipeline. Earlier, an orphaned Selenium headless Chrome tree (8 processes, approximately 52.64 MiB RSS) and its associated obsolete Chrome profile (125.91 MiB disk) were safely cleared after verifying its ChromeDriver parent had exited. A subsequent RAM sample found 15.58 GiB physical RAM and 3.75 GiB free. This difference is not attributable solely to the 53 MiB Chrome cleanup: Ollama, Qwen/ComfyUI and WSL workloads were changing independently. Qwen/ComfyUI was actively using approximately 3.3 GiB at the later sample, and was deliberately protected.

The Local Worker at 127.0.0.1:28764 and Tailscale Worker at ywshtmr.tail8fd68c.ts.net:28765 remained ready=true, zerobase2. No active Qwen, HoloScope, Ollama, Docker, KeibaAI, Local Worker, or other Chrome profile was terminated. Evidence in research folders was not bulk-deleted: most are disk files and do not consume resident RAM.

## Permanent source-level improvement

- tools/minimalizer_browser_profile_lifecycle.py creates unique temporary, explicitly tagged Minimalizer-only Chrome profiles under Windows TEMP/MinimalizerE2E/run-<unique-id>. The cache is deleted on normal benchmark exit. Original saved images and JSON evidence remain in separate output directories. If Windows cache locks interrupt deletion, the ownership marker is restored so that safe inspection is still possible.
- tools/run_browser_facet_v15_chrome_compare.py, tools/run_browser_shape_v14_chrome_compare.py and tools/run_browser_sharp_lite_chrome_compare.py now use managed disposable profiles and nested finally blocks to tear down ChromeDriver, HTTP server and browser caches even when verification throws.
- tools/cleanup_minimalizer_orphan_chrome.py is a manual, nonresident one-shot guard. The default is AUDIT ONLY. Applying cleanup is opt-in and restricted to a signed profile, old headless WebDriver Chrome, missing ChromeDriver/creator parents, exclusive same-profile Chrome descendants, and an explicit minimum 60-minute age. It rechecks creation time and process tree immediately before acting; no generic taskkill or other project service actions.
- tests/test_minimalizer_browser_resource_hygiene.py includes synthetic adversarial safety tests, including user-Chrome exclusions, active parents, shared profile rejection, and recovery of the ownership tag after a simulated Windows cache lock.
- .github/workflows/minimalizer-browser-resource-hygiene.yml checks source syntax and tests without launching Chrome/GPU/worker and without installing a resident monitor.

## Usage

Audit only, does not kill anything:
    python -m tools.cleanup_minimalizer_orphan_chrome

Explicit safe cleanup only if reviewed candidates exist:
    python -m tools.cleanup_minimalizer_orphan_chrome --apply

A new actual Windows dry run reported orphan_candidate_count=0. This phase therefore did not force any additional process termination. Profiles from other apps, the real user Chrome profile, source evidence and active projects are never eligible. Do not globally kill chrome.exe, stop WSL/Docker, or clear all TEMP files. When active AI workloads finish, memory will generally be released by those processes without killing ongoing user tasks.

Canonical code is GitHub main. Backup and RAM/process guard evidence is stored under Google Drive chatGPT及びCodex用/Minimalizer/ResourceHygiene_20261008. The on-demand approach respects the project instruction to minimize RDC, background processes and needless local sources of truth.
