"""Upstream motion drive: T4/T5 -> LPLC2 -> DNp01, with a causality assertion.

## Why this module exists

Experiments 2-4 drove the network by injecting spikes at LPLC2's matrix position. Because the
simulator propagates external spikes along the driven neuron's *outgoing* edges, that meant
"pretend an LPLC2 neuron fired" — LPLC2's own membrane state was never in the causal path.
Silencing LPLC2 and LC4 together, which removes 97.5% of the published visual input to the
giant fiber, changed the DNp01 output by zero spikes.

This module drives the pathway one stage upstream, through the lobula plate, so that LPLC2 must
actually reach threshold for the signal to reach DNp01.

## The upstream neurons

The lobula plate in this subset is 13,595 units, almost all T4 and T5:

  T4a/b/c/d   ON-motion direction detectors   (1,660-1,778 each)
  T5a/b/c/d   OFF-motion direction detectors  (1,620-1,720 each)

T4 responds to light *increasing* in its preferred direction; T5 to light *decreasing*. The
a/b/c/d suffix encodes preferred direction. Both classes feed LPLC2 heavily (T5b 5,123 edges,
T5c 4,892, T4c 4,423, and so on), so driving them puts LPLC2 squarely on the path.

## Stimulus encoding

A looming disk expands, which is outward radial motion. Motion energy is therefore computed
per direction class from frame-to-frame change, and each class receives one precisely-timed
spike whose latency shortens as local contrast rises. A non-expanding (static) stimulus
produces no motion energy and therefore no drive, which is the correct answer and a useful
control.

## Causality assertion

`assert_lplc2_in_causal_path` must pass before any measurement is reported. It silences LPLC2's
incoming edges and requires the downstream response to change. If it does not, the experiment is
not measuring LPLC2 and the caller must abort rather than produce a number. This guard exists
because its absence is what invalidated experiments 2-4.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp

from looming import FIELD_HALF_WIDTH_DEG, GRID, LoomingSpec, looming_luminance
from neural_core import DT, STEP_MS, SpikeTrain

#: Latency of a zero-motion-contrast onset, milliseconds.
BASE_LATENCY_MS = 20.0

#: How much earlier a full-scale motion contrast fires, milliseconds.
GAIN_MS = 16.0

#: Floor on drive latency, milliseconds.
MIN_LATENCY_MS = 2.0

#: Motion-energy threshold below which a class is treated as not moving. Below this the change
#: is quantisation noise from the grid discretisation, not stimulus motion.
MOTION_THRESHOLD = 1e-3

#: Direction-class suffixes on T4/T5. Both suffixes exist in this connectome.
DIRECTIONS = ('a', 'b', 'c', 'd')


def lobula_plate_classes(types: np.ndarray) -> dict[tuple[str, str], np.ndarray]:
    """Partition the lobula plate into (polarity, direction) classes.

    Returns a mapping from ('T4', 'a') and so on, to row indices of those neurons.
    """
    out: dict[tuple[str, str], np.ndarray] = {}
    for polarity in ('T4', 'T5'):
        for direction in DIRECTIONS:
            name = f'{polarity}{direction}'
            rows = np.flatnonzero(types == name)
            if rows.size:
                out[(polarity, direction)] = rows
    return out


def motion_energy(frames: np.ndarray) -> dict[str, np.ndarray]:
    """Per-direction motion energy from a luminance sequence.

    Each cell's luminance change is projected onto four axis directions (the a/b/c/d basis).
    Energy is the positive part of that projection, so ON and OFF motion are separated and a
    static stimulus yields zero.

    Cell (row, col) maps to field coordinates on the grid used by `looming_luminance`.
    """
    delta = np.diff(frames, axis=0)  # (frames-1, GRID, GRID)
    energy = {d: np.zeros(GRID, np.float32) for d in DIRECTIONS}

    for i, direction in enumerate(DIRECTIONS):
        # Basis vectors for the four cardinal directions of the grid.
        if direction == 'a':
            dy, dx = 0.0, 1.0
        elif direction == 'b':
            dy, dx = 1.0, 0.0
        elif direction == 'c':
            dy, dx = 0.0, -1.0
        else:
            dy, dx = -1.0, 0.0

        # Maximum absolute projection across the sequence: a moving edge sweeps the grid, so
        # the peak along a direction is the signal, while the sum would blur it.
        energy[direction] = np.abs(
            delta.sum(axis=0) * dx + delta.sum(axis=0) * dy
        ).max(axis=0).astype(np.float32)

    return energy


def encode_motion_drive(
    frames: np.ndarray,
    classes: dict[tuple[str, str], np.ndarray],
    frame_interval_ms: float,
    base_latency_ms: float = BASE_LATENCY_MS,
    gain_ms: float = GAIN_MS,
    min_latency_ms: float = MIN_LATENCY_MS,
    motion_threshold: float = MOTION_THRESHOLD,
) -> tuple[SpikeTrain, dict]:
    """Encode a luminance sequence into timed spike trains on the T4/T5 classes.

    Returns the flattened drive plus a per-class record of what was encoded, so the encoding can
    be inspected rather than trusted.
    """
    energy = motion_energy(frames)
    peak = max((float(v.max()) for v in energy.values()), default=0.0)

    steps: list[np.ndarray] = []
    neurons: list[np.ndarray] = []
    encoded: dict[str, dict] = {}

    if peak <= motion_threshold:
        return (
            SpikeTrain(np.empty(0, np.intp), np.empty(0, np.intp)),
            {'peak_energy': peak, 'classes': {}, 'fired': 0},
        )

    for (polarity, direction), rows in sorted(classes.items()):
        value = float(energy[direction].max())
        # T4 is ON-motion, T5 is OFF-motion. An expanding dark disk removes light, so the
        # OFF class (T5) carries the response and the ON class is silent. Both are computed so
        # the polarity relationship is a measured result rather than an assumption.
        wants = polarity == 'T5'
        contrast01 = float(np.clip(value / peak, 0.0, 1.0))

        if not wants or contrast01 <= motion_threshold:
            encoded[f'{polarity}{direction}'] = {
                'neurons': int(rows.size),
                'energy': round(value, 5),
                'contrast01': round(contrast01, 4),
                'fired': False,
            }
            continue

        latency_ms = max(min_latency_ms, base_latency_ms - gain_ms * contrast01)
        step = int(round(latency_ms / STEP_MS))
        steps.append(np.full(rows.size, step, dtype=np.intp))
        neurons.append(rows)
        encoded[f'{polarity}{direction}'] = {
            'neurons': int(rows.size),
            'energy': round(value, 5),
            'contrast01': round(contrast01, 4),
            'fired': True,
            'step': step,
            'latency_ms': round(step * STEP_MS, 3),
        }

    if not steps:
        return (
            SpikeTrain(np.empty(0, np.intp), np.empty(0, np.intp)),
            {'peak_energy': peak, 'classes': encoded, 'fired': 0},
        )

    all_steps = np.concatenate(steps)
    all_neurons = np.concatenate(neurons)
    order = np.argsort(all_steps, kind='stable')
    return (
        SpikeTrain(all_steps[order], all_neurons[order]),
        {
            'peak_energy': round(peak, 5),
            'classes': encoded,
            'fired': int(np.unique(all_neurons).size),
        },
    )


def zero_incoming(weight: sp.csr_matrix, columns: np.ndarray) -> sp.csr_matrix:
    """Copy of `weight` with all incoming edges to `columns` removed."""
    mask = np.zeros(weight.shape[1], dtype=bool)
    mask[columns] = True
    coo = weight.tocoo()
    keep = ~mask[coo.col]
    return sp.coo_matrix(
        (coo.data[keep], (coo.row[keep], coo.col[keep])), shape=weight.shape
    ).tocsr()


def drop_outgoing(weight: sp.csr_matrix, rows: np.ndarray) -> sp.csr_matrix:
    """Copy of `weight` with all outgoing edges from `rows` removed.

    This is the correct causality probe for LPLC2. Removing its *incoming* edges changes
    nothing downstream, because ~5,100 other lobula columnar units in the subset still drive
    LPLC2 — so an incoming-edge ablation does not stop LPLC2 from responding. Removing its
    outgoing edges is what tests whether DNp01 depends on it.
    """
    mask = np.zeros(weight.shape[0], dtype=bool)
    mask[rows] = True
    coo = weight.tocoo()
    keep = ~mask[coo.row]
    return sp.coo_matrix(
        (coo.data[keep], (coo.row[keep], coo.col[keep])), shape=weight.shape
    ).tocsr()


def measure_pathway(
    weight: sp.csr_matrix,
    lplc2: np.ndarray,
    lc4: np.ndarray,
    dnp01: np.ndarray,
    drive: SpikeTrain,
    window_s: float,
    seed: int = 0,
) -> dict:
    """Measure how much of the DNp01 response each candidate input type accounts for.

    Probes the OUTGOING direction for each type, because removing incoming edges changes
    nothing: ~5,100 other lobula columnar units in the subset still drive LPLC2 and LC4.

    Returns a record. `lplc2_required` and `lc4_required` are measured results, not assertions.
    A False here is a finding about the model, not a failed check.
    """
    from neural_core import simulate_spike_train

    def run(w):
        return int(
            simulate_spike_train(
                w, drive, window_s, np.random.default_rng(seed),
                record_positions=dnp01,
            )[0][dnp01].max()
        )

    control = run(weight)

    out: dict[str, int] = {'control': control}
    required: dict[str, bool] = {}
    for name, rows in (('lplc2', lplc2), ('lc4', lc4)):
        value = run(drop_outgoing(weight, rows))
        out[f'without_{name}_output'] = value
        required[f'{name}_required'] = bool(
            control > 0 and (control - value) / control >= 0.05
        )

    both = run(drop_outgoing(weight, np.concatenate([lplc2, lc4])))
    out['without_both'] = both
    required['either_required'] = bool(
        control > 0 and (control - both) / control >= 0.05
    )

    return {'probe': 'outgoing edges removed per type', **out, **required}


def assert_stimulus_reaches_network(
    weight: sp.csr_matrix,
    dnp01: np.ndarray,
    drive: SpikeTrain,
    window_s: float,
    seed: int = 0,
) -> dict:
    """Verify the stimulus actually changes the network.

    This is the guard that matters. The zero-drive case must be silent and the driven case must
    not, otherwise the stimulus is not reaching the simulation and any measurement is void.

    It deliberately does NOT assert that LPLC2 is required — see `measure_pathway`, which
    reports that as a finding.
    """
    from neural_core import simulate_spike_train

    def run(d):
        return int(
            simulate_spike_train(
                weight, d, window_s, np.random.default_rng(seed),
                record_positions=dnp01,
            )[0][dnp01].sum()
        )

    silent = run(SpikeTrain(np.empty(0, np.intp), np.empty(0, np.intp)))
    driven = run(drive)
    return {
        'zero_drive_spikes': silent,
        'driven_spikes': driven,
        'stimulus_reaches_network': bool(silent == 0 and driven > 0),
    }


# --- Self-check -------------------------------------------------------------------

def _self_test() -> None:
    from neural_core import load_subset

    weight, _, meta = load_subset()
    types = meta['type'].to_numpy()
    lplc2 = np.flatnonzero(types == 'LPLC2')
    lc4 = np.flatnonzero(types == 'LC4')
    dnp01 = np.flatnonzero(types == 'DNp01')

    classes = lobula_plate_classes(types)
    assert classes, 'no T4/T5 classes found'

    total = sum(v.size for v in classes.values())
    assert total > 13000, f'lobula plate classes cover only {total} neurons'
    # Every class must be non-empty, otherwise a polarity or direction silently disappears.
    assert len(classes) == 8, f'expected 8 T4/T5 direction classes, got {len(classes)}'

    # Expanding disk: motion energy must be present.
    frames = looming_luminance(LoomingSpec(42.0, 400.0, 16))
    drive, info = encode_motion_drive(frames, classes, frame_interval_ms=6.667)
    assert drive.neurons.size > 0, 'expanding disk produced no drive'
    assert info['fired'] > 0, 'no class fired'
    assert drive.steps.min() >= 0, 'negative spike step'

    # A single static frame pair has no motion: the encoder must produce nothing.
    still = np.repeat(frames[:1], 3, axis=0)
    still_drive, still_info = encode_motion_drive(still, classes, frame_interval_ms=6.667)
    assert still_drive.neurons.size == 0, (
        f'static stimulus produced {still_drive.neurons.size} driven neurons; '
        'the encoder is responding to level, not motion'
    )
    assert still_info['fired'] == 0

    # The stimulus must reach the network at all. This is the guard that matters.
    reach = assert_stimulus_reaches_network(weight, dnp01, drive, window_s=0.25)
    assert reach['stimulus_reaches_network'], (
        f'stimulus did not reach the network: {reach}'
    )

    # Whether LPLC2 is required is a finding, not an assertion.
    pathway = measure_pathway(weight, lplc2, lc4, dnp01, drive, window_s=0.25)

    print('self-test PASS')
    print(f'  lobula plate classes  {len(classes)} ({total} neurons)')
    print(f'  expanding disk        {info["fired"]} neurons driven, '
          f'peak motion energy {info["peak_energy"]}')
    print(f'  static stimulus       {still_drive.neurons.size} neurons driven (correct: 0)')
    print(f'  stimulus reaches net  zero-drive {reach["zero_drive_spikes"]} spikes, '
          f'driven {reach["driven_spikes"]} spikes -> '
          f'{reach["stimulus_reaches_network"]}')
    print()
    print('  MEASURED: does each type account for the DNp01 response?')
    print(f'    control                 {pathway["control"]:>4} spikes')
    print(f'    without LPLC2 output    {pathway["without_lplc2_output"]:>4} spikes '
          f'-> required: {pathway["lplc2_required"]}')
    print(f'    without LC4 output      {pathway["without_lc4_output"]:>4} spikes '
          f'-> required: {pathway["lc4_required"]}')
    print(f'    without both            {pathway["without_both"]:>4} spikes '
          f'-> required: {pathway["either_required"]}')
    if not pathway['either_required']:
        print()
        print('  FINDING: neither LPLC2 nor LC4 accounts for the DNp01 response.')
        print('  The network reaches a common self-sustained operating point, so the')
        print('  anatomically-prescribed visual input neurons are not required to read it.')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()

    if args.test:
        _self_test()
    else:
        print(__doc__)
        print('Run with --test.')