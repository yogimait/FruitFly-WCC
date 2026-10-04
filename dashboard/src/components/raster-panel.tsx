import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import type { ExperimentState, RasterRow } from '@/lib/experiment'

const AXIS_STROKE = 'var(--color-border)'
const SPIKE_STROKE = 'var(--color-spike)'

/**
 * Spike raster: one row per neuron group, spikes plotted as ticks on a shared time axis.
 *
 * The window is supplied by the measurement rather than hard-coded, so ticks fill the axis
 * instead of being compressed into the first fraction of a fixed 100 ms span.
 *
 * SVG rather than canvas because the row count is small (a handful of groups) and the markup
 * stays inspectable during a live demo.
 */
function Raster({ rows, windowMs }: { rows: readonly RasterRow[]; windowMs: number }) {
  if (rows.length === 0) {
    return (
      <p className="py-6 text-center font-mono text-xs text-ink-faint">
        no spikes recorded
      </p>
    )
  }

  const height = Math.max(rows.length * 18, 60)
  const width = 600

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="w-full"
      role="img"
      aria-label="Spike raster by neuron group"
    >
      {rows.map((row, rowIndex) => {
        const y = rowIndex * 18 + 9
        return (
          <g key={row.group}>
            <line
              x1={0}
              y1={y}
              x2={width}
              y2={y}
              stroke={AXIS_STROKE}
              strokeWidth={0.5}
            />
            {row.spikesMs
              .filter((t) => t >= 0 && t <= windowMs)
              .map((t, i) => (
                <line
                  key={`${row.group}-${i}`}
                  x1={(t / windowMs) * width}
                  y1={y - 5}
                  x2={(t / windowMs) * width}
                  y2={y + 5}
                  stroke={SPIKE_STROKE}
                  strokeWidth={1.5}
                />
              ))}
          </g>
        )
      })}
    </svg>
  )
}

export function RasterPanel({ state }: { state: ExperimentState }) {
  const windowMs = state.rasterWindowMs ?? 40

  return (
    <Card>
      <CardHeader>
        <CardTitle>Spike raster</CardTitle>
        <CardDescription>
          0–{windowMs} ms · T4/T5 drive in, DNp01 out
        </CardDescription>
      </CardHeader>

      <Raster rows={state.raster} windowMs={windowMs} />

      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 font-mono text-xs text-ink-faint">
        {state.raster.map((row) => (
          <span key={row.group}>
            {row.group} <span className="text-spike">{row.spikesMs.length}</span>
          </span>
        ))}
      </div>

      <p className="mt-3 text-xs text-ink-faint">
        Computational experiment. Neural activity does not imply biological preference,
        attraction, or learning — nothing in this pipeline trains or updates weights.
      </p>
    </Card>
  )
}