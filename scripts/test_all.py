"""Run every check in the project, in dependency order.

One command, non-zero exit on any failure:

    python scripts/test_all.py

Checks
  1. neural_core     frozen dynamics: pathway present, unstimulated network silent
  2. looming         stimulus monotonic, timing not flat, recruitment scales with size
  3. upstream_drive  lobula plate classes complete, static stimulus silent, stimulus reaches
                     the network
  4. measure_final   produces data/measurement.json with the expected fields
  5. export_static   produces the deployable static files
  6. serve           backend envelope, view mapping, unmeasured-null, negative findings, routes
  7. dashboard       TypeScript build passes (skipped if bun is unavailable)
  8. dashboard lint  oxlint reports no errors (skipped if bun is unavailable)

The dashboard's rendered output is verified separately by verify_camera_tuning.py and
verify_dashboard.py, which need a running dev server. See README.md.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / 'scripts'
MEASUREMENT = REPO_ROOT / 'data' / 'measurement.json'

PY = sys.executable

CHECKS: list[tuple[str, list[str] | None]] = [
    ('neural_core', [PY, str(SCRIPTS / 'neural_core.py'), '--test']),
    ('looming', [PY, str(SCRIPTS / 'looming.py'), '--test']),
    ('upstream_drive', [PY, str(SCRIPTS / 'upstream_drive.py'), '--test']),
    ('measure_final', [PY, str(SCRIPTS / 'measure_final.py'), '--quick']),
    ('export_static', [PY, str(SCRIPTS / 'export_static.py')]),
    ('serve', [PY, str(SCRIPTS / 'test_serve.py')]),
]


def verify_measurement() -> list[str]:
    """Assert the measurement file has the fields the dashboard renders.

    Checked here rather than in the dashboard because a missing field silently renders
    "not measured", which looks fine and is useless in a demo (AGENTS.md 6).
    """
    import json

    problems: list[str] = []
    if not MEASUREMENT.exists():
        return ['data/measurement.json missing']

    m = json.loads(MEASUREMENT.read_text(encoding='utf-8'))

    for key in ('meta', 'response_surface', 'window_finding', 'attribution',
                'causality', 'drive_sweep', 'reproducibility', 'verdict', 'conclusion'):
        if key not in m:
            problems.append(f'missing section: {key}')
    if problems:
        return problems

    if not m['response_surface']:
        problems.append('response_surface is empty')
    if not m['drive_sweep'].get('rows'):
        problems.append('drive_sweep has no rows')
    if m['causality'].get('stimulus_reaches_network') is not True:
        problems.append('reachability guard did not pass — measurements are not valid')
    for trial in m['reproducibility'].get('trials', []):
        if trial.get('firstSpikeMs') is None:
            problems.append(f'seed {trial["seed"]} has no measured first spike')
            break
    if not m.get('conclusion'):
        problems.append('no conclusion recorded')
    return problems


def run_bun(script: str) -> tuple[bool, str]:
    dashboard = REPO_ROOT / 'dashboard'
    if not (dashboard / 'package.json').exists():
        return True, f'skipped (no dashboard/package.json)'
    try:
        proc = subprocess.run(
            ['bun', 'run', script],
            cwd=dashboard, capture_output=True, text=True, timeout=600,
        )
    except FileNotFoundError:
        return True, f'skipped (bun not on PATH)'
    except subprocess.TimeoutExpired:
        return False, f'bun {script} timed out'
    if proc.returncode != 0:
        return False, (proc.stderr or proc.stdout)[-800:]
    return True, 'ok'


def main() -> None:
    results: list[tuple[str, bool, str]] = []

    for name, cmd in CHECKS:
        assert cmd is not None
        print(f'--- {name} ---', flush=True)
        proc = subprocess.run(cmd, cwd=SCRIPTS, capture_output=True, text=True)
        if proc.returncode == 0:
            first = (proc.stdout.strip().splitlines() or [''])[0]
            print(f'    PASS  {first}')
            results.append((name, True, 'ok'))
        else:
            tail = (proc.stderr or proc.stdout).strip().splitlines()[-3:]
            print(f'    FAIL  {" | ".join(tail)}')
            results.append((name, False, 'non-zero exit'))

    print('--- measurement schema ---', flush=True)
    problems = verify_measurement()
    if problems:
        print(f'    FAIL  {"; ".join(problems)}')
        results.append(('measurement schema', False, '; '.join(problems)))
    else:
        print('    PASS  all required sections present, guard passed')
        results.append(('measurement schema', True, 'ok'))

    print('--- dashboard build ---', flush=True)
    ok, detail = run_bun('build')
    print(f'    {"PASS" if ok else "FAIL"}  {detail}')
    results.append(('dashboard build', ok, detail))

    print('--- dashboard lint ---', flush=True)
    ok, detail = run_bun('lint')
    print(f'    {"PASS" if ok else "FAIL"}  {detail}')
    results.append(('dashboard lint', ok, detail))

    print()
    failed = [r for r in results if not r[1]]
    print('=' * 62)
    for name, ok, _ in results:
        print(f'  {"PASS" if ok else "FAIL"}  {name}')
    print('=' * 62)
    if failed:
        print(f'{len(failed)} of {len(results)} checks failed')
        sys.exit(1)
    print(f'all {len(results)} checks passed')


if __name__ == '__main__':
    main()