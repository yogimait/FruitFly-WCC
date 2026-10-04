import { useCallback, useEffect, useRef, useState } from 'react'

export type FeedSource = 'synthetic' | 'camera'

/**
 * Photoreceptor sampling grid, box-averaged.
 *
 * Resolution is a real trade-off, and both extremes were measured and rejected:
 *
 *   8x8, point-sampled  - a block spans 80x60 px, so a face moving slowly changes almost
 *                         nothing and real motion fell below any usable bar.
 *   40x40, point-sampled - reads raw per-pixel sensor jitter; a still webcam measured a
 *                         peak of 17 luminance levels of pure noise.
 *
 * 16x16 box-averaged balances the two: each block is 40x30 px, which is wide enough to average
 * out compression and sensor noise but small enough that a moving face still shifts several
 * block means. 256 samples also sits below the connectome's 4,107 photoreceptor input ports, so
 * this is a coarse sampling of a real input layer rather than an invented one.
 *
 * Exported because the sampling canvas must be exactly this size. When the two disagreed, the
 * canvas was 8x8 while `drawImage` targeted 16x16: only the top-left quadrant of the frame was
 * sampled and the remaining half of the grid read as permanently zero.
 */
export const CAMERA_GRID = 16

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
  /**
   * Per-cell motion energy on the 8x8 grid, as absolute luminance change in 0-255 units.
   * Real measured data, deliberately not normalised — see the comment where it is set.
   */
  const [grid, setGrid] = useState<number[] | null>(null)

  // Previous downsampled frame, for the motion measure the encoder actually uses.
  const prevRef = useRef<Uint8ClampedArray | null>(null)

  /**
   * Exponential smoothing over frames.
   *
   * A webcam delivers noisy frames, and per-frame differencing makes even a stationary subject
   * flicker. Smoothing keeps a genuinely still scene still while still tracking real movement
   * within a couple of frames.
   */
  const SMOOTHING = 0.35

  const smoothRef = useRef<number[] | null>(null)

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
    const GRID = CAMERA_GRID

    const tick = () => {
      const video = videoRef.current
      const canvas = canvasRef.current
      if (video && canvas && video.videoWidth > 0) {
        const ctx = canvas.getContext('2d', { willReadFrequently: true })
        if (ctx) {
          ctx.drawImage(video, 0, 0, GRID, GRID)
          const { data } = ctx.getImageData(0, 0, GRID, GRID)

          const raw_cells = new Array<number>(GRID * GRID).fill(0)
          let total = 0

          if (prevRef.current) {
            const prev = prevRef.current
            for (let cell = 0; cell < GRID * GRID; cell++) {
              const d = Math.abs(data[cell * 4] - prev[cell * 4])
              raw_cells[cell] = d
              total += d
            }
          }
          const mean = total / (GRID * GRID * 255)

          // Smooth the per-cell field so a stationary subject does not flicker.
          const prevSmooth = smoothRef.current
          const smoothed = prevSmooth
            ? raw_cells.map((v, i) => prevSmooth[i] * (1 - SMOOTHING) + v * SMOOTHING)
            : raw_cells
          smoothRef.current = smoothed

          // Cells are reported as ABSOLUTE luminance change (0-255), not normalised against
          // the frame's own peak. Normalising by the peak made the result depend on how
          // bright the strongest change happened to be: a synthetic high-contrast bar reads
          // 1.0 and drives the encoder, while a real face under room light peaks near 4
          // levels and reads ~0.15, below any drive threshold. Absolute values make both
          // cases behave the same way and let the encoder apply one fixed criterion.
          setGrid(smoothed)

          prevRef.current = new Uint8ClampedArray(data)
          setMotionRaw(mean)
          // Baseline floor keeps a still scene visibly alive rather than looking switched off.
          setMotion(Math.min(1, 0.15 + Math.sqrt(Math.min(1, mean * 7)) * 0.85))
        }
      }
      raf = requestAnimationFrame(tick)
    }

    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [source, status])

  useEffect(() => () => streamRef.current?.getTracks().forEach((t) => t.stop()), [])

  // Measurement hook. The noise floor and the drive threshold are chosen from measured values
  // (scripts/measure_noise_floor.py), and neither is guessable from the rendered UI. Exposing
  // the raw grid lets that script read the same numbers the encoder reads, instead of inferring
  // them from a screenshot. Read-only, and only useful while the camera is live.
  useEffect(() => {
    const w = window as unknown as Record<string, unknown>
    w.__gridProbe = () => grid
    return () => {
      delete w.__gridProbe
    }
  }, [grid])

  return { videoRef, canvasRef, status, motion, motionRaw, grid, start, stop }
}
