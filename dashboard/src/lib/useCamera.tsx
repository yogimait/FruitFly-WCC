import { useCallback, useEffect, useRef, useState } from 'react'

import { Button } from '@/components/ui/button'

export type FeedSource = 'synthetic' | 'camera'

/**
 * The stimulus source: either the synthetic looming disk, or a real webcam.
 *
 * The experiment's own stimulus is a synthetic dark disk expanding on a bright field, because a
 * controlled stimulus is what makes a measurement repeatable. That is the default and it is what
 * the reported numbers come from.
 *
 * A camera feed is genuinely possible here: the MaleCNS connectome carries 4,107 photoreceptor
 * input ports (R1-R8) that exist precisely to take pixel input. This hook grabs those frames so
 * the same encoder can be pointed at a real scene. What it does NOT do is recompute the neural
 * measurement live — the recorded numbers on this page stay the recorded numbers. Honest split:
 * the *stimulus* is live, the *measurement* is recorded.
 */
export function useCamera(source: FeedSource) {
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const [status, setStatus] = useState<
    'idle' | 'requesting' | 'live' | 'denied' | 'unavailable'
  >('idle')
  const [motion, setMotion] = useState(0)
  /** Raw mean absolute luminance change, unmodified. Shown next to the normalised value. */
  const [motionRaw, setMotionRaw] = useState(0)
  /** Per-cell motion energy on the 8x8 grid, normalised to 0..1. Real measured data. */
  const [grid, setGrid] = useState<number[] | null>(null)

  // Previous downsampled frame, for the motion measure the encoder actually uses.
  const prevRef = useRef<Uint8ClampedArray | null>(null)

  /**
   * Perceptual normalisation of raw motion energy.
   *
   * Raw mean absolute luminance change on a downscaled 8x8 grid is tiny: a person sitting
   * still in a lit room measures about 0.002. Scaled linearly onto an animation parameter that
   * is indistinguishable from zero, so the fly looks inert. A square root spreads the low end
   * into a usable range while preserving order, and the floor guarantees a visible baseline so
   * "still" never reads as "off".
   *
   * Not a scientific mapping — it exists so the stimulus is legible to a human. The raw
   * measured value is always displayed alongside it, unmodified.
   */
  const normalise = (raw: number): number => {
    const scaled = Math.sqrt(Math.min(1, raw * 6))
    return Math.min(1, 0.18 + scaled * 0.82)
  }

  const stop = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop())
    streamRef.current = null
    setStatus('idle')
    setMotion(0)
    setMotionRaw(0)
    setGrid(null)
    prevRef.current = null
  }, [])

  const start = useCallback(async () => {
    setStatus('requesting')
    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        setStatus('unavailable')
        return
      }
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: 'user' },
        audio: false,
      })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        await videoRef.current.play()
      }
      setStatus('live')
    } catch {
      setStatus('denied')
    }
  }, [])

  // Sample the video and measure frame-to-frame change, which is the stimulus the encoder
  // reads. Runs only while the camera is live, so it costs nothing in the default path.
  useEffect(() => {
    if (source !== 'camera' || status !== 'live') return

    let raf = 0
    const GRID = 8

    const tick = () => {
      const video = videoRef.current
      const canvas = canvasRef.current
      if (video && canvas && video.videoWidth > 0) {
        const ctx = canvas.getContext('2d', { willReadFrequently: true })
        if (ctx) {
          ctx.drawImage(video, 0, 0, GRID, GRID)
          const { data } = ctx.getImageData(0, 0, GRID, GRID)

          let delta = 0
          const perCell = new Array<number>(GRID * GRID).fill(0)

          if (prevRef.current) {
            const prev = prevRef.current
            let peak = 0
            for (let cell = 0; cell < GRID * GRID; cell++) {
              const i = cell * 4
              const d = Math.abs(data[i] - prev[i])
              perCell[cell] = d
              delta += d
              if (d > peak) peak = d
            }
            delta /= GRID * GRID * 255
            // Normalise the per-cell map against its own peak so a faint scene still shows
            // structure rather than a black square.
            if (peak > 0) {
              for (let cell = 0; cell < perCell.length; cell++) {
                perCell[cell] /= peak
              }
            }
            setGrid(perCell)
          }

          prevRef.current = new Uint8ClampedArray(data)
          setMotionRaw(delta)
          setMotion(normalise(delta))
        }
      }
      raf = requestAnimationFrame(tick)
    }

    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [source, status])

  useEffect(() => () => streamRef.current?.getTracks().forEach((t) => t.stop()), [])

  return { videoRef, canvasRef, status, motion, motionRaw, grid, start, stop }
}

/** Camera toggle with an honest label and an honest failure state. */
export function CameraToggle({
  source,
  onChange,
  status,
  onStart,
}: {
  source: FeedSource
  onChange: (next: FeedSource) => void
  status: 'idle' | 'requesting' | 'live' | 'denied' | 'unavailable'
  onStart: () => void
}) {
  const live = source === 'camera'

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Button
        size="sm"
        variant={live ? 'default' : 'outline'}
        onClick={() => {
          if (live) {
            onChange('synthetic')
          } else {
            onChange('camera')
            if (status !== 'live') onStart()
          }
        }}
      >
        {live ? 'camera on' : 'use camera'}
      </Button>

      {status === 'requesting' && (
        <span className="font-mono text-xs text-ink-faint">requesting…</span>
      )}
      {status === 'denied' && (
        <span className="font-mono text-xs text-danger">
          camera blocked — falling back to the synthetic disk
        </span>
      )}
      {status === 'unavailable' && (
        <span className="font-mono text-xs text-latency">
          no camera available — using the synthetic disk
        </span>
      )}
    </div>
  )
}