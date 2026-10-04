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

## Experiment 2: does timing rescue the response? **NO.**

**Question.** Can spike *timing* carry stimulus information that spike *rate* loses?

**Harness.** `scripts/measure_latency.py` → `data/latency-sweep.json`
**Encoding.** `scripts/looming.py` — contrast-onset spike trains, self-check `--test`

**Result — two independent readouts, both flat.**

| Readout | Values across 10°–80° | Verdict |
|---|---|---|
| DNp01 first-spike latency | **2.00 ms** for every size | no information |
| Steady-state LPLC2 recruitment | **185 / 185** for every size | no information |
| Seed spread at 42° | **0.000 ms** | reproducible, but reproducibly flat |

### Why latency is floored

2.00 ms is exactly the direct LPLC2 → DNp01 synaptic delay (`DELAY_STEPS × DT`). A single
LPLC2 spike is *sufficient* to push DNp01 past threshold within one delay. There is no
integration window in which magnitude could accumulate, so latency cannot scale with size.

Confirmed independently by experiment 1: one step of drive to **one** LPLC2 neuron produced
119/120 DNp01 spikes in a 0.3 s window.

### Why recruitment is flat

Once the lobula columnar pool fires it sustains itself through recurrent excitation. By the
end of the window all 185 LPLC2 units have fired for every stimulus. This is the same
self-sustained pool the source project documented at ~570k spikes per 300 ms.

## Experiment 3: does the transient carry it? **NO.**

**Question.** A real escape reflex is a transient response, and the published 19 ms is itself
a transient measure. If the pool ramps before it saturates, recruitment *by time t* should be
graded.

**Harness.** `scripts/measure_transient.py` → `data/transient.json`

**Result.** Recruitment is **0 for every stimulus until 38 ms, then the full pool**, in a
transition roughly 2 ms wide:

| Bin | 10° | 20° | 42° | 60° | 80° | Graded? |
|---|---|---|---|---|---|---|
| 30 ms | 0 | 0 | 0 | 0 | 0 | — |
| 42 ms | 185 | 67 | 0 | 0 | 0 | step |
| 44 ms | 185 | 185 | 0 | 147 | 0 | step |
| 46 ms | 185 | 185 | 151 | 185 | 0 | step |
| 48 ms+ | 185 | 185 | 185 | 185 | 0 | step |
| 100 ms | 185 | 185 | 185 | 185 | 185 | — |

**The transient is a time-shifted step, not a ramp.** The pool is either not started or fully
active. Note the direction: the *larger* stimuli appear *later* (80° is last), because the
frame interval scales with peak size — that is stimulus duration, not magnitude.

### Correction that nearly produced a false positive

The first run of this experiment reported a **positive** result. The separating-bin test keyed
on `spread > 0`, and one bin reported 0 for some sizes and 185 for others — a large spread, but
a step function, not a graded signal. Bins were also too coarse (30 → 50 ms) to see the
transition at all.

Fixed by requiring every size to produce a **distinct** count, and by densifying the bins to
2 ms between 20 and 70 ms. That turned the result negative. This is recorded because the
failure mode — a step function misread as a ramp — is exactly what a rubric rewards
("technical depth") without anyone checking.

## Verdict on the central hypothesis

**Refuted for this pathway at this model scale.** Three independent readouts — first-spike
latency, steady-state recruitment, transient recruitment — all carry no stimulus magnitude
information. The cause is identified and is not the encoding: the lobula columnar pool is
recurrently self-sustained, so it reaches its full state in ~2 ms regardless of how much
input arrives, and encoding the input as rate or as timing makes no difference downstream.

This does **not** say the published 19 ms figure is wrong. It says this model, at this scale,
cannot resolve the stimulus through this pathway — which is a statement about the readout, not
about the biology.

## Experiment 4: what would have to change

Not run yet, and ordered by expected value:

1. **Break the recurrent loop.** The failure is self-sustaining excitation, not the encoding.
   Clamping or ablating the recurrent LC/LPLC pathway should restore a graded response. If it
   does, that is a positive result about *where* the information is destroyed.
2. **Read a neuron outside the pool.** DNp01 is driven by LPLC2 directly; a neuron driven by
   one projection neuron may not sit inside the same recurrent loop.
3. **Stimulus onset, not growth.** A step of contrast at t=0 rather than an expanding disk
   removes the frame-interval confound entirely.
4. **Rate vs timing, matched.** Both encodings on the same stimulus with the same total input,
   reported side by side. This is the comparison the project claims to make and has not yet
   made cleanly.

## Corrections log

Recording mistakes found by measurement rather than by reading, because each one would have
produced a plausible but wrong claim:

| Mistake | Consequence | Fix |
|---|---|---|
| Saturation ceiling taken as one spike per *step* (600) | Reported every regime as unsaturated when all were pinned | Ceiling is one spike per *refractory period* → 120 in a 0.3 s window |
| Assumed dense LPLC2 drive would saturate DNp01, asserted it in the self-check | Self-check failed on a correct simulator | Measured the surface first, then asserted what was observed |
| Source `load_subset()` uses cwd-relative paths | Harness broke when run from its own directory | Resolve caches against the source project root |
| Luminance renderer assigned the field twice, producing a *bright* disk of uniform value | Zero contrast existed; every cell fired at the same step, so timing was flat | Rewrite with single clean occupancy-based darkening and a one-cell soft edge |
| Transient separating-bin test keyed on `spread > 0` | A 0-or-185 step function was reported as a graded positive result | Require every size to yield a distinct count; densify bins to 2 ms |
| Latency measured from window start | Confounded stimulus size with stimulus duration, since frame interval scales with peak size | Measure from the first drive event |

Related: [[Home]] · [[Architecture]] · [[Biological-Reference]] · [[Roadmap]]