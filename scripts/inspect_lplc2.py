"""Inspect LPLC2 metadata: does the connectome carry a retinotopy, or would we invent one?

Read-only. Answers a design question before any encoder is written: the contrast-onset drive
must map stimulus position onto LPLC2 neurons. If the annotation carries spatial information
we use it. If not, the retinotopy is a modelling assumption and must be declared as one
(AGENTS.md 8 - ask rather than guess at simulation semantics).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from neural_core import SOURCE_PROJECT, load_subset


def main() -> None:
    _, body_ids, meta = load_subset()

    print('=== meta columns ===')
    print(list(meta.columns))

    lplc2 = meta[meta['type'] == 'LPLC2'].copy()
    print()
    print(f'=== LPLC2 rows: {len(lplc2)} ===')
    print(lplc2.head(10).to_string())

    print()
    print('=== per-column summary for LPLC2 ===')
    for col in meta.columns:
        values = lplc2[col]
        unique = values.nunique(dropna=False)
        sample = values.dropna().unique()[:6]
        print(f'  {col:16s} dtype={str(values.dtype):10s} unique={unique:5d}  {sample}')

    print()
    print('=== candidate spatial fields ===')
    for col in ('somaSide', 'instance', 'group', 'superclass', 'class'):
        if col in lplc2.columns:
            counts = lplc2[col].value_counts(dropna=False)
            print(f'  {col}: {dict(counts)}')

    # Do any other neuron types in the subset carry any coordinate-like attribute?
    print()
    print('=== whole-subset columns with numeric variety (candidate coordinates) ===')
    numeric = meta.select_dtypes(include=[np.number])
    for col in numeric.columns:
        if meta[col].nunique(dropna=False) > 1:
            print(f'  {col}: min={meta[col].min()} max={meta[col].max()} unique={meta[col].nunique()}')

    print()
    print('=== LC4, for comparison ===')
    lc4 = meta[meta['type'] == 'LC4']
    print(f'  rows {len(lc4)}, somaSide {dict(lc4["somaSide"].value_counts())}')


if __name__ == '__main__':
    main()