import { cva, type VariantProps } from 'class-variance-authority'
import type { ComponentProps } from 'react'

import { cn } from '@/lib/utils'

const badgeVariants = cva(
  'inline-flex items-center rounded-md border px-2 py-0.5 font-mono text-xs whitespace-nowrap',
  {
    variants: {
      tone: {
        neutral: 'border-border bg-surface-raised text-ink-muted',
        spike: 'border-spike/40 bg-spike/10 text-spike',
        latency: 'border-latency/40 bg-latency/10 text-latency',
        target: 'border-target/40 bg-target/10 text-target',
        danger: 'border-danger/40 bg-danger/10 text-danger',
      },
    },
    defaultVariants: { tone: 'neutral' },
  },
)

type BadgeProps = ComponentProps<'span'> & VariantProps<typeof badgeVariants>

export function Badge({ className, tone, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ tone }), className)} {...props} />
}