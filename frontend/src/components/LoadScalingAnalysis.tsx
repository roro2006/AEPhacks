import { useState, useEffect } from 'react'
import { Clock, Loader2, AlertTriangle, TrendingUp, Zap, Sun, Moon } from 'lucide-react'

interface HourlyResult {
  hour: number
  scale_factor: number
  converged: boolean
  total_load_mw: number
  total_gen_mw: number
  max_loading_pct: number
  avg_loading_pct: number
  overloaded_count: number
  high_stress_count: number
  caution_count: number
  error?: string
}

interface DailyAnalysisResult {
  success: boolean
  summary: {
    total_hours: number
    hours_converged: number
    hours_failed: number
    peak_loading: {
      hour: number
      max_loading_pct: number
      scale_factor: number
      overloaded_count: number
    }
    peak_overloads: {
      hour: number
      overloaded_count: number
      max_loading_pct: number
      scale_factor: number
    }
    most_stressed_lines: Array<{
      name: string
      max_loading_pct: number
      hour_of_max: number
      scale_at_max: number
    }>
  }
  hourly_results: HourlyResult[]
}

const LoadScalingAnalysis = () => {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<DailyAnalysisResult | null>(null)
  const [selectedHour, setSelectedHour] = useState<number | null>(null)

  const runDailyAnalysis = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch('http://localhost:5000/api/load-scaling/daily?hours=24')

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`)
      }

      const data: DailyAnalysisResult = await response.json()

      if (!data.success) {
        setError(data.error || 'Analysis failed')
        setResult(null)
      } else {
        setResult(data)
        setSelectedHour(null)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run daily analysis')
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  const formatHour = (hour: number) => {
    const period = hour >= 12 ? 'PM' : 'AM'
    const displayHour = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour
    return `${displayHour}${period}`
  }

  const getLoadingColor = (loading_pct: number) => {
    if (loading_pct >= 100) return '#ef4444'
    if (loading_pct >= 90) return '#f97316'
    if (loading_pct >= 60) return '#eab308'
    return '#10b981'
  }

  const getScaleEmoji = (scale: number) => {
    if (scale >= 1.05) return <Sun size={14} />
    if (scale <= 0.95) return <Moon size={14} />
    return <Clock size={14} />
  }

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{
        padding: '1rem',
        background: 'rgba(255, 255, 255, 0.05)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: '12px 12px 0 0'
      }}>
        <h3 style={{
          margin: '0 0 0.5rem 0',
          fontSize: '1.125rem',
          fontWeight: 600,
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem'
        }}>
          <TrendingUp size={20} />
          Daily Load Scaling Analysis
        </h3>
        <p style={{
          margin: 0,
          fontSize: '0.875rem',
          color: '#9ca3af',
          lineHeight: 1.5
        }}>
          Analyzes how load/generation changes throughout the day stress the transmission system.
          Uses a sine wave (±10% from nominal) to approximate daily variations.
        </p>
      </div>

      {/* Run Analysis Button */}
      <div style={{ padding: '1rem', borderBottom: '1px solid rgba(255, 255, 255, 0.1)' }}>
        <button
          onClick={runDailyAnalysis}
          disabled={loading}
          style={{
            width: '100%',
            padding: '0.875rem',
            background: loading ? 'rgba(96, 165, 250, 0.5)' : 'linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%)',
            color: '#fff',
            border: 'none',
            borderRadius: '10px',
            fontSize: '0.9375rem',
            fontWeight: 600,
            cursor: loading ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.5rem',
            transition: 'all 0.2s',
            boxShadow: loading ? 'none' : '0 4px 12px rgba(59, 130, 246, 0.3)'
          }}
        >
          {loading ? (
            <>
              <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} />
              Analyzing 24 Hours...
            </>
          ) : (
            <>
              <Zap size={16} />
              Run Daily Analysis
            </>
          )}
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div style={{
          margin: '1rem',
          padding: '1rem',
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          borderRadius: '10px',
          display: 'flex',
          alignItems: 'flex-start',
          gap: '0.75rem'
        }}>
          <AlertTriangle size={20} style={{ color: '#ef4444', flexShrink: 0, marginTop: '0.125rem' }} />
          <div>
            <div style={{ fontWeight: 600, color: '#ef4444', marginBottom: '0.25rem' }}>Analysis Failed</div>
            <div style={{ fontSize: '0.875rem', color: '#f5f5f7' }}>{error}</div>
          </div>
        </div>
      )}

      {/* Results */}
      {result && (
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '1rem'
        }}>
          {/* Summary Cards */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '0.75rem',
            marginBottom: '1.5rem'
          }}>
            <div style={{
              background: 'rgba(255, 255, 255, 0.05)',
              padding: '1rem',
              borderRadius: '10px',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}>
              <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.5rem' }}>
                Peak Loading
              </div>
              <div style={{
                fontSize: '1.75rem',
                fontWeight: 700,
                color: getLoadingColor(result.summary.peak_loading.max_loading_pct)
              }}>
                {result.summary.peak_loading.max_loading_pct.toFixed(1)}%
              </div>
              <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.25rem' }}>
                at {formatHour(result.summary.peak_loading.hour)}
              </div>
            </div>

            <div style={{
              background: 'rgba(255, 255, 255, 0.05)',
              padding: '1rem',
              borderRadius: '10px',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}>
              <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.5rem' }}>
                Max Overloads
              </div>
              <div style={{
                fontSize: '1.75rem',
                fontWeight: 700,
                color: result.summary.peak_overloads.overloaded_count > 0 ? '#ef4444' : '#10b981'
              }}>
                {result.summary.peak_overloads.overloaded_count}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.25rem' }}>
                {result.summary.peak_overloads.overloaded_count > 0
                  ? `at ${formatHour(result.summary.peak_overloads.hour)}`
                  : 'No overloads'}
              </div>
            </div>
          </div>

          {/* Hourly Timeline */}
          <div style={{ marginBottom: '1.5rem' }}>
            <h4 style={{
              margin: '0 0 0.75rem 0',
              fontSize: '0.9375rem',
              fontWeight: 600,
              color: '#f5f5f7'
            }}>
              24-Hour Timeline
            </h4>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(12, 1fr)',
              gap: '0.375rem'
            }}>
              {result.hourly_results.map((hour) => {
                const isPeak = hour.hour === result.summary.peak_loading.hour
                const hasOverload = hour.overloaded_count > 0

                return (
                  <div
                    key={hour.hour}
                    onClick={() => setSelectedHour(hour.hour === selectedHour ? null : hour.hour)}
                    style={{
                      aspectRatio: '1',
                      background: selectedHour === hour.hour
                        ? 'rgba(96, 165, 250, 0.3)'
                        : 'rgba(255, 255, 255, 0.05)',
                      border: `2px solid ${
                        selectedHour === hour.hour ? '#60a5fa' :
                        hasOverload ? '#ef4444' :
                        isPeak ? '#f97316' :
                        getLoadingColor(hour.max_loading_pct)
                      }`,
                      borderRadius: '6px',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justifyContent: 'center',
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                      position: 'relative'
                    }}
                    title={`${formatHour(hour.hour)}: ${hour.max_loading_pct.toFixed(1)}% max loading`}
                  >
                    <div style={{ fontSize: '0.625rem', color: '#9ca3af', fontWeight: 600 }}>
                      {hour.hour}
                    </div>
                    {hasOverload && (
                      <AlertTriangle size={10} style={{ color: '#ef4444', marginTop: '2px' }} />
                    )}
                    {isPeak && !hasOverload && (
                      <TrendingUp size={10} style={{ color: '#f97316', marginTop: '2px' }} />
                    )}
                  </div>
                )
              })}
            </div>

            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              marginTop: '0.5rem',
              fontSize: '0.75rem',
              color: '#9ca3af'
            }}>
              <span>12AM</span>
              <span>6AM</span>
              <span>12PM</span>
              <span>6PM</span>
              <span>11PM</span>
            </div>
          </div>

          {/* Selected Hour Details */}
          {selectedHour !== null && (() => {
            const hourData = result.hourly_results[selectedHour]
            return (
              <div style={{
                background: 'rgba(96, 165, 250, 0.1)',
                border: '1px solid rgba(96, 165, 250, 0.3)',
                borderRadius: '10px',
                padding: '1rem',
                marginBottom: '1.5rem'
              }}>
                <h4 style={{
                  margin: '0 0 0.75rem 0',
                  fontSize: '0.9375rem',
                  fontWeight: 600,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}>
                  <Clock size={16} />
                  {formatHour(selectedHour)} ({selectedHour}:00)
                </h4>

                <div style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: '0.5rem'
                }}>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#9ca3af' }}>Load Scale</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                      {getScaleEmoji(hourData.scale_factor)}
                      {(hourData.scale_factor * 100).toFixed(0)}%
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#9ca3af' }}>Total Load</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>
                      {hourData.total_load_mw.toFixed(0)} MW
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#9ca3af' }}>Max Loading</div>
                    <div style={{
                      fontSize: '1.25rem',
                      fontWeight: 700,
                      color: getLoadingColor(hourData.max_loading_pct)
                    }}>
                      {hourData.max_loading_pct.toFixed(1)}%
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#9ca3af' }}>Avg Loading</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>
                      {hourData.avg_loading_pct.toFixed(1)}%
                    </div>
                  </div>
                </div>

                {hourData.overloaded_count > 0 && (
                  <div style={{
                    marginTop: '0.75rem',
                    padding: '0.5rem',
                    background: 'rgba(239, 68, 68, 0.1)',
                    borderRadius: '6px',
                    fontSize: '0.8125rem',
                    color: '#ef4444',
                    fontWeight: 600
                  }}>
                    ⚠️ {hourData.overloaded_count} line{hourData.overloaded_count !== 1 ? 's' : ''} overloaded
                  </div>
                )}
              </div>
            )
          })()}

          {/* Most Stressed Lines */}
          {result.summary.most_stressed_lines.length > 0 && (
            <div>
              <h4 style={{
                margin: '0 0 0.75rem 0',
                fontSize: '0.9375rem',
                fontWeight: 600,
                color: '#f5f5f7'
              }}>
                Most Stressed Lines (24hr Max)
              </h4>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {result.summary.most_stressed_lines.slice(0, 5).map((line) => (
                  <div
                    key={line.name}
                    style={{
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: `1px solid ${getLoadingColor(line.max_loading_pct)}`,
                      borderRadius: '8px',
                      padding: '0.75rem',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center'
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>
                        {line.name}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.25rem' }}>
                        Peak at {formatHour(line.hour_of_max)}
                      </div>
                    </div>
                    <div style={{
                      fontSize: '1.25rem',
                      fontWeight: 700,
                      color: getLoadingColor(line.max_loading_pct)
                    }}>
                      {line.max_loading_pct.toFixed(1)}%
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Initial State */}
      {!result && !loading && !error && (
        <div style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '2rem',
          textAlign: 'center',
          color: '#9ca3af'
        }}>
          <TrendingUp size={48} style={{ marginBottom: '1rem', opacity: 0.5 }} />
          <p style={{ margin: 0, fontSize: '0.875rem', lineHeight: 1.6 }}>
            Click "Run Daily Analysis" to analyze how load changes throughout the day affect transmission line stress.
          </p>
          <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.75rem' }}>
            Analyzes 24 hours with PyPSA power flow solver
          </p>
        </div>
      )}
    </div>
  )
}

export default LoadScalingAnalysis
