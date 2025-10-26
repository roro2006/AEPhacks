const API_BASE = 'http://localhost:5000/api'

export interface WeatherParams {
  ambient_temp: number
  wind_speed: number
  wind_angle: number
  sun_time: number
  date: string
}

export interface LineRating {
  name: string
  branch_name: string
  conductor: string
  MOT: number
  voltage_kv: number
  rating_amps: number
  rating_mva: number
  static_rating_mva: number
  flow_mva: number
  loading_pct: number
  margin_mva: number
  stress_level: 'normal' | 'caution' | 'high' | 'critical'
  bus0: string
  bus1: string
}

export interface Summary {
  total_lines: number
  overloaded_lines: number
  high_stress_lines: number
  caution_lines: number
  avg_loading: number
  max_loading: number
  critical_lines: Array<{
    name: string
    branch_name: string
    loading_pct: number
    margin_mva: number
  }>
}

export interface RatingResponse {
  weather: WeatherParams
  lines: LineRating[]
  summary: Summary
}

export interface GridTopology {
  lines: any
  buses: any
}

export interface ThresholdPoint {
  temperature: number
  overloaded_lines: number
  high_stress_lines: number
  avg_loading: number
  max_loading: number
}

export interface ThresholdResponse {
  temperature_range: [number, number]
  wind_speed: number
  first_overload_temp: number | null
  progression: ThresholdPoint[]
}

export async function fetchLineRatings(weather: WeatherParams): Promise<RatingResponse> {
  const response = await fetch(`${API_BASE}/lines/ratings`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(weather),
  })

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`)
  }

  return response.json()
}

export async function fetchGridTopology(): Promise<GridTopology> {
  const response = await fetch(`${API_BASE}/grid/topology`)

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`)
  }

  return response.json()
}

export async function fetchThresholdAnalysis(
  tempRange: [number, number],
  windSpeed: number,
  step: number = 1
): Promise<ThresholdResponse> {
  const response = await fetch(`${API_BASE}/lines/threshold`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      temp_range: tempRange,
      wind_speed: windSpeed,
      step,
    }),
  })

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`)
  }

  return response.json()
}

export async function analyzeContingency(
  outageLine: string,
  weather: WeatherParams
): Promise<any> {
  const response = await fetch(`${API_BASE}/contingency/n1`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      outage_line: outageLine,
      ...weather,
    }),
  })

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`)
  }

  return response.json()
}

export interface MapResponse {
  map_html: string
  summary: Summary
  weather: WeatherParams
}

export interface LineDetails {
  found: boolean
  name?: string
  branch_name?: string
  loading_pct?: number
  stress_level?: string
  rating_mva?: number
  flow_mva?: number
  margin_mva?: number
  voltage_kv?: number
  conductor?: string
  connections?: string
  message?: string
}

export async function fetchMapHTML(weather: WeatherParams): Promise<MapResponse> {
  const response = await fetch(`${API_BASE}/map/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(weather),
  })

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`)
  }

  return response.json()
}

export async function fetchLineDetails(
  lineId: string,
  weather: WeatherParams
): Promise<LineDetails> {
  const response = await fetch(`${API_BASE}/map/line/${lineId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(weather),
  })

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`)
  }

  return response.json()
}

// Outage Simulation Types and Functions

export interface AvailableLine {
  name: string
  bus0: string
  bus1: string
  s_nom: number
  description: string
}

export interface AvailableLinesResponse {
  success: boolean
  lines: AvailableLine[]
  total_count: number
}

export interface LineLoadingChange {
  name: string
  bus0: string
  bus1: string
  s_nom: number
  flow_mw: number
  flow_mva: number
  loading_pct: number
  baseline_loading_pct: number
  loading_change_pct: number
  is_active: boolean
  is_outaged: boolean
  status: 'outaged' | 'overloaded' | 'high_stress' | 'caution' | 'normal'
}

export interface IslandedBus {
  bus_id: string
  bus_name: string
  voltage_kv: number
  x: number
  y: number
}

export interface OutageMetrics {
  total_lines: number
  outaged_lines_count: number
  active_lines_count: number
  overloaded_count: number
  high_stress_count: number
  affected_lines_count: number
  islanded_buses_count: number
  max_loading_pct: number
  avg_loading_pct: number
  max_loading_increase: number
  baseline_max_loading: number
  baseline_avg_loading: number
}

export interface OutageSimulationResult {
  success: boolean
  outage_lines: string[]
  overloaded_lines: LineLoadingChange[]
  high_stress_lines: LineLoadingChange[]
  loading_changes: LineLoadingChange[]
  islanded_buses: IslandedBus[]
  affected_lines: LineLoadingChange[]
  metrics: OutageMetrics
  power_flow_info?: {
    converged: boolean
    max_error?: number
    linear: boolean
  }
  error?: string
}

export async function fetchAvailableLines(): Promise<AvailableLinesResponse> {
  const response = await fetch(`${API_BASE}/outage/available-lines`)

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`)
  }

  return response.json()
}

export async function simulateOutage(
  outageLines: string[],
  useLpf: boolean = false
): Promise<OutageSimulationResult> {
  const response = await fetch(`${API_BASE}/outage/simulate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      outage_lines: outageLines,
      use_lpf: useLpf,
    }),
  })

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`)
  }

  return response.json()
}

export async function fetchOutageMapHTML(
  outageResult: OutageSimulationResult
): Promise<MapResponse> {
  const response = await fetch(`${API_BASE}/map/outage`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      outage_result: outageResult,
    }),
  })

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`)
  }

  return response.json()
}
