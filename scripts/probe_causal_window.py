"""Diagnostic: which upstream type is in DNp01's causal path, and at what window length?

Read-only probe. No assertions about the answer -- it prints the surface so the window and
the causal type are chosen from measurement rather than assumed.
"""

from __future__ import annotations

import numpy as np

from looming import LoomingSpec, looming_luminance
from neural_core import ceiling_spikes, load_subset, simulate_spike_train
from upstream_drive import (
    encode_motion_drive,
    lobula_plate_classes,
    zero_incoming,
)


def main() -> None:
    weight, _, meta = load_subset()
    types = meta['type'].to_numpy()
    lplc2 = np.flatnonzero(types == 'LPLC2')
    lc4 = np.flatnonzero(types == 'LC4')
    dnp01 = np.flatnonzero(types == 'DNp01')

    classes = lobula_plate_classes(types)
    frames = looming_luminance(LoomingSpec(42.0, 400.0, 16))
    drive, info = encode_motion_drive(frames, classes, 6.667)

    print(f'drive: {drive.neurons.size} neurons, steps {np.unique(drive.steps)}, '
          f'latency {np.unique(drive.steps)[0] * 0.5:.1f} ms')
    print()

    def run(w, d, window):
        counts, _ = simulate_spike_train(
            w, d, window, np.random.default_rng(0), record_positions=dnp01
        )
        return int(counts[dnp01].max())

    ablate_lplc2 = zero_incoming(weight, lplc2)
    ablate_lc4 = zero_incoming(weight, lc4)
    ablate_desc = zero_incoming(weight, dnp01)

    print('=== DNp01 spikes vs measurement window ===')
    print(f'{"window":>9} {"ceil":>5} {"ctrl":>6} {"-LPLC2":>7} {"-LC4":>6} '
          f'{"LPLC2 chg":>11} {"LC4 chg":>9}')
    for window in (0.005, 0.01, 0.02, 0.03, 0.05, 0.08, 0.12, 0.25):
        base = run(weight, drive, window)
        no_lplc2 = run(ablate_lplc2, drive, window)
        no_lc4 = run(ablate_lc4, drive, window)
        chg_l = (base - no_lplc2) / base * 100 if base else 0.0
        chg_4 = (base - no_lc4) / base * 100 if base else 0.0
        print(
            f'{window * 1000:>8.0f}ms {ceiling_spikes(window):>5} {base:>6} '
            f'{no_lplc2:>7} {no_lc4:>6} {chg_l:>10.1f}% {chg_4:>8.1f}%'
        )

    print()
    print('=== does input magnitude matter at the shortest window? ===')
    print('(drive only a fraction of T4/T5 neurons; DNp01 spikes at 20 ms)')
    for fraction in (1.0, 0.5, 0.25, 0.1, 0.05, 0.02, 0.01):
        subset_rows = np.unique(drive.neurons)
        keep = subset_rows[: max(1, int(subset_rows.size * fraction))]
        mask = np.isin(drive.neurons, keep)
        scaled = type(drive)(
            drive.steps[mask],
            drive.neurons[mask],
        )
        counts, _ = simulate_spike_train(
            weight, scaled, 0.02, np.random.default_rng(0), record_positions=dnp01
        )
        print(
            f'  {fraction:>5.2f} of T4/T5 ({len(keep):>5} neurons)  '
            f'DNp01 {int(counts[dnp01].max()):>3}'
        )


if __name__ == '__main__':
    main()