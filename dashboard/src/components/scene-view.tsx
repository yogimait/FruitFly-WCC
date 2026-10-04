import { lazy, Suspense } from 'react'

import { Badge } from '@/components/ui/badge'
import type { ExperimentState } from '@/lib/experiment'
import type { FeedSource } from '@/lib/useCamera'

/**
 * Hosts the 3D scene. The fly, the stimulus disk and the brain glow are lazily loaded so
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
  source = 'synthetic',
  liveMotion = null,
}: {
  state: ExperimentState
  playing: boolean
  progress: number
  source?: FeedSource
  liveMotion?: number | null
}) {
  const rate = state.giantFiber?.rateHz ?? null
  const saturated = state.giantFiber?.saturated ?? false
  const cameraMode = source === 'camera' && liveMotion !== null

  return (
    <div className="relative overflow-hidden rounded-lg border border-border bg-[#0a0c11]">
      <Suspense
        fallback={
          <div className="flex h-[420px] items-center justify-center font-mono text-xs text-ink-faint">
            loading…
          </div>
        }
      >
        <Canvas
          camera={{ position: [0.35, 0.3, 3.2], fov: 44 }}
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
            liveMotion={cameraMode ? liveMotion : null}
          />
        </Canvas>
      </Suspense>

      {/* Minimal in-scene annotation. The picture carries the meaning; this only names the
          two objects so neither is mistaken for part of the fly. */}
      <div className="pointer-events-none absolute inset-x-0 top-0 flex items-start justify-between p-3">
        <span className="font-mono text-xs text-ink-faint">
          {cameraMode ? 'your camera — live' : 'approaching disk'}
        </span>
        <div className="flex flex-col items-end gap-1">
          {saturated && !cameraMode && <Badge tone="danger">saturated</Badge>}
          <span className="font-mono text-xs text-spike">
            {cameraMode
              ? `motion ${(liveMotion ?? 0).toFixed(3)}`
              : rate === null
                ? 'brain idle'
                : `brain ${rate.toFixed(0)} Hz`}
          </span>
        </div>
      </div>

      <div className="pointer-events-none absolute inset-x-0 bottom-0 flex items-end justify-between p-3">
        <span className="font-mono text-xs text-ink-faint">fly</span>
        <span className="font-mono text-xs text-ink-faint">
          {cameraMode
            ? 'reacting to your camera'
            : playing
              ? 'replaying'
              : 'press start'}
        </span>
      </div>

      {cameraMode && (
        <p className="pointer-events-none absolute inset-x-0 bottom-9 px-3 text-center font-mono text-[10px] text-ink-faint">
          fly motion is driven by your camera for illustration · not a neural measurement
        </p>
      )}
    </div>
  )
}