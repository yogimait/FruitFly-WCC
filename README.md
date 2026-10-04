# README — Fruitfly-WCC

WCC Launchpad 30 entry. A measurement harness for the fruitfly escape reflex: does spike
**timing** carry stimulus information that spike **rate** cannot, on the real LPLC2 → DNp01
pathway of the male *Drosophila* connectome?

## The result

**Question.** Can spike timing carry stimulus information that spike rate cannot?

**Answer: no — not in this network.** Three measurements, all reproducible:

**Robust finding.** DNp01 saturation is a *window-length* artefact, not a drive-strength one.
It escapes its refractory ceiling in windows up to 300 ms and is pinned from 400 ms.

**Negative finding.** Stimulus magnitude is not recoverable from this readout. DNp01 returns
5 spikes whether 67 lobula plate neurons are driven or 6,719 — invariant across a 100× range —
and its output does not change when LPLC2 and LC4 are silenced (97 / 97 / 96 spikes against a
control of 97), the two types carrying 97.5% of the published visual input to the giant fiber.

**Structural validation.** The connectome reproduces the published attribution of giant-fiber
input: LPLC2 41.4% / LC4 54.2% by signed weight, against a published 52.2% / 45.2%.

First DNp01 spike lands at **8.00 ms** against a published **19 ms**, spread 0.00 ms across
seeds. The discrepancy is between the connectome and the physiology the model reproduces, not in
the connectome itself.

The negative result is the deliverable: a saturated, magnitude-invariant, input-independent
readout cannot support a decision, and adding neurons would not fix it. Full data and reasoning
in [`docs/Experiments.md`](docs/Experiments.md).

## Run it

The Python side needs the source project's virtualenv, which holds numpy, scipy and pandas.
No new Python dependencies. The dashboard needs [bun](https://bun.sh).

**To just view the dashboard** — no server, no Python running:

```powershell
cd dashboard
bun install
bun run dev
```

That is enough. The measurement was exported to `dashboard/public/api/` and `bun run dev`
serves those static files, exactly as a deployed build does.

Press **use camera** to drive the stimulus from your webcam. The live raster is the *encoder's*
predicted input timing, not a simulation of the 19,267 neurons — the interface says so on screen.

**To run the measurement and the full test suite:**

```powershell
$py = "D:\Projects\timepass\fruitfly\.venv\Scripts\python.exe"

# everything: 9 checks, ~10 s
& $py scripts\test_all.py

# copy a fresh measurement into dashboard/public/api
& $py scripts\export_static.py
```

**To serve the API instead of the static export** — optional, useful while iterating on a
measurement without rebuilding the dashboard:

```powershell
& $py scripts\serve.py --port 8768
```

**To run the browser verifiers**, with a dev server on 5173 (or `bun run preview --port 5177`
for `verify_dashboard.py`):

```powershell
& $py scripts\verify_dashboard.py       # rendered values, accessibility, camera path
& $py scripts\verify_camera_tuning.py   # noise must be silent, real motion must drive spikes
& $py scripts\measure_noise_floor.py    # measures the noise floor, sweeps candidate thresholds
```

Details in [`docs/Testing.md`](docs/Testing.md).

### Deploying

`dist/` is a plain static site. Any host works:

```powershell
cd dashboard
bun run build
```

Then deploy `dashboard/dist` to Vercel, Netlify, GitHub Pages, or any static host. There is no
server, no Python, and no GPU on the deployed host — the simulation runs offline and its output
ships as JSON. Judges should be told this plainly: **the recorded measurement is served, not
recomputed.**

To test the deployable artifact locally:

```powershell
python -m http.server 8080 -d dashboard\dist
```

## What is where

| Path | Contents |
|---|---|
| `scripts/neural_core.py` | Frozen LIF dynamics with deterministic spike-train input. Constants imported from the source project, never copied. |
| `scripts/looming.py` | Analytic looming-disk renderer and the contrast-onset encoder. |
| `scripts/upstream_drive.py` | T4/T5 motion drive, one stage upstream of LPLC2. Carries the reachability guard. |
| `scripts/measure_final.py` | The measurement run. Produces everything the dashboard renders. |
| `scripts/measure_*.py` | Response surface, transient, latency sweep, noise floor. |
| `scripts/serve.py` | Optional HTTP API over the data files. Stdlib only, runs no simulation. |
| `scripts/test_all.py` | The nine-check suite. One command. |
| `scripts/test_serve.py` | Backend tests: envelope, view mapping, null handling, routes. |
| `scripts/verify_*.py` | Browser verifiers for the rendered UI and the camera path. |
| `scripts/fake_video.py` | Shared Y4M fake-webcam clips for the browser tests. |
| `data/measurement.json` | The measurement record. Every dashboard number traces here. |
| `dashboard/` | React 19 + Vite 8 + Tailwind 4, three.js fly, Recharts. |
| `docs/` | [Experiments](docs/Experiments.md), [Architecture](docs/Architecture.md), [API](docs/API.md), [Data-Model](docs/Data-Model.md), [Testing](docs/Testing.md), [Biological-Reference](docs/Biological-Reference.md), [Problem-Statement](docs/Problem-Statement.md), [Roadmap](docs/Roadmap.md). |
| `AGENTS.md` | Project rules. §1 hackathon constraint, §6 numerical honesty. |
| `DISCLOSURE.md` | Organiser Rule 4 compliance: pre-event vs in-window work. |

## Honest limits

- **The central result is negative.** Stimulus magnitude is not recoverable from this readout,
  and the anatomical input is not required. As built, this network cannot support a decision.
- **The live browser raster is an encoder prediction, not neural output.** No LIF integration
  runs in the browser.
- **The causal path upstream of LPLC2 is unresolved.** Experiments 2–4 were confounded by driving
  LPLC2's matrix position, which propagates along its outgoing edges without making LPLC2 spike.
  Diagnosed and recorded in [`docs/Roadmap.md`](docs/Roadmap.md), not quietly dropped.
- **Not reflex-grade.** A 1–2 s simulation step is ~50× slower than the real 19 ms escape
  latency. This is a measurement tool, not a flight controller.
- **Not a product.** No user, no deployment target.
- **Not learning.** No weights update anywhere in the pipeline.
- **Stimulus enters at the lobula columnar**, not the retina, so retinal and lamina processing
  are excluded.
- **No retinotopy.** The subset annotations carry no spatial information about LPLC2 beyond
  `somaSide`, so the neuron-to-cell mapping is a stated convention, not anatomy.
- **Deterministic dynamics.** A 0.00 ms seed spread means no seed noise, not a robust result.
- **The camera noise floor is synthetic**, measured against generated clips rather than real
  hardware.

Four of our own analyses produced false positives before correction, all recorded in
[`docs/Experiments.md`](docs/Experiments.md) §Corrections log.

## Sources

MaleCNS v1.0 connectome. LIF constants per Shiu et al. 2024 (*Nature* 634:210–219). Published
targets per Ache et al. 2019 (*Curr Biol*), von Reyn et al. 2017, Klapoetke et al. 2017 (*eLife*),
and Card & von Reyn / *PLOS Biology* 2025. Full citations with values in
[`docs/Biological-Reference.md`](docs/Biological-Reference.md).