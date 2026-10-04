# README — Fruitfly-WCC

WCC Launchpad 30 entry. A measurement harness for the fruitfly escape reflex: does spike
**timing** carry stimulus information that spike **rate** cannot, on the real LPLC2 → DNp01
pathway of the male *Drosophila* connectome?

## The result

**Robust finding.** DNp01 saturation is a *window-length* artefact, not a drive-strength one.
It escapes its refractory ceiling in windows up to 300 ms and is pinned from 400 ms.

**Negative finding.** Stimulus magnitude is not recoverable from this readout. DNp01 returns
5 spikes whether 67 lobula plate neurons are driven or 6,719 — invariant across a 100× range —
and its output does not change when LPLC2 and LC4 are silenced, the two types carrying 97.5%
of the published visual input to the giant fiber.

**Structural validation.** The connectome reproduces the published attribution of giant-fiber
input: LPLC2 41.4% / LC4 54.2% by signed weight, against a published 52.2% / 45.2%.

The discrepancy is between the connectome and the physiology the model reproduces, not in the
connectome itself. Full data and the reasoning in [`docs/Experiments.md`](docs/Experiments.md).

## Run it

The Python side needs the source project's virtualenv, which holds numpy, scipy and pandas.
No new Python dependencies.

**To just view the dashboard** — no server, no Python running:

```powershell
cd dashboard
bun install
bun run dev
```

That is enough. The measurement was exported to `dashboard/public/api/` and `bun run dev`
serves those static files, exactly as a deployed build does.

**To re-run the measurement** after changing anything in `scripts/`:

```powershell
$py = "D:\Projects\timepass\fruitfly\.venv\Scripts\python.exe"

# 1. self-checks (fast)
& $py scripts\neural_core.py    --test
& $py scripts\looming.py        --test
& $py scripts\upstream_drive.py --test

# 2. run all checks, including the measurement:  ~10 s
& $py scripts\test_all.py

# 3. copy the fresh measurement into dashboard/public/api
& $py scripts\export_static.py
```

`scripts/serve.py --port 8768` is an **optional** way to browse the data files over HTTP. It is
not required for the dashboard, which reads the static export.

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
| `scripts/serve.py` | Optional static HTTP viewer for the data files. Not needed by the dashboard. Uses the project response envelope. |
| `scripts/verify_dashboard.py` | Asserts the UI renders measured values, not placeholders. |
| `data/measurement.json` | The measurement record. Every dashboard number traces here. |
| `dashboard/` | React 19 + Vite 8 + Tailwind 4, three.js fly, Recharts. |
| `docs/` | [Experiments](docs/Experiments.md), [Biological-Reference](docs/Biological-Reference.md), [Architecture](docs/Architecture.md), [Problem-Statement](docs/Problem-Statement.md), [Roadmap](docs/Roadmap.md). |
| `AGENTS.md` | Project rules. §1 hackathon constraint, §6 numerical honesty. |
| `DISCLOSURE.md` | Organiser Rule 4 compliance: pre-event vs in-window work. |

## Honest limits

- **Not reflex-grade.** A 1–2 s simulation step is ~50× slower than the real 19 ms escape
  latency. This is a measurement tool, not a flight controller.
- **Not a product.** No user, no deployment target.
- **Not learning.** No weights update anywhere in the pipeline.
- **Stimulus enters at the lobula columnar**, not the retina, so retinal and lamina processing
  are excluded.
- **No retinotopy.** The subset annotations carry no spatial information about LPLC2 beyond
  `somaSide`, so the neuron-to-cell mapping is a stated convention, not anatomy.
- **The central hypothesis was never validly tested.** Experiments 2–4 were confounded by
  driving LPLC2's matrix position, which propagates along its outgoing edges without making
  LPLC2 spike. That is diagnosed and recorded rather than quietly dropped.

Four of our own analyses produced false positives before correction, all recorded in
[`docs/Experiments.md`](docs/Experiments.md) §Corrections log.

## Sources

MaleCNS v1.0 connectome. LIF constants per Shiu et al. 2024 (*Nature* 634:210–219). Published
targets per Ache et al. 2019 (*Curr Biol*), von Reyn et al. 2017, Klapoetke et al. 2017 (*eLife*),
and Card & von Reyn / *PLOS Biology* 2025. Full citations with values in
[`docs/Biological-Reference.md`](docs/Biological-Reference.md).