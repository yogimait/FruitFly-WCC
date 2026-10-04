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
import { type ExperimentState, type SweepPoint } from '@/lib/experiment'

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

function toFinite(value: TooltipValue): number | null {
  if (value === null || value === undefined) return null
  const n = typeof value === 'number' ? value : Number(Array.isArray(value) ? value[0] : value)
  return Number.isFinite(n) ? n : null
}

function formatHz(value: TooltipValue) {
  const n = toFinite(value)
  return n === null ? 'no response' : `${n.toFixed(0)} Hz`
}

function formatPct(value: TooltipValue) {
  const n = toFinite(value)
  return n === null ? 'no response' : `${n.toFixed(1)}% of ceiling`
}

/** Recharts accepts a loose row type; ours is stricter, so bridge it once here. */
function toRows(sweep: readonly SweepPoint[]) {
  return sweep as unknown as Record<string, unknown>[]
}

/**
 * DNp01 firing rate as a percentage of its refractory ceiling, against window length.
 *
 * The x-axis is the measurement window, not stimulus size. That is the whole point of this
 * chart: the same stimulus produces a different apparent response purely because of how long
 * you look. The dashed line is where the response would sit if it were pinned.
 */
export function SaturationChart({ state }: { state: ExperimentState }) {
  const rows = state.sweep.map((p) => ({
    windowMs: p.angularSizeDeg,
    percentOfCeiling:
      p.angularSizeDeg > 0 ? Math.min(100, (p.responseHz ?? 0) * 100) : null,
    saturated: p.saturated,
  }))
  const hasData = rows.some((r) => r.percentOfCeiling !== null)

  return (
    <Card>
      <CardHeader>
        <CardTitle>Response vs measurement window</CardTitle>
        <CardDescription>
          Same stimulus throughout. Only the window changes.
        </CardDescription>
      </CardHeader>

      {!hasData ? (
        <p className="py-8 text-center font-mono text-xs text-ink-faint">
          sweep not measured
        </p>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={toRows(rows as unknown as SweepPoint[])}>
            <CartesianGrid stroke={GRID} strokeDasharray="2 4" />
            <XAxis
              dataKey="windowMs"
              stroke={AXIS.stroke}
              fontSize={AXIS.fontSize}
              tickLine={false}
              label={{
                value: 'measurement window (ms)',
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
              unit="%"
              domain={[0, 105]}
            />
            <Tooltip
              contentStyle={TOOLTIP_STYLE}
              formatter={(value) => [formatPct(value), 'of refractory ceiling']}
            />
            <ReferenceLine
              y={100}
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
              dataKey="percentOfCeiling"
              stroke="var(--color-latency)"
              strokeWidth={2}
              dot={{ r: 3, fill: 'var(--color-latency)' }}
              connectNulls={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      )}

      {/* Recharts renders to canvas/SVG with no text, so the plotted numbers are unreachable
          for anyone not looking at the chart. This is the same data as a real table. */}
      <table className="sr-only">
        <caption>Response versus measurement window</caption>
        <thead>
          <tr>
            <th scope="col">Window (ms)</th>
            <th scope="col">Response (% of refractory ceiling)</th>
            <th scope="col">Saturated</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.windowMs}>
              <th scope="row">{r.windowMs}</th>
              <td>{r.percentOfCeiling === null ? 'not measured' : `${r.percentOfCeiling}%`}</td>
              <td>{r.saturated ? 'yes' : 'no'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  )
}

/**
 * How much the drive sweep actually varies the response.
 *
 * This is the negative result as a chart: the x-axis spans a 100x range of driven neurons and
 * the line does not move. A flat line here is the finding, not a failure to plot.
 */
export function SweepChart({ state }: { state: ExperimentState }) {
  const drive = state.findings?.driveSweep
  const rows = (drive?.rows ?? []).map((r) => ({
    neuronsDriven: r.neurons_driven,
    dnp01Spikes: r.dnp01_spikes,
  }))
  const hasData = rows.length > 0

  return (
    <Card>
      <CardHeader>
        <CardTitle>Does more input produce more response?</CardTitle>
        <CardDescription>
          {drive ? `${drive.window_ms} ms window` : 'No measurement loaded'}
        </CardDescription>
      </CardHeader>

      {!hasData ? (
        <p className="py-8 text-center font-mono text-xs text-ink-faint">
          drive sweep not measured
        </p>
      ) : (
        <>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={toRows(rows as unknown as SweepPoint[])}>
              <CartesianGrid stroke={GRID} strokeDasharray="2 4" />
              <XAxis
                dataKey="neuronsDriven"
                stroke={AXIS.stroke}
                fontSize={AXIS.fontSize}
                tickLine={false}
                label={{
                  value: 'lobula plate neurons driven (log-ish spacing)',
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
                width={40}
                tickFormatter={(v: number) => `${v}`}
              />
              <Tooltip
                contentStyle={TOOLTIP_STYLE}
                formatter={(value) => [formatHz(value), 'DNp01 spikes']}
              />
              <Line
                type="monotone"
                dataKey="dnp01Spikes"
                stroke="var(--color-spike)"
                strokeWidth={2}
                dot={{ r: 4, fill: 'var(--color-spike)' }}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>

          <p className="mt-3 rounded-md border border-danger/30 bg-danger/[0.06] px-3 py-2 text-xs leading-relaxed text-ink-muted">
            <strong className="text-danger">Flat line — that is the finding.</strong> The
            response is identical across a 100× range of drive, which is why stimulus magnitude
            cannot be read from this network.
          </p>

          {/* Text alternative for the chart above. A flat line is easy to miss and impossible
              to read without sight, and here the flatness IS the result. */}
          <table className="sr-only">
            <caption>DNp01 spike count versus number of lobula plate neurons driven</caption>
            <thead>
              <tr>
                <th scope="col">Neurons driven</th>
                <th scope="col">DNp01 spikes</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.neuronsDriven}>
                  <th scope="row">{r.neuronsDriven.toLocaleString()}</th>
                  <td>{r.dnp01Spikes}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </Card>
  )
}