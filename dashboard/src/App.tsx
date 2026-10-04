import { useState } from 'react'

import {
  ReproPanel,
  SeparabilityPanel,
} from '@/components/measure-panels'
import { LatencyPanel } from '@/components/latency-panel'
import { RasterPanel } from '@/components/raster-panel'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { REFERENCE } from '@/lib/experiment'
import { sendControl, useExperimentState } from '@/lib/useExperiment'

export default function App() {
  const state = useExperimentState()
  const [busy, setBusy] = useState(false)

  async function run(action: Parameters<typeof sendControl>[0]) {
    setBusy(true)
    try {
      await sendControl(action)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="min-h-svh bg-background">
      <header className="border-b border-border px-6 py-4">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-base font-medium text-ink">
              LPLC2 → DNp01 latency
            </h1>
            <p className="mt-0.5 font-mono text-xs text-ink-faint">
              MaleCNS v1.0 · {state.status}
              {state.simulatedMs !== null && ` · ${state.simulatedMs.toFixed(0)} ms sim`}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button size="sm" disabled={busy} onClick={() => void run('start')}>
              Start
            </Button>
            <Button
              size="sm"
              variant="outline"
              disabled={busy}
              onClick={() => void run('step')}
            >
              Step
            </Button>
            <Button
              size="sm"
              variant="outline"
              disabled={busy}
              onClick={() => void run('stop')}
            >
              Stop
            </Button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-4 px-6 py-6">
        <div className="grid gap-4 md:grid-cols-2">
          <LatencyPanel state={state} />
          <RasterPanel state={state} />
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <ReproPanel state={state} />
          <SeparabilityPanel state={state} />
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Why 19 ms</CardTitle>
            <CardDescription>
              Published targets this experiment is tested against
            </CardDescription>
          </CardHeader>
          <ul className="space-y-2 font-mono text-xs">
            <li className="flex flex-wrap items-center gap-2">
              <Badge tone="target">{REFERENCE.latencyMs.unit}</Badge>
              <span className="text-ink-muted">{REFERENCE.latencyMs.label}</span>
              <span className="text-ink">{REFERENCE.latencyMs.value}</span>
              <span className="text-ink-faint">— {REFERENCE.latencyMs.source}</span>
            </li>
            <li className="flex flex-wrap items-center gap-2">
              <Badge tone="target">{REFERENCE.sizeThresholdDeg.unit}</Badge>
              <span className="text-ink-muted">
                {REFERENCE.sizeThresholdDeg.label}
              </span>
              <span className="text-ink">{REFERENCE.sizeThresholdDeg.value}</span>
              <span className="text-ink-faint">
                — {REFERENCE.sizeThresholdDeg.source}
              </span>
            </li>
            <li className="flex flex-wrap items-center gap-2">
              <Badge tone="target">{REFERENCE.gfVisualInputShare.unit}</Badge>
              <span className="text-ink-muted">
                {REFERENCE.gfVisualInputShare.label}
              </span>
              <span className="text-ink">
                {REFERENCE.gfVisualInputShare.value}
              </span>
              <span className="text-ink-faint">
                — {REFERENCE.gfVisualInputShare.source}
              </span>
            </li>
          </ul>
        </Card>

        {state.message && (
          <p className="font-mono text-xs text-ink-faint">{state.message}</p>
        )}
      </main>
    </div>
  )
}