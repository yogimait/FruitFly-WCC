# Problem Statement

Track: **Agentic AI**. Tracks are areas, not briefs — this is our own problem statement.

## The problem

An AI agent that senses the world has to make a decision on every observation. Today that decision goes to a large language model: a network round-trip, tens of milliseconds to seconds of latency, and tens of watts. That is affordable on a laptop. It is not affordable on a drone, a hearing aid, a security camera, or a wearable, and on those devices the network connection may not exist at all.

The usual answer — "use a small CNN instead of an LLM" — helps, but it inherits the same structure: a trained network, evaluated frame by frame, burning power continuously to answer a question that is usually "nothing is happening."

The escape reflex of a real fly answers that question for about **19 milliseconds**, using ~185 neurons, with no trained weights and no network call.

## Why it is a real gap, not a synthetic one

| Evidence | Source |
|---|---|
| 97.5% of visual input to the descending neuron that triggers escape comes from just two cell types (LPLC2, LC4) | Card & von Reyn; PLOS Biol 2025 |
| **The timing of a single spike** in that neuron decides short vs long escape — an ~8 ms behavioural difference | Card; Ache et al. 2019 |
| Total escape sensory latency: **19 ms** | Ache et al. 2019, *Curr Biol* |
| LPLC2 achieves ultra-selectivity through **radial motion opponency**, not rate coding | Klapoetke et al. 2017 |

The second row is the argument. In the real animal, *when* the neuron fires changes the behaviour. Any readout that discards spike timing — which is what averaging over a window does — throws away the part that matters.

## What we build

A measurement harness. It drives the real LPLC2 → DNp01 pathway from the MaleCNS v1.0 connectome with **contrast-onset timing** instead of Poisson rate, reads the descending-neuron response, and reports the first-spike latency next to the published 19 ms.

We are not claiming a product. We are testing whether a published, connectome-accurate spiking model reproduces a published physiological result, and reporting what happens either way.

## Who it is for

Two honest answers, not one flattering one:

- **Primary: us.** We want to understand how a spiking network responds to stimuli. The project exists because this question is worth answering, not because a market was identified.
- **Secondary: anyone building an always-on sensor.** The narrow technical result — a cheap local layer that decides *whether* an expensive layer needs waking — is the reusable idea. We cannot demonstrate that this week, and we do not claim to.

## Claims and non-claims

Stated up front so nothing is discovered on stage (`AGENTS.md` §6).

**We claim:**
- A connectome-accurate spiking model can be driven by stimulus timing and its output measured against real electrophysiology.
- Neuron selection is justified by published anatomy, not by an arbitrary threshold: the backward-from-output rule and the empirical anatomy agree independently.
- Results are reported as measured, including when they fail the pre-registered checks.

**We do not claim:**
- **Not reflex-grade.** A 1–2 s simulation step is ~50× slower than real escape latency. This is a measurement tool.
- **Not a product.** No user, no deployment target, no market.
- **Not learning.** No weights update anywhere in the pipeline.
- **Not retinal.** Stimulus enters at the lobula columnar; retinal and lamina processing are excluded. We therefore predict a latency *below* 19 ms and say why.
- **Not neuromorphic hardware.** We run on CPU. "Milliwatt" describes the eventual platform, never what we ran.

## Honest position on the hackathon

This is a learning project with a realistic ceiling of roughly 50–60 out of 100. It will not win the ₹50,000 against 2,700 entries. That was assessed and accepted before the build started, in exchange for working on something with no competitor at the hackathon.

Judged as a research exhibit, the biology is real and the comparison is falsifiable. That is the case being made.

Related: [[Home]] · [[Biological-Reference]] · [[Architecture]] · [[Roadmap]]