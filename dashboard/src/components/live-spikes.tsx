/**
 * Live spike raster panel.
 *
 * Renders whatever `predictSpikes` produced for the current camera frame. The model itself lives
 * in lib/spike-encoder.ts, separate from this view.
 */

import {
  BASE_LATENCY_MS,
  GAIN_MS,
  MIN_LATENCY_MS,
  SPIKE_GROUPS,
  WINDOW_MS,
  type LiveSpike,
} from '@/lib/spike-encoder'

interface Props {
  grid: readonly number[] | null
  spikes: readonly LiveSpike[]
}

export function LiveSpikePanel({ grid, spikes }: Props) {
  if (!grid) {
    return (
      <section className="rounded-lg border border-border bg-surface p-4">
        <h2 className="text-sm font-medium text-ink">Live spikes</h2>
        <p className="mt-1 font-mono text-xs text-ink-faint">
          waiting for the second camera frame…
        </p>
      </section>
    )
  }

  const padLeft = 96
  const padRight = 34
  const rowHeight = 26
  const height = SPIKE_GROUPS.length * rowHeight + 16
  const width = 600
  const plotWidth = width - padLeft - padRight

  return (
    <section className="rounded-lg border border-border bg-surface p-4">
      <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-sm font-medium text-ink">
          Live spikes — encoder output from your camera
        </h2>
        <span className="font-mono text-xs text-ink-faint">0–{WINDOW_MS} ms window</span>
      </div>

      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="w-full"
        role="img"
        aria-label="Live spike raster computed from camera motion"
      >
        {SPIKE_GROUPS.map(({ group, label }, rowIndex) => {
          const y = rowIndex * rowHeight + 18
          const ticks = spikes.filter((s) => s.group === group)
          return (
            <g key={group}>
              <text
                x={0}
                y={y + 3}
                fill="var(--color-ink-faint)"
                fontSize={10}
                fontFamily="var(--font-mono)"
              >
                {label}
              </text>
              <line
                x1={padLeft}
                y1={y}
                x2={padLeft + plotWidth}
                y2={y}
                stroke="var(--color-border)"
                strokeWidth={0.5}
              />
              {ticks.map((s, i) => (
                <line
                  key={`${group}-${i}`}
                  x1={padLeft + Math.min(1, s.t) * plotWidth}
                  y1={y - 7}
                  x2={padLeft + Math.min(1, s.t) * plotWidth}
                  y2={y + 7}
                  stroke="var(--color-spike)"
                  strokeWidth={1 + s.strength * 2}
                  opacity={0.35 + s.strength * 0.65}
                />
              ))}
              <text
                x={width}
                y={y + 3}
                fill="var(--color-spike)"
                fontSize={10}
                fontFamily="var(--font-mono)"
                textAnchor="end"
              >
                {ticks.length}
              </text>
            </g>
          )
        })}
      </svg>

      <div className="mt-2 font-mono text-xs text-ink-faint">
        Left edge is {MIN_LATENCY_MS} ms, the earliest the encoder can fire. Sharper luminance
        change pulls spikes left.
      </div>

      <p className="mt-3 text-xs leading-relaxed text-ink-faint">
        Spike timing is computed from your frames using the same contrast-onset rule as the
        offline run: sharper change fires earlier, by up to {GAIN_MS} ms, against a{' '}
        {BASE_LATENCY_MS} ms baseline. This is the <em>encoder</em>, the last step before the
        network — the 19,267 neurons are not simulated here, so these are predicted input times,
        not measured neural output.
      </p>
    </section>
  )
}