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

All of the following was written after 10:00 IST on 4 Oct 2026. Commit hashes are in
`git log --oneline`.

### Core product — measurement pipeline

| Item | Notes |
|---|---|
| `scripts/neural_core.py` | Frozen LIF dynamics with deterministic spike-train input. Imports constants from the source project rather than copying them, so they cannot silently diverge. Self-check asserts the pathway exists and that unstimulated networks stay silent. |
| `scripts/looming.py` | Contrast-onset encoder. Analytic looming-disk renderer. Self-check `--test`. |
| `scripts/upstream_drive.py` | T4/T5 motion drive, one stage upstream of LPLC2. Carries the reachability guard. |
| `scripts/measure_final.py` | The measurement run. Produces `data/measurement.json`, which is every number the dashboard shows. |
| `scripts/measure_response_surface.py` | Experiment 1. Sweeps drive sparsity, onset and window length. |
| `scripts/measure_latency.py`, `scripts/measure_transient.py` | First-spike latency and cumulative recruitment across the sweep. |
| `scripts/ablate_recurrence.py` | Four arms: control, feed-forward, no self-loops, rate-vs-timing matched. |
| `scripts/what_drives_dnp01.py` | Structural and causal attribution of input to DNp01 against the published 52.2% / 45.2%. |
| `scripts/probe_response.py`, `scripts/probe_causal_window.py`, `scripts/inspect_*.py` | Interactive probes and read-only inspection. Measurement only. |
| `data/*.json` | Six measured datasets: response surface, latency sweep, transient, ablation, DNp01 drivers, measurement. |

**Modified from source:** none. `neural_core.py` reimplements the delivery loop to accept timed
input; the constants (`DT`, `V_REST`, `V_RESET`, `V_TH`, `DECAY_M`, `DECAY_SYN`,
`REFRACT_STEPS`, `DELAY_STEPS`) are imported from `lif_escape.py`, not duplicated.

### Product surface — backend, dashboard, camera

| Item | Notes |
|---|---|
| `scripts/serve.py` | HTTP API over the data files. Python standard library only, no framework. Runs **no** simulation — it serves what `measure_final.py` wrote, so it cannot disagree with the files on disk. |
| `scripts/export_static.py` | Writes the same payload into `dashboard/public/api/`, so a static build needs no Python process. |
| `dashboard/` app | Single self-explanatory view: procedural 3D fly, recorded spike raster, headline measurements, data disclosure. React 19 + Vite 8 + Tailwind 4. |
| `dashboard/` camera path | Live webcam stimulus. Samples a 16×16 box-averaged luminance grid and applies the same contrast-onset encoder as the offline run. |
| `dashboard/src/lib/spike-encoder.ts` | The encoder model, pure and separate from rendering. Drives the live raster. |
| `media/demo.mp4` | 66 s demo. Source composition kept alongside it so it can be regenerated. |

### Verification

| Item | Notes |
|---|---|
| `scripts/test_all.py` | Nine-check suite, one command, non-zero exit on failure. |
| `scripts/test_serve.py` | Backend tests: response envelope, view mapping against the same files the server reads, unmeasured fields staying `null`, negative findings surviving the view layer, live HTTP routes. |
| `scripts/verify_dashboard.py` | Asserts the rendered UI shows measured values rather than placeholders, plus accessibility affordances and the camera path. |
| `scripts/verify_camera_tuning.py` | Noise must drive nothing; a real moving subject must drive cells and spikes. |
| `scripts/measure_noise_floor.py` | Measures the noise floor and sweeps candidate drive thresholds, so the bar is chosen from data. |
| `scripts/fake_video.py` | Shared fake-webcam clips so the floor measurement and the response test cannot drift apart. |

**Known methodological limitation, discovered in-window and not fixed:** the simulator delivers
external drive along the driven neuron's *outgoing* edges, so injecting drive at LPLC2's matrix
position does not place LPLC2's membrane state in the causal path. Experiments 2–4 therefore
measure the network's response to a synthetic input port rather than LPLC2's response to a
stimulus. Recorded in `docs/Experiments.md` §Experiment 4 and `docs/Roadmap.md`.

## Pre-event scaffolding (commit `a7fd1dc`, `caa36b8`)

Written before 10:00 IST on 4 Oct 2026. **None of this is the core product** — it is configuration, documentation, and a UI shell. The measured pipeline is built in-window.

| Item | Nature |
|---|---|
| `dashboard/` | Fresh `bun create vite` React 19 + TS scaffold, plus Tailwind 4, `class-variance-authority`, `clsx`, `tailwind-merge`, `lucide-react`. UI components composed by hand following shadcn conventions — no shadcn CLI, no copied shadcn source |
| `dashboard/` 3D | `three` + `@react-three/fiber` + `@react-three/drei` + `recharts`, added for the visualization and charts |
| `dashboard/` fly | **procedural geometry written for this project** — spheres, cylinders and planes. No third-party model, mesh, or texture file is used, so no external asset licence applies |
| `docs/Biological-Reference.md` | Literature values gathered from published sources. Contains **no measurements of our own** |
| `docs/Architecture.md`, `docs/Home.md`, `AGENTS.md` | Documentation and rules |
| `.vibe-wise/` | Learning notes. Gitignored |

No simulation, encoding, readout, or experiment code existed at this point. The three UI files
above were a shell: the measured pipeline, the API, the camera path, the tests and the video were
all built in-window.

## What the core product turned out to be

Built in-window after 10:00 IST:

1. Contrast-onset spike-train encoder, one stage upstream of LPLC2
2. Temporal readout (first-spike latency) plus rate, and the invariance test that refuted the
   original hypothesis
3. Experiment harness: response surface, drive sweep, ablation, seed trials, falsification guards
4. A backend that serves the measurement without recomputing it
5. A dashboard that displays measured values and says plainly when something was not measured
6. A live camera path that drives the same encoder from real frames

The central hypothesis — that spike timing beats spike rate — was **refuted by the measurement**.
The deliverable is that negative result, stated plainly, together with the tooling that produced
it. See `README.md` and `docs/Experiments.md`.

## External assets

| Asset | Source | Licence / note |
|---|---|---|
| MaleCNS v1.0 connectome | Public dataset (FlyWire / neuPrint) | Structure only; weights unmodified |
| Shiu et al. 2024, *Nature* 634:210-219 | Published parameters | LIF constants, cited |
| Kakaria & de Bivort 2017; Jürgensen et al. 2021; Lazar et al. 2021; Paul et al. 2015 | Published parameters | LIF constants, cited |
| GSAP 3.14.2 (CDN) | Demo video composition only | Used at render time by `media/demo-composition.html`; not a runtime dependency of the dashboard |

No third-party code is vendored. Python dependencies are those already installed in the source
project's `.venv`; no new Python package was added. Dashboard dependencies are the ones listed in
the pre-event scaffolding table above.

**Considered and rejected:** a Sketchfly/Sketchfab fruitfly model for the 3D scene. Rejected
because the licence was unspecified, the asset was not downloadable, and an iframe cannot be
tinted or bound to measured data. The fly stayed procedural, so no external asset licence
applies.