import { useState, useEffect } from 'react'
import { Zap, Loader2, AlertTriangle, Activity, TrendingUp } from 'lucide-react'
import {
  fetchAvailableLines,
  simulateOutage,
  type AvailableLine,
  type OutageSimulationResult,
} from '../services/api'

interface OutageAnalysisProps {
  onOutageComplete?: (result: OutageSimulationResult | null) => void
}

const OutageAnalysis: React.FC<OutageAnalysisProps> = ({ onOutageComplete }) => {
  const [availableLines, setAvailableLines] = useState<AvailableLine[]>([])
  const [selectedLines, setSelectedLines] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [loadingLines, setLoadingLines] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<OutageSimulationResult | null>(null)
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    loadAvailableLines()
  }, [])

  const loadAvailableLines = async () => {
    setLoadingLines(true)
    setError(null)
    try {
      const response = await fetchAvailableLines()
      setAvailableLines(response.lines)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load available lines')
    } finally {
      setLoadingLines(false)
    }
  }

  const runSimulation = async () => {
    if (selectedLines.length === 0) {
      setError('Please select at least one line to simulate outage')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const simulationResult = await simulateOutage(selectedLines, false)

      if (!simulationResult.success) {
        setError(simulationResult.error || 'Simulation failed')
        setResult(null)
        onOutageComplete?.(null)
      } else {
        setResult(simulationResult)
        // Notify parent component to update map
        onOutageComplete?.(simulationResult)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run outage simulation')
      setResult(null)
      onOutageComplete?.(null)
    } finally {
      setLoading(false)
    }
  }

  const toggleLineSelection = (lineName: string) => {
    setSelectedLines((prev) =>
      prev.includes(lineName)
        ? prev.filter((l) => l !== lineName)
        : [...prev, lineName]
    )
  }

  const clearSelection = () => {
    setSelectedLines([])
    setResult(null)
    setError(null)
    // Clear map back to normal view
    onOutageComplete?.(null)
  }

  const filteredLines = availableLines.filter((line) =>
    line.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
    line.name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'overloaded':
        return '#ef4444'
      case 'high_stress':
        return '#f97316'
      case 'caution':
        return '#eab308'
      case 'normal':
        return '#10b981'
      default:
        return '#9ca3af'
    }
  }

  return (
    <div style={{ padding: '1.5rem', color: '#f5f5f7' }}>
      {/* Header */}
      <div style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
          <Zap size={24} color="#eab308" />
          <h2 style={{ fontSize: '1.25rem', margin: 0 }}>
            Transmission Line Outage Simulation
          </h2>
        </div>
        <p style={{ color: '#9ca3af', fontSize: '0.875rem', margin: 0 }}>
          Simulate removal of transmission lines and analyze network stress impacts
        </p>
      </div>

      {/* Line Selection */}
      <div
        style={{
          background: 'rgba(255, 255, 255, 0.05)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '12px',
          padding: '1.25rem',
          marginBottom: '1.5rem',
        }}
      >
        <h3 style={{ fontSize: '1rem', marginBottom: '1rem', fontWeight: 600 }}>
          Select Lines to Outage
        </h3>

        {/* Search Box */}
        <input
          type="text"
          placeholder="Search lines..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          style={{
            width: '100%',
            padding: '0.75rem',
            background: 'rgba(0, 0, 0, 0.3)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            borderRadius: '8px',
            color: '#f5f5f7',
            fontSize: '0.875rem',
            marginBottom: '1rem',
          }}
        />

        {/* Selected Count */}
        {selectedLines.length > 0 && (
          <div
            style={{
              padding: '0.75rem',
              background: 'rgba(234, 179, 8, 0.1)',
              border: '1px solid rgba(234, 179, 8, 0.3)',
              borderRadius: '8px',
              marginBottom: '1rem',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <span style={{ fontSize: '0.875rem' }}>
              {selectedLines.length} line{selectedLines.length !== 1 ? 's' : ''} selected (N-{selectedLines.length} contingency)
            </span>
            <button
              onClick={clearSelection}
              style={{
                background: 'rgba(255, 255, 255, 0.1)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                borderRadius: '6px',
                padding: '0.375rem 0.75rem',
                color: '#f5f5f7',
                fontSize: '0.8125rem',
                cursor: 'pointer',
              }}
            >
              Clear All
            </button>
          </div>
        )}

        {/* Line List */}
        {loadingLines ? (
          <div style={{ textAlign: 'center', padding: '2rem' }}>
            <Loader2 size={32} className="spinner" />
            <p style={{ marginTop: '1rem', color: '#9ca3af', fontSize: '0.875rem' }}>
              Loading available lines...
            </p>
          </div>
        ) : (
          <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
            {filteredLines.map((line) => (
              <div
                key={line.name}
                onClick={() => toggleLineSelection(line.name)}
                style={{
                  padding: '0.75rem',
                  background: selectedLines.includes(line.name)
                    ? 'rgba(234, 179, 8, 0.15)'
                    : 'rgba(255, 255, 255, 0.05)',
                  border: `1px solid ${
                    selectedLines.includes(line.name)
                      ? 'rgba(234, 179, 8, 0.5)'
                      : 'rgba(255, 255, 255, 0.1)'
                  }`,
                  borderRadius: '8px',
                  marginBottom: '0.5rem',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => {
                  if (!selectedLines.includes(line.name)) {
                    e.currentTarget.style.background = 'rgba(255, 255, 255, 0.08)'
                  }
                }}
                onMouseLeave={(e) => {
                  if (!selectedLines.includes(line.name)) {
                    e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)'
                  }
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.875rem', marginBottom: '0.25rem' }}>
                      {line.name}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#9ca3af' }}>
                      {line.bus0} → {line.bus1} | {line.s_nom.toFixed(1)} MVA
                    </div>
                  </div>
                  <div
                    style={{
                      width: '20px',
                      height: '20px',
                      border: `2px solid ${
                        selectedLines.includes(line.name) ? '#eab308' : 'rgba(255, 255, 255, 0.3)'
                      }`,
                      borderRadius: '4px',
                      background: selectedLines.includes(line.name) ? '#eab308' : 'transparent',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    {selectedLines.includes(line.name) && (
                      <span style={{ color: '#000', fontSize: '0.875rem', fontWeight: 700 }}>✓</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Simulate Button */}
        <button
          onClick={runSimulation}
          disabled={loading || selectedLines.length === 0}
          style={{
            width: '100%',
            padding: '0.875rem',
            background: loading || selectedLines.length === 0 ? 'rgba(255, 255, 255, 0.1)' : '#eab308',
            border: 'none',
            borderRadius: '8px',
            color: loading || selectedLines.length === 0 ? '#9ca3af' : '#000',
            fontSize: '0.9375rem',
            fontWeight: 600,
            cursor: loading || selectedLines.length === 0 ? 'not-allowed' : 'pointer',
            marginTop: '1rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.5rem',
          }}
        >
          {loading ? (
            <>
              <Loader2 size={16} className="spinner" />
              Simulating Outage...
            </>
          ) : (
            <>
              <Activity size={16} />
              Simulate Outage
            </>
          )}
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div
          style={{
            padding: '1rem',
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '10px',
            marginBottom: '1.5rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
          }}
        >
          <AlertTriangle size={20} color="#ef4444" />
          <span style={{ fontSize: '0.875rem' }}>{error}</span>
        </div>
      )}

      {/* Results */}
      {result && result.success && (
        <>
          {/* Summary Metrics */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
            <div
              style={{
                background: 'rgba(239, 68, 68, 0.1)',
                border: '2px solid rgba(239, 68, 68, 0.3)',
                borderRadius: '10px',
                padding: '1.25rem',
              }}
            >
              <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.5rem', textTransform: 'uppercase', fontWeight: 600 }}>
                Overloaded Lines
              </div>
              <div style={{ fontSize: '2rem', fontWeight: 700, color: '#ef4444' }}>
                {result.metrics.overloaded_count}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.25rem' }}>
                Lines exceeding 100% capacity
              </div>
            </div>

            <div
              style={{
                background: 'rgba(249, 115, 22, 0.1)',
                border: '2px solid rgba(249, 115, 22, 0.3)',
                borderRadius: '10px',
                padding: '1.25rem',
              }}
            >
              <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.5rem', textTransform: 'uppercase', fontWeight: 600 }}>
                High Stress Lines
              </div>
              <div style={{ fontSize: '2rem', fontWeight: 700, color: '#f97316' }}>
                {result.metrics.high_stress_count}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.25rem' }}>
                Lines at 90-100% loading
              </div>
            </div>

            <div
              style={{
                background: 'rgba(234, 179, 8, 0.1)',
                border: '2px solid rgba(234, 179, 8, 0.3)',
                borderRadius: '10px',
                padding: '1.25rem',
              }}
            >
              <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.5rem', textTransform: 'uppercase', fontWeight: 600 }}>
                Affected Lines
              </div>
              <div style={{ fontSize: '2rem', fontWeight: 700, color: '#eab308' }}>
                {result.metrics.affected_lines_count}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.25rem' }}>
                Lines with loading change &gt;10%
              </div>
            </div>

            <div
              style={{
                background: result.metrics.islanded_buses_count > 0 ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)',
                border: `2px solid ${result.metrics.islanded_buses_count > 0 ? 'rgba(239, 68, 68, 0.3)' : 'rgba(16, 185, 129, 0.3)'}`,
                borderRadius: '10px',
                padding: '1.25rem',
              }}
            >
              <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.5rem', textTransform: 'uppercase', fontWeight: 600 }}>
                Islanded Buses
              </div>
              <div style={{ fontSize: '2rem', fontWeight: 700, color: result.metrics.islanded_buses_count > 0 ? '#ef4444' : '#10b981' }}>
                {result.metrics.islanded_buses_count}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.25rem' }}>
                Disconnected network buses
              </div>
            </div>
          </div>

          {/* Detailed Metrics */}
          <div
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '12px',
              padding: '1.25rem',
              marginBottom: '1.5rem',
            }}
          >
            <h3 style={{ fontSize: '1rem', marginBottom: '1rem', fontWeight: 600 }}>
              Network Loading Comparison
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.375rem' }}>
                  Max Loading (Before → After)
                </div>
                <div style={{ fontSize: '1.25rem', fontWeight: 600 }}>
                  {result.metrics.baseline_max_loading.toFixed(1)}% →{' '}
                  <span style={{ color: result.metrics.max_loading_pct > 100 ? '#ef4444' : '#eab308' }}>
                    {result.metrics.max_loading_pct.toFixed(1)}%
                  </span>
                  {result.metrics.max_loading_increase > 0 && (
                    <span style={{ fontSize: '0.875rem', color: '#f97316', marginLeft: '0.5rem' }}>
                      (+{result.metrics.max_loading_increase.toFixed(1)}%)
                    </span>
                  )}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.375rem' }}>
                  Avg Loading (Before → After)
                </div>
                <div style={{ fontSize: '1.25rem', fontWeight: 600 }}>
                  {result.metrics.baseline_avg_loading.toFixed(1)}% →{' '}
                  <span style={{ color: result.metrics.avg_loading_pct > result.metrics.baseline_avg_loading ? '#f97316' : '#10b981' }}>
                    {result.metrics.avg_loading_pct.toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Overloaded Lines Table */}
          {result.overloaded_lines.length > 0 && (
            <div
              style={{
                background: 'rgba(239, 68, 68, 0.05)',
                border: '1px solid rgba(239, 68, 68, 0.2)',
                borderRadius: '12px',
                padding: '1.25rem',
                marginBottom: '1.5rem',
              }}
            >
              <h3 style={{ fontSize: '1rem', marginBottom: '1rem', fontWeight: 600, color: '#ef4444' }}>
                ⚠️ Overloaded Lines ({result.overloaded_lines.length})
              </h3>
              <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                {result.overloaded_lines.map((line) => (
                  <div
                    key={line.name}
                    style={{
                      padding: '0.75rem',
                      background: 'rgba(239, 68, 68, 0.1)',
                      border: '1px solid rgba(239, 68, 68, 0.3)',
                      borderRadius: '8px',
                      marginBottom: '0.5rem',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <div style={{ fontWeight: 600 }}>{line.name}</div>
                      <div style={{ fontWeight: 700, color: '#ef4444' }}>
                        {line.loading_pct.toFixed(1)}%
                      </div>
                    </div>
                    <div style={{ fontSize: '0.8125rem', color: '#9ca3af', marginBottom: '0.375rem' }}>
                      {line.bus0} → {line.bus1}
                    </div>
                    <div style={{ fontSize: '0.8125rem' }}>
                      Flow: {line.flow_mva.toFixed(1)} / {line.s_nom.toFixed(1)} MVA
                      <span style={{ marginLeft: '1rem', color: '#f97316' }}>
                        Change: +{line.loading_change_pct.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Islanded Buses */}
          {result.islanded_buses.length > 0 && (
            <div
              style={{
                background: 'rgba(239, 68, 68, 0.05)',
                border: '1px solid rgba(239, 68, 68, 0.2)',
                borderRadius: '12px',
                padding: '1.25rem',
                marginBottom: '1.5rem',
              }}
            >
              <h3 style={{ fontSize: '1rem', marginBottom: '1rem', fontWeight: 600, color: '#ef4444' }}>
                🏝️ Islanded Buses ({result.islanded_buses.length})
              </h3>
              <div>
                {result.islanded_buses.map((bus) => (
                  <div
                    key={bus.bus_id}
                    style={{
                      padding: '0.75rem',
                      background: 'rgba(239, 68, 68, 0.1)',
                      border: '1px solid rgba(239, 68, 68, 0.3)',
                      borderRadius: '8px',
                      marginBottom: '0.5rem',
                    }}
                  >
                    <div style={{ fontWeight: 600 }}>{bus.bus_name || bus.bus_id}</div>
                    <div style={{ fontSize: '0.8125rem', color: '#9ca3af' }}>
                      {bus.voltage_kv} kV | Coordinates: ({bus.y.toFixed(3)}, {bus.x.toFixed(3)})
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Most Affected Lines */}
          {result.affected_lines.length > 0 && (
            <div
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '12px',
                padding: '1.25rem',
              }}
            >
              <h3 style={{ fontSize: '1rem', marginBottom: '1rem', fontWeight: 600 }}>
                <TrendingUp size={18} style={{ display: 'inline-block', marginRight: '0.5rem' }} />
                Most Affected Lines (Top 10)
              </h3>
              <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                {result.affected_lines.slice(0, 10).map((line) => (
                  <div
                    key={line.name}
                    style={{
                      padding: '0.75rem',
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      borderRadius: '8px',
                      marginBottom: '0.5rem',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <div style={{ fontWeight: 600 }}>{line.name}</div>
                      <div style={{ fontWeight: 700, color: getStatusColor(line.status) }}>
                        {line.baseline_loading_pct.toFixed(1)}% → {line.loading_pct.toFixed(1)}%
                      </div>
                    </div>
                    <div style={{ fontSize: '0.8125rem', color: '#9ca3af' }}>
                      {line.bus0} → {line.bus1}
                      <span
                        style={{
                          marginLeft: '1rem',
                          color: line.loading_change_pct > 0 ? '#f97316' : '#10b981',
                          fontWeight: 600,
                        }}
                      >
                        {line.loading_change_pct > 0 ? '+' : ''}
                        {line.loading_change_pct.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default OutageAnalysis
