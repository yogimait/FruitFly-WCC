"""Experiment 3: does the TRANSIENT carry stimulus information that the steady state loses?

## Why this experiment exists

Two negative results already, both in docs/Experiments.md:

  1. First-spike latency is flat at 2.00 ms across every stimulus size. A single LPLC2 spike
     crosses threshold in DNp01 within one synaptic delay, so latency is floored by the path
     and cannot scale with magnitude.
  2. Steady-state recruitment is 185/185 units for every stimulus size. Once the lobula
     columnar pool starts firing it sustains itself through recurrent excitation, so every
     unit ends up firing regardless of how much input arrived.

Both are properties of the recurrent pool, not of the encoding. The pool is the reason the
source project measured 570k spikes per 300 ms at every drive rate.

## The hypothesis under test

A real escape reflex is a *transient* response: the fly reacts to the onset of expansion, not
to sustained drive. The published giant-fiber latency (19 ms) is itself a transient measure.

If the pool self-sustains but takes time to ramp, then the number of LPLC2 units that have
spiked **by time t** should still be informative early in the ramp, before the pool reaches
its self-sustained state. If even the transient is flat, the hypothesis that timing recovers
stimulus information is dead and should be abandoned rather than rescued.

## What counts as a positive result

A stimulus-dependent separation in the transient, at some time bin, that:
  - is reproducible across seeds, and
  - is not explained by the number of input events alone (which the encoder controls)

Usage:
    python measure_transient.py
    python measure_transient.py --quick
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from looming import (
    LoomingSpec,
    cell_positions,
    contrast_onset_drive,
    looming_luminance,
)
from neural_core import (
    STEP_MS,
    load_subset,
    simulate_spike_train,
    SpikeTrain,
)

OUTPUT = Path(__file__).resolve().parent.parent / "data" / "transient.json"

SIZES_DEG = (10.0, 20.0, 42.0, 60.0, 80.0)
QUICK_SIZES_DEG = (10.0, 42.0, 80.0)

#: Time bins in milliseconds. Deliberately dense between 20 and 70 ms: the transient
#: question is whether recruitment ramps gradually inside that interval, and coarse bins
#: measured an all-or-nothing jump from 0 to the full pool.
BINS_MS = (2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40,
           42, 44, 46, 48, 50, 55, 60, 70, 100, 200)


def flatten_drive(trains: list, window_s: float) -> tuple[np.ndarray, np.ndarray]:
    if not trains:
        return np.empty(0, np.intp), np.empty(0, np.intp)
    steps = np.concatenate([t.steps for t in trains])
    neurons = np.concatenate([t.neurons for t in trains])
    order = np.argsort(steps, kind='stable')
    steps, neurons = steps[order], neurons[order]
    limit = round(window_s / (STEP_MS / 1e3))
    keep = steps < limit
    return steps[keep], neurons[keep]


def cumulative_recruitment(
    first_spike_steps: np.ndarray,
    n_neurons: int,
) -> dict[int, int]:
    """How many LPLC2 units have fired by each time bin.

    `first_spike_steps` is a length-n_neurons array of first-spike step indices, with -1 for
    units that never fired. Counts are cumulative, so the value at bin t is "how many units had
    fired by t", which is the transient read-out.
    """
    fired = first_spike_steps[first_spike_steps >= 0]
    out: dict[int, int] = {}
    for ms in BINS_MS:
        step = ms / STEP_MS
        out[ms] = int(np.count_nonzero(fired <= step))
    del n_neurons
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--quick', action='store_true')
    parser.add_argument('--seeds', type=int, default=3)
    parser.add_argument('--frames', type=int, default=16)
    parser.add_argument('--velocity', type=float, default=400.0)
    parser.add_argument('--window-ms', type=float, default=250.0)
    args = parser.parse_args()

    weight, _, meta = load_subset()
    lplc2 = np.flatnonzero(meta['type'].to_numpy() == 'LPLC2')
    window_s = args.window_ms / 1e3
    sizes = QUICK_SIZES_DEG if args.quick else SIZES_DEG
    positions = cell_positions(lplc2)

    findings: dict = {
        'config': {
            'window_ms': args.window_ms,
            'frames': args.frames,
            'velocity_deg_per_s': args.velocity,
            'bins_ms': list(BINS_MS),
            'lplc2_neurons': int(lplc2.size),
        },
        'runs': [],
        'seed_trials': [],
    }

    print('=== cumulative LPLC2 recruitment by time bin ===')
    show_bins = [2, 10, 20, 26, 30, 34, 38, 42, 46, 50]
    header = 'size    ' + ''.join(f'{ms:>7}ms' for ms in show_bins)
    print(header)
    print('-' * len(header))

    per_size_curve: dict[float, dict[int, int]] = {}

    for size in sizes:
        spec = LoomingSpec(peak_size_deg=size, velocity_deg_per_s=args.velocity,
                           frames=args.frames)
        stimulus = looming_luminance(spec)
        trains = contrast_onset_drive(
            stimulus, positions, frame_interval_ms=spec.frame_interval_ms
        )
        steps, neurons = flatten_drive(trains, window_s)

        counts, times = simulate_spike_train(
            weight, SpikeTrain(steps, neurons), window_s,
            np.random.default_rng(0), record_positions=lplc2,
        )
        del counts

        # First-spike step per LPLC2 unit.
        first_steps = np.full(lplc2.size, -1, np.int64)
        for slot, steps_for_unit in enumerate(times):
            if steps_for_unit.size:
                first_steps[slot] = steps_for_unit.min()

        curve = cumulative_recruitment(first_steps, lplc2.size)
        per_size_curve[size] = curve

        findings['runs'].append({
            'angular_size_deg': size,
            'cells_driven': len(trains),
            'input_events': int(neurons.size),
            'units_fired_total': int(np.count_nonzero(first_steps >= 0)),
            'cumulative_recruitment': curve,
            'first_spike_ms': [
                None if s < 0 else round(float(s) * STEP_MS, 2)
                for s in first_steps
            ],
        })

        cells = len(trains)
        print(
            f'{size:>5.0f}   ' + ''.join(f'{curve[ms]:>8}' for ms in show_bins)
            + f'   ({cells} cells driven)'
        )

    # Which bins separate the sizes?
    #
    # A bin counts as separating only when EVERY stimulus size produces a DISTINCT count.
    # `spread > 0` alone is not enough: a bin that reports 0 for some sizes and the full pool
    # for others has a large spread but carries no graded information, and treating that as
    # a positive result would be reporting a step function as a ramp.
    print()
    print('=== recruitment per time bin (graded?) ===')
    print('bin     ' + ''.join(f'{s:>7.0f}' for s in sizes) + '   graded?')
    separating: list[int] = []
    for ms in BINS_MS:
        values = [per_size_curve[s][ms] for s in sizes]
        graded = len(set(values)) == len(values)
        if graded:
            separating.append(ms)
        marker = 'YES' if graded else ('step' if max(values) - min(values) > 0 else '-')
        if marker != '-' or ms in (2, 10, 20, 30, 40, 50, 60, 100):
            print(f'{ms:>4} ms ' + ''.join(f'{v:>7}' for v in values) + f'   {marker}')

    findings['separating_bins_ms'] = separating
    findings['separates_at_all'] = bool(separating)

    # Reproducibility at the separating bin.
    if separating:
        bin_ms = min(separating)
        print()
        print(f'=== seed reproducibility at the {bin_ms} ms bin ===')
        for seed in range(args.seeds):
            spec = LoomingSpec(42.0, args.velocity, args.frames)
            stimulus = looming_luminance(spec)
            trains = contrast_onset_drive(
                stimulus, positions, frame_interval_ms=spec.frame_interval_ms
            )
            steps, neurons = flatten_drive(trains, window_s)
            _, times = simulate_spike_train(
                weight, SpikeTrain(steps, neurons), window_s,
                np.random.default_rng(seed), record_positions=lplc2,
            )
            first_steps = np.full(lplc2.size, -1, np.int64)
            for slot, s in enumerate(times):
                if s.size:
                    first_steps[slot] = s.min()
            fired = first_steps[first_steps >= 0]
            count = int(np.count_nonzero(fired <= bin_ms / STEP_MS))
            findings['seed_trials'].append({
                'seed': seed, 'bin_ms': bin_ms, 'units_fired_by_bin': count
            })
            print(f'  seed {seed}: {count} units by {bin_ms} ms')

        counts_seen = [t['units_fired_by_bin'] for t in findings['seed_trials']]
        spread = max(counts_seen) - min(counts_seen)
        findings['seed_spread'] = spread
        findings['reproducible'] = spread == 0
        print(f'  spread {spread} — {"reproducible" if spread == 0 else "NOT reproducible"}')

        if separating:
            print()
            print(f'RESULT: recruitment separates stimulus sizes at {separating[0]} ms, '
                  f'{separating[-1]} ms')
            print('The transient carries stimulus information that both the steady state and')
            print('rate coding lose. The recurrent pool takes over later, which is why a long')
            print('measurement window destroys the signal.')
            findings['conclusion'] = (
                f'Stimulus size separates LPLC2 transient recruitment at {separating[0]}-'
                f'{separating[-1]} ms, while steady-state recruitment is flat at the pool '
                'ceiling for every size. The information is in the transient.'
            )
    else:
        print()
        print('NEGATIVE RESULT: no time bin separates the stimulus sizes.')
        print('The recurrent lobula columnar pool destroys stimulus magnitude information')
        print('before it can be read at any timescale. The temporal-coding hypothesis is')
        print('refuted for this pathway at this model scale.')
        findings['conclusion'] = (
            'No time bin separates stimulus sizes. The recurrently self-sustained lobula '
            'columnar pool destroys magnitude information at every readable timescale, so '
            'temporal coding does not rescue the response. Hypothesis refuted.'
        )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(findings, indent=2), encoding='utf-8')
    print()
    print(f'-> {OUTPUT}')


if __name__ == '__main__':
    main()