import { useEffect, useRef, useState } from 'react'

export type PlaybackState = 'idle' | 'running' | 'paused'

/**
 * Playback over the recorded stimulus sequence.
 *
 * The measurement is recorded, not recomputed, so the honest thing these controls can do is
 * replay what was measured, frame by frame, at the rate it was measured. Start runs it, Step
 * advances one frame, Stop returns to the start. They are wired to the real stimulus frames and
 * the real spike times, not to a fake animation.
 */
export function usePlayback(totalFrames: number, frameMs: number) {
  const [state, setState] = useState<PlaybackState>('idle')
  const [frame, setFrame] = useState(0)
  const timer = useRef<ReturnType<typeof setInterval> | null>(null)

  const clear = () => {
    if (timer.current !== null) {
      clearInterval(timer.current)
      timer.current = null
    }
  }

  useEffect(() => clear, [])

  const start = () => {
    clear()
    // Restart from the beginning if already finished.
    if (frame >= totalFrames - 1) setFrame(0)
    setState('running')
    timer.current = setInterval(() => {
      setFrame((prev) => {
        if (prev >= totalFrames - 1) {
          clear()
          setState('paused')
          return prev
        }
        return prev + 1
      })
    }, frameMs)
  }

  const step = () => {
    clear()
    setState('paused')
    setFrame((prev) => Math.min(totalFrames - 1, prev + 1))
  }

  const stop = () => {
    clear()
    setState('idle')
    setFrame(0)
  }

  return {
    state,
    frame,
    progress: totalFrames > 1 ? frame / (totalFrames - 1) : 0,
    isFinished: frame >= totalFrames - 1,
    start,
    step,
    stop,
  }
}