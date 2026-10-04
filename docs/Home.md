# Fruitfly-WCC

Hackathon entry for **WCC Launchpad 30** — 4 Oct 2026 10:00 IST → 5 Oct 2026 14:00 IST. Solo, Agentic AI track.

Spiking-neural-network perception: a descending-neuron-rooted subset of the male fruitfly connectome, driven by spike **timing** instead of spike **rate**, measured against a baseline.

## Status

Pre-event. Scaffolding and documentation only — core pipeline code is written in-window per organiser Rule 1.

## Scope Decision

**Chosen: temporal coding over a descending-neuron-rooted subset.**

Three candidate directions were considered at the first design checkpoint:

| Direction | What it fixes | Cost |
|---|---|---|
| 1. Unpinned drive regime | Saturation in the current 19k subset | Setup hours we do not have |
| 2. Scored task with ground truth | Makes "better than random" a number | No physical environment to film |
| 3. **Temporal coding** | **Rate saturation — the root cause** | **Deepest learning payoff** |

Direction 3 was chosen because rate saturation is the underlying blocker: rate coding caps how much a spike can carry, so no amount of extra neurons fixes it. Spike *timing* carries strictly more information per spike.

**Whole-connectome live simulation was rejected:** 165,122 neurons and ~40M spikes per step implies 40–80 s per decision on CPU. That yields ~40 decisions across the entire 30-hour event — no loop, no demo. Worse, adding 146k neurons to an already-saturated recurrent network risks *worsening* saturation, which is the exact problem being fixed.

**Neuron selection rule (chosen): backward from the output.** Start from the 40 descending neurons — the only directly readable layer — and trace back only what feeds them. Smallest network that still produces a decision.

**Why not the alternatives:** the full 165,122-neuron connectome and the ~95,200-neuron anatomical visual chain stay available for *offline analysis* on disk. The live loop uses only the subset that measurably carries signal.

## Architecture (proposed, not implemented)

The proposed flow, unchanged in shape from the source simulation but with timing-sensitive encoding:

```
frame → 8x8 luminance grid → spike-train drive (precise timing, not Poisson rate)
      → LIF subset (connectome weights) → 40 descending neurons
      → temporal readout (latency / onset / first-spike) → decision
```

The frozen research layers (weight construction, LIF dynamics) are not modified. Only the *input encoding* and the *readout* change.

## Documentation

| Note | Contents |
|---|---|
| [[Architecture]] | Component boundaries, data flow, what is frozen vs new |
| [[Experiments]] | Saturation sweep, separability measurement, temporal results |
| [[Roadmap]] | In-window build plan, cut list, future work |
| [[Problem-Statement]] | Problem evidence, target user, claims and non-claims |

## Rules

`AGENTS.md` at repo root. Note especially §1 (hackathon constraint — no core code before 10:00) and §6 (numerical honesty).

## Provenance

Code and data derived from `D:\Projects\timepass\fruitfly`. Full listing in `DISCLOSURE.md`.

Related: [[Working-Style]]