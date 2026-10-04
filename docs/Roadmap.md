# Roadmap

## Pre-event, complete (before 10:00 IST 4 Oct)

Core pipeline code is deliberately absent — organiser Rule 1.

- [x] Scope decision and rejection rationale — `docs/Home.md`
- [x] Published reference targets and pre-registered falsification criteria — `docs/Biological-Reference.md`
- [x] Architecture and stated compromises — `docs/Architecture.md`
- [x] Project rules incl. numerical honesty — `AGENTS.md`
- [x] Disclosure skeleton — `DISCLOSURE.md`
- [x] React dashboard scaffold, builds clean, dev server verified

## Blocking issue — must be fixed before further experiments

Experiment 4 found that the simulator delivers external drive along the driven neuron's
**outgoing** edges. Injecting drive at LPLC2's matrix position therefore never places LPLC2's
membrane state in the causal path, so experiments 2–4 measured the network's response to a
synthetic input port rather than LPLC2's response to a stimulus.

Two changes, in this order, and the second is a guard that should have existed from the start:

1. **Drive upstream of LPLC2** — through the lobula plate (13,595 units) or the full lobula
   columnar — so LPLC2 must actually fire for the signal to reach DNp01.
2. **Assert LPLC2 is in the causal path before measuring.** Silence LPLC2 and require the
   downstream response to change. If it does not, abort rather than report a number.

Until both are in place, treat experiments 2–4 as method development, not as results.

## In-window plan — complete

Hours are build time, not wall clock. The event runs 30 hours; the work fits in ten.

| Block | Deliverable | Status |
|---|---|---|
| 0 | Frozen dynamics harness + response surface measurement | **done** — [[Experiments]] §1 |
| 1 | Contrast-onset encoder: frame → precisely-timed spike train | **done** — `looming.py`, `spike-encoder.ts` |
| 2 | Drive the lobula plate, measure DNp01 first-spike latency | **done** — 8.00 ms |
| 3 | Seed trials | **done** — spread 0.00 ms, deterministic |
| 4 | Escape saturation | **done** — window-length artefact, not drive |
| 5 | Angular-size sweep for a peak near 42° | **not run** — separability was a precondition and it failed |
| 6 | Separability above noise floor | **done** — failed; see [[Experiments]] |
| 7 | Dashboard wired to measured JSON | **done** |
| 8 | Backend, tests, docs | **done** — [[API]], [[Testing]] |
| 9 | Live camera stimulus with encoder raster | **done** |
| 10 | Writeup, disclosure, demo video | **done** |

**Block 6 was the kill switch.** Separability above the noise floor did not hold, so the angular-
size sweep that depended on it (block 5) was never run. Reporting that plainly was worth more
than a curve fitted to noise.

**Measurement window is a first-class experimental parameter.** DNp01 is unsaturated at or below
300 ms and pinned from 400 ms, so every measurement records the window it used.

**The kill criteria are the point.** An experiment that cannot fail proves nothing, and a null
result reported plainly is worth more than a passing number obtained by tuning.

## Cut list, decided in advance

Agreed not to be revisited mid-build:

- No login, no settings page, no policy editor
- No whole-connectome live simulation
- No learning, no reward modulation, no STDP
- No event-camera input
- No mobile layout
- No database beyond JSON files in `data/`

## Honest limits to state in the writeup

Per `AGENTS.md` §6, name these before a judge does:

1. **The response is invariant to stimulus magnitude** and does not require LPLC2 or LC4. This is
   the central negative result, and it means this network cannot support a decision as built.
2. **The live browser raster is an encoder prediction, not neural output.** No LIF integration
   runs in the browser. The interface states this on screen.
3. Stimulus enters at the lobula columnar, so retinal and lamina processing are excluded.
4. Nothing learns. No weights update anywhere in the pipeline.
5. The connectome weights are real and published; the stimulus is synthetic.
6. Dynamics are deterministic — a 0.00 ms seed spread means no seed noise, not a robust result.
7. The camera noise floor is measured against synthetic clips, not real hardware.

## Future work — write it, do not build it

- **Put the stimulus upstream of LPLC2.** The causal-path defect above is still open. Injecting at
  the lobula plate rather than at LPLC2's matrix position would make the anatomical input
  genuinely necessary, and would test whether invariance is an artefact of where drive enters.
- **Temporal code at the retina.** Removing the largest compromise by running contrast onset
  through a real lamina.
- **Reward-modulated plasticity.** Everything is currently frozen.
- **Event-camera input.** Fires on change rather than sampling, matching the encoder built here.
- **The full 95,200-neuron visual chain.** On disk, feasible offline; would let the neuron
  selection be validated rather than assumed.

## Related

[[Home]] · [[Architecture]] · [[API]] · [[Data-Model]] · [[Testing]] ·
[[Biological-Reference]] · [[Experiments]]