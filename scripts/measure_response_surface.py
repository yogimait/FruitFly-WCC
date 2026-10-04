"""Measure the LPLC2 -> DNp01 response surface and write data/response-surface.json.

This is the experiment that decides whether temporal coding is viable. The source project
reported DNp01 pinned at its refractory ceiling for all pool-wide drive rates 10-50 Hz. The
question here is narrower and falsifiable: *is there any drive configuration in which DNp01
is not pinned?*

Three axes are swept:
  1. Drive sparsity  - how many LPLC2 neurons receive input
  2. Drive onset     - when the first input arrives
  3. Window length   - whether a shorter window escapes the pool's self-sustained firing

Every number written here is measured. Nothing is inferred. Per AGENTS.md 6 the JSON records
the saturation verdict explicitly so the dashboard cannot show a saturated result as valid.

Usage:
    python measure_response_surface.py
    python measure_response_surface.py --quick    # fewer points, for a fast check
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from neural_core import (
    DT,
    REFRACT_STEPS,
    STEP_MS,
    ceiling_spikes,
    first_spike_ms,
    is_saturated,
    load_subset,
    simulate_spike_train,
    SpikeTrain,
)

OUTPUT = Path(__file__).resolve().parent.parent / "data" / "response-surface.json"


def _run(
    weight,
    lplc2: np.ndarray,
    dnp01: np.ndarray,
    steps: np.ndarray,
    window_s: float,
) -> dict:
    drive = SpikeTrain(steps, lplc2)
    t0 = time.time()
    counts, times = simulate_spike_train(
        weight, drive, window_s, np.random.default_rng(0), record_positions=dnp01
    )
    elapsed = time.time() - t0

    gf = counts[dnp01]
    recorded = [t for t in times if t.size]
    first = first_spike_ms(recorded[0]) if recorded else None

    return {
        'n_driven': int(lplc2.size),
        'n_drive_steps': int(steps.size),
        'lplc2_mean_rate_hz': round(float(counts[lplc2].mean() / window_s), 2),
        'dnp01_spikes': int(gf.sum()),
        'dnp01_max_spikes': int(gf.max()),
        'dnp01_ceiling': ceiling_spikes(window_s),
        'dnp01_first_spike_ms': None if first is None else round(first, 3),
        'saturated': is_saturated(gf, window_s),
        'runtime_s': round(elapsed, 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--quick', action='store_true')
    args = parser.parse_args()

    weight, body_ids, meta = load_subset()
    lplc2 = np.flatnonzero(meta['type'].to_numpy() == 'LPLC2')
    dnp01 = np.flatnonzero(meta['type'].to_numpy() == 'DNp01')

    findings: dict = {
        'frozen_constants': {
            'dt_ms': round(STEP_MS, 4),
            'refractory_steps': REFRACT_STEPS,
            'refractory_ms': round(REFRACT_STEPS * STEP_MS, 3),
        },
        'subset': {
            'neurons': int(weight.shape[0]),
            'edges': int(weight.nnz),
            'lplc2_count': int(lplc2.size),
            'dnp01_count': int(dnp01.size),
        },
        'sparsity_sweep': [],
        'onset_sweep': [],
        'window_sweep': [],
    }

    window_s = 0.3
    steps_full = np.arange(round(window_s / DT))

    fractions = (1.0, 0.25, 0.05, 0.01) if args.quick else (
        1.0, 0.5, 0.25, 0.1, 0.05, 0.02, 0.01, 0.005, 0.002
    )
    print('=== drive sparsity (0.3 s window) ===')
    for fraction in fractions:
        n = max(1, int(round(lplc2.size * fraction)))
        record = _run(weight, lplc2[:n], dnp01, steps_full, window_s)
        record['fraction'] = fraction
        findings['sparsity_sweep'].append(record)
        print(
            f"  frac {fraction:>6.3f}  driven {record['n_driven']:>4}  "
            f"DNp01 {record['dnp01_max_spikes']:>4}/{record['dnp01_ceiling']}  "
            f"sat {record['saturated']}  first {record['dnp01_first_spike_ms']}"
        )

    onsets = (0, 10, 40) if args.quick else (0, 2, 5, 10, 20, 40, 80, 160)
    print()
    print('=== drive onset (2 LPLC2 neurons, single step of input) ===')
    for onset in onsets:
        record = _run(weight, lplc2[:2], dnp01, np.array([onset]), window_s)
        record['onset_step'] = onset
        record['onset_ms'] = round(onset * STEP_MS, 3)
        findings['onset_sweep'].append(record)
        print(
            f"  onset {onset:>4} ({record['onset_ms']:>7.2f} ms)  "
            f"DNp01 {record['dnp01_max_spikes']:>4}  "
            f"first {record['dnp01_first_spike_ms']} ms"
        )

    windows = (0.02, 0.1) if args.quick else (0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.3)
    print()
    print('=== window length (2 LPLC2 neurons, continuous drive) ===')
    for w in windows:
        steps = np.arange(round(w / DT))
        record = _run(weight, lplc2[:2], dnp01, steps, w)
        record['window_s'] = w
        record['ceiling_hz'] = round(1.0 / (REFRACT_STEPS * DT), 2)
        findings['window_sweep'].append(record)
        print(
            f"  window {w * 1e3:>6.1f} ms  "
            f"DNp01 {record['dnp01_max_spikes']:>4}/{record['dnp01_ceiling']:>4}  "
            f"sat {record['saturated']}  rate {record['lplc2_mean_rate_hz']} Hz"
        )

    saturated_count = sum(
        1
        for group in ('sparsity_sweep', 'onset_sweep', 'window_sweep')
        for row in findings[group]
        if row['saturated']
    )
    total = sum(len(findings[g]) for g in ('sparsity_sweep', 'onset_sweep', 'window_sweep'))
    findings['summary'] = {
        'measurements': total,
        'saturated': saturated_count,
        'any_unsaturated': saturated_count < total,
        'conclusion': (
            'DNp01 remains pinned at its refractory ceiling across every drive sparsity, '
            'onset and window tested. Rate-based readout cannot resolve the stimulus.'
            if saturated_count == total
            else 'At least one regime escapes the ceiling; inspect the sweep for it.'
        ),
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(findings, indent=2), encoding='utf-8')

    print()
    print(f"measurements {total}, saturated {saturated_count}")
    print(f'conclusion: {findings["summary"]["conclusion"]}')
    print(f'-> {OUTPUT}')


if __name__ == '__main__':
    main()