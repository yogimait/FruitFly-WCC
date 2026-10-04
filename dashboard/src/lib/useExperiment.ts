import { useEffect, useRef, useState } from 'react'

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
 * Polls the measurement harness for the current experiment state.
 *
 * Polling rather than SSE or WebSocket: the Python side writes a JSON snapshot per run,
 * and a single LIF step takes 1-2 s. A 1 s poll is comfortably faster than the producer,
 * so a stream would add a server protocol for no observable gain. Simpler is correct here.
 */
export function useExperimentState(intervalMs = 1000): ExperimentState {
  const [state, setState] = useState<ExperimentState>(EMPTY)
  const hasError = useRef(false)

  useEffect(() => {
    let cancelled = false

    async function poll() {
      try {
        const response = await fetch('/api/experiment')
        if (!response.ok) throw new Error(`HTTP ${response.status}`)

        const next = (await response.json()) as ExperimentState
        if (!cancelled) {
          setState(next)
          hasError.current = false
        }
      } catch {
        // Harness not running yet is the normal pre-event state, not an error to surface.
        if (!cancelled && !hasError.current) setState(EMPTY)
      }
    }

    void poll()
    const timer = setInterval(poll, intervalMs)
    return () => {
      cancelled = true
      clearInterval(timer)
    }
  }, [intervalMs])

  return state
}

export type RunControl = 'start' | 'stop' | 'step' | 'reset'

export async function sendControl(action: RunControl): Promise<void> {
  await fetch('/api/control', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action }),
  })
}