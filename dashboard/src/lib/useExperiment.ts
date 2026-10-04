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
      try {
        const response = await fetch('/api/experiment')
        const envelope = (await response.json()) as {
          status: boolean
          statusCode: number
          data?: ExperimentState
          message?: string
        }

        if (!cancelled) {
          if (envelope.status && envelope.data) {
            setState(envelope.data)
            setServerError(null)
          } else {
            setServerError(envelope.message ?? `HTTP ${envelope.statusCode}`)
          }
        }
      } catch {
        if (!cancelled) {
          setServerError(
            'measurement API unreachable — run scripts/serve.py',
          )
        }
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