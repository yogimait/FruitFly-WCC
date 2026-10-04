/**
 * Camera toggle with an honest label and an honest failure state.
 *
 * Lives apart from the useCamera hook so both files export only what they should: this one only
 * components, the hook only logic. Mixing them breaks React Fast Refresh.
 */

import { Button } from '@/components/ui/button'
import type { FeedSource } from '@/lib/useCamera'

export type CameraStatus = 'idle' | 'requesting' | 'live' | 'denied' | 'unavailable'

export function CameraToggle({
  source,
  onChange,
  status,
  onStart,
}: {
  source: FeedSource
  onChange: (next: FeedSource) => void
  status: CameraStatus
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