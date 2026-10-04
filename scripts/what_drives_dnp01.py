"""What actually drives DNp01 in this model?

## Why

Experiment 4 produced two results that do not fit the project's working hypothesis:

  - Arm 1 (all incoming edges to the 185 LPLC2 units removed) gives a DNp01 response
    BYTE-IDENTICAL to the control: 85 / 82 / 75 spikes at 10 / 42 / 80 degrees.
  - Arm 2 (only LPLC2's outgoing edges removed) silences the whole network, including DNp01.

Arm 1 says LPLC2's activity is not what makes DNp01 fire. Arm 2 says LPLC2's output is
load-bearing for the network. Both can be true only if the network sustains itself on a path
that bypasses LPLC2, and LPLC2 sits downstream of that path rather than upstream of DNp01.

That would contradict the published anatomy. Card & von Reyn, and PLOS Biol 2025, report that
97.5% of visual input to the giant fiber comes from LPLC2 (52.2%) and LC4 (45.2%).

So: measure the actual causal input to DNp01 rather than assuming it, and compare the model's
attribution against the published attribution.

Usage:
    python what_drives_dnp01.py
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp

from neural_core import SOURCE_PROJECT, load_subset

OUTPUT = Path(__file__).resolve().parent.parent / "data" / "dnp01-drivers.json"

#: Published attribution, from docs/Biological-Reference.md.
PUBLISHED = {'LPLC2': 52.2, 'LC4': 45.2, 'other': 2.6}


def main() -> None:
    weight, body_ids, meta = load_subset()
    types = meta['type'].to_numpy()
    dnp01 = np.flatnonzero(types == 'DNp01')

    findings: dict = {
        'subset': {'neurons': int(weight.shape[0]), 'edges': int(weight.nnz)},
        'dnp01': {'count': int(dnp01.size)},
        'published_attribution_percent': PUBLISHED,
    }

    # --- Structural: what has edges INTO DNp01, and with what signed weight? ---
    print('=== structural input to DNp01 ===')
    coo = weight.tocoo()
    mask = np.isin(coo.col, dnp01)
    rows = coo.row[mask]
    cols = coo.col[mask]
    vals = coo.data[mask]

    print(f'incoming edges: {vals.size}')
    print(f'  excitatory (+): {int((vals > 0).sum())}')
    print(f'  inhibitory (-): {int((vals < 0).sum())}')
    print(f'  total signed weight: {vals.sum():.1f}')

    by_type: dict[str, dict[str, float]] = defaultdict(lambda: {'edges': 0, 'weight': 0.0})
    for row, col, val in zip(rows, cols, vals):
        presyn_type = str(types[row])
        entry = by_type[presyn_type]
        entry['edges'] += 1
        entry['weight'] += float(val)

    print()
    print(f'{"presyn type":<22} {"edges":>7} {"signed weight":>14}')
    for name, entry in sorted(by_type.items(), key=lambda kv: -abs(kv[1]['weight'])):
        print(f"{name:<22} {int(entry['edges']):>7} {entry['weight']:>14.1f}")

    total_abs = sum(abs(e['weight']) for e in by_type.values()) or 1.0
    model_share = {
        name: round(abs(e['weight']) / total_abs * 100, 1) for name, e in by_type.items()
    }
    findings['model_attribution_percent'] = model_share

    print()
    print('=== attribution comparison ===')
    print(f'{"type":<10} {"published":>10} {"model":>10}')
    for name in ('LPLC2', 'LC4'):
        pub = PUBLISHED[name]
        mod = model_share.get(name, 0.0)
        print(f'{name:<10} {pub:>9.1f}% {mod:>9.1f}%')
    other_pub = PUBLISHED['other']
    other_mod = round(100 - sum(model_share.get(n, 0.0) for n in ('LPLC2', 'LC4')), 1)
    print(f'{"other":<10} {other_pub:>9.1f}% {other_mod:>9.1f}%')

    findings['divergence'] = {
        'lplc2_published': PUBLISHED['LPLC2'],
        'lplc2_model': model_share.get('LPLC2', 0.0),
        'lc4_published': PUBLISHED['LC4'],
        'lc4_model': model_share.get('LC4', 0.0),
    }

    # --- Causal: silence each candidate in turn and re-measure DNp01 ---
    print()
    print('=== causal test: silence each input type, measure DNp01 ===')
    print('(a single 42-degree looming drive, 250 ms window)')

    from looming import LoomingSpec, cell_positions, contrast_onset_drive, looming_luminance
    from neural_core import STEP_MS, SpikeTrain, is_saturated, simulate_spike_train

    lplc2 = np.flatnonzero(types == 'LPLC2')
    lc4 = np.flatnonzero(types == 'LC4')
    positions = cell_positions(lplc2)

    spec = LoomingSpec(42.0, 400.0, 16)
    stimulus = looming_luminance(spec)
    trains = contrast_onset_drive(stimulus, positions, frame_interval_ms=spec.frame_interval_ms)
    steps = np.concatenate([t.steps for t in trains])
    neurons = np.concatenate([t.neurons for t in trains])
    order = np.argsort(steps, kind='stable')
    steps, neurons = steps[order], neurons[order]
    keep = steps < round(0.25 / (STEP_MS / 1e3))
    drive = SpikeTrain(steps[keep], neurons[keep])

    def run(w, label):
        counts, _ = simulate_spike_train(
            w, drive, 0.25, np.random.default_rng(0), record_positions=dnp01
        )
        gf = counts[dnp01]
        total = int(counts.sum())
        print(f'  {label:<34} DNp01 {int(gf.max()):>4} spikes   '
              f'network {total:>9}')
        return {'dnp01_spikes': int(gf.max()), 'network_spikes': total,
                'saturated': is_saturated(gf, 0.25)}

    def zero_incoming(w, columns):
        m = np.zeros(w.shape[1], dtype=bool)
        m[columns] = True
        c = w.tocoo()
        keep = ~m[c.col]
        return sp.coo_matrix(
            (c.data[keep], (c.row[keep], c.col[keep])), shape=w.shape
        ).tocsr()

    causal = {
        'control': run(weight, 'control (nothing removed)'),
        'lplc2_silenced': run(zero_incoming(weight, lplc2), 'LPLC2 input removed'),
        'lc4_silenced': run(zero_incoming(weight, lc4), 'LC4 input removed'),
        'both_silenced': run(zero_incoming(weight, np.concatenate([lplc2, lc4])),
                             'LPLC2 + LC4 input removed'),
    }
    findings['causal'] = causal

    control_dn = causal['control']['dnp01_spikes']
    print()
    print('=== what DNp01 depends on ===')
    for key in ('lplc2_silenced', 'lc4_silenced', 'both_silenced'):
        delta = causal[key]['dnp01_spikes'] - control_dn
        pct = 0.0 if control_dn == 0 else delta / control_dn * 100
        print(f'  {key:<18} DNp01 change {delta:>+5} ({pct:>+6.1f}%)')

    findings['conclusion'] = (
        f"Removing all incoming drive to LPLC2 changes the DNp01 response by "
        f"{causal['lplc2_silenced']['dnp01_spikes'] - control_dn:+d} spikes. "
        f"Removing LPLC2 and LC4 together changes it by "
        f"{causal['both_silenced']['dnp01_spikes'] - control_dn:+d} spikes. "
        f"Published anatomy attributes 97.5% of GF visual input to these two types."
    )
    print()
    print(findings['conclusion'])

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(findings, indent=2), encoding='utf-8')
    print(f'\n-> {OUTPUT}')


if __name__ == '__main__':
    main()