# Fruitfly-WCC

Hackathon entry for **WCC Launchpad 30** — 4 Oct 2026 10:00 IST → 5 Oct 2026 14:00 IST. Solo, Agentic AI track.

Spiking-neural-network perception: a descending-neuron-rooted subset of the male fruitfly
connectome, asked whether spike **timing** carries what spike **rate** cannot.

## Status

In-window. Experiment complete and measured. Dashboard, backend, tests and docs are implemented;
see [[Roadmap]] for what remains out of scope.

## The question, and the answer

**Can spike timing see what spike rate cannot? No — not in this network.**

Three measurements, all reproducible:

| Finding | Evidence |
|---|---|
| Saturation is a **window-length** artefact, not a drive artefact | DNp01 escapes its refractory ceiling up to a 300 ms window and is pinned from 400 ms |
| The response is **invariant to stimulus magnitude** | 5 spikes whether 67 or 6,719 lobula plate neurons are driven — a 100× range |
| The anatomical input is **not required** | Removing LPLC2 output, LC4 output, or both leaves DNp01 at 97 / 97 / 96 spikes vs a control of 97 |

The last two are negative results and are reported as such. LPLC2 and LC4 carry 97.5% of the
published giant-fibre visual input, yet neither is necessary in the simulated pathway, and
stimulus magnitude does not move the readout at all. Structural attribution agrees on which
populations matter but disagrees on the balance: LPLC2 **41.4%** / LC4 **54.2%** here, against a
published **52.2%** / **45.2%**.

First DNp01 spike lands at **8.00 ms** against a published **19 ms**, with a spread of 0.00 ms
across seeds. Deterministic dynamics mean that spread is the absence of seed noise, not evidence
of a robust result.

## Why this matters anyway

The negative result is the deliverable. Rate coding caps how much a spike can carry, so a
saturated, magnitude-invariant, input-independent readout cannot support a decision — and the
fix is not more neurons. Adding 146k neurons to an already self-sustained recurrent network
risks worsening exactly the saturation being investigated.

## What is actually implemented

```
camera or synthetic disk → luminance grid → contrast-onset encoder → LIF subset (19,267 neurons)
  → 40 descending neurons → readout (rate, first-spike latency)
```

The stimulus can be **live** from a webcam. The **measurement is recorded** and served as data.
The live raster in the browser is the *encoder's* predicted input timing, not a simulation of the
19,267 neurons, and the interface says so on screen.

## Documentation

| Note | Contents |
|---|---|
| [[Architecture]] | Component boundaries, data flow, frozen vs new, stated compromises |
| [[Data-Model]] | Every file in `data/`, its provenance, and the API contract |
| [[API]] | Backend endpoints, response envelope, error codes |
| [[Testing]] | The nine automated checks, the browser verifiers, and how to run them |
| [[Experiments]] | What we measure, what each result means |
| [[Biological-Reference]] | Published targets (19 ms, 42°, 97.5%) and falsification criteria |
| [[Problem-Statement]] | Problem evidence, target user, claims and non-claims |
| [[Roadmap]] | Cut list and future work |

## The experiment in one line

Drive the lobula columnar pool with contrast-onset **timing**, measure the **DNp01 first-spike
latency**, and test whether the response varies with **stimulus magnitude** — the thing a
decision would actually need.

Related: [[Working-Style]]