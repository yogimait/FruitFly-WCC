import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  REFERENCE,
  type ExperimentState,
  type SweepPoint,
} from '@/lib/experiment'

const AXIS = { stroke: 'var(--color-ink-faint)', fontSize: 11 }
const GRID = 'var(--color-border)'

const TOOLTIP_STYLE = {
  background: 'var(--color-surface-raised)',
  border: '1px solid var(--color-border)',
  borderRadius: 6,
  fontSize: 12,
} as const

type TooltipValue =
  | number
  | string
  | ReadonlyArray<number | string>
  | null
  | undefined

/**
 * Recharts hands the formatter a loose `ValueType | undefined`, not a narrowed numeric
 * type. Coerce here rather than casting at each call site: a null reading must render as
 * "no response", never as 0 (AGENTS.md §6).
 */
function toFinite(value: TooltipValue): number | null {
  if (value === null || value === undefined) return null
  const n = typeof value === 'number' ? value : Number(Array.isArray(value) ? value[0] : value)
  return Number.isFinite(n) ? n : null
}

function formatMs(value: TooltipValue) {
  const n = toFinite(value)
  return n === null ? 'no response' : `${n.toFixed(2)} ms`
}

function formatHz(value: TooltipValue) {
  const n = toFinite(value)
  return n === null ? 'no response' : `${n.toFixed(1)} Hz`
}

/** Recharts accepts a loose row type; ours is stricter, so bridge it once here. */
function toRows(sweep: readonly SweepPoint[]) {
  return sweep as unknown as Record<string, unknown>[]
}

/**
 * Latency across the angular-size sweep, against the published 42 deg threshold.
 *
 * The 42 deg line is the von Reyn eta-model prediction for where a real GF response peaks.
 * Whether our curve peaks there is the test. A curve that peaks at a sweep boundary means
 * the range was too narrow to locate the maximum, which is a failed test rather than a
 * result — see docs/Biological-Reference.md falsification criteria.
 */
export function SweepChart({ state }: { state: ExperimentState }) {
  const hasData = state.sweep.some((p) => p.latencyMs !== null)

  return (
    <Card>
      <CardHeader>
        <CardTitle>DNp01 latency vs stimulus size</CardTitle>
        <CardDescription>
          Published response peaks near {REFERENCE.sizeThresholdDeg.value}
          {REFERENCE.sizeThresholdDeg.unit}
        </CardDescription>
      </CardHeader>

      {!hasData ? (
        <p className="py-8 text-center font-mono text-xs text-ink-faint">
          sweep not measured
        </p>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={toRows(state.sweep)}>
            <CartesianGrid stroke={GRID} strokeDasharray="2 4" />
            <XAxis
              dataKey="angularSizeDeg"
              stroke={AXIS.stroke}
              fontSize={AXIS.fontSize}
              tickLine={false}
              label={{
                value: 'angular size (deg)',
                position: 'insideBottom',
                offset: -2,
                fill: 'var(--color-ink-faint)',
                fontSize: 11,
              }}
            />
            <YAxis
              stroke={AXIS.stroke}
              fontSize={AXIS.fontSize}
              tickLine={false}
              width={52}
              tickFormatter={(v: number) => `${v} ms`}
            />
            <Tooltip
              contentStyle={TOOLTIP_STYLE}
              formatter={(value) => [formatMs(value), 'measured']}
            />
            <ReferenceLine
              y={REFERENCE.latencyMs.value}
              stroke="var(--color-target)"
              strokeDasharray="4 4"
              label={{
                value: `published ${REFERENCE.latencyMs.value} ms`,
                fill: 'var(--color-target)',
                fontSize: 10,
                position: 'insideBottomRight',
              }}
            />
            <Line
              type="monotone"
              dataKey="latencyMs"
              stroke="var(--color-spike)"
              strokeWidth={2}
              dot={{ r: 3, fill: 'var(--color-spike)' }}
              connectNulls={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </Card>
  )
}

/**
 * Rate response across the sweep, with the refractory ceiling marked.
 *
 * This is the saturation story in one picture. A flat line at the ceiling means the output
 * is pinned and every latency derived from it is uninformative — the reason temporal coding
 * was chosen over rate coding in the first place.
 */
export function SaturationChart({ state }: { state: ExperimentState }) {
  const hasData = state.sweep.some((p) => p.responseHz !== null)
  const ceiling = REFERENCE.refractoryCeilingHz

  return (
    <Card>
      <CardHeader>
        <CardTitle>Descending-neuron rate vs stimulus size</CardTitle>
        <CardDescription>
          Refractory ceiling ~{ceiling} Hz · a flat line at the ceiling means the output is
          pinned
        </CardDescription>
      </CardHeader>

      {!hasData ? (
        <p className="py-8 text-center font-mono text-xs text-ink-faint">
          sweep not measured
        </p>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={toRows(state.sweep)}>
            <CartesianGrid stroke={GRID} strokeDasharray="2 4" />
            <XAxis
              dataKey="angularSizeDeg"
              stroke={AXIS.stroke}
              fontSize={AXIS.fontSize}
              tickLine={false}
              label={{
                value: 'angular size (deg)',
                position: 'insideBottom',
                offset: -2,
                fill: 'var(--color-ink-faint)',
                fontSize: 11,
              }}
            />
            <YAxis
              stroke={AXIS.stroke}
              fontSize={AXIS.fontSize}
              tickLine={false}
              width={52}
              domain={[0, Math.ceil(ceiling * 1.15)]}
              tickFormatter={(v: number) => `${v} Hz`}
            />
            <Tooltip
              contentStyle={TOOLTIP_STYLE}
              formatter={(value) => [formatHz(value), 'measured']}
            />
            <ReferenceLine
              y={REFERENCE.refractoryCeilingHz}
              stroke="var(--color-danger)"
              strokeDasharray="4 4"
              label={{
                value: 'refractory ceiling',
                fill: 'var(--color-danger)',
                fontSize: 10,
                position: 'insideBottomRight',
              }}
            />
            <Line
              type="monotone"
              dataKey="responseHz"
              stroke="var(--color-latency)"
              strokeWidth={2}
              dot={{ r: 3, fill: 'var(--color-latency)' }}
              connectNulls={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </Card>
  )
}