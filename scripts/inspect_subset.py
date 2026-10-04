"""Inspect frozen LIF constants and the LPLC2 -> DNp01 subset. Read-only verification."""

import sys

sys.path.insert(0, r"D:\Projects\timepass\fruitfly")

import numpy as np
import pandas as pd
import scipy.sparse as sp

from lif_escape import (
    DT,
    V_REST,
    V_RESET,
    V_TH,
    DECAY_M,
    DECAY_SYN,
    REFRACT_STEPS,
    DELAY_STEPS,
)

print("=== frozen constants ===")
print(f"DT             {DT}")
print(f"V_REST         {V_REST}")
print(f"V_RESET        {V_RESET}")
print(f"V_TH           {V_TH}")
print(f"DECAY_M        {DECAY_M}")
print(f"DECAY_SYN      {DECAY_SYN}")
print(f"REFRACT_STEPS  {REFRACT_STEPS} -> {REFRACT_STEPS * DT * 1e3:.2f} ms")
print(f"DELAY_STEPS    {DELAY_STEPS} -> {DELAY_STEPS * DT * 1e3:.2f} ms")
print(f"steps in 0.3 s {round(0.3 / DT)}")
print(f"max spikes/0.3s per neuron {round(0.3 / DT)} (1 spike/step bound)")

data = r"D:\Projects\timepass\fruitfly\data"
W = sp.load_npz(data + r"\visual-subset-male-cns-v1.0.npz").tocsr()
ids = np.load(data + r"\visual-subset-male-cns-v1.0.bodyids.npy")
meta = pd.read_feather(data + r"\visual-subset-male-cns-v1.0.meta.feather")

print()
print("=== subset ===")
print(f"neurons {W.shape[0]}  edges {W.nnz}")

for t in ("LPLC2", "DNp01", "LC4"):
    pos = np.flatnonzero(meta["type"].to_numpy() == t)
    print(f"  {t:8s} {pos.size:6d}")

lplc2 = np.flatnonzero(meta["type"].to_numpy() == "LPLC2")
dnp01 = np.flatnonzero(meta["type"].to_numpy() == "DNp01")

print()
print("=== LPLC2 -> DNp01 direct edges ===")
sub = W[lplc2][:, dnp01]
print(f"  nonzero {sub.nnz}  sum {sub.sum():.1f}")

print()
print("=== LPLC2 outgoing weight ===")
out_deg = np.diff(W.indptr)
print(f"  LPLC2 out-degree min {out_deg[lplc2].min()} max {out_deg[lplc2].max()}")
print(f"  row sums min {np.asarray(W[lplc2].sum(axis=1)).min():.2f} max {np.asarray(W[lplc2].sum(axis=1)).max():.2f}")

print()
print("=== how many LPLC2 neurons exist in whole-brain cache ===")
print("  (source docs report 185 in subset; ~80 per optic lobe in literature)")