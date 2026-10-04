import { lazy, Suspense } from 'react'

import { Badge } from '@/components/ui/badge'
import type { ExperimentState } from '@/lib/experiment'

/**
 * The 3D fly is code-split out of the initial bundle.
 *
 * three.js is ~1.2 MB minified. Loading it eagerly tripled the first paint for a panel that
 * is only visible on the `live` tab. Lazy-loading keeps the sweep and reference tabs — the
 * ones carrying the actual measurements — fast to first paint.
 */
const Fly = lazy(() =>
  import('./fly').then((m) => ({ default: m.Fly })),
)

/** Isolated so @react-three/fiber stays inside the lazily-loaded chunk. */
const FlyCanvas = lazy(() =>
  import('@react-three/fiber').then((m) => ({
    default: function FlyCanvas({
      spikeHz,
      saturated,
      running,
    }: {
      spikeHz: number | null
      saturated: boolean
      running: boolean
    }) {
      const Canvas = m.Canvas
      return (
        <Canvas
          camera={{ position: [0.15, 0.35, 1.6], fov: 40 }}
          dpr={[1, 2]}
          gl={{ antialias: true }}
        >
          <ambientLight intensity={0.75} />
          <hemisphereLight args={['#cbd5e1', '#1c1917', 0.5]} />
          <directionalLight position={[2, 3, 2]} intensity={1.5} />
          <directionalLight
            position={[-2.5, 0.5, 1]}
            intensity={0.6}
            color="#7dd3fc"
          />
          <Fly spikeHz={spikeHz} saturated={saturated} running={running} />
        </Canvas>
      )
    },
  })),
)

export function FlyPanel({ state }: { state: ExperimentState }) {
  const rate = state.giantFiber?.rateHz ?? null
  const saturated = state.giantFiber?.saturated ?? false

  return (
    <section className="flex flex-col overflow-hidden rounded-lg border border-border bg-surface">
      <header className="flex items-baseline justify-between gap-3 border-b border-border px-4 py-3">
        <div>
          <h2 className="text-sm font-medium text-ink">
            Drosophila melanogaster — adult male
          </h2>
          <p className="mt-0.5 font-mono text-xs text-ink-faint">
            schematic · procedural geometry · brain glow = DNp01 activity
          </p>
        </div>
        {saturated && <Badge tone="danger">SATURATED</Badge>}
      </header>

      <div className="h-64 w-full">
        <Suspense
          fallback={
            <div className="flex h-full items-center justify-center font-mono text-xs text-ink-faint">
              loading 3D…
            </div>
          }
        >
          <FlyCanvas
            spikeHz={rate}
            saturated={saturated}
            running={state.status === 'running'}
          />
        </Suspense>
      </div>

      <footer className="border-t border-border px-4 py-2">
        <p className="font-mono text-xs text-ink-faint">
          wing beat{' '}
          <span className="text-spike">
            {rate === null ? 'not measured' : `${rate.toFixed(1)} Hz`}
          </span>
          {rate === null && ' · showing idle animation'}
        </p>
        <p className="mt-1.5 text-xs text-ink-faint">
          Body proportions are approximate. This is a schematic for orientation, not a
          morphometric reconstruction. Wing motion visualises the measured spike rate and
          is not a simulation of flight.
        </p>
      </footer>
    </section>
  )
}