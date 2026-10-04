import { useEffect, useState } from 'react'

import type { ExperimentState } from './experiment'

const EMPTY: ExperimentState = {
  status: 'idle',
  message: null,
  angularSizeDeg: null,
  simulatedMs: null,
  lplc2: null,
  giantFiber: null,
  trials: [],
  separability: [],
  sweep: [],
  raster: [],
}

/**
 * Polls the measurement API for the current state.
 *
 * Polling rather than SSE or WebSocket: the Python side produces a measurement offline and
 * serves a static snapshot, so there is no producer faster than the poll interval. A stream
 * would add a server protocol for no observable gain.
 *
 * The endpoint uses the response envelope ({status, statusCode, data}), so `data` is unwrapped
 * here once rather than at every call site.
 */
export function useExperimentState(intervalMs = 2000): ExperimentState {
  const [state, setState] = useState<ExperimentState>(EMPTY)
  const [serverError, setServerError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function poll() {
      // Try the bare path first (served by scripts/serve.py in dev, and by real hosts that do
      // extensionless resolution), then the explicit .json path (served as a plain static file
      // by export_static.py, including `python -m http.server` which does not resolve bare
      // paths). One of the two always works, so the dashboard is host-independent.
      const candidates = ['/api/experiment', '/api/experiment.json']

      for (const path of candidates) {
        try {
          const response = await fetch(path)
          const envelope = (await response.json()) as {
            status: boolean
            statusCode: number
            data?: ExperimentState
            message?: string
          }

          if (envelope.status && envelope.data) {
            if (!cancelled) {
              setState(envelope.data)
              setServerError(null)
            }
            return
          }

          // A well-formed failure envelope is a real answer, not a transport problem.
          if (envelope.statusCode >= 400 && envelope.statusCode < 500) {
            if (!cancelled) {
              setState(EMPTY)
              setServerError(envelope.message ?? `HTTP ${envelope.statusCode}`)
            }
            return
          }
        } catch {
          // Try the next candidate.
        }
      }

      if (!cancelled) {
        setServerError('measurement API unreachable — run scripts/serve.py')
      }
    }

    void poll()
    const timer = setInterval(poll, intervalMs)
    return () => {
      cancelled = true
      clearInterval(timer)
    }
  }, [intervalMs])

  return { ...state, serverError }
}

export type RunControl = 'start' | 'stop' | 'step' | 'reset'

export async function sendControl(action: RunControl): Promise<void> {
  await fetch('/api/control', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action }),
  })
}