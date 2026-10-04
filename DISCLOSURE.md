# Disclosure

Organiser Rule 4: *"Templates or code you wrote earlier must be clearly disclosed."*

This file is the single source of truth for what existed before the hackathon period (before **4 Oct 2026, 10:00 IST**) and what was built during it.

## Source project

**`D:\Projects\timepass\fruitfly`** — FruitFly MaleCNS v1.0 whole-brain LIF simulation. Built by the entrant before the event. Used as the basis for this entry. Treated as read-only; not modified.

### Pre-existing assets reused

Weights and data (copied or read in place):

| Asset | Contents |
|---|---|
| `data/visual-subset-male-cns-v1.0.npz` | 19,267-neuron signed weight submatrix (CSR) |
| `data/visual-subset-male-cns-v1.0.bodyids.npy` | bodyId ordering |
| `data/visual-subset-male-cns-v1.0.meta.feather` | type / instance / superclass / somaSide / neurotransmitter / sign |
| `data/connectome-signed-male-cns-v1.0-traced.npz` | whole connectome, 165,122 neurons, 25.56M edges — **offline analysis only** |
| `data/connectome-signed-male-cns-v1.0-traced.bodyids.npy` | whole-connectome bodyId ordering |
| `data/temporal-snr-results.json` / `.csv` | prior spike-timing SNR measurements |
| `data/temporal-readout-results.json` / `.csv` | prior temporal onset readout results |

Code (reused, unmodified, or modified only as noted in the in-window section):

| File | Role |
|---|---|
| `lif_escape.py` | LIF neuron dynamics, synaptic delivery, sign convention |
| `simulate_visual_subset.py` | standalone 19,267-neuron subset simulator |
| `structured_drive.py` | image → 8x8 grid → Poisson spike rates (**modified in-window**: rate → spike-train encoding) |
| `neural_readout.py` | 40 descending-neuron readout (**modified in-window**: added temporal readout) |
| `extract_visual_subset.py` | deterministic subset extraction (method reused for the output-rooted rule) |
| `stochastic_response.py`, `temporal_snr.py`, `temporal_readout.py` | measurement harnesses reused for separability analysis |

### Known pre-existing limitation being addressed

Descending-neuron rates saturate near 400 Hz and quantize at 1.67 Hz, giving ~0–1.2 Hz differences between stimuli. The prior policy's decision mix was therefore effectively noise-driven. This was measured and documented by the source project before the event (`docs/Final-Demo.md` § Policy, `docs/Action-Policy.md` §4).

## Built during the event

| Item | Commit | Notes |
|---|---|---|
| `scripts/neural_core.py` | `pending` | Frozen LIF dynamics with deterministic spike-train input. Imports constants from the source project rather than copying them, so they cannot silently diverge. Self-check asserts the pathway exists and that unstimulated networks stay silent. |
| `scripts/measure_response_surface.py` | `pending` | Experiment 1. Sweeps drive sparsity, onset and window length. Writes `data/response-surface.json`. |
| `scripts/probe_response.py` | `pending` | Interactive probe used to find the unescaped regime. Measurement only, no assertions. |
| `scripts/looming.py` | `pending` | Contrast-onset encoder. Analytic looming-disk renderer. Self-check `--test`. |
| `scripts/measure_latency.py` | `pending` | Experiment 2. DNp01 latency and LPLC2 recruitment across stimulus size. |
| `scripts/measure_transient.py` | `pending` | Experiment 3. Cumulative LPLC2 recruitment by time bin at 2 ms resolution. |
| `scripts/ablate_recurrence.py` | `pending` | Experiment 4. Four arms: control, feed-forward, no self-loops, rate-vs-timing matched. |
| `scripts/what_drives_dnp01.py` | `pending` | Structural and causal attribution of input to DNp01 against the published 52.2% / 45.2%. |
| `scripts/inspect_subset.py`, `scripts/inspect_lplc2.py` | `pending` | Read-only inspection of constants, subset and LPLC2 metadata. |
| `data/*.json` | `pending` | 5 measured datasets: response surface, latency sweep, transient, ablation, DNp01 drivers. |
| `docs/Experiments.md` | `pending` | Experiment log, including four corrections made by measurement rather than by reading. |

**Modified from source:** none. `neural_core.py` reimplements the delivery loop to accept
timed input; the constants (`DT`, `V_REST`, `V_RESET`, `V_TH`, `DECAY_M`, `DECAY_SYN`,
`REFRACT_STEPS`, `DELAY_STEPS`) are imported from `lif_escape.py`, not duplicated.

**Known methodological limitation, discovered in-window and not yet fixed:** the simulator
delivers external drive along the driven neuron's *outgoing* edges, so injecting drive at
LPLC2's matrix position does not place LPLC2's membrane state in the causal path. Experiments
2–4 therefore measure the network's response to a synthetic input port rather than LPLC2's
response to a stimulus. See `docs/Experiments.md` §Experiment 4.

## Pre-event scaffolding (commit `a7fd1dc`, `caa36b8`)

Written before 10:00 IST on 4 Oct 2026. **None of this is the core product** — it is configuration, documentation, and a UI shell. The measured pipeline is built in-window.

| Item | Nature |
|---|---|
| `dashboard/` | Fresh `bun create vite` React 19 + TS scaffold, plus Tailwind 4, `class-variance-authority`, `clsx`, `tailwind-merge`, `lucide-react`. UI components composed by hand following shadcn conventions — no shadcn CLI, no copied shadcn source |
| `dashboard/` 3D | `three` + `@react-three/fiber` + `@react-three/drei` + `recharts`, added for the visualization and charts |
| `dashboard/` fly | `src/components/fly.tsx` is **procedural geometry written for this project** — spheres, cylinders and planes. No third-party model, mesh, or texture file is used, so no external asset licence applies |
| `docs/Biological-Reference.md` | Literature values gathered from published sources. Contains **no measurements of our own** |
| `docs/Architecture.md`, `docs/Home.md`, `AGENTS.md` | Documentation and rules |
| `.vibe-wise/` | Learning notes. Gitignored |

No simulation, encoding, readout, or experiment code has been written yet.

## What the core product will be

Built in-window after 10:00 IST:

1. Contrast-onset spike-train encoder (modifies source `structured_drive.py`)
2. Latency and separability readout (extends source `neural_readout.py`)
3. Experiment harness: angular-size sweep, seed trials, falsification checks
4. Wiring the dashboard to measured output

## External assets

| Asset | Source | Licence / note |
|---|---|---|
| MaleCNS v1.0 connectome | Public dataset (FlyWire / neuPrint) | Structure only; weights unmodified |
| Shiu et al. 2024, *Nature* 634:210-219 | Published parameters | LIF constants, cited |
| Kakaria & de Bivort 2017; Jürgensen et al. 2021; Lazar et al. 2021; Paul et al. 2015 | Published parameters | LIF constants, cited |

No third-party code is vendored. Dependencies are those already installed in the source project's `.venv`.