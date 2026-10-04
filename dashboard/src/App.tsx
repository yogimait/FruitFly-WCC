import { useState } from 'react'

import { FindingsPanel } from '@/components/findings-panel'
import { ReproPanel } from '@/components/measure-panels'
import { RasterPanel } from '@/components/raster-panel'
import { SceneView } from '@/components/scene-view'
import { SaturationChart, SweepChart } from '@/components/sweep-charts'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { REFERENCE } from '@/lib/experiment'
import { useExperimentState } from '@/lib/useExperiment'
import { usePlayback } from '@/lib/usePlayback'

const STIMULUS_FRAMES = 16
const FRAME_MS = 667

export default function App() {
  const state = useExperimentState()
  const [showData, setShowData] = useState(false)
  const playback = usePlayback(STIMULUS_FRAMES, FRAME_MS)
  const playing = playback.state === 'running'

  const gf = state.giantFiber
  const invariant = state.findings?.verdict?.magnitude_invariant

  return (
    <div className="min-h-svh bg-background">
      <header className="sticky top-0 z-10 border-b border-border bg-background/95 backdrop-blur">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3 px-6 py-3">
          <div className="flex items-center gap-3">
            <h1 className="text-sm font-medium text-ink">
              Can spike timing see what spike rate cannot?
            </h1>
            {invariant === true && <Badge tone="danger">answer: no</Badge>}
          </div>

          <div className="flex items-center gap-2">
            <Button size="sm" onClick={playback.start}>
              {playing ? 'Running…' : 'Start'}
            </Button>
            <Button size="sm" variant="outline" onClick={playback.step}>
              Step
            </Button>
            <Button size="sm" variant="outline" onClick={playback.stop}>
              Stop
            </Button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl space-y-4 px-6 py-6">
        <SceneView state={state} playing={playing} progress={playback.progress} />

        <div className="grid gap-4 sm:grid-cols-3">
          <Card className="sm:col-span-1">
            <p className="font-mono text-xs text-ink-faint">response</p>
            <p className="mt-1 font-mono text-2xl text-spike">
              {gf ? `${gf.spikeCount}` : '—'}
            </p>
            <p className="font-mono text-xs text-ink-faint">
              {gf ? `${gf.rateHz?.toFixed(0)} Hz` : 'not measured'}
            </p>
          </Card>

          <Card className="sm:col-span-1">
            <p className="font-mono text-xs text-ink-faint">first spike</p>
            <p className="mt-1 font-mono text-2xl text-spike">
              {gf?.firstSpikeMs ? `${gf.firstSpikeMs.toFixed(2)} ms` : '—'}
            </p>
            <p className="font-mono text-xs text-ink-faint">
              real flies: {REFERENCE.latencyMs.value} ms
            </p>
          </Card>

          <Card className="sm:col-span-1">
            <p className="font-mono text-xs text-ink-faint">input driven</p>
            <p className="mt-1 font-mono text-2xl text-spike">67–6,719</p>
            <p className="font-mono text-xs text-ink-faint">same response</p>
          </Card>
        </div>

        <RasterPanel state={state} progress={playback.progress} />
        <ReproPanel state={state} />

        <button
          onClick={() => setShowData((v) => !v)}
          className="font-mono text-xs text-ink-faint underline underline-offset-4 hover:text-ink-muted"
        >
          {showData ? 'hide data' : 'show data & sources'}
        </button>

        {showData && (
          <div className="space-y-4">
            <div className="grid gap-4 lg:grid-cols-2">
              <SweepChart state={state} />
              <SaturationChart state={state} />
            </div>
            <FindingsPanel state={state} />
            <Card>
              <p className="font-mono text-xs text-ink-faint">sources</p>
              <ul className="mt-2 space-y-1 font-mono text-xs text-ink-muted">
                <li>19 ms escape latency — Ache et al. 2019, Curr Biol</li>
                <li>42° looming size threshold — von Reyn et al. 2017</li>
                <li>
                  97.5% giant-fiber input from LPLC2 + LC4 — PLOS Biol 2025
                </li>
                <li>MaleCNS v1.0 connectome; LIF constants — Shiu et al. 2024</li>
              </ul>
            </Card>
          </div>
        )}

        {state.serverError && (
          <p className="font-mono text-xs text-danger">{state.serverError}</p>
        )}

        <p className="pb-6 text-xs text-ink-faint">
          Simulated from a published connectome. Nothing is trained. Measured offline and served
          as data.
        </p>
      </main>
    </div>
  )
}