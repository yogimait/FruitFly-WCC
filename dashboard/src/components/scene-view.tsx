import { lazy, Suspense } from 'react'

import { Badge } from '@/components/ui/badge'
import type { ExperimentState } from '@/lib/experiment'

/**
 * Hosts the 3D scene. The fly, the approaching disk and the brain glow are lazily loaded so
 * three.js stays out of the initial bundle.
 */
const FlyScene = lazy(() =>
  import('./fly-scene').then((m) => ({ default: m.FlyScene })),
)

const Canvas = lazy(() => import('@react-three/fiber').then((m) => ({ default: m.Canvas })))

export function SceneView({
  state,
  playing,
  progress,
}: {
  state: ExperimentState
  playing: boolean
  progress: number
}) {
  const rate = state.giantFiber?.rateHz ?? null
  const saturated = state.giantFiber?.saturated ?? false

  return (
    <div className="relative overflow-hidden rounded-lg border border-border bg-[#0a0c11]">
      <Suspense
        fallback={
          <div className="flex h-[460px] items-center justify-center font-mono text-xs text-ink-faint">
            loading…
          </div>
        }
      >
        <Canvas
          camera={{ position: [0, 0.35, 2.4], fov: 42 }}
          dpr={[1, 1.75]}
          gl={{ antialias: true }}
        >
          <ambientLight intensity={0.7} />
          <hemisphereLight args={['#cbd5e1', '#0a0c11', 0.5]} />
          <directionalLight position={[2, 3, 2]} intensity={1.4} />
          <directionalLight position={[-2.5, 0.5, 1]} intensity={0.5} color="#7dd3fc" />
          <FlyScene
            spikeHz={rate}
            saturated={saturated}
            playing={playing}
            progress={progress}
          />
        </Canvas>
      </Suspense>

      {/* In-scene annotation, the minimum needed to read the picture. */}
      <div className="pointer-events-none absolute inset-x-0 top-0 flex items-start justify-between p-3">
        <span className="font-mono text-xs text-ink-faint">
          approaching object
        </span>
        <div className="flex flex-col items-end gap-1">
          {saturated && <Badge tone="danger">saturated</Badge>}
          <span className="font-mono text-xs text-spike">
            {rate === null ? 'brain idle' : `brain ${rate.toFixed(0)} Hz`}
          </span>
        </div>
      </div>

      <div className="pointer-events-none absolute inset-x-0 bottom-0 flex items-end justify-between p-3">
        <span className="font-mono text-xs text-ink-faint">fly</span>
        <span className="font-mono text-xs text-ink-faint">
          {playing ? 'replaying stimulus' : 'press start'}
        </span>
      </div>
    </div>
  )
}