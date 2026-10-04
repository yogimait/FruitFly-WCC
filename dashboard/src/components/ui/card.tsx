import type { ComponentProps } from 'react'

import { cn } from '@/lib/utils'

type CardProps = ComponentProps<'section'>

export function Card({ className, ...props }: CardProps) {
  return (
    <section
      className={cn('rounded-lg border border-border bg-surface p-4', className)}
      {...props}
    />
  )
}

type CardHeaderProps = ComponentProps<'header'>

export function CardHeader({ className, ...props }: CardHeaderProps) {
  return (
    <header
      className={cn('mb-3 flex items-baseline justify-between gap-3', className)}
      {...props}
    />
  )
}

type CardTitleProps = ComponentProps<'h2'>

export function CardTitle({ className, ...props }: CardTitleProps) {
  return <h2 className={cn('text-sm font-medium text-ink', className)} {...props} />
}

type CardDescriptionProps = ComponentProps<'p'>

export function CardDescription({ className, ...props }: CardDescriptionProps) {
  return <p className={cn('text-xs text-ink-faint', className)} {...props} />
}