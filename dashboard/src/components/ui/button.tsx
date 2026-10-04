import { cva, type VariantProps } from 'class-variance-authority'
import type { ComponentProps } from 'react'

import { cn } from '@/lib/utils'

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 rounded-md border font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-40',
  {
    variants: {
      variant: {
        default: 'border-transparent bg-spike text-background hover:opacity-90',
        outline: 'border-border bg-surface-raised text-ink hover:border-spike/50',
        ghost: 'border-transparent text-ink-muted hover:bg-surface-raised',
      },
      size: {
        default: 'h-9 px-4 text-sm',
        sm: 'h-7 px-2.5 text-xs',
      },
    },
    defaultVariants: { variant: 'default', size: 'default' },
  },
)

type ButtonProps = ComponentProps<'button'> & VariantProps<typeof buttonVariants>

export function Button({ className, variant, size, ...props }: ButtonProps) {
  return (
    <button className={cn(buttonVariants({ variant, size }), className)} {...props} />
  )
}