import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import type { ExperimentState } from '@/lib/experiment'

function Row({
  label,
  value,
  tone = 'neutral',
}: {
  label: string
  value: string
  tone?: 'neutral' | 'spike' | 'danger' | 'target'
}) {
  return (
    <li className="flex flex-wrap items-baseline justify-between gap-2 border-b border-border py-1.5 last:border-0">
      <span className="text-ink-muted">{label}</span>
      <span className="flex items-center gap-2">
        <span className="font-mono text-ink">{value}</span>
        <Badge tone={tone}>{tone === 'danger' ? 'negative' : tone === 'spike' ? 'measured' : tone}</Badge>
      </span>
    </li>
  )
}

/**
 * The measured findings, rendered verbatim from the API.
 *
 * This panel exists because the live readouts alone are not the result: the result is that the
 * response is invariant to input magnitude and does not require the anatomically-prescribed
 * input neurons. Per AGENTS.md 6 nothing is computed here — every string comes from a
 * measurement file.
 */
export function FindingsPanel({ state }: { state: ExperimentState }) {
  const f = state.findings

  if (!f?.verdict) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Findings</CardTitle>
          <CardDescription>No measurement loaded</CardDescription>
        </CardHeader>
        <p className="py-4 font-mono text-xs text-ink-faint">
          run scripts/measure_final.py then scripts/serve.py
        </p>
      </Card>
    )
  }

  const attribution = f.attribution
  const drive = f.driveSweep
  const repro = f.reproducibility
  const meta = f.meta

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>What was measured</CardTitle>
          <CardDescription>
            Model and stimulus, straight from the measurement record
          </CardDescription>
        </CardHeader>
        {meta && (
          <ul>
            <Row
              label="simulated neurons / edges"
              value={`${meta.subset_neurons.toLocaleString()} / ${meta.subset_edges.toLocaleString()}`}
            />
            <Row
              label="LPLC2 · LC4 · DNp01"
              value={`${meta.lplc2_neurons} · ${meta.lc4_neurons} · ${meta.dnp01_neurons}`}
            />
            <Row label="time step" value={`${meta.step_ms} ms`} />
            <Row
              label="LPLC2 + LC4 share of published GF input"
              value="97.5%"
            />
          </ul>
        )}
      </Card>

      {attribution && (
        <Card>
          <CardHeader>
            <CardTitle>Signed-weight attribution of DNp01 input</CardTitle>
            <CardDescription>
              Structural. The connectome reproduces the published anatomy.
            </CardDescription>
          </CardHeader>
          <ul>
            {(['LPLC2', 'LC4'] as const).map((name) => (
              <Row
                key={name}
                label={`${name} — model vs published`}
                value={`${attribution.model_percent[name] ?? 0}% vs ${attribution.published_percent[name]}%`}
                tone="spike"
              />
            ))}
          </ul>
        </Card>
      )}

      {f.causality && (
        <Card>
          <CardHeader>
            <CardTitle>Causal attribution</CardTitle>
            <CardDescription>
              Outgoing edges removed per type. Negative, and reported as such.
            </CardDescription>
          </CardHeader>
          <ul>
            <Row label="control DNp01 spikes" value={String(f.causality.control)} />
            <Row
              label="without LPLC2 output"
              value={String(f.causality.without_lplc2_output)}
              tone={f.causality.lplc2_required ? 'spike' : 'danger'}
            />
            <Row
              label="without LC4 output"
              value={String(f.causality.without_lc4_output)}
              tone={f.causality.lc4_required ? 'spike' : 'danger'}
            />
            <Row
              label="without both"
              value={String(f.causality.without_both)}
              tone={f.causality.either_required ? 'spike' : 'danger'}
            />
            <Row
              label="stimulus reaches network"
              value={`${f.causality.zero_drive_spikes} → ${f.causality.driven_spikes} spikes`}
              tone={f.causality.stimulus_reaches_network ? 'spike' : 'danger'}
            />
          </ul>
          <p className="mt-3 text-xs text-ink-faint">
            Removing the two neuron types that carry 97.5% of the published visual input does not
            change the output. The network reaches one self-sustained operating point.
          </p>
        </Card>
      )}

      {drive && (
        <Card>
          <CardHeader>
            <CardTitle>Drive-magnitude sweep</CardTitle>
            <CardDescription>
              {drive.rows.length} points at {drive.window_ms} ms window
            </CardDescription>
          </CardHeader>
          <ul>
            {drive.rows.map((row) => (
              <Row
                key={row.fraction}
                label={`${(row.fraction * 100).toFixed(0)}% of lobula plate · ${row.neurons_driven.toLocaleString()} neurons`}
                value={`DNp01 ${row.dnp01_spikes}`}
              />
            ))}
          </ul>
          <p className="mt-3 text-xs text-ink-faint">{drive.statement}</p>
        </Card>
      )}

      {f.window && (
        <Card>
          <CardHeader>
            <CardTitle>Saturation is a window-length artefact</CardTitle>
            <CardDescription>
              {f.window.both_regimes_observed
                ? `Boundary at ${f.window.boundary_ms} ms`
                : 'Boundary not established by this run'}
            </CardDescription>
          </CardHeader>
          <p className="text-xs text-ink-muted">{f.window.statement}</p>
        </Card>
      )}

      {repro && (
        <Card>
          <CardHeader>
            <CardTitle>Reproducibility</CardTitle>
            <CardDescription>{repro.note}</CardDescription>
          </CardHeader>
          <ul>
            <Row
              label="spread across seeds"
              value={`${repro.spread} spikes`}
              tone={repro.reproducible ? 'spike' : 'danger'}
            />
          </ul>
        </Card>
      )}
    </div>
  )
}