"""Contrast-onset spike-train encoding for the LPLC2 -> DNp01 measurement.

This is the in-window core experiment: replace spike *rate* encoding with spike *timing*
encoding and measure whether the descending-neuron response changes.

## What changes relative to the source project

The source `structured_drive.py` maps an 8x8 grid of image features onto the lobula columnar
pool and assigns each neuron a firing *rate*. This module keeps that neuron-to-cell mapping
**exactly** and replaces only the output: a neuron receives **one precisely-timed spike** at a
step determined by local contrast, instead of a Poisson train at a rate. Nothing else changes,
so any difference in the measured response is attributable to the encoding.

## Stimulus

Looming disks — an expanding dark disk — because that is the ethologically relevant stimulus
for this pathway and the one von Reyn et al. 2017 modelled with the eta (size) and rho
(velocity) components. Generated analytically, so angular size and angular velocity are
independent, continuous parameters.

## Declared assumption: no retinotopy

The subset annotations carry no spatial information about LPLC2 beyond `somaSide`
(L: 94, R: 91). There is no eccentricity, no dendritic position, no angular coordinate.

The neuron-to-cell assignment below is therefore inherited from the source project's
`structured_rates`, which assigns cells to the bodyId-sorted pool in a fixed order. That
assignment is a **convention, not anatomy** — it carries no claim about which LPLC2 neuron
sees which part of the visual field.

Consequence, stated plainly: this experiment measures whether *timing* carries stimulus
information that *rate* loses. It does not model spatial organisation, and no result here
supports a claim about receptive fields.

## Timing model

Real ON-transient photoreceptors respond faster at higher contrast. Encoded as a latency
that shortens with contrast magnitude:

    latency_ms = base_ms - gain_ms * contrast01      (clamped to >= min_ms)

Stronger onset -> earlier spike. The mapping is monotone and continuous, so distinct stimuli
produce distinct timing patterns rather than a binary on/off.

Usage:
    python looming.py --test          # self-check
    python looming.py --demo          # print one stimulus's timing table
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass

import numpy as np

from neural_core import DT, STEP_MS, SpikeTrain

#: Grid resolution inherited from the source project, so the cell set matches exactly.
GRID = 8
N_CELLS = GRID * GRID

#: Latency of a zero-contrast (pure baseline) onset, milliseconds.
BASE_LATENCY_MS = 24.0

#: How much earlier a full-scale contrast onset fires, milliseconds.
GAIN_MS = 20.0

#: Floor so a maximum-contrast onset cannot fire before the drive can propagate.
MIN_LATENCY_MS = 2.0

#: Angular radius beyond which the disk leaves the modelled field of view, degrees.
FIELD_HALF_WIDTH_DEG = 60.0


@dataclass(frozen=True)
class LoomingSpec:
    """A looming-disk stimulus.

    Attributes
    ----------
    peak_size_deg:
        Maximum angular diameter of the disk, degrees. The eta (size) parameter.
    velocity_deg_per_s:
        Constant angular expansion rate. The rho (velocity) parameter.
    frames:
        Number of frames to generate. Frame interval is derived from the velocity so the
        disk reaches `peak_size_deg` exactly on the last frame.
    """

    peak_size_deg: float
    velocity_deg_per_s: float = 400.0
    frames: int = 16

    def __post_init__(self) -> None:
        if self.peak_size_deg <= 0:
            raise ValueError('peak_size_deg must be positive')
        if self.velocity_deg_per_s <= 0:
            raise ValueError('velocity_deg_per_s must be positive')
        if self.frames < 2:
            raise ValueError('need at least 2 frames to define a change')

    @property
    def frame_interval_s(self) -> float:
        """Seconds between frames, so the disk grows by one frame-step each interval."""
        # Angular *radius* per second is velocity/2, since velocity is quoted as the
        # diameter growth rate used by von Reyn et al.
        radius_per_s = self.velocity_deg_per_s / 2.0
        diameter_step = self.peak_size_deg / (self.frames - 1)
        return diameter_step / self.velocity_deg_per_s if self.velocity_deg_per_s else 1.0

    @property
    def frame_interval_ms(self) -> float:
        return self.frame_interval_s * 1e3

    def sizes_deg(self) -> np.ndarray:
        """Angular diameter of the disk on each frame, degrees."""
        return np.linspace(0.0, self.peak_size_deg, self.frames)


#: Luminance inside the disk. The object is an occluder: dark on a bright field.
DISK_LUMINANCE = 0.15


def looming_luminance(spec: LoomingSpec) -> np.ndarray:
    """Render the stimulus as a stack of luminance grids.

    Returns an array of shape (frames, GRID, GRID) with values in [0, 1].

    The field starts bright and the expanding disk darkens it. The boundary is softened over
    one cell width so that as the edge crosses a cell, luminance falls *progressively* rather
    than in a single step. That matters: a hard step would make every cell's contrast
    identical and flatten the timing, which is the signal under test.

    Cell (row, col) maps to field coordinate x = (col + 0.5)/GRID - 0.5, scaled so the grid
    spans +-FIELD_HALF_WIDTH_DEG.
    """
    half = FIELD_HALF_WIDTH_DEG
    coords = (np.arange(GRID) + 0.5) / GRID * 2.0 - 1.0
    x, y = np.meshgrid(coords * half, coords * half)
    distance = np.sqrt(x * x + y * y)

    # One cell width of softening at the disk boundary.
    edge_width = half / GRID

    frames = np.empty((spec.frames, GRID, GRID), np.float32)
    for i, diameter in enumerate(spec.sizes_deg()):
        radius = diameter / 2.0
        # 0 outside the boundary, 1 well inside it.
        occupancy = np.clip((radius + edge_width - distance) / (2.0 * edge_width), 0.0, 1.0)
        frames[i] = 1.0 - occupancy * (1.0 - DISK_LUMINANCE)

    return frames.astype(np.float32)


def cell_positions(lplc2: np.ndarray) -> dict[int, np.ndarray]:
    """Assign each LPLC2 neuron a grid cell, using the source project's convention.

    The source `structured_rates` sorts the pool by bodyId and assigns
    `cell = k % (GRID*GRID)`. Reproduced here so the neuron-to-cell relation is identical and
    the only variable under test is the encoding.

    Declared assumption: this is a fixed ordering convention, NOT a retinotopy. The subset
    annotations carry no spatial information about LPLC2.
    """
    assignment: dict[int, list[int]] = {}
    for k, neuron in enumerate(lplc2):
        assignment.setdefault(k % N_CELLS, []).append(int(neuron))
    return {cell: np.array(n, dtype=np.intp) for cell, n in assignment.items()}


def contrast_onset_drive(
    frames: np.ndarray,
    positions: dict[int, np.ndarray],
    base_latency_ms: float = BASE_LATENCY_MS,
    gain_ms: float = GAIN_MS,
    min_latency_ms: float = MIN_LATENCY_MS,
    frame_interval_ms: float | None = None,
) -> list[SpikeTrain]:
    """Contrast-onset encoding: luminance frames -> one timed spike train per cell.

    For each cell, the frame-to-frame luminance change is taken as local contrast. A cell that
    darkens (the disk edge crossing it) fires once, at a latency that shortens with the size
    of the change. Cells that do not change get no spikes.

    Parameters
    ----------
    frames:
        (frames, GRID, GRID) luminance stack from `looming_luminance`.
    positions:
        Cell index -> neuron positions, from `cell_positions`.
    frame_interval_ms:
        Time between frames. Defaults to the interval implied by `frames`, treated as 0 when
        not supplied so a caller measuring a static sequence gets onset-relative times.

    Returns
    -------
    A list of SpikeTrain, one per cell that fired, sorted by cell index. Each train carries
    the steps at which that cell's neurons should receive input.

    Note on magnitudes: contrast is normalised per cell against that cell's own luminance
    range across the sequence, so the encoding is invariant to overall stimulus brightness.
    That matters because the network should respond to *change*, not to absolute level.
    """
    if frames.ndim != 3 or frames.shape[1:] != (GRID, GRID):
        raise ValueError(f'expected (frames, {GRID}, {GRID}) luminance, got {frames.shape}')

    delta = np.diff(frames, axis=0)  # (frames-1, GRID, GRID)
    interval = 0.0 if frame_interval_ms is None else frame_interval_ms

    trains: list[SpikeTrain] = []
    for cell in sorted(positions):
        row, col = divmod(cell, GRID)
        changes = delta[:, row, col]

        # Strongest darkening across the sequence: the disk edge crossing this cell.
        drop_index = int(np.argmin(changes))
        contrast = float(-changes[drop_index])  # positive when the cell darkened
        if contrast <= 0:
            continue

        # Normalise against this cell's own full luminance range so absolute brightness
        # does not enter the encoding.
        cell_series = frames[:, row, col]
        span = float(cell_series.max() - cell_series.min())
        if span <= 0:
            continue
        contrast01 = float(np.clip(contrast / span, 0.0, 1.0))

        latency_ms = max(
            min_latency_ms, base_latency_ms - gain_ms * contrast01
        )
        step = int(round((drop_index * interval + latency_ms) / STEP_MS))
        trains.append(SpikeTrain(np.array([step], dtype=np.intp), positions[cell]))

    return trains


def merge_trains(trains: list[SpikeTrain], n_neurons: int) -> SpikeTrain:
    """Flatten per-cell trains into one, for callers that drive the whole pool at once."""
    steps = np.concatenate([t.steps for t in trains]) if trains else np.empty(0, np.intp)
    neurons = np.concatenate([t.neurons for t in trains]) if trains else np.empty(0, np.intp)
    del n_neurons
    return SpikeTrain(np.sort(steps), neurons)


# --- Self-check -------------------------------------------------------------------

def _self_test() -> None:
    spec = LoomingSpec(peak_size_deg=40.0, velocity_deg_per_s=400.0, frames=16)
    frames = looming_luminance(spec)

    assert frames.shape == (16, GRID, GRID), f'unexpected frame shape {frames.shape}'
    assert 0.0 <= frames.min() and frames.max() <= 1.0, 'luminance outside [0, 1]'

    # The disk grows, so the field must lose total luminance monotonically.
    totals = frames.sum(axis=(1, 2))
    assert np.all(np.diff(totals) <= 1e-4), 'luminance did not decrease monotonically'

    # Cells map onto the whole pool without omission or duplication.
    lplc2 = np.arange(185)
    positions = cell_positions(lplc2)
    assigned = sum(v.size for v in positions.values())
    assert assigned == lplc2.size, f'assigned {assigned} of {lplc2.size} neurons'
    assert len(positions) == N_CELLS, f'expected {N_CELLS} cells, got {len(positions)}'

    trains = contrast_onset_drive(frames, positions, frame_interval_ms=spec.frame_interval_ms)
    assert trains, 'no cells fired — contrast encoding produced no drive'

    # Latency must shorten with contrast: the earliest spike is earlier than the latest.
    firsts = np.array([t.steps.min() for t in trains])
    assert firsts.max() > firsts.min(), 'every cell fired at the same step; timing is flat'
    assert firsts.min() >= 0, 'negative spike step'

    # A larger disk must recruit more cells, which is the stimulus-dependence we measure.
    small = contrast_onset_drive(
        looming_luminance(LoomingSpec(10.0, 400.0, 16)), positions,
        frame_interval_ms=spec.frame_interval_ms,
    )
    large = contrast_onset_drive(
        looming_luminance(LoomingSpec(80.0, 400.0, 16)), positions,
        frame_interval_ms=spec.frame_interval_ms,
    )
    assert len(large) > len(small), (
        f'bigger disk recruited no more cells: {len(small)} -> {len(large)}'
    )

    print('self-test PASS')
    print(f'  stimulus          peak {spec.peak_size_deg} deg, {spec.frames} frames')
    print(f'  frame interval    {spec.frame_interval_ms:.3f} ms')
    print(f'  cells driven      {len(trains)} / {N_CELLS}  (10 deg: {len(small)}, 80 deg: {len(large)})')
    print(f'  spike step range  {firsts.min()} .. {firsts.max()} '
          f'({firsts.min() * STEP_MS:.2f} .. {firsts.max() * STEP_MS:.2f} ms)')
    print(f'  latency model     {BASE_LATENCY_MS} ms base - {GAIN_MS} ms gain, floor {MIN_LATENCY_MS} ms')


def _demo() -> None:
    spec = LoomingSpec(peak_size_deg=40.0, velocity_deg_per_s=400.0, frames=16)
    frames = looming_luminance(spec)
    positions = cell_positions(np.arange(185))
    trains = contrast_onset_drive(frames, positions, frame_interval_ms=spec.frame_interval_ms)

    print(f'stimulus: peak {spec.peak_size_deg} deg, {spec.frames} frames, '
          f'{spec.frame_interval_ms:.3f} ms apart')
    print(f'disk diameter per frame (deg): {np.round(spec.sizes_deg(), 2)}')
    print()
    print('cell  neurons  contrast  latency_ms  step')
    for train in sorted(trains, key=lambda t: t.steps.min())[:20]:
        step = int(train.steps.min())
        print(f'{len(train.neurons):>4}  {step * STEP_MS:>10.2f}  {step:>5}')
    print()
    print(f'{len(trains)} of {N_CELLS} cells fired')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--test', action='store_true')
    parser.add_argument('--demo', action='store_true')
    args = parser.parse_args()

    if args.test:
        _self_test()
    elif args.demo:
        _demo()
    else:
        print(__doc__)