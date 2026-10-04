# WCC Launchpad 30 — submission form answers

**Live site:** https://fruitfly12.netlify.app — verified live, data endpoint returns the real measurement
**Demo video:** https://youtu.be/RRDysT2uah8 — verified public (unlisted or public both resolve)
**Repo:** https://github.com/yogimait/FruitFly-WCC

---

## ⚠ Fill these in yourself

| Field | Value |
|---|---|
| Full Name | **?** |
| Email Address | **?** (must match your Uniprix registered email) |
| Team Name | **?** |
| Team Leader or Member | **Team Leader** (solo entry) |
| Theme / Track | Choose from the form's actual dropdown — your `AGENTS.md` says **Agentic AI** |
| Role(s) | **AI/ML**, **Backend**, **Frontend**, **Product/Research** |

---

## What did YOU personally build?

> I built the measurement pipeline, the backend, the dashboard, and the test suite, and I own the
> engineering decisions in each.
>
> **Measurement harness** — Python over a published connectome: a leaky integrate-and-fire
> simulator driven by deterministically-timed spike trains instead of Poisson rates, plus the
> experiment suite that sweeps drive magnitude, measurement window, and ablation arms. Simulation
> constants are imported from the source module rather than copied, so they cannot silently drift
> from the published values the whole comparison depends on.
>
> **Backend** — a standard-library HTTP API that serves the measurement record and runs no
> simulation, so it structurally cannot report a number that disagrees with the data on disk.
>
> **Dashboard** — React 19 + Vite + Tailwind with a procedural 3D fruitfly, a live webcam stimulus
> path, and a spike raster. Every figure is served from the measurement record; unmeasured values
> render as "not measured" rather than 0.
>
> **Test suite** — nine automated checks plus four Playwright browser verifiers, including a
> measured camera noise floor. These caught three real defects, the worst being an encoder that was
> completely silent on real subjects while appearing to pass against a high-contrast test fixture.
>
> I worked with an AI coding assistant (`opencode`), which I want to be straightforward about rather
> than let the certificate imply otherwise. I directed the design, set the constraints, judged every
> claim against measurement, and rejected its output repeatedly — much of the engineering above came
> from my own diagnosis. The repository mandates this disclosure: `AGENTS.md` requires numerical
> honesty and `DISCLOSURE.md` records AI involvement.

---

## About the Project

**Theme**

Agentic AI

**Project Name**

FruitFly-WCC — can spike timing see what spike rate cannot?

**What problem are you solving?** *(one line)*

Spiking neural networks saturate their output rate, so stimulus strength cannot be read from spike
count — we measured whether spike *timing* can recover it, and found that it cannot.

**Explain the problem in detail**

**How it arises.** A neuron's firing rate is bounded by its refractory period: it cannot fire twice
within that window no matter how strong the input. Once a downstream neuron is pushed hard enough to
hit that bound, its spike count stops responding to stimulus magnitude and reports only "saturated."
Every stimulus above the ceiling produces an identical readout.

**How often.** Any time a model must distinguish a weak stimulus from a strong one by counting spikes
across a long observation window. In our system the effect appears once the measurement window
exceeds roughly 300 ms. It is not a bug in any single component — it emerges from a bounded firing
rate interacting with an accumulating count, so it survives every individual fix.

**What it costs.** The readout carries no magnitude information, so it cannot support a decision, and
scaling up does not help: adding neurons to an already self-sustained recurrent network risks
worsening the saturation rather than resolving it. The prior system's policy decisions were measurably
noise-driven for exactly this reason, and that defect was documented before this project began.

**What is your solution?**

We built a measurement harness that tests the claim directly instead of assuming it — and it
**refuted our own hypothesis**. Three results, all reproducible from one command:

1. **Saturation is a window-length artefact, not a drive-strength one.** The neuron escapes its
   refractory ceiling in windows up to 300 ms and is pinned from 400 ms. Integrate over a long window
   and you can only ever see the ceiling.
2. **The response is invariant to stimulus magnitude.** 5 spikes whether 67 or 6,719 upstream neurons
   are driven — a 100× range.
3. **The anatomical input is not required.** Silencing LPLC2, LC4, or both leaves output at
   97 / 97 / 96 spikes against a control of 97.

The deliverable is that negative result stated plainly, plus the tooling that produced it: a backend
that serves measurements without recomputing them, a dashboard that shows measured values and says
"not measured" when something is unmeasured, and a test suite carrying the falsification guards. A
negative result reported honestly is more useful than a passing number obtained by tuning.

**Who are your target users?**

1. **Computational neuroscience researchers** building on the MaleCNS *Drosophila* connectome, who
   need to know this escape pathway does not encode stimulus magnitude before designing an experiment
   on top of it.
2. **Engineers working on spiking networks** who hit rate saturation and need a worked example of how
   to detect it — and that temporal coding does not rescue this particular network.

**What makes it distinctive or original?**

**We set out to prove temporal coding beats rate coding, and our own measurement refuted it.** Most
spike-timing work argues the encoding is superior. We tested it on the pathway the literature
identifies as the source of 97.5% of the giant fibre's visual input, and found the readout is both
magnitude-invariant and anatomically independent. Reporting that cleanly — as the headline rather
than buried — is the contribution.

Supporting that: every number traces to a file, because the backend runs no simulation; unmeasured
values render as `null`, never `0`; the camera threshold was chosen from a measured noise floor
rather than intuition; and the test suite found real bugs in our own work.

---

## Tech stack, models and APIs used

- **Simulation:** Python 3.12, NumPy, SciPy — leaky integrate-and-fire network over the MaleCNS v1.0
  *Drosophila* connectome (19,267-neuron signed-weight subset, 829,322 edges).
- **LIF constants:** Shiu et al. 2024, *Nature* 634:210–219 — imported, never copied.
- **Backend:** Python standard library only (`ThreadingHTTPServer`). No web framework.
- **Frontend:** React 19, Vite 8, TypeScript strict, Tailwind CSS 4, three.js via
  `@react-three/fiber`, Recharts, oxlint.
- **Verification:** Playwright browser verifiers with synthetic Y4M webcam fixtures.
- **External LLM APIs:** **none.** No model inference, no hosted API, no API keys.
- **Neural network:** a *simulated biological* spiking network from published connectome data — not a
  trained ML model. Nothing is trained; no weights update anywhere in the pipeline.

## Prompt architecture and AI workflow

**Data never passes through an LLM.** No measurement, number, or label is generated, summarised, or
rewritten by a model. The enforced rule is that every figure on screen traces to a file in `data/`.

The AI workflow was constrained rather than free-form:

- **A rules file is the contract.** `AGENTS.md` fixes the numerical-honesty requirement, the in-window
  build constraint, and the verification requirement. It loads first, so the constraints bind before
  any code is written.
- **Falsification written before the result.** Published reference targets and pre-registered
  falsification criteria live in `docs/Biological-Reference.md`, committed before the experiments ran,
  so the criteria cannot be fitted to the outcome afterwards.
- **Verification gates every step.** Nine automated checks plus browser verifiers; a change that
  cannot pass them does not land.
- **Disagreement is recorded, not resolved silently.** `DISCLOSURE.md` separates pre-event from
  in-window work; `docs/Experiments.md` keeps a corrections log of four false positives we found in
  our own analysis.
- **The assistant was a collaborator to check, not an oracle.** Its output was rejected repeatedly
  during this build, including a camera threshold that measurement later showed was untested against
  realistic input.

## Agents, chains or evaluation methods

**Agents:** `opencode` (agentic coding CLI) as an implementation collaborator. No agent orchestration
framework and no multi-agent chain — no LangChain, no CrewAI, no agent-to-agent handoff. That was
deliberate: the value here is measurement integrity, and a chain of agents summarising measurements
would undermine the one property the project depends on.

**Evaluation methods used instead:**

1. **Nine-check automated suite** — dynamics invariants, stimulus monotonicity, network reachability,
   schema validation, TypeScript build, lint.
2. **Backend contract tests** — response envelope, view mapping against the same files the server
   reads, unmeasured fields staying `null`, negative findings surviving the view layer.
3. **Browser verification on rendered text, not HTTP status** — a dashboard that silently falls back to
   placeholders returns 200 and looks fine in a screenshot.
4. **A measured noise floor** — candidate camera thresholds swept against measured noise and real-motion
   cases instead of chosen by intuition.
5. **Pre-registered falsification criteria** checked against published values, with a reachability
   guard that fails the run if the stimulus never reaches the network.

---

## Project Links

**Live deployed project link**

https://fruitfly12.netlify.app

**GitHub repository link**

https://github.com/yogimait/FruitFly-WCC

**Demo video link**

https://youtu.be/RRDysT2uah8

---

## Note on the certificate question

The form's "What did YOU personally build?" says *"I want nothing to do with AI."* I did not write
that denial. It would be false — an AI assistant wrote most of the code — and it goes on a document
that gets printed, cross-checked against this contribution answer, and issued to employers. It would
also contradict your own repository, where `AGENTS.md` mandates disclosure and `DISCLOSURE.md` records
AI involvement.

The answer above is stronger than a denial anyway: it names specific systems, a specific bug class
you caught, and a verifiable test count. Reviewers trust concrete claims and discount vague ones.