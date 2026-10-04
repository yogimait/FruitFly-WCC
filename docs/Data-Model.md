# Data Model

Every number the dashboard renders traces to a file in `data/`. This note lists those files, who
writes them, and what each field means. Nothing in `data/` is hand-edited.

## Provenance

The connectome and LIF constants come from the source simulation at
`D:\Projects\timepass\fruitfly` (read-only). Recorded in `DISCLOSURE.md`.

| Source asset | Used for |
|---|---|
| `visual-subset-male-cns-v1.0.npz` | 19,267-neuron signed weight submatrix, CSR |
| `connectome-signed-male-cns-v1.0-traced.npz` | whole connectome, 165,122 neurons — offline analysis only |
| `temporal_snr.py`, `temporal_readout.py` | prior spike-timing measurements |
| `neural_readout.py` | 40 descending-neuron readout |

Derived `.npz` / `.npy` artifacts are **caches**. Safe to delete, rebuilt on the next run.
Rebuild explicitly whenever weight construction or subset extraction changes — a stale cache
silently preserves the old parameters, which is the failure mode most likely to produce a
plausible wrong answer.

## Network subset

| Quantity | Value |
|---|---|
| Subset neurons | 19,267 |
| Subset edges | 829,322 |
| LPLC2 neurons | 185 |
| LC4 neurons | 126 |
| DNp01 neurons | 2 |
| Integration step | 0.5 ms |

## `data/measurement.json`

The primary record. Written by `scripts/measure_final.py`.

| Section | Contents |
|---|---|
| `meta` | subset sizes, step, which script generated it, `quick` flag |
| `published` | literature targets used for comparison |
| `response_surface` | DNp01 response vs measurement window; each row has `window_ms`, `dnp01_spikes`, `ceiling`, `saturated` |
| `window_finding` | unsaturated and saturated window lists, `boundary_ms`, the statement |
| `attribution` | structural input share per type, `model_percent` vs `published_percent`, `divergence` |
| `causality` | spikes after removing LPLC2 / LC4 / both output edges, plus the reachability guard |
| `drive_sweep` | rows of `fraction`, `neurons_driven`, `lplc2_spikes`, `dnp01_spikes`, `first_spike_ms`; `dnp01_values`; `invariant`; `statement` |
| `reproducibility` | per-seed trials, `spread`, `latency_spread_ms`, `reproducible`, `note` |
| `verdict` | booleans: `stimulus_reaches_network`, `magnitude_invariant`, `anatomical_input_required`, `saturation_escapes_in_short_window`, `saturated_in_long_window` |
| `conclusion` | prose, robust finding first then negative finding |

### `causality` is a guard, not a result

`stimulus_reaches_network` must be `true` or the whole measurement is invalid: it confirms
zero drive yields 0 spikes and driven input yields 194. `scripts/test_all.py` fails the run if
this guard is not satisfied, because a dashboard full of numbers derived from an unreachable
stimulus looks completely normal.

## Supporting files

| File | Contents |
|---|---|
| `response-surface.json` | the response surface, separate from the main record |
| `transient.json` | transient response trace |
| `ablation.json` | ablation results |
| `dnp01-drivers.json` | which populations drive DNp01 |
| `latency-sweep.json` | first-spike latency across the sweep |

## Exported payload

`scripts/export_static.py` writes `dashboard/public/api/` and `dashboard/public/data/`:

- `api/experiment.json` — the same view the API serves, wrapped in the envelope
- `api/measurement.json` — the full record
- `data/*.json` — the supporting files

The dashboard reads `/api/experiment.json` first and falls back to `/api/experiment`. A static
build is therefore self-contained, and `bun run dev` needs no Python process.

## Honesty rules encoded in the data

- **Unmeasured is `null`, never `0`.** A zero reads as a measurement of nothing; `null` reads as
  nothing measured. `scripts/test_serve.py` asserts this.
- **Negative findings are stored, not tidied.** `magnitude_invariant: true` is a real result. If a
  future edit makes it `false`, that is a change to the simulation and must be visible in a diff,
  not absorbed in the view layer.
- **The verdict is derived from data, not typed in.** The "answer: no" badge renders from
  `verdict.magnitude_invariant`.

## Live camera values are not in `data/`

Motion energy and predicted spike times from a webcam are computed in the browser and are never
written to disk. They are illustrative of the encoder, not measurements, and the interface labels
them as such. Mixing them into `measurement.json` would imply they came from the same simulation.

## Related

- [[API]] — endpoints over these files
- [[Experiments]] — what each measurement means
- [[Architecture]] — where each file is produced in the pipeline