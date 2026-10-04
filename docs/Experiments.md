# Experiments

What we measure, what the values mean, and what each result implies. Every number here traces
to a file in `data/` — see `AGENTS.md` §6.

## Experiment 1: response surface of the LPLC2 → DNp01 pathway

**Question.** Is there any drive configuration in which DNp01 escapes its refractory ceiling?

This is the question the whole project rests on. The source project reported DNp01 pinned at
239/240 spikes for all pool-wide drive rates 10–50 Hz, and concluded rate-based readout
cannot resolve the stimulus. If that holds universally, temporal coding has nothing to
recover and the project is over before it starts.

**Harness.** `scripts/measure_response_surface.py` → `data/response-surface.json`
Self-check: `scripts/neural_core.py --test`

**Axes swept.** Drive sparsity (fraction of LPLC2 driven), drive onset (when input arrives),
window length.

**Result — 24 measurements.**

| Sweep | Finding |
|---|---|
| Sparsity, 0.3 s window | **Pinned at 120/120 for every fraction**, from all 185 LPLC2 neurons down to 1. Sparsity does not help. |
| Onset, single input step | **Pinned at 119/120 regardless of onset.** Delaying input to 80 ms still yields 87 spikes in the remaining window. |
| Window length, continuous drive | **Escapes below ~150 ms.** 5 ms → 1/2 spikes. 20 ms → 7/8. 50 ms → 19/20. 100 ms → 39/40. **200 ms → 79/80 (saturated). 300 ms → 119/120 (saturated).** |

### Conclusions

1. **Saturation is a window-length artefact, not a drive-strength artefact.** Making the
   stimulus weaker does nothing; making the measurement window shorter does everything.
   That is exactly the diagnosis rate coding forces on you — integrate over a long window and
   you can only see the ceiling.

2. **The unescaped regime is 5–100 ms.** This is where timing lives. A fly's real escape
   latency is **19 ms** (Ache et al. 2019) — comfortably inside the window where the network
   is *not* saturated. The published figure and the model's unescaped regime agree.

3. **First-spike latency is measurable and behaves correctly.** Single-step drive at onset 0
   gives DNp01 first spike at **6.0 ms**; onset 80 ms gives **86.0 ms**. The offset is exactly
   80 ms, i.e. the output faithfully tracks input timing with a fixed ~6 ms internal delay.

4. **The 6 ms internal delay is far below the 19 ms published value.** Our stimulus enters at
   the lobula columnar, so retinal and lamina processing are excluded — exactly as
   `docs/Architecture.md` predicts. This is the predicted direction of the discrepancy, not a
   contradiction.

### What this changes

The original plan assumed saturation would have to be *escaped* by tuning the drive. It does
not have to be escaped at all: **just measure in a short window.** That is a simpler and more
honest result than finding an exotic drive regime, and it is the same insight that motivates
temporal over rate coding — a short window preserves when spikes happened.

## Experiment 2: latency vs stimulus size

**Status.** Not yet run. Depends on the contrast-onset encoder (block 1 of [[Roadmap]]).

Sweep angular size, measure DNp01 first-spike latency in a 50 ms window, and test whether the
response peaks near the published 42° threshold (von Reyn 2017).

**Pre-registered failure conditions** ([[Biological-Reference]] §Falsification criteria):

- fails if the peak lands on a sweep boundary, meaning the range was too narrow
- fails if latency is not reproducible across seeds (spread ≥ 1 ms)
- reported as saturated even when passing if the window is too long

## Experiment 3: stimulus separability

**Status.** Not yet run.

Pairwise distance between descending-neuron responses to distinct stimuli, above the noise
floor. The source project measured ~0–1.2 Hz differences under rate coding; temporal
readout in a short window is the hypothesis under test.

**Fails** if the distance is indistinguishable from a random pair.

## Corrections log

Recording mistakes found by measurement rather than by reading, because each one would have
produced a plausible but wrong claim:

| Mistake | Consequence | Fix |
|---|---|---|
| Saturation ceiling taken as one spike per *step* (600) | Reported every regime as unsaturated when all were pinned | Ceiling is one spike per *refractory period* → 120 in a 0.3 s window |
| Assumed dense LPLC2 drive would saturate DNp01, asserted it in the self-check | Self-check failed on a correct simulator | Measured the surface first, then asserted what was observed |
| Source `load_subset()` uses cwd-relative paths | Harness broke when run from its own directory | Resolve caches against the source project root |

Related: [[Home]] · [[Architecture]] · [[Biological-Reference]] · [[Roadmap]]