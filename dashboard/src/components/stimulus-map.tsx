/**
 * Live stimulus map: the 8x8 per-cell motion energy measured from the camera.
 *
 * This replaces the recorded spike raster while the camera is live, because that raster is
 * measured from the synthetic disk and would sit at zero while a real scene was driving the
 * stimulus — looking broken and implying the network had gone quiet.
 *
 * What is shown here is real: mean absolute luminance change per cell, on the same 8x8 grid
 * the encoder samples, computed in this browser from the camera frames. It is the stimulus
 * reaching the encoder, not a simulated neural response, and the panel says so.
 */

interface Props {
  grid: readonly number[] | null
  raw: number
  normalised: number
}

export function StimulusMapPanel({ grid, raw, normalised }: Props) {
  const cells = 64

  if (!grid) {
    return (
      <section className="rounded-lg border border-border bg-surface p-4">
        <h2 className="text-sm font-medium text-ink">Live stimulus map</h2>
        <p className="mt-1 font-mono text-xs text-ink-faint">
          waiting for the second camera frame…
        </p>
      </section>
    )
  }

  return (
    <section className="rounded-lg border border-border bg-surface p-4">
      <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-sm font-medium text-ink">
          Live stimulus map — 8×8 motion energy
        </h2>
        <span className="font-mono text-xs text-ink-faint">from your camera</span>
      </div>

      <div className="flex flex-wrap items-start gap-5">
        <div
          className="grid shrink-0 gap-px"
          style={{ gridTemplateColumns: 'repeat(8, 1fr)' }}
          role="img"
          aria-label="8 by 8 heatmap of per-cell motion energy from the camera"
        >
          {Array.from({ length: cells }, (_, i) => {
            const v = grid[i] ?? 0
            // Green at rest, hot at high energy, so activity is obvious at a glance.
            const hue = 150 - v * 140
            return (
              <div
                key={i}
                className="h-5 w-5 rounded-[2px]"
                style={{
                  background: `hsl(${hue} 85% ${18 + v * 55}%)`,
                  opacity: 0.35 + v * 0.65,
                }}
                title={`cell ${Math.floor(i / 8)},${i % 8}: ${v.toFixed(3)}`}
              />
            )
          })}
        </div>

        <dl className="min-w-0 flex-1 space-y-1.5 font-mono text-xs">
          <div className="flex justify-between gap-3">
            <dt className="text-ink-faint">measured motion</dt>
            <dd className="text-ink">{raw.toFixed(4)}</dd>
          </div>
          <div className="flex justify-between gap-3">
            <dt className="text-ink-faint">response level</dt>
            <dd className="text-spike">{(normalised * 100).toFixed(0)}%</dd>
          </div>
          <div className="flex justify-between gap-3">
            <dt className="text-ink-faint">hot cells</dt>
            <dd className="text-ink">
              {grid.filter((v) => v > 0.35).length} / {cells}
            </dd>
          </div>
        </dl>
      </div>

      <p className="mt-3 text-xs leading-relaxed text-ink-faint">
        Each square is one cell of the grid the encoder samples, shaded by how much that cell
        changed since the previous frame. Brighter means more motion energy reaching the
        encoder. This is your camera, measured live — not a simulated neural response.
      </p>
    </section>
  )
}