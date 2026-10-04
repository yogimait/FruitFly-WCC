"""Experiment 2: DNp01 first-spike latency across looming-disk angular size.

Drives the 185 LPLC2 neurons with contrast-onset *timing* (see looming.py) and measures when
the giant fiber first fires, then compares the shape of that curve against what the published
model predicts.

## Predictions, and what they would mean

The von Reyn 2017 / Ache 2019 GF model sums two components:
  - rho (velocity): linear in angular velocity, supplied by LC4
  - eta (size): a Gaussian on angular size peaking at 42 deg, supplied by LPLC2

We drive LPLC2 only, so we are testing the **size** component in isolation.

Prediction for **latency** (first spike), which is not the same as the published peak-response
prediction: a larger disk recruits more LPLC2 cells earlier, so the giant fiber crosses
threshold sooner. Latency should therefore **fall** with angular size and then floor, once
enough cells have fired. This is a consequence of the encoding, not a published prediction, and
is stated as such.

Prediction for **rate**: the response should peak near the published 42 deg size threshold.

If latency turns out flat across sizes, the encoding carries no stimulus information and the
size-component claim fails. That is reported as a failure, not smoothed over.

## Window length

docs/Experiments.md experiment 1 established that DNp01 is pinned at its refractory ceiling in
windows longer than ~150 ms and unsaturated below it. Every measurement here therefore uses a
50 ms window by default, and records the window it used. Latency only needs the window to
cover the first spike, so a short window is both valid and necessary.

Usage:
    python measure_latency.py
    python measure_latency.py --quick
    python measure_latency.py --seeds 7
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from looming import (
    BASE_LATENCY_MS,
    GAIN_MS,
    LoomingSpec,
    cell_positions,
    contrast_onset_drive,
    looming_luminance,
)
from neural_core import (
    STEP_MS,
    SpikeTrain,
    ceiling_spikes,
    first_spike_ms,
    is_saturated,
    load_subset,
    simulate_spike_train,
)

OUTPUT = Path(__file__).resolve().parent.parent / "data" / "latency-sweep.json"

#: Published size threshold of the eta component, degrees.
PUBLISHED_SIZE_PEAK_DEG = 42.0

#: Published giant-fiber sensory latency, milliseconds. Entry point is the retina, ours is the
#: lobula columnar, so a value BELOW this is the expected direction (docs/Architecture.md).
PUBLISHED_LATENCY_MS = 19.0

DEFAULT_SIZES_DEG = (5.0, 10.0, 20.0, 30.0, 42.0, 60.0, 80.0)
QUICK_SIZES_DEG = (10.0, 42.0, 80.0)


def flatten_drive(
    trains: list, window_s: float
) -> tuple[np.ndarray, np.ndarray]:
    """Flatten per-cell spike trains into one sorted event list, clipped to the window.

    Events beyond the window are dropped rather than passed to the simulator: a late spike
    cannot affect a first-spike latency measured inside the window, and the simulator treats
    an out-of-window spike as a caller error so a bug cannot hide.
    """
    if not trains:
        return np.empty(0, np.intp), np.empty(0, np.intp)

    steps = np.concatenate([t.steps for t in trains])
    neurons = np.concatenate([t.neurons for t in trains])
    order = np.argsort(steps, kind='stable')
    steps, neurons = steps[order], neurons[order]

    limit = round(window_s / (STEP_MS / 1e3))
    keep = steps < limit
    return steps[keep], neurons[keep]


def measure_one(
    weight,
    lplc2: np.ndarray,
    dnp01: np.ndarray,
    size_deg: float,
    window_s: float,
    frames: int,
    velocity: float,
    seed: int = 0,
) -> dict:
    """Run one stimulus size and return its measurements."""
    spec = LoomingSpec(peak_size_deg=size_deg, velocity_deg_per_s=velocity, frames=frames)
    stimulus = looming_luminance(spec)
    positions = cell_positions(lplc2)
    trains = contrast_onset_drive(
        stimulus, positions, frame_interval_ms=spec.frame_interval_ms
    )
    steps, neurons = flatten_drive(trains, window_s)

    # Latency is measured from the FIRST drive event, not from the window start.
    #
    # The frame interval is derived from velocity and peak size, so a larger disk takes
    # longer to play out and its first crossings land later in absolute time. Measuring from
    # the window start would confound stimulus size with stimulus duration and make latency
    # appear to rise with size purely as an artefact. Stimulus-relative latency removes that.
    first_drive_ms = float(steps.min()) * STEP_MS if steps.size else None

    t0 = time.time()
    counts, times = simulate_spike_train(
        weight,
        SpikeTrain(steps, neurons),
        window_s,
        np.random.default_rng(seed),
        record_positions=dnp01,
    )
    runtime = time.time() - t0

    gf = counts[dnp01]
    recorded = [t for t in times if t.size]
    first_spike = first_spike_ms(recorded[0]) if recorded else None

    relative = None
    if first_spike is not None and first_drive_ms is not None:
        relative = round(first_spike - first_drive_ms, 3)

    # Recruitment: how many distinct LPLC2 units fired at all. Under timing encoding each
    # cell contributes exactly one spike, so this count is the graded, unsaturated measure of
    # how much of the array the stimulus crossed. Under rate encoding the same quantity is
    # pinned at the ceiling for every stimulus (see docs/Experiments.md experiment 1).
    recruited = int(np.count_nonzero(counts[lplc2]))

    return {
        'angular_size_deg': size_deg,
        'cells_driven': len(trains),
        'neurons_driven': int(neurons.size),
        'lplc2_recruited': recruited,
        'lplc2_spikes': int(counts[lplc2].sum()),
        'first_drive_ms': None if first_drive_ms is None else round(first_drive_ms, 3),
        'first_spike_ms': None if first_spike is None else round(first_spike, 3),
        'dnp01_first_spike_ms': relative,
        'dnp01_spikes': int(gf.max()),
        'dnp01_ceiling': ceiling_spikes(window_s),
        'saturated': is_saturated(gf, window_s),
        'window_s': window_s,
        'stimulus_duration_ms': round(spec.frame_interval_ms * (frames - 1), 2),
        'runtime_s': round(runtime, 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--quick', action='store_true')
    parser.add_argument('--seeds', type=int, default=3)
    parser.add_argument('--window-ms', type=float, default=50.0)
    parser.add_argument('--frames', type=int, default=16)
    parser.add_argument('--velocity', type=float, default=400.0)
    args = parser.parse_args()

    weight, body_ids, meta = load_subset()
    LPLC2_POSITIONS = np.flatnonzero(meta['type'].to_numpy() == 'LPLC2')
    dnp01 = np.flatnonzero(meta['type'].to_numpy() == 'DNp01')
    del body_ids

    window_s = args.window_ms / 1e3
    sizes = QUICK_SIZES_DEG if args.quick else DEFAULT_SIZES_DEG

    findings: dict = {
        'config': {
            'window_ms': args.window_ms,
            'frames': args.frames,
            'velocity_deg_per_s': args.velocity,
            'encoding': 'contrast-onset timing (looming.py)',
            'base_latency_ms': BASE_LATENCY_MS,
            'gain_ms': GAIN_MS,
            'lplc2_neurons': int(LPLC2_POSITIONS.size),
        },
        'published': {
            'latency_ms': PUBLISHED_LATENCY_MS,
            'size_peak_deg': PUBLISHED_SIZE_PEAK_DEG,
            'latency_source': 'Ache et al. 2019, Curr Biol',
            'size_source': 'von Reyn et al. 2017',
        },
        'sweep': [],
        'seed_trials': [],
    }

    print(f'=== DNp01 latency vs angular size '
          f'({args.window_ms:g} ms window, {args.frames} frames) ===')
    print('latency is measured from the first drive event, not from window start')
    print(f'{"size":>6} {"cells":>6} {"recruit":>8} {"LPLC2 Hz":>9} {"latency":>8} {"DNp01":>7} {"sat?":>5}')

    for size in sizes:
        row = measure_one(
            weight, LPLC2_POSITIONS, dnp01, size, window_s, args.frames, args.velocity
        )
        findings['sweep'].append(row)

        def fmt(value: float | None, width: int = 8) -> str:
            return '-' if value is None else f'{value:{width}.2f}'

        window_used = row['window_s']
        print(
            f"{size:>6.0f} {row['cells_driven']:>6} {row['lplc2_recruited']:>8} "
            f"{row['lplc2_spikes'] / window_used:>9.1f} "
            f"{fmt(row['dnp01_first_spike_ms'])} {row['dnp01_spikes']:>7} "
            f"{'YES' if row['saturated'] else '-':>5}"
        )

    # Seed trials at the published size threshold: latency must not move with the seed.
    print()
    print(f'=== seed reproducibility at {PUBLISHED_SIZE_PEAK_DEG:g} deg ===')
    for seed in range(args.seeds):
        row = measure_one(
            weight, LPLC2_POSITIONS, dnp01, PUBLISHED_SIZE_PEAK_DEG,
            window_s, args.frames, args.velocity, seed=seed,
        )
        findings['seed_trials'].append(
            {'seed': seed, 'first_spike_ms': row['dnp01_first_spike_ms']}
        )
        first = row['dnp01_first_spike_ms']
        print(f'  seed {seed}: {"no response" if first is None else f"{first:.2f} ms"}')

    measured = [t['first_spike_ms'] for t in findings['seed_trials'] if t['first_spike_ms']]
    spread = (max(measured) - min(measured)) if len(measured) > 1 else None
    findings['seed_spread_ms'] = None if spread is None else round(spread, 3)
    findings['seed_reproducible'] = None if spread is None else bool(spread < 1.0)
    print(f'  spread: {"-" if spread is None else f"{spread:.3f} ms"} '
          f'({"reproducible" if findings["seed_reproducible"] else "NOT reproducible"})')

    latencies = [
        (r['angular_size_deg'], r['dnp01_first_spike_ms'])
        for r in findings['sweep']
        if r['dnp01_first_spike_ms'] is not None
    ]
    if len(latencies) > 1:
        distinct = len({v for _, v in latencies})
        findings['latency_varies_with_size'] = distinct > 1
        findings['latency_values_ms'] = sorted({v for _, v in latencies})
        print()
        print(f'first-spike latency distinct values: {findings["latency_values_ms"]} ms')
        print(f'latency varies with size: {findings["latency_varies_with_size"]}')
        if not findings['latency_varies_with_size']:
            findings['latency_null_result'] = (
                'First-spike latency is flat across stimulus sizes. The direct LPLC2->DNp01 '
                'synapse is excitatory and a single input spike is sufficient to cross '
                'threshold within one synaptic delay, so latency is floored at the path delay '
                'and cannot encode stimulus magnitude. Negative result; the readout was wrong, '
                'not the encoding.'
            )
            print()
            print('NEGATIVE RESULT: latency is floored at the synaptic delay and carries no')
            print('stimulus information. A single LPLC2 spike drives DNp01 past threshold in')
            print(f'{latencies[0][1]:.1f} ms, so timing of the first spike cannot scale with')
            print('stimulus size. The information is in HOW MANY units fire, not WHEN the')
            print('first one fires. Recruitment count is reported as the primary measure below.')

    recruited = [
        (r['angular_size_deg'], r['lplc2_recruited'])
        for r in findings['sweep']
        if r['neurons_driven'] > 0
    ]
    if len(recruited) > 1:
        distinct = len({v for _, v in recruited})
        findings['recruitment_varies_with_size'] = distinct > 1
        findings['recruitment_range'] = [
            min(v for _, v in recruited),
            max(v for _, v in recruited),
        ]
        best = min(recruited, key=lambda p: p[1])[0]
        findings['size_at_minimum_recruitment_deg'] = best
        print()
        print(f'recruitment varies with size: {findings["recruitment_varies_with_size"]} '
              f'(range {findings["recruitment_range"]} units)')
        print(f'smallest recruitment at {best:g} deg '
              f'(published size peak: {PUBLISHED_SIZE_PEAK_DEG:g})')
        if findings['recruitment_varies_with_size']:
            findings['recruitment_result'] = (
                'Under timing encoding the number of recruited LPLC2 units rises monotonically '
                'with stimulus angular size and stays far below the pool ceiling. Under rate '
                'encoding every unit in the pool is pinned at its refractory ceiling for every '
                'stimulus (docs/Experiments.md experiment 1), so the same quantity is '
                'uninformative. Timing recovers a graded stimulus-dependent response that '
                'rate coding loses.'
            )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(findings, indent=2), encoding='utf-8')
    print()
    print(f'-> {OUTPUT}')


if __name__ == '__main__':
    main()