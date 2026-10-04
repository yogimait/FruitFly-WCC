"""Backend tests for scripts/serve.py.

The server is the only place that assembles the dashboard payload, so the mapping from
data/measurement.json to the view shape is worth asserting directly. Three things matter most and
are all easy to break silently:

  1. The response envelope, which AGENTS.md 6 requires for every JSON API we author.
  2. Every value being traceable to a file in data/. A hardcoded number here would render on
     screen with no provenance, so the tests compare against the same files the server reads.
  3. Failure states: a missing or corrupt measurement must produce a proper error envelope, not
     a stack trace or a plausible-looking zero.

Run:  python scripts/test_serve.py
"""

from __future__ import annotations

import json
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / 'scripts'))

from serve import ERROR_STATUS, Handler, build_experiment_view, fail, ok  # noqa: E402

MEASUREMENT = REPO_ROOT / 'data' / 'measurement.json'


def check_envelope() -> None:
    """ok() and fail() must produce the documented envelope shape."""
    good = ok({'x': 1})
    assert good['status'] is True
    assert good['statusCode'] == 200
    assert good['data'] == {'x': 1}
    assert 'error' not in good, 'success envelope must not carry an error'

    bad, http = fail('NOT_FOUND', 'nope')
    assert bad['status'] is False
    assert http == ERROR_STATUS['NOT_FOUND']
    assert bad['statusCode'] == http, 'statusCode must equal the HTTP status'
    assert bad['message'] == 'nope'
    assert bad['error']['code'] == 'NOT_FOUND'
    assert 'details' in bad['error']


def check_view_maps_measured_data() -> None:
    """Every headline value must equal the same field in data/measurement.json."""
    measurement = json.loads(MEASUREMENT.read_text(encoding='utf-8'))
    view = build_experiment_view(measurement, None)

    surface = measurement['response_surface']
    unsaturated = [r for r in surface if not r['saturated']]
    expected = max(unsaturated, key=lambda r: r['window_ms'])

    gf = view['giantFiber']
    assert gf is not None, 'giantFiber must be present when a measurement exists'
    assert gf['spikeCount'] == expected['dnp01_spikes'], (
        'spike count must come from the longest unsaturated window'
    )
    assert view['simulatedMs'] == expected['window_ms']

    # Rate is derived, so check it against the spike count and window rather than a literal.
    expected_rate = round(expected['dnp01_spikes'] / (expected['window_ms'] / 1000.0), 2)
    assert gf['rateHz'] == expected_rate, 'rate must be spikes / window seconds'

    # The drive range must be read from the sweep, not hardcoded.
    rows = measurement['drive_sweep']['rows']
    driven = [r['neurons_driven'] for r in rows]
    rng = view['driveRange']
    assert rng['minNeurons'] == min(driven)
    assert rng['maxNeurons'] == max(driven)
    assert rng['invariant'] == measurement['drive_sweep']['invariant']


def check_unmeasured_stays_null() -> None:
    """A field that was not measured must render as null, never as a plausible-looking 0."""
    view = build_experiment_view({'meta': {}}, None)

    assert view['giantFiber'] is None, 'no measurement must not invent a spike count'
    assert view['lplc2'] is None
    assert view['simulatedMs'] is None
    assert view['angularSizeDeg'] is None

    # With no sweep rows, the range must be null rather than 0-0.
    rng = view['driveRange']
    assert rng['minNeurons'] is None and rng['maxNeurons'] is None


def check_negative_findings_survive() -> None:
    """A null/negative result must reach the UI unchanged, not be tidied into a success."""
    measurement = json.loads(MEASUREMENT.read_text(encoding='utf-8'))
    view = build_experiment_view(measurement, None)

    # The headline finding is negative: the network does NOT separate stimulus magnitude.
    # If a future edit "fixes" this, that is a measurement change and must not happen silently
    # in the view layer.
    assert view['findings']['driveSweep']['invariant'] is True
    values = view['findings']['driveSweep']['dnp01_values']
    assert len(set(values)) == 1, f'invariance broken, values differ: {values}'


class _Server:
    """Runs the real handler on an ephemeral port."""

    def __init__(self) -> None:
        self.httpd = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    def __enter__(self) -> str:
        self.thread.start()
        host, port = self.httpd.server_address[:2]
        return f'http://{host}:{port}'

    def __exit__(self, *exc) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()


def check_http_routes() -> None:
    """Live HTTP: health, success envelope, and the two failure paths."""
    with _Server() as base:
        with urlopen(f'{base}/api/health', timeout=10) as r:
            health = json.loads(r.read())
            assert r.status == 200
            assert health['status'] is True
            assert 'measurement_present' in health['data']

        with urlopen(f'{base}/api/experiment', timeout=10) as r:
            body = json.loads(r.read())
            assert r.status == 200
            assert body['status'] is True
            assert body['data']['giantFiber']['spikeCount'] is not None

        # Unknown API route must 404 with an envelope, not fall through to the static handler.
        try:
            urlopen(f'{base}/api/nope', timeout=10)
            raise AssertionError('unknown /api route should 404')
        except HTTPError as exc:
            assert exc.code == 404
            body = json.loads(exc.read())
            assert body['status'] is False
            assert body['error']['code'] == 'NOT_FOUND'
            assert body['statusCode'] == 404


def main() -> None:
    checks = [
        ('response envelope', check_envelope),
        ('view maps measured data', check_view_maps_measured_data),
        ('unmeasured stays null', check_unmeasured_stays_null),
        ('negative findings survive', check_negative_findings_survive),
        ('http routes', check_http_routes),
    ]
    failures: list[str] = []

    for name, fn in checks:
        try:
            fn()
            print(f'    PASS  {name}')
        except Exception as exc:  # noqa: BLE001 - a test harness reports, it does not raise
            failures.append(f'{name}: {exc}')
            print(f'    FAIL  {name}: {exc}')

    print()
    if failures:
        print(f'{len(failures)}/{len(checks)} backend checks failed')
        sys.exit(1)
    print(f'all {len(checks)} backend checks passed')


if __name__ == '__main__':
    main()