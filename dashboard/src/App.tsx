import { useState } from 'react'

import { FindingsPanel } from '@/components/findings-panel'
import { FlyPanel } from '@/components/fly-panel'
import {
  ReproPanel,
  SeparabilityPanel,
} from '@/components/measure-panels'
import { LatencyPanel } from '@/components/latency-panel'
import { RasterPanel } from '@/components/raster-panel'
import {
  SaturationChart,
  SweepChart,
} from '@/components/sweep-charts'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { REFERENCE } from '@/lib/experiment'
import { sendControl, useExperimentState } from '@/lib/useExperiment'

const TABS = ['live', 'sweep', 'findings', 'reference'] as const
type Tab = (typeof TABS)[number]

export default function App() {
  const state = useExperimentState()
  const [busy, setBusy] = useState(false)
  const [tab, setTab] = useState<Tab>('live')

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
      <header className="sticky top-0 z-10 border-b border-border bg-background/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-6 py-3">
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

        <nav className="mx-auto flex max-w-6xl gap-1 px-6 pb-2">
          {TABS.map((name) => (
            <button
              key={name}
              onClick={() => setTab(name)}
              className={
                tab === name
                  ? 'rounded-md bg-surface-raised px-3 py-1 font-mono text-xs text-ink'
                  : 'rounded-md px-3 py-1 font-mono text-xs text-ink-faint hover:text-ink-muted'
              }
            >
              {name}
            </button>
          ))}
        </nav>
      </header>

      <main className="mx-auto max-w-6xl space-y-4 px-6 py-6">
        {tab === 'live' && (
          <>
            <div className="grid gap-4 lg:grid-cols-3">
              <div className="lg:col-span-2">
                <FlyPanel state={state} />
              </div>
              <LatencyPanel state={state} />
            </div>

            <div className="grid gap-4 lg:grid-cols-2">
              <RasterPanel state={state} />
              <div className="space-y-4">
                <ReproPanel state={state} />
                <SeparabilityPanel state={state} />
              </div>
            </div>
          </>
        )}

        {tab === 'sweep' && (
          <>
            <div className="grid gap-4 lg:grid-cols-2">
              <SweepChart state={state} />
              <SaturationChart state={state} />
            </div>
            <SeparabilityPanel state={state} />
          </>
        )}

        {tab === 'findings' && <FindingsPanel state={state} />}

        {tab === 'reference' && (
          <Card>
            <CardHeader>
              <CardTitle>Published targets</CardTitle>
              <CardDescription>
                Every number this project is tested against, and where it comes from. Full
                citations in docs/Biological-Reference.md.
              </CardDescription>
            </CardHeader>
            <ul className="space-y-3">
              {[
                REFERENCE.latencyMs,
                REFERENCE.sizeThresholdDeg,
                REFERENCE.gfVisualInputShare,
              ].map((r) => (
                <li
                  key={r.label}
                  className="flex flex-wrap items-center gap-2 border-b border-border pb-2 font-mono text-xs last:border-0"
                >
                  <Badge tone="target">
                    {r.value} {r.unit}
                  </Badge>
                  <span className="text-ink-muted">{r.label}</span>
                  <span className="ml-auto text-ink-faint">{r.source}</span>
                </li>
              ))}
            </ul>
          </Card>
        )}

        {state.serverError && (
          <p className="rounded-md border border-danger/40 bg-danger/10 px-3 py-2 font-mono text-xs text-danger">
            {state.serverError}
          </p>
        )}

        {state.message && (
          <p className="font-mono text-xs text-ink-faint">{state.message}</p>
        )}

        <p className="pb-4 text-xs text-ink-faint">
          Computational experiment. No weights are trained or updated anywhere in this
          pipeline. Neural activity does not imply biological preference, attraction, or
          learning. Body geometry is schematic and carries no biological claim.
        </p>
      </main>
    </div>
  )
}