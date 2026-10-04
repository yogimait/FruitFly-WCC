import type { ComponentProps } from 'react'

import { cn } from '@/lib/utils'

type ProgressProps = ComponentProps<'div'> & {
  value: number
  max?: number
  tone?: 'spike' | 'latency' | 'target'
}

const toneClass = {
  spike: 'bg-spike',
  latency: 'bg-latency',
  target: 'bg-target',
}

export function Progress({
  value,
  max = 100,
  tone = 'spike',
  className,
  ...props
}: ProgressProps) {
  const pct = max > 0 ? Math.min(100, Math.max(0, (value / max) * 100)) : 0

  return (
    <div
      role="progressbar"
      aria-valuenow={value}
      aria-valuemin={0}
      aria-valuemax={max}
      className={cn('h-1.5 w-full overflow-hidden rounded-full bg-surface-raised', className)}
      {...props}
    >
      <div
        className={cn('h-full transition-[width] duration-150', toneClass[tone])}
        style={{ width: `${pct}%` }}
      />
    </div>
  )
}