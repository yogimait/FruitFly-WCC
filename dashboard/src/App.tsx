import { useEffect, useMemo, useState } from 'react'

import { CameraToggle } from '@/components/camera-toggle'
import { FindingsPanel } from '@/components/findings-panel'
import { ReproPanel } from '@/components/measure-panels'
import { RasterPanel } from '@/components/raster-panel'
import { SceneView } from '@/components/scene-view'
import { LiveSpikePanel } from '@/components/live-spikes'
import { SaturationChart, SweepChart } from '@/components/sweep-charts'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { REFERENCE } from '@/lib/experiment'
import { predictSpikes, type LiveSpike } from '@/lib/spike-encoder'
import { CAMERA_GRID, useCamera, type FeedSource } from '@/lib/useCamera'
import { useExperimentState } from '@/lib/useExperiment'
import { usePlayback } from '@/lib/usePlayback'

const STIMULUS_FRAMES = 16
const FRAME_MS = 667
/** Stable identity, so deriving "no spikes" during render does not change every frame. */
const EMPTY_SPIKES: readonly LiveSpike[] = []

export default function App() {
  const state = useExperimentState()
  const [showData, setShowData] = useState(false)
  const [source, setSource] = useState<FeedSource>('synthetic')
  const playback = usePlayback(STIMULUS_FRAMES, FRAME_MS)
  const camera = useCamera(source)
  const playing = playback.state === 'running'
  const cameraLive = source === 'camera' && camera.status === 'live'
  const invariant = state.findings?.verdict?.magnitude_invariant
  const [liveSpikes, setLiveSpikes] = useState<readonly LiveSpike[]>(EMPTY_SPIKES)

  // Spikes are recomputed on animation frames rather than on camera frames, so the raster
  // refreshes continuously instead of waiting for the next camera sample. The reset when the
  // camera goes away is derived during render instead of set in the effect, so leaving camera
  // mode does not trigger a second render pass.
  const spikesForPanel = cameraLive ? liveSpikes : EMPTY_SPIKES
  useEffect(() => {
    if (!cameraLive) return
    let raf = 0
    const tick = () => {
      setLiveSpikes(predictSpikes(camera.grid, camera.motion))
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [cameraLive, camera.grid, camera.motion])

  // The fly's brightness follows real descending-neuron output rather than raw motion, so its
  // visible reaction and the raster on screen are driven by the same number.
  const liveDrive = useMemo(() => {
    if (!cameraLive) return null
    const dn = spikesForPanel.filter((s) => s.group === 'DNp01').length
    return Math.min(1, dn / 7)
  }, [cameraLive, spikesForPanel])

  const gf = state.giantFiber
  const driveRange = state.driveRange

  return (
    <div className="min-h-svh bg-background">
      <a
          href="#main"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-20 focus:rounded focus:bg-surface focus:px-3 focus:py-2 focus:font-mono focus:text-xs focus:text-spike"
        >
          skip to measurement
        </a>

        <header className="sticky top-0 z-10 border-b border-border bg-background/95 backdrop-blur">
          <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3 px-6 py-3">
            <div className="flex items-center gap-3">
              <h1 className="text-sm font-medium text-ink">
                Can spike timing see what spike rate cannot?
              </h1>
              {invariant === true && <Badge tone="danger">answer: no</Badge>}
            </div>

            <div
              className="flex items-center gap-2"
              role="group"
              aria-label="synthetic stimulus playback"
            >
            <Button size="sm" onClick={playback.start} disabled={cameraLive}>
              {playing ? 'Running…' : 'Start'}
            </Button>
            <Button size="sm" variant="outline" onClick={playback.step} disabled={cameraLive}>
              Step
            </Button>
            <Button size="sm" variant="outline" onClick={playback.stop} disabled={cameraLive}>
              Stop
            </Button>
          </div>
        </div>
      </header>

      <main id="main" className="mx-auto max-w-5xl space-y-4 px-6 py-6">
        {/* Loading and failure are distinct states. Before the first successful load there is
            nothing to show, and saying "no data" would be wrong — it has not been fetched yet. */}
        {!state.loaded && !state.serverError && (
          <p role="status" className="font-mono text-xs text-ink-faint">
            loading measurement…
          </p>
        )}

        {state.serverError && (
          <Card>
            <p role="alert" className="font-mono text-xs text-danger">
              {state.serverError}
            </p>
            <p className="mt-2 font-mono text-xs text-ink-faint">
              Generate the data with <code>python scripts/measure_final.py</code>, then export
              it with <code>python scripts/export_static.py</code>.
            </p>
          </Card>
        )}

        <SceneView
          state={state}
          playing={playing}
          progress={playback.progress}
          source={source}
          liveMotion={cameraLive ? camera.motion : null}
          liveDrive={liveDrive}
        />

        {/* One video element, styled either as a visible preview or hidden. Two elements sharing
            one ref would attach the stream to only one of them. The preview is visible so a
            live feed is distinguishable from a broken one. */}
        <video
          ref={camera.videoRef}
          className={
            cameraLive
              ? 'h-32 w-48 rounded-md border border-border object-cover'
              : 'hidden'
          }
          playsInline
          muted
          aria-label={cameraLive ? 'live camera feed' : undefined}
        />
        {/* Sized from the same constant the sampler uses. A mismatch here silently samples a
            fraction of the frame and zeroes the rest. The `react/refs` rule is off in
            .oxlintrc.json because passing a ref to the `ref` prop is correct React, not a
            `.current` read during render. */}
        <canvas
          ref={camera.canvasRef}
          className="hidden"
          width={CAMERA_GRID}
          height={CAMERA_GRID}
          aria-hidden="true"
        />

        {cameraLive && (
          <div className="flex flex-wrap items-center gap-4">
            <div className="font-mono text-xs">
              <p className="text-ink-faint">live motion energy from your camera</p>
              <p className="mt-0.5 text-xl text-spike">{camera.motion.toFixed(4)}</p>
            </div>
            <p className="max-w-sm text-xs text-ink-faint">
              Computed in this browser from your frames on the same {CAMERA_GRID}×{CAMERA_GRID}{' '}
              grid the encoder samples. The fly reacts to <em>this</em> value. The measured
              spike counts further down are recorded from the synthetic disk and are not
              recomputed here.
            </p>
          </div>
        )}

        <div className="flex flex-wrap items-center justify-between gap-3">
          <CameraToggle
            source={source}
            onChange={(next) => {
              setSource(next)
              if (next === 'synthetic') camera.stop()
            }}
            status={camera.status}
            onStart={camera.start}
          />
          {cameraLive && (
            <span className="font-mono text-xs text-ink-faint">
              live stimulus, recorded measurement
            </span>
          )}
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <Card>
            <p className="font-mono text-xs text-ink-faint">response</p>
            <p className="mt-1 font-mono text-2xl text-spike">{gf ? `${gf.spikeCount}` : '—'}</p>
            <p className="font-mono text-xs text-ink-faint">
              {gf ? `${gf.rateHz?.toFixed(0)} Hz` : 'not measured'}
            </p>
          </Card>

          <Card>
            <p className="font-mono text-xs text-ink-faint">first spike</p>
            <p className="mt-1 font-mono text-2xl text-spike">
              {gf?.firstSpikeMs ? `${gf.firstSpikeMs.toFixed(2)} ms` : '—'}
            </p>
            <p className="font-mono text-xs text-ink-faint">
              real flies: {REFERENCE.latencyMs.value} ms
            </p>
          </Card>

          {/* Range comes from the measured drive sweep; it was a hardcoded literal here. */}
          <Card>
            <p className="font-mono text-xs text-ink-faint">input driven</p>
            <p className="mt-1 font-mono text-2xl text-spike">
              {driveRange
                ? `${driveRange.minNeurons?.toLocaleString() ?? '—'}–${driveRange.maxNeurons?.toLocaleString() ?? '—'}`
                : '—'}
            </p>
            <p className="font-mono text-xs text-ink-faint">
              {driveRange?.invariant ? 'same response' : 'not measured'}
            </p>
          </Card>
        </div>

        <RasterPanel state={state} progress={playback.progress} hidden={cameraLive} />
        {cameraLive && (
          <LiveSpikePanel grid={camera.grid} spikes={spikesForPanel} />
        )}
        <ReproPanel state={state} />

        <button
          type="button"
          onClick={() => setShowData((v) => !v)}
          aria-expanded={showData}
          aria-controls="data-and-sources"
          className="font-mono text-xs text-ink-faint underline underline-offset-4 hover:text-ink-muted focus-visible:outline focus-visible:outline-2 focus-visible:outline-spike"
        >
          {showData ? 'hide data' : 'show data & sources'}
        </button>

        {showData && (
          <div id="data-and-sources" className="space-y-4">
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
                <li>97.5% giant-fiber input from LPLC2 + LC4 — PLOS Biol 2025</li>
                <li>MaleCNS v1.0 connectome; LIF constants — Shiu et al. 2024</li>
              </ul>
            </Card>
          </div>
        )}

        <p className="pb-6 text-xs text-ink-faint">
          Simulated from a published connectome. Nothing is trained. The stimulus can be live;
          the measurement is recorded and served as data.
        </p>
      </main>
    </div>
  )
}