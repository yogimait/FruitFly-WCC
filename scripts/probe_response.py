"""Probe the LPLC2 -> DNp01 response surface. Measurement only, no assertions.

Purpose: find the drive regime in which DNp01 is NOT pinned at its refractory ceiling.
The source project reports DNp01 saturated at 239/240 across all pool-wide drive rates
10-50 Hz, which is the blocker this project exists to address. Before asserting anything
about saturation, measure where the response actually moves.
"""

from __future__ import annotations

import time

import numpy as np

from neural_core import (
    STEP_MS,
    first_spike_ms,
    is_saturated,
    load_subset,
    simulate_spike_train,
    SpikeTrain,
)


def probe_drive_sparsity(
    weight,
    lplc2: np.ndarray,
    dnp01: np.ndarray,
    steps_total: int,
) -> None:
    """Sweep what fraction of LPLC2 neurons are driven, and how long for."""
    print('=== drive sparsity sweep (0.3 s window) ===')
    print(f'{"frac":>6} {"neurons":>8} {"steps_on":>9} {"LPLC2 Hz":>9} {"DNp01":>8} {"sat?":>5} {"1st ms":>8}')

    for fraction in (1.0, 0.5, 0.25, 0.1, 0.05, 0.02, 0.01, 0.005):
        n_driven = max(1, int(round(lplc2.size * fraction)))
        driven = lplc2[:n_driven]
        # Drive every neuron in the pool for the whole window: uniform, dense in time.
        drive = SpikeTrain(np.arange(steps_total), driven)

        t0 = time.time()
        counts, times = simulate_spike_train(
            weight, drive, 0.3, np.random.default_rng(0), record_positions=dnp01
        )
        elapsed = time.time() - t0

        gf = counts[dnp01]
        first = min(
            (first_spike_ms(t) for t in times if t.size),
            default=None,
        )
        sat = 'YES' if is_saturated(gf, 0.3) else '-'
        print(
            f'{fraction:>6.3f} {n_driven:>8} {steps_total:>9} '
            f'{(counts[lplc2].sum() / lplc2.size) / 0.3:>9.1f} '
            f'{int(gf.sum()):>8} {sat:>5} '
            f'{"-" if first is None else f"{first:>8.2f}"}'
            f'   [{elapsed:.1f}s]'
        )


def probe_timing(
    weight,
    lplc2: np.ndarray,
    dnp01: np.ndarray,
) -> None:
    """Where does the first DNp01 spike land as a function of drive onset step?"""
    print()
    print('=== drive onset sweep (single step of drive, 2 LPLC2 neurons) ===')
    print(f'{"onset step":>11} {"onset ms":>9} {"1st ms":>8} {"DNp01 spikes":>13} {"sat?":>5}')

    few = lplc2[:2]
    for onset in (0, 2, 5, 10, 20, 40, 80):
        drive = SpikeTrain(np.array([onset]), few)
        counts, times = simulate_spike_train(
            weight, drive, 0.3, np.random.default_rng(0), record_positions=dnp01
        )
        gf = counts[dnp01]
        recorded = [t for t in times if t.size]
        first = first_spike_ms(recorded[0]) if recorded else None
        sat = 'YES' if is_saturated(gf, 0.3) else '-'
        print(
            f'{onset:>11} {onset * STEP_MS:>9.2f} '
            f'{"-" if first is None else f"{first:>8.2f}"} '
            f'{int(gf.sum()):>13} {sat:>5}'
        )


def main() -> None:
    weight, body_ids, meta = load_subset()
    lplc2 = np.flatnonzero(meta['type'].to_numpy() == 'LPLC2')
    dnp01 = np.flatnonzero(meta['type'].to_numpy() == 'DNp01')
    steps_total = round(0.3 / (STEP_MS / 1e3))

    print(f'subset {weight.shape[0]} neurons, {weight.nnz} edges')
    print(f'LPLC2 {lplc2.size}, DNp01 {dnp01.size}, window {steps_total} steps')
    print()

    probe_drive_sparsity(weight, lplc2, dnp01, steps_total)
    probe_timing(weight, lplc2, dnp01)


if __name__ == '__main__':
    main()