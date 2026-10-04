# API

The backend is `scripts/serve.py` — Python standard library only, no framework. It reads what
`scripts/measure_final.py` wrote and serves it. **No simulation runs in the server process**, so
the API cannot produce a number that disagrees with the files on disk.

```bash
python scripts/serve.py --port 8768
```

The dashboard does not require this server. `scripts/export_static.py` writes the same payload to
`dashboard/public/api/`, so a static build is self-contained. The API exists for iterating on the
measurement without rebuilding the dashboard.

## Response envelope

Every JSON response uses one envelope, per `AGENTS.md` 6.

Success:

```json
{ "status": true, "statusCode": 200, "data": {} }
```

Failure:

```json
{
  "status": false,
  "statusCode": 404,
  "message": "No such endpoint: /api/nope",
  "error": { "code": "NOT_FOUND", "details": {} }
}
```

`statusCode` in the body always equals the real HTTP status. Success bodies never carry `error`.

## Endpoints

### `GET /api/health`

Readiness probe. Always 200, even when no measurement exists, so a probe distinguishes "server
up, data missing" from "server down".

```json
{
  "status": true,
  "statusCode": 200,
  "data": { "measurement_present": true, "measurement_path": "..." }
}
```

### `GET /api/experiment`

The live view. Assembles every panel the dashboard renders from `data/measurement.json` and
`data/response-surface.json`.

Notable fields:

| Field | Source | Notes |
|---|---|---|
| `giantFiber.spikeCount` | longest **unsaturated** window | `null` when nothing is measured |
| `giantFiber.rateHz` | derived | `spikeCount / windowSeconds`, rounded to 2 dp |
| `driveRange.minNeurons` / `maxNeurons` | `drive_sweep.rows[].neurons_driven` | min and max over the sweep |
| `driveRange.invariant` | `drive_sweep.invariant` | the negative result, passed through |
| `findings.*` | the measurement sections | rendered verbatim |
| `sweep[].angularSizeDeg` | `window_ms` | **name is historical**; the axis is labelled in the UI |

`angularSizeDeg` carries a window in milliseconds. The field name predates the response-surface
work and renaming it would break the deployed payload for no gain, so the UI labels the axis
explicitly instead. Flagged here because a field whose name lies is a trap.

### `GET /api/measurement`

The complete measurement record, unwrapped from the envelope's `data`.

### `POST /api/control`

Accepts `{"action": "start" | "stop" | "step" | "reset"}` and reports honestly:

```json
{
  "status": true,
  "statusCode": 200,
  "data": {
    "accepted": true,
    "runs_live": false,
    "message": "Measurements are produced by scripts/measure_final.py and served from data/measurement.json."
  }
}
```

`runs_live` is `false` because it is false. There is no live simulation loop; the endpoint does
not pretend otherwise.

## Error codes

| Code | HTTP | When |
|---|---|---|
| `MEASUREMENT_NOT_FOUND` | 503 | `data/measurement.json` absent; run `measure_final.py` |
| `READ_ERROR` | 500 | the file exists but is unreadable or not valid JSON |
| `NOT_FOUND` | 404 | unknown `/api/*` route |
| `METHOD_NOT_ALLOWED` | 405 | reserved; no current route returns it |

Unknown `/api/*` paths are answered with the envelope rather than falling through to the static
file handler, so a typo returns a structured error instead of an HTML 404.

## Caching

`Cache-Control: no-store`. The measurement can be rewritten by a script while the server runs,
and a cached payload would quietly disagree with the files on disk.

## Related

- [[Data-Model]] — the files behind these endpoints
- [[Testing]] — `scripts/test_serve.py` asserts the envelope, the view mapping, and these routes
- [[Architecture]] — where the server sits in the pipeline