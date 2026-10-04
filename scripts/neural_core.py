"""Frozen LIF dynamics for the LPLC2 -> DNp01 measurement harness.

The dynamics here are FROZEN and must not be changed. They are copied from the source
project (`D:\\Projects\\timepass\\fruitfly\\lif_escape.py`) so that a result measured here
is comparable to Shiu et al. 2024 and therefore to the published 19 ms figure in
docs/Biological-Reference.md. Editing any constant below invalidates that comparison.

What this module adds over the source `simulate_visual_subset.simulate` is a deterministic
spike-train input path. The source takes a Poisson *rate* per input neuron; we need to inject
*precisely timed* spikes, because spike timing rather than spike rate is the object of study
(AGENTS.md 2, Architecture: only the encoding and the readout may change).

Sign and delivery conventions are inherited unchanged:
  - weight matrix stored (pre, post) as CSR; delivery sums ROWS (presynaptic fan-out)
  - external drive is routed through the same delayed synaptic path as internal spikes
"""

from __future__ import annotations

import sys
from collections import deque
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp

# The source project is read-only and authoritative for the frozen layers. Importing the
# constants rather than duplicating them means a stale copy here can never silently diverge
# from the simulation the reference values were published against.
SOURCE_PROJECT = Path(r"D:\Projects\timepass\fruitfly")

if str(SOURCE_PROJECT) not in sys.path:
    sys.path.insert(0, str(SOURCE_PROJECT))

from lif_escape import (  # noqa: E402  (path must be set first)
    DECAY_M,
    DECAY_SYN,
    DELAY_STEPS,
    DT,
    REFRACT_STEPS,
    V_RESET,
    V_REST,
    V_TH,
)

#: Time step of the discretisation, seconds.
STEP_S = DT

#: Milliseconds per step, the unit all reported latencies use.
STEP_MS = DT * 1e3

def max_rate_hz(duration_s: float) -> float:
    """Upper bound on measurable firing rate: one spike per refractory period.

    A neuron fires at most once per `REFRACT_STEPS`, so the ceiling over a window is
    `window_steps / REFRACT_STEPS`, not `window_steps`. Measured DNp01 counts reach exactly
    this value, which is how the source project's "239/240 ceiling" arises.
    """
    return 1.0 / (REFRACT_STEPS * DT)


def ceiling_spikes(duration_s: float) -> int:
    """Maximum spikes a neuron can emit in a window of `duration_s`."""
    return round(duration_s / (REFRACT_STEPS * DT))


@dataclass(frozen=True)
class SpikeTrain:
    """A deterministic set of externally-driven spikes.

    Attributes
    ----------
    steps:
        Sorted integer step indices at which the driven neurons receive input.
    neurons:
        Positions (row indices into the weight matrix) of the driven neurons. Every neuron
        in this list spikes at every step in `steps`; per-neuron selectivity is expressed by
        using several SpikeTrain objects rather than one combined train.
    """

    steps: np.ndarray
    neurons: np.ndarray

    def __post_init__(self) -> None:
        if self.steps.ndim != 1:
            raise ValueError("steps must be one-dimensional")
        if self.neurons.ndim != 1:
            raise ValueError("neurons must be one-dimensional")

    @property
    def n_events(self) -> int:
        return int(self.steps.size) * int(self.neurons.size)


def simulate_spike_train(
    weight_matrix: sp.csr_matrix,
    drive: SpikeTrain,
    duration_s: float,
    rng: np.random.Generator,
    record_positions: np.ndarray | None = None,
) -> tuple[np.ndarray, list[np.ndarray]]:
    """Run the frozen LIF dynamics with a deterministic spike-train input.

    Parameters
    ----------
    weight_matrix:
        CSR (pre, post) signed weight matrix, exactly as stored in the source caches.
        NT signs are already baked in, so no sign handling happens here.
    drive:
        Timed input spikes. May be empty, in which case the network simply runs unstimulated.
    duration_s:
        Simulation window in seconds.
    rng:
        Generator for any stochastic internal noise. The current dynamics are deterministic,
        so this is threaded through for future use rather than consumed today; passing a
        seeded generator keeps that extension reproducible.
    record_positions:
        Optional row indices whose spike step indices are recorded. Non-invasive: the
        dynamics and the draw sequence are identical whether or not recording is on.

    Returns
    -------
    counts:
        Per-neuron spike counts, shape (n_neurons,).
    times:
        For each entry of `record_positions`, the array of step indices at which that neuron
        spiked. Spike time in milliseconds is `step * STEP_MS`.
    """
    del rng  # Dynamics are deterministic; no stochastic term exists to consume.

    steps_total = round(duration_s / DT)
    n_neurons = weight_matrix.shape[0]

    voltage = np.full(n_neurons, V_REST, np.float32)
    syn_current = np.zeros(n_neurons, np.float32)
    refractory = np.zeros(n_neurons, np.int32)
    counts = np.zeros(n_neurons, np.int64)

    # External events bucketed by step, so lookup during the loop is O(1) per step.
    external_by_step: dict[int, np.ndarray] = {}
    if drive.neurons.size and drive.steps.size:
        valid = drive.steps < steps_total
        if not np.all(valid):
            raise ValueError(
                f"drive has {int((~valid).sum())} spikes at or after the window end "
                f"({steps_total} steps = {steps_total * STEP_MS:.1f} ms)"
            )
        for step in drive.steps:
            external_by_step.setdefault(int(step), drive.neurons)

    record_index = None
    spike_times: list[list[int]] = []
    if record_positions is not None:
        record_positions = np.asarray(record_positions, dtype=np.intp)
        record_index = np.full(n_neurons, -1, np.int32)
        record_index[record_positions] = np.arange(record_positions.size)
        spike_times = [[] for _ in range(record_positions.size)]

    delay_ring: deque[np.ndarray | None] = deque([None] * DELAY_STEPS)

    for step in range(steps_total):
        # Synaptic delivery: sum rows so current flows along presynaptic fan-out.
        delivered = delay_ring.popleft()
        if delivered is not None and delivered.size:
            syn_current += np.asarray(
                weight_matrix[delivered, :].sum(axis=0)
            ).ravel()

        external = external_by_step.get(step)
        if external is None:
            external = np.empty(0, dtype=np.intp)

        refractory[refractory > 0] -= 1
        excitable = refractory == 0

        # Leaky integration; refractory neurons are clamped to reset, matching the source.
        voltage[excitable] = (
            voltage[excitable] - V_REST
        ) * DECAY_M + V_REST + syn_current[excitable]
        voltage[~excitable] = V_RESET
        syn_current *= DECAY_SYN

        fired = np.flatnonzero((voltage >= V_TH) & excitable)
        if fired.size:
            voltage[fired] = V_RESET
            refractory[fired] = REFRACT_STEPS
            counts[fired] += 1
            if record_index is not None:
                mapped = record_index[fired]
                mapped = mapped[mapped >= 0]
                for slot in mapped:
                    spike_times[slot].append(step)

        if fired.size or external.size:
            delay_ring.append(np.unique(np.concatenate([fired, external])))
        else:
            delay_ring.append(None)

    recorded = [np.asarray(t, dtype=np.int64) for t in spike_times]
    return counts, recorded


def first_spike_ms(steps: np.ndarray) -> float | None:
    """First spike time in milliseconds, or None when the neuron never spiked."""
    if steps.size == 0:
        return None
    return float(steps.min()) * STEP_MS


def is_saturated(counts: np.ndarray, window_s: float, ceiling_fraction: float = 0.98) -> bool:
    """Whether an output neuron sits at its refractory ceiling.

    The bound is one spike per refractory period, so within a window of
    `window_steps = window_s / DT` steps a neuron can emit at most
    `window_steps / REFRACT_STEPS` spikes. At or above `ceiling_fraction` of that, the count
    reflects the ceiling rather than the stimulus.

    This is the pre-registered confound from docs/Biological-Reference.md: a saturated
    output makes every latency derived from it uninformative, and must be reported as such
    even when other tests pass.
    """
    if counts.size == 0:
        return False
    return bool(counts.max() >= ceiling_fraction * ceiling_spikes(window_s))


# --- Self-check -------------------------------------------------------------------
# Run with `python neural_core.py --test`. Asserts the frozen contract holds and that the
# simulator behaves on inputs whose answer is known analytically, so a regression in the
# dynamics fails loudly instead of quietly producing plausible wrong numbers (AGENTS.md 9).

def load_subset() -> tuple[sp.csr_matrix, np.ndarray, pd.DataFrame]:
    """Load the frozen subset caches from the source project.

    The source `load_subset()` uses paths relative to the process working directory, which
    breaks as soon as the harness runs from its own directory. Resolve them against the
    source project root so this harness works from any cwd.
    """
    import pandas as pd

    data = SOURCE_PROJECT / "data"
    weight = sp.load_npz(data / "visual-subset-male-cns-v1.0.npz").tocsr()
    body_ids = np.load(data / "visual-subset-male-cns-v1.0.bodyids.npy")
    meta = pd.read_feather(data / "visual-subset-male-cns-v1.0.meta.feather")
    return weight, body_ids, meta


def _self_test() -> None:
    weight, body_ids, meta = load_subset()
    n_neurons = weight.shape[0]
    assert n_neurons == 19267, f'expected 19,267-neuron subset, got {n_neurons}'

    lplc2 = np.flatnonzero(meta['type'].to_numpy() == 'LPLC2')
    dnp01 = np.flatnonzero(meta['type'].to_numpy() == 'DNp01')
    assert lplc2.size == 185, f'expected 185 LPLC2, got {lplc2.size}'
    assert dnp01.size == 2, f'expected 2 DNp01, got {dnp01.size}'

    # The pathway we measure must exist and match the source project's validation.
    pathway = weight[lplc2][:, dnp01]
    assert pathway.nnz == 185, f'expected 185 LPLC2->DNp01 edges, got {pathway.nnz}'

    # Zero drive: no output spikes. Guards against a stuck initialisation or a bias term.
    counts, _ = simulate_spike_train(
        weight, SpikeTrain(np.empty(0, np.intp), lplc2), 0.05, np.random.default_rng(0)
    )
    assert counts.sum() == 0, f'unstimulated network fired {counts.sum()} spikes'

    # LPLC2 itself must spike when driven; it is cholinergic and drives the output directly.
    counts, _ = simulate_spike_train(
        weight,
        SpikeTrain(np.arange(20), lplc2),
        0.05,
        np.random.default_rng(0),
        record_positions=lplc2,
    )
    assert counts[lplc2].sum() > 0, 'LPLC2 received drive but produced no spikes'

    # Saturation must be detected when the drive is dense enough to pin the output.
    dense = SpikeTrain(np.arange(600), lplc2)
    counts, _ = simulate_spike_train(weight, dense, 0.3, np.random.default_rng(0))
    assert is_saturated(counts[dnp01], 0.3), 'dense drive did not saturate DNp01'

    # A spike outside the window is a caller error, not a silent truncation.
    try:
        simulate_spike_train(
            weight, SpikeTrain(np.array([9999]), lplc2), 0.05, np.random.default_rng(0)
        )
    except ValueError:
        pass
    else:
        raise AssertionError('out-of-window spike was accepted silently')

    print('self-test PASS')
    print(f'  subset neurons      {n_neurons}')
    print(f'  LPLC2 driven        {lplc2.size}')
    print(f'  DNp01 read          {dnp01.size}')
    print(f'  pathway edges       {pathway.nnz}')
    print(f'  step                {STEP_MS:.2f} ms')
    print(f'  refractory          {REFRACT_STEPS} steps = {REFRACT_STEPS * STEP_MS:.2f} ms')
    print(f'  synaptic delay      {DELAY_STEPS} steps = {DELAY_STEPS * STEP_MS:.2f} ms')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Frozen LIF core with spike-train input')
    parser.add_argument('--test', action='store_true', help='run the self-check')
    args = parser.parse_args()

    if args.test:
        _self_test()
    else:
        print(__doc__)
        print('Run with --test to verify the frozen contract.')