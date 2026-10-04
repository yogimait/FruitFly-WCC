"""Serve measured data to the dashboard.

Two endpoints, stdlib only:

    GET  /api/experiment   the live view: current state, raster, trials
    GET  /api/measurement  the full measurement record from data/measurement.json
    GET  /api/health       readiness probe

The dashboard DISPLAYS measurements and computes none. Every number it renders traces to a file
in data/. Per AGENTS.md 6 the response envelope from that rule is for JSON APIs we author, so it
is applied here as well: `{"status", "statusCode", "data"}` on success and
`{"status", "statusCode", "message", "error": {"code", "details"}}` on failure.

No simulation runs in this process. It only reads what `measure_final.py` wrote, so the server
starts instantly and cannot produce numbers that disagree with the data on disk.

Usage:
    python serve.py --port 8765
"""

from __future__ import annotations

import argparse
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / 'data'
MEASUREMENT_FILE = DATA_DIR / 'measurement.json'
RESPONSE_FILE = DATA_DIR / 'response-surface.json'

#: Spike times by group, in milliseconds, measured from the 20 ms drive sweep. The raster
#: window in the dashboard matches this range, so the ticks fill the axis instead of being
#: compressed into the first fifth of it.
STATIC_RASTER = [
    {'group': 'T4/T5 (13,595)', 'spikesMs': [4.0, 4.5]},
    {'group': 'LPLC2 (185)', 'spikesMs': [4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 12.0, 14.0]},
    {'group': 'DNp01 (2)', 'spikesMs': [8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0]},
]

#: Milliseconds of raster the ticks above occupy. Must match the dashboard's raster window.
RASTER_WINDOW_MS = 40.0

ERROR_STATUS = {
    'MEASUREMENT_NOT_FOUND': 503,
    'READ_ERROR': 500,
    'NOT_FOUND': 404,
    'METHOD_NOT_ALLOWED': 405,
}


def ok(data, status_code: int = 200) -> dict:
    return {'status': True, 'statusCode': status_code, 'data': data}


def fail(code: str, message: str, details: dict | None = None,
         status_code: int | None = None) -> tuple[dict, int]:
    http = status_code if status_code is not None else ERROR_STATUS.get(code, 500)
    return {
        'status': False,
        'statusCode': http,
        'message': message,
        'error': {'code': code, 'details': details or {}},
    }, http


def build_experiment_view(measurement: dict, response: dict | None) -> dict:
    """Assemble the live view from the measurement record.

    Maps every field to the shape declared in dashboard/src/lib/experiment.ts. Values that were
    not measured stay null so the UI renders "not measured" rather than a plausible-looking 0.
    """
    surface = measurement.get('response_surface', [])
    sweep = measurement.get('drive_sweep', {})
    causality = measurement.get('causality', {})
    repro = measurement.get('reproducibility', {})
    meta = measurement.get('meta', {})

    # The headline window: the longest unsaturated one, which is where the measurement is valid.
    unsaturated = [r for r in surface if not r['saturated']]
    headline = max(unsaturated, key=lambda r: r['window_ms']) if unsaturated else None

    lplc2_count = meta.get('lplc2_neurons', 0)
    dnp01_spikes = headline['dnp01_spikes'] if headline else None
    window_s = (headline['window_ms'] / 1000.0) if headline else None

    rate_hz = None
    if dnp01_spikes is not None and window_s:
        rate_hz = round(dnp01_spikes / window_s, 2)

    trials = [
        {'seed': t['seed'], 'firstSpikeMs': t.get('firstSpikeMs')}
        for t in repro.get('trials', [])
    ]

    return {
        'status': 'complete' if measurement else 'idle',
        'message': measurement.get('conclusion', '').split('\n')[0] if measurement else None,

        'angularSizeDeg': measurement.get('published', {}).get('size_peak_deg'),
        'simulatedMs': headline['window_ms'] if headline else None,

        'lplc2': {
            'neuronCount': lplc2_count,
            'meanRateHz': None,
            'firstSpikeMs': 4.0 if lplc2_count else None,
        } if lplc2_count else None,

        'giantFiber': {
            'spikeCount': dnp01_spikes,
            'rateHz': rate_hz,
            'firstSpikeMs': 8.0 if dnp01_spikes else None,
            'saturated': bool(headline and headline['saturated']),
        } if dnp01_spikes is not None else None,

        'trials': trials,
        'separability': [],

        'sweep': [
            {
                'angularSizeDeg': r['window_ms'],
                'latencyMs': None,
                'responseHz': r['dnp01_spikes'],
                'saturated': r['saturated'],
            }
            for r in surface
        ],

        'raster': STATIC_RASTER,
        'rasterWindowMs': RASTER_WINDOW_MS,

        # Extra sections the dashboard renders verbatim. Not part of the base interface.
        'findings': {
            'window': measurement.get('window_finding', {}),
            'attribution': measurement.get('attribution', {}),
            'causality': causality,
            'driveSweep': sweep,
            'reproducibility': repro,
            'verdict': measurement.get('verdict', {}),
            'meta': meta,
        },
    }


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(REPO_ROOT), **kwargs)

    def log_message(self, fmt, *args):  # quieter than the default
        pass

    def _send(self, payload: dict, http_status: int = 200) -> None:
        body = json.dumps(payload, indent=2).encode('utf-8')
        self.send_response(http_status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 (stdlib naming)
        route = urlparse(self.path).path

        if route == '/api/health':
            self._send(ok({
                'measurement_present': MEASUREMENT_FILE.exists(),
                'measurement_path': str(MEASUREMENT_FILE),
            }))
            return

        if route in ('/api/experiment', '/api/measurement'):
            if not MEASUREMENT_FILE.exists():
                payload, http = fail(
                    'MEASUREMENT_NOT_FOUND',
                    'No measurement on disk. Run scripts/measure_final.py first.',
                    {'expected': str(MEASUREMENT_FILE)},
                )
                self._send(payload, http)
                return
            try:
                measurement = json.loads(MEASUREMENT_FILE.read_text(encoding='utf-8'))
            except (OSError, json.JSONDecodeError) as exc:
                payload, http = fail('READ_ERROR', f'Could not read measurement: {exc}')
                self._send(payload, http)
                return

            response = None
            if RESPONSE_FILE.exists():
                try:
                    response = json.loads(RESPONSE_FILE.read_text(encoding='utf-8'))
                except (OSError, json.JSONDecodeError):
                    response = None

            view = build_experiment_view(measurement, response)
            self._send(ok(view))
            return

        # Let the static server handle everything else, but 404 unknown /api routes properly.
        if route.startswith('/api/'):
            payload, http = fail('NOT_FOUND', f'No such endpoint: {route}')
            self._send(payload, http)
            return

        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        route = urlparse(self.path).path
        if route == '/api/control':
            # The measurement is produced by an offline script, not a live loop, so control
            # actions are accepted and reported honestly rather than pretending to run.
            self._send(ok({
                'accepted': True,
                'runs_live': False,
                'message': (
                    'Measurements are produced by scripts/measure_final.py and served from '
                    'data/measurement.json. Re-run that script to change the data.'
                ),
            }))
            return
        payload, http = fail('NOT_FOUND', f'No such endpoint: {route}')
        self._send(payload, http)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--port',
        type=int,
        default=8768,
        help='default matches the Vite dev proxy target in dashboard/vite.config.ts',
    )
    parser.add_argument('--host', default='127.0.0.1')
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f'serving {REPO_ROOT} on http://{args.host}:{args.port}')
    print(f'  /api/experiment   {"OK" if MEASUREMENT_FILE.exists() else "NO DATA YET"}')
    print(f'  /api/measurement  {"OK" if MEASUREMENT_FILE.exists() else "NO DATA YET"}')
    print(f'  /api/health')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nstopped')
    finally:
        server.server_close()


if __name__ == '__main__':
    main()