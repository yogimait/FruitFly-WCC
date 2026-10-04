import { Badge } from '@/components/ui/badge'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { REFERENCE, type ExperimentState } from '@/lib/experiment'

function ms(value: number | null): string {
  return value === null ? 'not measured' : `${value.toFixed(2)} ms`
}

/**
 * The headline panel: measured DNp01 first-spike latency beside the published value.
 *
 * Per AGENTS.md §6 an unmeasured value renders as "not measured", never as 0. A zero here
 * would read as "instant response", which is a biological falsehood.
 */
export function LatencyPanel({ state }: { state: ExperimentState }) {
  const measured = state.giantFiber?.firstSpikeMs ?? null
  const reference = REFERENCE.latencyMs.value
  const saturated = state.giantFiber?.saturated ?? false

  return (
    <Card>
      <CardHeader>
        <CardTitle>DNp01 first-spike latency</CardTitle>
        <CardDescription>Measured against {REFERENCE.latencyMs.source}</CardDescription>
      </CardHeader>

      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <span className="font-mono text-3xl text-spike">{ms(measured)}</span>
        <span className="font-mono text-sm text-ink-faint">
          vs {reference} ms published
        </span>
      </div>

      <div className="mt-4 space-y-1">
        <div className="flex justify-between font-mono text-xs text-ink-faint">
          <span>0</span>
          <span>measured</span>
          <span>published {reference} ms</span>
        </div>
        <Progress
          value={measured ?? 0}
          max={reference * 2}
          tone="spike"
          aria-label="Measured latency against published value"
        />
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {saturated ? (
          <Badge tone="danger">SATURATED — result unreliable</Badge>
        ) : measured === null ? (
          <Badge tone="neutral">awaiting measurement</Badge>
        ) : (
          <Badge tone="spike">unpinned — measurement valid</Badge>
        )}
        {state.angularSizeDeg !== null && (
          <Badge tone="neutral">stimulus {state.angularSizeDeg}°</Badge>
        )}
      </div>

      {saturated && (
        <p className="mt-3 text-xs text-danger">
          Output is at its refractory ceiling, so this number reflects the ceiling rather
          than the stimulus. Report it as saturated regardless of the value.
        </p>
      )}

      <p className="mt-3 text-xs text-ink-faint">
        Our stimulus enters at the lobula columnar, not the retina, so this excludes
        retinal and lamina processing. We therefore predict a value below{' '}
        {reference} ms rather than equal to it.
      </p>
    </Card>
  )
}