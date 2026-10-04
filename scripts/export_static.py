"""Export the measurement as static files so the dashboard deploys anywhere.

## Why this exists

The simulation runs on this laptop and cannot be hosted by Vercel, Netlify or GitHub Pages.
But the *output* of the simulation is a 44 KB JSON file, and that is all the dashboard reads.

So the deployable artifact is a static site: the built dashboard plus `data/` copied in as
static assets. No server, no Python, no GPU, no network call. It runs from a CDN, a file share,
or `python -m http.server`.

This script performs that copy and writes the endpoint shapes the dashboard already expects, so
no dashboard code changes between local and deployed.

## Outputs

    dashboard/public/api/experiment.json   the live view (envelope shaped)
    dashboard/public/api/measurement.json  the full record
    dashboard/public/data/*.json           every raw dataset, for provenance

## Usage

    python scripts/export_static.py
    cd dashboard && bun run build
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from serve import build_experiment_view

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / 'data'
PUBLIC_DIR = REPO_ROOT / 'dashboard' / 'public'

API_DIR = PUBLIC_DIR / 'api'
PUBLIC_DATA = PUBLIC_DIR / 'data'


def main() -> None:
    measurement_file = DATA_DIR / 'measurement.json'
    if not measurement_file.exists():
        raise SystemExit(
            'data/measurement.json not found — run scripts/measure_final.py first'
        )

    measurement = json.loads(measurement_file.read_text(encoding='utf-8'))
    response_file = DATA_DIR / 'response-surface.json'
    response = None
    if response_file.exists():
        response = json.loads(response_file.read_text(encoding='utf-8'))

    API_DIR.mkdir(parents=True, exist_ok=True)
    PUBLIC_DATA.mkdir(parents=True, exist_ok=True)

    view = build_experiment_view(measurement, response)

    # Same envelope shape the dev server returns, so the dashboard's unwrapping code is
    # identical in both environments.
    (API_DIR / 'experiment.json').write_text(
        json.dumps({'status': True, 'statusCode': 200, 'data': view}, indent=2),
        encoding='utf-8',
    )
    (API_DIR / 'measurement.json').write_text(
        json.dumps({'status': True, 'statusCode': 200, 'data': measurement}, indent=2),
        encoding='utf-8',
    )

    copied = 0
    for path in sorted(DATA_DIR.glob('*.json')):
        shutil.copy2(path, PUBLIC_DATA / path.name)
        copied += 1

    total_kb = sum(
        f.stat().st_size for f in list(API_DIR.glob('*.json')) + list(PUBLIC_DATA.glob('*.json'))
    ) / 1024

    print(f'exported {copied} datasets')
    print(f'  dashboard/public/api/experiment.json')
    print(f'  dashboard/public/api/measurement.json')
    print(f'  dashboard/public/data/*.json  ({copied} files)')
    print(f'  total {total_kb:.1f} KB')
    print()
    print('next:')
    print('  cd dashboard && bun run build')
    print('  serve dist/ with any static host, or:')
    print('  python -m http.server -d dashboard/dist 8080')


if __name__ == '__main__':
    main()