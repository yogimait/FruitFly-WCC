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

Populated as work proceeds, with commit references.

| Item | Commit | Notes |
|---|---|---|
| — | — | _No in-window work recorded yet._ |

## External assets

| Asset | Source | Licence / note |
|---|---|---|
| MaleCNS v1.0 connectome | Public dataset (FlyWire / neuPrint) | Structure only; weights unmodified |
| Shiu et al. 2024, *Nature* 634:210-219 | Published parameters | LIF constants, cited |
| Kakaria & de Bivort 2017; Jürgensen et al. 2021; Lazar et al. 2021; Paul et al. 2015 | Published parameters | LIF constants, cited |

No third-party code is vendored. Dependencies are those already installed in the source project's `.venv`.