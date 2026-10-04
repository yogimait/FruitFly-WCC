# AGENTS.md — Fruitfly-WCC Project Rules

Follow these rules throughout the entire project. These are persistent project-level instructions and should be considered before starting any development task (applies to all coding agents working in this repo, including opencode).

## 1. Hackathon Constraint (read first)

This repo is the submission for **WCC Launchpad 30** (4 Oct 2026 10:00 IST → 5 Oct 2026 14:00 IST submission close, solo entry).

- **Rule 1 (organiser):** the core product must be built during the official hackathon period.
- **Rule 4 (organiser):** templates or code written earlier must be clearly disclosed — see `DISCLOSURE.md`.
- **Rule 5 (organiser):** only work done during the event counts towards judging.

**Therefore: do not write core pipeline code before 10:00 IST on 4 Oct 2026.** Documentation, scaffolding, analysis notes, and problem-evidence gathering are permitted and encouraged beforehand. Any pre-event code must be listed in `DISCLOSURE.md`.

## 2. Project Scope

Primary track: **Agentic AI**. The track is an area, not a brief — this project supplies its own problem statement.

Chosen direction: **temporal coding over a descending-neuron-rooted subset** of the MaleCNS v1.0 connectome. Rationale in [[Home]] §Scope Decision. Do not expand the neuron count without a measured justification.

Out of scope, deliberately: whole-connectome live simulation (165,122 neurons, ~40M spikes/step, unrunnable on the demo timeline), reward-modulated learning, event-camera input. These belong in the future-work section of the writeup, not the build.

## 3. Living Documentation & Obsidian

Maintain the project's documentation continuously as the codebase evolves.

- Keep important project knowledge in well-structured Markdown files usable in an Obsidian Vault (the project's `docs/` folder).
- Document meaningful changes: architecture, data models, pipelines, integrations, experiments, significant decisions.
- Do not document trivial changes: styling, renames, formatting, minor refactors.
- Keep related documents connected using Obsidian wiki links such as `[[Architecture]]`, `[[Data-Model]]`.
- When creating or updating docs, maintain logical relationships rather than adding isolated files.
- Documentation is the project's long-term technical memory for developers and coding agents.

## 4. High-Quality Markdown Documentation

All docs must be clear, structured, and useful.

- Proper Markdown headings and hierarchy.
- Bulleted and numbered lists where appropriate.
- Markdown tables when information is naturally tabular.
- Mermaid diagrams for architecture, workflows, data flow, sequences, or any concept where a visual improves understanding.
- Explain what something does, how it works, and **why decisions were made**.
- Avoid walls of text and documenting obvious implementation detail.
- Keep docs visually clean; link to existing docs instead of duplicating.
- Documentation must describe what **is implemented**, not what is planned. Planned work belongs in [[Roadmap]].

## 5. Professional Code Quality

Write code to a professional, production-quality software engineering standard.

- Consistent naming per language: `snake_case` for Python modules, functions, variables.
- Meaningful names for variables, functions, classes, files.
- Functions and modules focused and single-responsibility.
- No messy code, unnecessary complexity, duplication, dead code, unused files, imports, or variables. Remove obsolete code when no longer required.
- No unnecessary dependencies: do not add one when a simple existing solution or the standard library suffices.
- Follow existing project architecture and conventions.
- Apply KISS, DRY, YAGNI, and separation of concerns pragmatically.

## 6. Numerical Honesty (project-critical)

This project simulates a biological network. Invalid results are worse than no results.

- **Never claim a result that was not measured.** Every number in the UI, README, or writeup must trace to a file in `data/`.
- Report negative and null findings honestly rather than tuning them away.
- Any mapping between neural activity and a software action is an **experimental convention, not a biological finding**, and must be labelled as such in code comments, the UI, and every exported artifact.
- No claim of attraction, preference, learning, or reward — nothing in this pipeline trains or updates weights.
- Raw data in `data/` is never hand-edited. Derived `*.npz` / `*.npy` artifacts are caches: safe to delete, rebuilt on next run. Rebuild explicitly whenever weight construction or subset extraction changes.
- A stale cache silently preserves old parameters. When in doubt, delete and rebuild.

## 7. Mandatory Rule & Context Review

Before any meaningful task:

1. Review this `AGENTS.md` and `README.md`.
2. Understand the requested task and which rules apply.
3. Inspect the relevant code, data files, and documentation before making changes.
4. Implement the changes.
5. Update relevant documentation when the change is significant.
6. Before finishing, verify implementation and documentation are clean and consistent.

These rules apply automatically to every task in this project. The user does not need to repeat them.

## 8. Ambiguity

If a task is ambiguous in a way that could significantly affect architecture, numerical results, or simulation semantics, **ask before implementing**. Guessing at simulation parameters produces plausible-looking wrong answers.

## 9. Verification

Non-trivial logic leaves at least one runnable check behind: an `assert`-based self-check or a small test that fails if the logic breaks. No frameworks, no fixtures, no per-function suites unless the project already has them.

Prefer a self-check over introducing a test framework.

## Project Context

Hackathon entry built on the existing FruitFly MaleCNS v1.0 LIF simulation at `D:\Projects\timepass\fruitfly` (read-only source; provenance recorded in `DISCLOSURE.md`).

Source assets relevant to this project:
- `visual-subset-male-cns-v1.0.npz` — 19,267-neuron signed weight submatrix (CSR)
- `connectome-signed-male-cns-v1.0-traced.npz` — whole connectome, 165,122 neurons, 25.56M edges (offline analysis only)
- `temporal_snr.py`, `temporal_readout.py` — prior spike-timing measurements
- `neural_readout.py` — 40 descending-neuron readout

Known blocker being addressed: descending-neuron rates saturate near 400 Hz and quantize at 1.67 Hz, so channel differences between stimuli are ~0–1.2 Hz and policy decisions are effectively noise-driven.