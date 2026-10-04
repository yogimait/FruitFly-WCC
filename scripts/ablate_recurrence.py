"""Experiment 4: ablate the recurrent lobula columnar loop and re-test.

## The question

Experiments 2 and 3 found no stimulus information at any readout, and identified the cause as
the recurrently self-sustained lobula columnar pool. That is a claim about *where* the
information dies, and it is falsifiable: if the recurrent loop is the cause, removing it should
restore a graded, stimulus-dependent response.

If removing it does NOT restore a graded response, then the self-sustaining pool is a symptom
rather than the cause, and the whole diagnosis is wrong.

## Arms

  0  control        unchanged weights. Expected: flat, per experiments 2 and 3.
  1  feed-forward   all incoming edges to the 185 LPLC2 units removed. LPLC2 responds only to
                    the external drive, so the recurrent loop cannot exist.
  2  no self-loops  only LPLC2 -> LPLC2 edges removed, leaving other lobula columnar input.
  3  matched rate   the same total input delivered as a Poisson RATE over the window, to compare
     vs timing      against arm 1's single timed spike. This is the rate-vs-timing comparison
                    the project claims to make and had not made cleanly, because in the control
                    the pool saturates both encodings identically.

Arm 3 is the one that speaks to the original hypothesis. If timing beats rate once the loop is
gone, the hypothesis was right about timing and wrong about the model being able to show it.

## Honesty

Every arm reports whether the output saturated. A positive result in an ablated arm says nothing
about the intact model and is labelled as such.

Usage:
    python ablate_recurrence.py
    python ablate_recurrence.py --quick
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import scipy.sparse as sp

from looming import (
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

OUTPUT = Path(__file__).resolve().parent.parent / "data" / "ablation.json"

SIZES_DEG = (10.0, 20.0, 42.0, 60.0, 80.0)
QUICK_SIZES_DEG = (10.0, 42.0, 80.0)


def zero_columns(weight: sp.csr_matrix, columns: np.ndarray) -> sp.csr_matrix:
    """Return a copy of `weight` with all incoming edges to `columns` removed.

    Zeroing a column removes everything arriving at that neuron, which is what "no recurrent
    input" means structurally. Done by rebuilding the CSR arrays rather than assigning into
    `.data`, because assigning into `.data` leaves explicit zeros behind and breaks
    `has_canonical_format` assumptions downstream.
    """
    mask = np.zeros(weight.shape[1], dtype=bool)
    mask[columns] = True

    coo = weight.tocoo()
    keep = ~mask[coo.col]
    return sp.coo_matrix(
        (coo.data[keep], (coo.row[keep], coo.col[keep])),
        shape=weight.shape,
    ).tocsr()


def drop_rows(weight: sp.csr_matrix, rows: np.ndarray) -> sp.csr_matrix:
    """Return a copy with all outgoing edges from `rows` removed."""
    mask = np.zeros(weight.shape[0], dtype=bool)
    mask[rows] = True

    coo = weight.tocoo()
    keep = ~mask[coo.row]
    return sp.coo_matrix(
        (coo.data[keep], (coo.row[keep], coo.col[keep])),
        shape=weight.shape,
    ).tocsr()


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


def measure(
    weight,
    lplc2: np.ndarray,
    dnp01: np.ndarray,
    steps: np.ndarray,
    neurons: np.ndarray,
    window_s: float,
    seed: int = 0,
) -> dict:
    """Run one configuration and return the three readouts used throughout this project."""
    counts, times = simulate_spike_train(
        weight, SpikeTrain(steps, neurons), window_s,
        np.random.default_rng(seed), record_positions=dnp01,
    )

    lplc2_times = simulate_spike_train(
        weight, SpikeTrain(steps, neurons), window_s,
        np.random.default_rng(seed), record_positions=lplc2,
    )[1]

    gf = counts[dnp01]
    recorded = [t for t in times if t.size]
    first = first_spike_ms(recorded[0]) if recorded else None

    first_steps = np.full(lplc2.size, -1, np.int64)
    for slot, unit_steps in enumerate(lplc2_times):
        if unit_steps.size:
            first_steps[slot] = unit_steps.min()

    fired = first_steps[first_steps >= 0]
    return {
        'input_events': int(neurons.size),
        'input_neurons': int(np.unique(neurons).size) if neurons.size else 0,
        'lplc2_recruited': int(np.count_nonzero(fired)),
        'lplc2_spikes': int(counts[lplc2].sum()),
        'lplc2_rate_hz': round(float(counts[lplc2].mean() / window_s), 2),
        'dnp01_first_spike_ms': None if first is None else round(first, 3),
        'dnp01_spikes': int(gf.max()),
        'dnp01_ceiling': ceiling_spikes(window_s),
        'saturated': is_saturated(gf, window_s),
    }


def graded(values: list[float | int | None]) -> bool:
    """Whether a readout is graded, i.e. every size yields a distinct value.

    `spread > 0` is not sufficient: a step function that reads 0 for some sizes and the full
    pool for others has a large spread but carries no magnitude information. That mistake
    produced a false positive in experiment 3.
    """
    clean = [v for v in values if v is not None]
    return len(set(clean)) == len(values) and len(values) > 1


def changed_by(arm_rows: list[dict], control_rows: list[dict], key: str) -> bool:
    """Whether the ablation changed a readout *relative to control*.

    An earlier version compared each arm in isolation and reported a positive result when the
    arm's values happened to be distinct — even though they were identical to the control, so
    the ablation had caused nothing. A positive ablation result must be a CHANGE against
    control. Comparing element-wise keeps that honest.
    """
    arm = [r[key] for r in arm_rows]
    control = [r[key] for r in control_rows]
    return arm != control


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--quick', action='store_true')
    parser.add_argument('--window-ms', type=float, default=250.0)
    parser.add_argument('--frames', type=int, default=16)
    parser.add_argument('--velocity', type=float, default=400.0)
    parser.add_argument('--seeds', type=int, default=3)
    args = parser.parse_args()

    weight, _, meta = load_subset()
    lplc2 = np.flatnonzero(meta['type'].to_numpy() == 'LPLC2')
    dnp01 = np.flatnonzero(meta['type'].to_numpy() == 'DNp01')
    window_s = args.window_ms / 1e3
    sizes = QUICK_SIZES_DEG if args.quick else SIZES_DEG
    positions = cell_positions(lplc2)

    # Arm 1: LPLC2 receives nothing but the external drive.
    w_feedforward = zero_columns(weight, lplc2)
    # Arm 2: only LPLC2 -> LPLC2 self-connections removed.
    w_noself = drop_rows(weight, lplc2)

    arms = {
        '0_control': (weight, 'unchanged weights'),
        '1_feedforward': (w_feedforward, 'all incoming edges to LPLC2 removed'),
        '2_no_self_loops': (w_noself, 'LPLC2 -> LPLC2 edges removed only'),
    }

    findings: dict = {
        'config': {
            'window_ms': args.window_ms,
            'frames': args.frames,
            'velocity_deg_per_s': args.velocity,
            'lplc2_neurons': int(lplc2.size),
            'edges_control': int(weight.nnz),
            'edges_feedforward': int(w_feedforward.nnz),
            'edges_no_self_loops': int(w_noself.nnz),
        },
        'arms': {},
    }

    print(f'=== experiment 4: recurrent-loop ablation ({args.window_ms:g} ms window) ===')
    for name, (w, description) in arms.items():
        print()
        print(f'--- arm {name}: {description} '
              f'({int(weight.nnz) - int(w.nnz)} edges removed) ---')
        print(f'{"size":>6} {"cells":>6} {"recruit":>8} {"LPLC2 Hz":>9} '
              f'{"1st ms":>8} {"DNp01":>7} {"sat?":>5}')

        rows = []
        for size in sizes:
            spec = LoomingSpec(peak_size_deg=size, velocity_deg_per_s=args.velocity,
                               frames=args.frames)
            stimulus = looming_luminance(spec)
            trains = contrast_onset_drive(
                stimulus, positions, frame_interval_ms=spec.frame_interval_ms
            )
            steps, neurons = flatten_drive(trains, window_s)
            row = measure(w, lplc2, dnp01, steps, neurons, window_s)
            row['angular_size_deg'] = size
            row['cells_driven'] = len(trains)
            rows.append(row)

            first = row['dnp01_first_spike_ms']
            print(
                f"{size:>6.0f} {row['cells_driven']:>6} {row['lplc2_recruited']:>8} "
                f"{row['lplc2_rate_hz']:>9.1f} "
                f"{'-' if first is None else f'{first:>8.2f}'} "
                f"{row['dnp01_spikes']:>7} "
                f"{'YES' if row['saturated'] else '-':>5}"
            )

        rec = [r['lplc2_recruited'] for r in rows]
        spikes = [r['lplc2_spikes'] for r in rows]
        dn = [r['dnp01_spikes'] for r in rows]
        lat = [r['dnp01_first_spike_ms'] for r in rows]

        findings['arms'][name] = {
            'description': description,
            'rows': rows,
            'recruitment_graded': graded(rec),
            'lplc2_spikes_graded': graded(spikes),
            'dnp01_spikes_graded': graded(dn),
            'latency_graded': graded(lat),
            'recruitment_values': rec,
            'lplc2_spikes_values': spikes,
            'dnp01_spikes_values': dn,
        }
        print(f'  recruitment graded: {graded(rec)}  {rec}')
        print(f'  LPLC2 spikes graded: {graded(spikes)}  {spikes}')
        print(f'  DNp01 spikes graded: {graded(dn)}  {dn}')
        print(f'  latency graded:      {graded(lat)}  {lat}')

    # --- Arm 3: rate vs timing, matched on total input, in the ablated model -------------
    print()
    print('--- arm 3_rate_vs_timing (feed-forward, matched input) ---')
    print(f'{"size":>6} {"enc":>8} {"events":>7} {"LPLC2 Hz":>9} {"1st ms":>8} {"DNp01":>7}')

    rate_rows = []
    for size in sizes:
        spec = LoomingSpec(peak_size_deg=size, velocity_deg_per_s=args.velocity,
                           frames=args.frames)
        stimulus = looming_luminance(spec)
        trains = contrast_onset_drive(
            stimulus, positions, frame_interval_ms=spec.frame_interval_ms
        )
        steps, neurons = flatten_drive(trains, window_s)
        n_events = int(neurons.size)

        timing = measure(w_feedforward, lplc2, dnp01, steps, neurons, window_s)
        timing['encoding'] = 'timing'

        # Rate encoding: the same events spread as a Poisson process over the window at the
        # rate that would produce that many events on average.
        rate = n_events / window_s
        rng = np.random.default_rng(0)
        all_steps = np.arange(round(window_s / (STEP_MS / 1e3)))
        p = rate * (STEP_MS / 1e3)
        chosen = all_steps[rng.random(all_steps.size) < p]
        chosen = np.repeat(chosen, n_events)
        rate_counts, rate_times = simulate_spike_train(
            w_feedforward, SpikeTrain(chosen, neurons), window_s,
            np.random.default_rng(0), record_positions=dnp01,
        )
        gf = rate_counts[dnp01]
        rec = [t for t in rate_times if t.size]
        first = first_spike_ms(rec[0]) if rec else None
        rate_row = {
            'angular_size_deg': size,
            'encoding': 'rate',
            'input_events': n_events,
            'mean_rate_hz': round(rate, 2),
            'lplc2_rate_hz': round(float(rate_counts[lplc2].mean() / window_s), 2),
            'dnp01_first_spike_ms': None if first is None else round(first, 3),
            'dnp01_spikes': int(gf.max()),
            'saturated': is_saturated(gf, window_s),
        }
        timing_row = {
            'angular_size_deg': size,
            'encoding': 'timing',
            'input_events': n_events,
            'lplc2_rate_hz': timing['lplc2_rate_hz'],
            'dnp01_first_spike_ms': timing['dnp01_first_spike_ms'],
            'dnp01_spikes': timing['dnp01_spikes'],
            'saturated': timing['saturated'],
        }
        rate_rows.append(rate_row)

        for row in (rate_row, timing_row):
            first = row['dnp01_first_spike_ms']
            print(
                f"{size:>6.0f} {row['encoding']:>8} {row['input_events']:>7} "
                f"{row['lplc2_rate_hz']:>9.1f} "
                f"{'-' if first is None else f'{first:>8.2f}'} "
                f"{row['dnp01_spikes']:>7}"
            )

    timing_dn = [r['dnp01_spikes'] for r in rate_rows if r['encoding'] == 'timing']
    rate_dn = [r['dnp01_spikes'] for r in rate_rows if r['encoding'] == 'rate']
    findings['arms']['3_rate_vs_timing'] = {
        'description': 'feed-forward model, same total input, rate spread vs single timed spike',
        'rows': rate_rows,
        'timing_graded': graded(timing_dn),
        'rate_graded': graded(rate_dn),
        'timing_values': timing_dn,
        'rate_values': rate_dn,
    }
    print(f'  timing graded: {graded(timing_dn)}  {timing_dn}')
    print(f'  rate graded:   {graded(rate_dn)}  {rate_dn}')

    # --- Seed reproducibility on the ablated arm ----------------------------------------
    print()
    print('--- seed reproducibility, arm 1_feedforward, 42 deg ---')
    seed_rows = []
    spec = LoomingSpec(42.0, args.velocity, args.frames)
    stimulus = looming_luminance(spec)
    trains = contrast_onset_drive(stimulus, positions, frame_interval_ms=spec.frame_interval_ms)
    steps, neurons = flatten_drive(trains, window_s)
    for seed in range(args.seeds):
        row = measure(w_feedforward, lplc2, dnp01, steps, neurons, window_s, seed=seed)
        seed_rows.append(row)
        print(f'  seed {seed}: LPLC2 {row["lplc2_spikes"]} spikes, '
              f'DNp01 {row["dnp01_spikes"]}')

    lplc2_vals = [r['lplc2_spikes'] for r in seed_rows]
    findings['seed_trials'] = seed_rows
    findings['seed_lplc2_spread'] = max(lplc2_vals) - min(lplc2_vals)
    print(f'  spread {findings["seed_lplc2_spread"]} '
          f'({"reproducible" if findings["seed_lplc2_spread"] == 0 else "NOT reproducible"})')

    # --- Verdict -------------------------------------------------------------------------
    # Compare each ablated arm against the CONTROL, never in isolation. An arm whose values are
    # distinct but identical to control has changed nothing.
    control_rows = findings['arms']['0_control']['rows']
    changes = {}
    for name in ('1_feedforward', '2_no_self_loops'):
        arm_rows = findings['arms'][name]['rows']
        changes[name] = {
            key: changed_by(arm_rows, control_rows, key)
            for key in ('lplc2_recruited', 'lplc2_spikes', 'dnp01_spikes',
                        'dnp01_first_spike_ms')
        }
    findings['changes_vs_control'] = changes

    ff = findings['arms']['1_feedforward']
    restored = any(changes['1_feedforward'].values())
    findings['verdict'] = {
        'information_restored_without_recurrence': restored,
        'lplc2_in_causal_path': changes['1_feedforward']['lplc2_spikes'],
        'rate_beats_timing': (
            findings['arms']['3_rate_vs_timing']['rate_graded']
            and not findings['arms']['3_rate_vs_timing']['timing_graded']
        ),
        'timing_beats_rate': (
            findings['arms']['3_rate_vs_timing']['timing_graded']
            and not findings['arms']['3_rate_vs_timing']['rate_graded']
        ),
    }

    print()
    print('=== verdict (compared against CONTROL, not in isolation) ===')
    for name, detail in changes.items():
        touched = [k for k, v in detail.items() if v]
        print(f'  {name:<18} changed: {touched if touched else "nothing"}')
    print(f'response changed by removing recurrence: {restored}')
    print(f'timing graded: {findings["arms"]["3_rate_vs_timing"]["timing_graded"]}, '
          f'rate graded: {findings["arms"]["3_rate_vs_timing"]["rate_graded"]}')

    touched_ff = [k for k, v in changes['1_feedforward'].items() if v]
    if not touched_ff:
        print()
        print('DIAGNOSIS: removing every incoming edge to LPLC2 changed nothing downstream.')
        print('The injected drive propagates along LPLC2 OUTPUT edges, so LPLC2 membrane state')
        print('is never in the causal path. This experiment does not measure LPLC2.')
        print('See scripts/what_drives_dnp01.py and docs/Experiments.md experiment 4.')

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(findings, indent=2), encoding='utf-8')
    print()
    print(f'-> {OUTPUT}')


if __name__ == '__main__':
    main()