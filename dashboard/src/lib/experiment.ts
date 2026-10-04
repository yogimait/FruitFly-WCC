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

/**
 * One point on the angular-size sweep.
 *
 * `latencyMs` is the headline measurement; `responseHz` is the rate readout that saturates.
 * Both are kept so the saturation story is visible in the same chart as the latency story.
 */
export interface SweepPoint {
  readonly angularSizeDeg: number
  readonly latencyMs: number | null
  readonly responseHz: number | null
  readonly saturated: boolean
}

export interface ExperimentState {
  readonly status: 'idle' | 'running' | 'complete' | 'failed'
  readonly message: string | null
  /** Set when the measurement API could not be reached or returned a failure envelope. */
  readonly serverError?: string | null

  /** Stimulus angular size in degrees, the sweep axis. */
  readonly angularSizeDeg: number | null
  /** Elapsed simulated milliseconds for the current run. */
  readonly simulatedMs: number | null

  readonly lplc2: Lplc2Stats | null
  readonly giantFiber: GiantFiberStats | null
  readonly trials: readonly LatencyTrial[]
  readonly separability: readonly SeparabilityPair[]
  readonly sweep: readonly SweepPoint[]

  /** Every spike time by neuron group, for the raster. */
  readonly raster: readonly RasterRow[]

  /** Milliseconds the raster window spans, so the axis matches the measured tick range. */
  readonly rasterWindowMs?: number

  /**
   * Measured findings, served alongside the live view. Each section maps to one file-backed
   * measurement; nothing here is computed in the browser.
   */
  readonly findings?: {
    readonly window?: {
      readonly unsaturated_windows_ms: readonly number[]
      readonly saturated_windows_ms: readonly number[]
      readonly boundary_ms: number | null
      readonly both_regimes_observed: boolean
      readonly statement: string
    }
    readonly attribution?: {
      readonly model_percent: Record<string, number>
      readonly published_percent: Record<string, number>
    }
    readonly causality?: {
      readonly control: number
      readonly without_lplc2_output: number
      readonly without_lc4_output: number
      readonly without_both: number
      readonly lplc2_required: boolean
      readonly lc4_required: boolean
      readonly either_required: boolean
      readonly zero_drive_spikes: number
      readonly driven_spikes: number
      readonly stimulus_reaches_network: boolean
    }
    readonly driveSweep?: {
      readonly window_ms: number
      readonly rows: readonly {
        readonly fraction: number
        readonly neurons_driven: number
        readonly lplc2_spikes: number
        readonly dnp01_spikes: number
        readonly first_spike_ms: number | null
      }[]
      readonly dnp01_values: readonly number[]
      readonly invariant: boolean
      readonly statement: string
    }
    readonly reproducibility?: {
      readonly trials: readonly { readonly seed: number; readonly dnp01_spikes: number }[]
      readonly spread: number
      readonly reproducible: boolean
      readonly note: string
    }
    readonly verdict?: Record<string, boolean>
    readonly meta?: {
      readonly subset_neurons: number
      readonly subset_edges: number
      readonly lplc2_neurons: number
      readonly lc4_neurons: number
      readonly dnp01_neurons: number
      readonly step_ms: number
    }
  }
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
  /**
   * Refractory ceiling for a 0.3 s window at 0.1 ms steps: one spike per step bounds the
   * maximum measurable rate at ~333 Hz per neuron. Source project measurements sit near
   * 400 Hz across longer windows.
   */
  readonly refractoryCeilingHz: number
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
  refractoryCeilingHz: 400,
}