"""Collect source-free L06 browser/runtime evidence for the adopted candidate.

The runner drives the real browser entry point and records only hashes, sizes,
headers, timings, and UI state.  It never writes source pixels, response bodies,
or screenshots to the receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import time
from typing import Any

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


EXPECTED_CANDIDATE = "381b0b5a6b52c25472c063c5ca55b65755f3602ab451f569fd6d6a27a20b775a"
SCHEMA = "minimalizer/local-l06/browser-performance/v1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _json_script(driver: webdriver.Chrome, script: str, *args: Any) -> Any:
    return driver.execute_script(script, *args)


def _wait(driver: webdriver.Chrome, predicate: str, timeout: float) -> Any:
    return WebDriverWait(driver, timeout, poll_frequency=0.25).until(
        lambda current: _json_script(current, predicate)
    )


def _install_fetch_probe(driver: webdriver.Chrome) -> None:
    _json_script(
        driver,
        """
        (() => {
          if (window.__minimalizerFetchProbeInstalled) return;
          window.__minimalizerFetchProbeInstalled = true;
          window.__minimalizerFetchEvents = [];
          const originalFetch = window.fetch.bind(window);
          window.fetch = async (...args) => {
            const started = performance.now();
            try {
              const response = await originalFetch(...args);
              const headers = {};
              for (const [key, value] of response.headers.entries()) {
                if (key.startsWith('x-minimalizer-') || key === 'content-type') {
                  headers[key] = value;
                }
              }
              window.__minimalizerFetchEvents.push({
                url: String(args[0]?.url || args[0] || ''),
                status: response.status,
                ok: response.ok,
                elapsed_ms: Math.round((performance.now() - started) * 1000) / 1000,
                headers,
              });
              return response;
            } catch (error) {
              window.__minimalizerFetchEvents.push({
                url: String(args[0]?.url || args[0] || ''),
                status: 0,
                ok: false,
                elapsed_ms: Math.round((performance.now() - started) * 1000) / 1000,
                error: String(error),
              });
              throw error;
            }
          };
        })();
        """,
    )


def _download_info(directory: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*")):
        if not path.is_file():
            continue
        entries.append({"name": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)})
    return entries


def _case(driver: webdriver.Chrome, url: str, name: str, source: Path, timeout: float, download_dir: Path) -> dict[str, Any]:
    driver.get(url)
    _wait(driver, "return document.readyState === 'complete'", 60)
    _install_fetch_probe(driver)
    source_sha = sha256(source)
    started = time.monotonic()
    file_input = driver.find_element(By.ID, "file-input")
    file_input.send_keys(str(source.resolve()))
    _wait(driver, "return document.querySelector('#minimalize-button').disabled === false", 30)
    driver.find_element(By.ID, "minimalize-button").click()
    _wait(
        driver,
        "return document.querySelector('#processing').hidden === true && "
        "document.querySelector('#result-preview').hidden === false",
        timeout,
    )
    png_done = time.monotonic()
    png_state = _json_script(
        driver,
        """
        return {
          title: document.querySelector('#result-title')?.textContent || '',
          meta: document.querySelector('#result-meta')?.textContent || '',
          status: document.querySelector('#status-message')?.textContent || '',
          preview_visible: document.querySelector('#result-preview')?.hidden === false,
          svg_visible: document.querySelector('#download-svg')?.hidden === false,
          fetches: window.__minimalizerFetchEvents || [],
        };
        """,
    )

    # The SVG button is the actual production UI path.  The browser download
    # directory receives only the private temporary response; the receipt keeps
    # its hash and size, never the body.
    svg_before = len(_download_info(download_dir))
    if not png_state["svg_visible"]:
        return {
            "source_sha256": source_sha,
            "source_bytes": source.stat().st_size,
            "source_name": source.name,
            "browser_render_pass": bool(png_state["preview_visible"]),
            "performance_pass": False,
            "hold_reason": "FORMAL_L04_SVG_DOWNLOAD_BUTTON_HIDDEN",
            "png_elapsed_ms": round((png_done - started) * 1000, 3),
            "png_to_svg_elapsed_ms": None,
            "total_elapsed_ms": round((png_done - started) * 1000, 3),
            "ui": {key: value for key, value in png_state.items() if key != "fetches"},
            "api_events": [event for event in png_state["fetches"] if "/api/" in event.get("url", "")],
            "downloaded_artifacts": [],
        }
    driver.find_element(By.ID, "download-svg").click()
    _wait(
        driver,
        "return (window.__minimalizerFetchEvents || []).filter((event) => "
        "event.url.includes('/api/') && event.status === 200).length >= 2",
        timeout,
    )
    _wait(driver, f"return document.readyState === 'complete'", 10)
    svg_done = time.monotonic()
    downloads = _download_info(download_dir)
    new_downloads = downloads[svg_before:]
    events = _json_script(driver, "return window.__minimalizerFetchEvents || [];")
    api_events = [event for event in events if "/api/" in event.get("url", "")]
    completed = len(api_events) >= 2 and all(event.get("status") == 200 for event in api_events[-2:])
    return {
        "source_sha256": source_sha,
        "source_bytes": source.stat().st_size,
        "source_name": source.name,
        "browser_render_pass": bool(png_state["preview_visible"] and completed),
        "performance_pass": bool(completed and (svg_done - started) <= timeout),
        "png_elapsed_ms": round((png_done - started) * 1000, 3),
        "png_to_svg_elapsed_ms": round((svg_done - png_done) * 1000, 3),
        "total_elapsed_ms": round((svg_done - started) * 1000, 3),
        "ui": {key: value for key, value in png_state.items() if key != "fetches"},
        "api_events": api_events,
        "downloaded_artifacts": new_downloads,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--candidate", default=EXPECTED_CANDIDATE)
    parser.add_argument("--case", action="append", required=True, metavar="NAME=PATH")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=float, default=600.0)
    args = parser.parse_args()
    if args.candidate != EXPECTED_CANDIDATE:
        raise SystemExit("candidate receipt is not the adopted 381b0b5a... receipt")

    cases: list[tuple[str, Path]] = []
    for raw in args.case:
        name, separator, path = raw.partition("=")
        if not separator or not name or not path:
            raise SystemExit(f"invalid --case: {raw}")
        source = Path(path)
        if not source.is_file():
            raise SystemExit(f"source file not found: {source}")
        cases.append((name, source))

    chrome_path = Path(os.environ.get("CHROME_PATH", r"C:\Program Files\Google\Chrome\Application\chrome.exe"))
    options = webdriver.ChromeOptions()
    if chrome_path.is_file():
        options.binary_location = str(chrome_path)
    for argument in ("--headless=new", "--no-sandbox", "--disable-gpu", "--disable-extensions", "--disable-dev-shm-usage", "--window-size=1280,1200", "--ignore-certificate-errors"):
        options.add_argument(argument)
    options.accept_insecure_certs = True
    with tempfile.TemporaryDirectory(prefix="minimalizer-l06-browser-") as temp:
        download_dir = Path(temp) / "downloads"
        download_dir.mkdir()
        options.add_experimental_option("prefs", {
            "download.default_directory": str(download_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
        })
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(60)
        try:
            result_cases = {name: _case(driver, args.url, name, source, args.timeout_seconds, download_dir) for name, source in cases}
        finally:
            driver.quit()

    all_pass = all(case["browser_render_pass"] and case["performance_pass"] for case in result_cases.values())
    payload = {
        "schema": SCHEMA,
        "status": "PASS" if all_pass else "HOLD",
        "candidate_receipt_sha256": args.candidate,
        "browser_render_pass": all(case["browser_render_pass"] for case in result_cases.values()),
        "performance_pass": all(case["performance_pass"] for case in result_cases.values()),
        "cases": result_cases,
        "source_free": True,
        "private_artifacts_written_to_receipt": False,
        "screenshots_written_to_receipt": False,
        "release_authorized": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # Windows cmd may use cp932; keep the console report printable without
    # changing the UTF-8 receipt written above.
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0 if all_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
