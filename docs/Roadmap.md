# Roadmap

## Pre-event, complete (before 10:00 IST 4 Oct)

Core pipeline code is deliberately absent — organiser Rule 1.

- [x] Scope decision and rejection rationale — `docs/Home.md`
- [x] Published reference targets and pre-registered falsification criteria — `docs/Biological-Reference.md`
- [x] Architecture and stated compromises — `docs/Architecture.md`
- [x] Project rules incl. numerical honesty — `AGENTS.md`
- [x] Disclosure skeleton — `DISCLOSURE.md`
- [x] React dashboard scaffold, builds clean, dev server verified

## In-window plan, roughly 10 hours

Hours are build time, not wall clock. The event runs 30 hours; the work fits in ten.

| Block | Hours | Deliverable | Status |
|---|---|---|---|
| 0 | 1 | Frozen dynamics harness + response surface measurement | **done** — [[Experiments]] §1 |
| 1 | 0.5 | Contrast-onset encoder: frame → precisely-timed spike train | next |
| 2 | 2 | Drive LPLC2, measure DNp01 first-spike latency in a 50 ms window | |
| 3 | 1.5 | Seed trials; confirm spread < 1 ms | Fails: stop, report non-reproducible |
| 4 | 1 | ~~Escape saturation~~ — solved by window length in block 0 | done |
| 5 | 1.5 | Angular-size sweep, look for peak near 42° | Fails: peak on a boundary, widen once |
| 6 | 1 | Separability above noise floor | Fails: indistinguishable from random, drop rung-3 claims |
| 7 | 1 | Wire dashboard to measured JSON | |
| 8 | 0.5 | Falsification checks as asserts (`AGENTS.md` §9) | |
| 9 | 0.5 | Writeup, disclose in-window commits | |
| 10 | 0.5 | Buffer | Submit by 8 AM, not 14:00 |

**Measurement window is now a first-class experimental parameter.** Block 0 showed DNp01 is
unsaturated below ~150 ms and pinned above ~200 ms, so blocks 2, 3 and 5 must use a window in
the 20–100 ms range. Every measurement records the window it used.

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

## Future work — write it, do not build it

These go in the writeup as the reason a judge should believe the work was heading somewhere:

- **Temporal code at the retina.** Contrast onset currently enters at the lobula columnar. Running it through a real lamina would remove the largest compromise.
- **Reward-modulated plasticity.** STDP or three-factor learning would make the network adapt rather than merely respond. Everything is currently frozen.
- **Event-camera input.** A camera that fires on change, rather than a camera that samples, matches the encoder we built and removes the frame-rate bottleneck.
- **The full 95,200-neuron visual chain.** Already on disk. Feasible offline, and it would let the neuron selection be validated rather than assumed.

## Honest limits to state in the writeup

Per `AGENTS.md` §6 and the writeup plan, name these before a judge does:

1. A 1–2 s simulation step is **not** a reflex. Real escape is ~19 ms. This is a measurement tool, not a flight controller.
2. Stimulus enters at the lobula columnar, so retinal and lamina processing are excluded.
3. Nothing learns. No weights update anywhere in the pipeline.
4. The connectome weights are real and published; the *stimulus* is synthetic.
5. Saturation is a known confound and is reported even when tests pass.

Related: [[Home]] · [[Architecture]] · [[Biological-Reference]] · [[Experiments]]