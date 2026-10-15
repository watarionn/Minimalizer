#!/usr/bin/env python3
"""Run private Run139 Chromium QA in separately bounded, fail-closed batches.

The historical 77-test monolithic invocation exceeded a short outer tool budget,
although its tests pass when allowed to finish. Invoke this tool twice:
  python run139_chunked_verify.py --workspace PRIVATE_DIR --group regression
  python run139_chunked_verify.py --workspace PRIVATE_DIR --group run139

This program never opens, uploads, copies, or modifies private evidence itself.
The tests are the unchanged originals from the private verified workspace.
"""
import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

GROUPS = {
    'regression': (('test_run134', 'test_run135', 'test_run135_gates',
                    'test_run135_model', 'test_run136', 'test_run137',
                    'test_run138'), 70),
    'run139': (('test_run139',), 7),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--group', choices=GROUPS, required=True)
    parser.add_argument('--timeout', type=int, default=90)
    parser.add_argument('--report', type=Path, default=None)
    parser.add_argument('--plan', action='store_true')
    args = parser.parse_args()
    if args.timeout < 10 or args.timeout > 900:
        parser.error('--timeout must be between 10 and 900 seconds')
    workspace = args.workspace.expanduser().resolve()
    modules, expected = GROUPS[args.group]
    command = [sys.executable, '-m', 'unittest', '-q', *modules]
    if args.plan:
        print(json.dumps({'workspace': str(workspace), 'group': args.group,
                          'command': command, 'expected_tests': expected}, ensure_ascii=False))
        return 0
    if not workspace.is_dir() or not all((workspace / (m + '.py')).is_file() for m in modules):
        print('FAIL: private workspace or required test modules missing', file=sys.stderr)
        return 2
    started = time.monotonic()
    try:
        result = subprocess.run(command, cwd=workspace, capture_output=True,
                                text=True, timeout=args.timeout, check=False)
        output = result.stdout + result.stderr
        elapsed = round(time.monotonic() - started, 3)
        match = re.search(r'^Ran (\d+) tests? in ([0-9.]+)s$', output, re.MULTILINE)
        passed = (result.returncode == 0 and match is not None
                  and int(match.group(1)) == expected
                  and re.search(r'^OK$', output, re.MULTILINE) is not None
                  and 'FAILED (' not in output)
        record = {'group': args.group, 'result': 'PASS' if passed else 'FAIL',
                  'expected_tests': expected,
                  'reported_tests': int(match.group(1)) if match else None,
                  'returncode': result.returncode, 'wall_seconds': elapsed,
                  'timeout_seconds': args.timeout, 'output_tail': output[-2500:]}
    except subprocess.TimeoutExpired as exc:
        record = {'group': args.group, 'result': 'TIMEOUT', 'expected_tests': expected,
                  'reported_tests': None, 'returncode': None,
                  'wall_seconds': round(time.monotonic() - started, 3),
                  'timeout_seconds': args.timeout,
                  'output_tail': str(exc)[-1000:]}
    print(json.dumps(record, ensure_ascii=False, indent=2))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return 0 if record['result'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
