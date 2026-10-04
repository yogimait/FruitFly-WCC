/**
 * Shapes returned by the Python measurement harness.
 *
 * These mirror the JSON written to `data/` by the experiment scripts. Per AGENTS.md §6,
 * every value rendered by the dashboard comes from a measured file on disk — never from
 * a placeholder. Fields that a given run did not measure stay `null` and the UI shows
 * "not measured" rather than a zero.
 */

/** A published value we are testing against. Source in docs/Biological-Reference.md. */
export interface ReferenceTarget {
  readonly label: string
  readonly value: number
  readonly unit: string
  readonly source: string
}

/** LPLC2 population, the input layer we drive. */
export interface Lplc2Stats {
  readonly neuronCount: number
  readonly meanRateHz: number
  readonly firstSpikeMs: number | null
}

/** DNp01 giant fiber, the output we can read. */
export interface GiantFiberStats {
  readonly spikeCount: number
  readonly rateHz: number
  /** First spike latency, stimulus onset to first DNp01 spike. The headline number. */
  readonly firstSpikeMs: number | null
  /** True when the output is at its refractory ceiling — the known confound. */
  readonly saturated: boolean
}

/** Temporal readout comparison across seeds, to show reproducibility. */
export interface LatencyTrial {
  readonly seed: number
  readonly firstSpikeMs: number | null
}

/** Pairwise separability between stimuli, above the noise floor. */
export interface SeparabilityPair {
  readonly a: string
  readonly b: string
  readonly distance: number
}

export interface ExperimentState {
  readonly status: 'idle' | 'running' | 'complete' | 'failed'
  readonly message: string | null

  /** Stimulus angular size in degrees, the sweep axis. */
  readonly angularSizeDeg: number | null
  /** Elapsed simulated milliseconds for the current run. */
  readonly simulatedMs: number | null

  readonly lplc2: Lplc2Stats | null
  readonly giantFiber: GiantFiberStats | null
  readonly trials: readonly LatencyTrial[]
  readonly separability: readonly SeparabilityPair[]

  /** Every spike time by neuron group, for the raster. */
  readonly raster: readonly RasterRow[]
}

export interface RasterRow {
  readonly group: string
  /** Spike times in ms. */
  readonly spikesMs: readonly number[]
}

export const REFERENCE: {
  readonly latencyMs: ReferenceTarget
  readonly sizeThresholdDeg: ReferenceTarget
  readonly gfVisualInputShare: ReferenceTarget
} = {
  latencyMs: {
    label: 'Published DNp01 sensory latency',
    value: 19,
    unit: 'ms',
    source: 'Ache et al. 2019, Curr Biol (delta_1 = 0.019 s)',
  },
  sizeThresholdDeg: {
    label: 'Published looming size threshold',
    value: 42,
    unit: 'deg',
    source: 'von Reyn et al. 2017, via Ache et al. 2019',
  },
  gfVisualInputShare: {
    label: 'GF visual input from LPLC2 + LC4',
    value: 97.5,
    unit: '%',
    source: 'Card & von Reyn; PLOS Biol 2025',
  },
}