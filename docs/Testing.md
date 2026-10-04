# Testing

One command runs everything that does not need a browser:

```bash
python scripts/test_all.py
```

Nine checks, non-zero exit on any failure.

## The nine checks

| # | Check | What it proves |
|---|---|---|
| 1 | `neural_core --test` | frozen dynamics: pathway present, unstimulated network silent |
| 2 | `looming --test` | stimulus monotonic, timing not flat, recruitment scales with stimulus size |
| 3 | `upstream_drive --test` | lobula plate classes complete, static stimulus silent, stimulus reaches the network |
| 4 | `measure_final --quick` | produces `data/measurement.json` with the expected fields |
| 5 | `export_static` | produces the deployable static files |
| 6 | `test_serve.py` | response envelope, view mapping, unmeasured-null, negative findings, HTTP routes |
| 7 | measurement schema | every section present and the reachability guard satisfied |
| 8 | dashboard build | TypeScript compiles |
| 9 | dashboard lint | oxlint reports no errors |

Checks 8 and 9 skip cleanly if `bun` is not on `PATH`.

## Browser verifiers

These need a running server and are therefore not in `test_all.py`.

```bash
cd dashboard && bun run dev          # or: bun run preview --port 5177
python scripts/verify_dashboard.py  # rendered values, accessibility, camera path
python scripts/verify_camera_tuning.py   # encoder response to noise vs real motion
python scripts/measure_noise_floor.py     # measures the noise floor, sweeps candidate bars
```

Start the dev server on **5173** for the camera scripts; they default to that port.
`verify_dashboard.py` defaults to **5177** and accepts a URL argument.

### Shared fake clips

`scripts/fake_video.py` generates the Y4M clips Chromium consumes directly, so the floor
measurement and the response test exercise identical stimuli and cannot drift apart:

| Clip | Property | Must |
|---|---|---|
| `still` | frozen frame | drive nothing |
| `noise` | stationary subject, sensor jitter | drive nothing |
| `face` | mid-contrast blob sweeping 180 px | drive cells and spikes |
| `bar` | high-contrast sweeping bar | drive cells and spikes |

`face` exists because the earlier tests used only `bar`. A high-contrast bar is the easy case, and
testing only it hid a defect where the encoder was completely silent on real subjects.

### A Chromium constraint worth knowing

`--use-file-for-fake-video-capture` is a **browser launch** option, not a context option. A
context created with `permissions=['camera']` on an ordinary browser gets whatever the host has,
usually nothing. Camera assertions need their own launched browser.

## Why the checks are shaped this way

- **Assert on rendered text, not HTTP status.** A dashboard that falls back to "not measured"
  returns 200 and looks fine in a screenshot. That is the failure worth catching.
- **Negative findings are asserted too.** `test_serve.py` checks that `magnitude_invariant` stays
  `true` and that the sweep values are all equal. If a future change "fixes" that, the test
  should fail loudly, because a measurement changed silently.
- **Unmeasured must stay `null`.** Asserted directly, because a `0` in the wrong place reads as a
  real result.
- **Thresholds are measured, not guessed.** `measure_noise_floor.py` prints which bars separate
  noise from motion; the chosen bar is justified in the source of
  `dashboard/src/lib/spike-encoder.ts`.

## Adding a check

Per `AGENTS.md` 9, non-trivial logic leaves one runnable check behind. Add the assertion to the
existing script for that area rather than introducing a test framework — the project has none, and
these scripts double as the verification harness.

## Known limits

- The noise floor is measured against **synthetic** clips whose noise peak is `0.0`, cleaner than
  a real webcam. Real sensor noise may sit higher; the drive bar of 6 has margin but is not
  measured against real hardware.
- `verify_camera_tuning.py` samples one moment of each clip, not a distribution over time.
- Browser verifiers are timing-dependent and have no retry; on a loaded machine they can flake.

## Related

- [[Data-Model]] — what is being verified
- [[API]] — the contract `test_serve.py` asserts
- [[Architecture]] — where each script sits in the pipeline