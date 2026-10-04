import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import type { ExperimentState } from '@/lib/experiment'

export function ReproPanel({ state }: { state: ExperimentState }) {
  const measured = state.trials.filter(
    (t): t is typeof t & { firstSpikeMs: number } => t.firstSpikeMs !== null,
  )
  const spread =
    measured.length > 1
      ? Math.max(...measured.map((t) => t.firstSpikeMs)) -
        Math.min(...measured.map((t) => t.firstSpikeMs))
      : null

  return (
    <Card>
      <CardHeader>
        <CardTitle>Reproducibility across seeds</CardTitle>
        <CardDescription>
          A latency that moves with the seed is not a measurement
        </CardDescription>
      </CardHeader>

      {state.trials.length === 0 ? (
        <p className="font-mono text-xs text-ink-faint">no trials recorded</p>
      ) : (
        <table className="w-full font-mono text-xs">
          <thead>
            <tr className="text-ink-faint">
              <th className="py-1 text-left font-normal">seed</th>
              <th className="py-1 text-right font-normal">first spike</th>
            </tr>
          </thead>
          <tbody>
            {state.trials.map((trial) => (
              <tr key={trial.seed} className="border-t border-border">
                <td className="py-1 text-ink-muted">{trial.seed}</td>
                <td className="py-1 text-right text-spike">
                  {trial.firstSpikeMs === null
                    ? 'no response'
                    : `${trial.firstSpikeMs.toFixed(2)} ms`}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {spread !== null && (
        <div className="mt-3 flex items-center gap-2">
          {spread < 1 ? (
            <Badge tone="spike">spread {spread.toFixed(2)} ms — reproducible</Badge>
          ) : (
            <Badge tone="latency">
              spread {spread.toFixed(2)} ms — exceeds 1 ms, treat as unreliable
            </Badge>
          )}
        </div>
      )}
    </Card>
  )
}

export function SeparabilityPanel({ state }: { state: ExperimentState }) {
  const pairs = state.separability

  return (
    <Card>
      <CardHeader>
        <CardTitle>Stimulus separability</CardTitle>
        <CardDescription>
          Rate-saturated readout gives ~0–1.2 Hz differences between stimuli. Does timing
          separate them?
        </CardDescription>
      </CardHeader>

      {pairs.length === 0 ? (
        <p className="font-mono text-xs text-ink-faint">no pairs measured</p>
      ) : (
        <ul className="space-y-1.5 font-mono text-xs">
          {pairs.map((pair) => (
            <li key={`${pair.a}-${pair.b}`} className="flex justify-between gap-3">
              <span className="truncate text-ink-muted">
                {pair.a} ↔ {pair.b}
              </span>
              <span className="text-spike">{pair.distance.toFixed(3)}</span>
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}