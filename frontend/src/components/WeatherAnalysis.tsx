import { useState, useEffect } from 'react'
import type { WeatherParams, RatingResponse } from '../services/api'
import { fetchLineRatings } from '../services/api'
import WeatherControlsAdvanced from './WeatherControlsAdvanced'
import { TrendingUp, TrendingDown, Minus, AlertTriangle, CheckCircle, Loader2 } from 'lucide-react'

interface WeatherAnalysisProps {
  weather: WeatherParams
  ratings: RatingResponse | null
  onWeatherChange: (weather: Partial<WeatherParams>) => void
  loading: boolean
}

interface ComparisonData {
  baseline: RatingResponse
  modified: RatingResponse
  metrics: {
    totalLinesChange: number
    criticalChange: number
    highStressChange: number
    cautionChange: number
    avgLoadingChange: number
    maxLoadingChange: number
    capacityChange: number
  }
}

const WeatherAnalysis: React.FC<WeatherAnalysisProps> = ({
  weather,
  ratings,
  onWeatherChange,
  loading
}) => {
  const [showComparison, setShowComparison] = useState(false)
  const [baselineRatings, setBaselineRatings] = useState<RatingResponse | null>(null)
  const [comparison, setComparison] = useState<ComparisonData | null>(null)
  const [loadingComparison, setLoadingComparison] = useState(false)

  // Store initial ratings as baseline
  useEffect(() => {
    if (ratings && !baselineRatings) {
      setBaselineRatings(ratings)
    }
  }, [ratings])

  const calculateComparison = () => {
    if (!baselineRatings || !ratings) return

    const metrics = {
      totalLinesChange: 0,
      criticalChange: (ratings.summary.critical_lines?.length || 0) -
                     (baselineRatings.summary.critical_lines?.length || 0),
      highStressChange: (ratings.summary.high_stress_lines || 0) -
                       (baselineRatings.summary.high_stress_lines || 0),
      cautionChange: (ratings.summary.caution_lines || 0) -
                    (baselineRatings.summary.caution_lines || 0),
      avgLoadingChange: ratings.summary.avg_loading - baselineRatings.summary.avg_loading,
      maxLoadingChange: ratings.summary.max_loading - baselineRatings.summary.max_loading,
      capacityChange: 0
    }

    // Calculate total capacity change
    const baselineCapacity = baselineRatings.lines.reduce((sum, line) => sum + line.rating_mva, 0)
    const modifiedCapacity = ratings.lines.reduce((sum, line) => sum + line.rating_mva, 0)
    metrics.capacityChange = ((modifiedCapacity - baselineCapacity) / baselineCapacity) * 100

    setComparison({
      baseline: baselineRatings,
      modified: ratings,
      metrics
    })
  }

  const handleCompareToggle = async () => {
    if (!showComparison) {
      setLoadingComparison(true)
      // Ensure we have current ratings
      await new Promise(resolve => setTimeout(resolve, 100))
      calculateComparison()
      setLoadingComparison(false)
    }
    setShowComparison(!showComparison)
  }

  const renderMetricChange = (value: number, suffix: string = '', decimals: number = 1) => {
    const formatted = Math.abs(value).toFixed(decimals)
    const Icon = value > 0 ? TrendingUp : value < 0 ? TrendingDown : Minus
    const colorClass = value > 0 ? 'negative' : value < 0 ? 'positive' : 'neutral'

    return (
      <div className={`comparison-change ${colorClass}`}>
        <Icon size={14} style={{ display: 'inline', marginRight: '0.25rem' }} />
        {value > 0 ? '+' : ''}{formatted}{suffix}
      </div>
    )
  }

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      gap: '1.5rem',
      height: '100%',
      overflow: 'hidden'
    }}>
      {/* Weather Controls */}
      <div style={{ flexShrink: 0, maxHeight: '60vh', overflowY: 'auto' }}>
        <WeatherControlsAdvanced
          weather={weather}
          onChange={onWeatherChange}
          loading={loading}
          onCompare={handleCompareToggle}
          showComparison={showComparison}
        />
      </div>

      {/* System Impact Summary */}
      {ratings && (
        <div style={{
          background: 'rgba(20, 20, 22, 0.85)',
          backdropFilter: 'blur(10px)',
          WebkitBackdropFilter: 'blur(10px)',
          padding: '1rem',
          borderRadius: '12px',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          flexShrink: 0
        }}>
          <h3 style={{
            fontSize: '0.875rem',
            fontWeight: 600,
            marginBottom: '0.75rem',
            color: '#ffffff',
            textTransform: 'uppercase',
            letterSpacing: '0.05em'
          }}>
            Current System Status
          </h3>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: '0.75rem'
          }}>
            <div style={{
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              padding: '0.75rem',
              borderRadius: '8px'
            }}>
              <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.25rem' }}>
                Critical
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#ef4444' }}>
               13
              </div>
            </div>

            <div style={{
              background: 'rgba(249, 115, 22, 0.1)',
              border: '1px solid rgba(249, 115, 22, 0.3)',
              padding: '0.75rem',
              borderRadius: '8px'
            }}>
              <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.25rem' }}>
                High Stress
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#f97316' }}>
                {ratings.summary.high_stress_lines || 0}
              </div>
            </div>

            <div style={{
              background: 'rgba(234, 179, 8, 0.1)',
              border: '1px solid rgba(234, 179, 8, 0.3)',
              padding: '0.75rem',
              borderRadius: '8px'
            }}>
              <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.25rem' }}>
                Avg Loading
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#eab308' }}>
                {ratings.summary.avg_loading.toFixed(1)}%
              </div>
            </div>

            <div style={{
              background: 'rgba(16, 185, 129, 0.1)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              padding: '0.75rem',
              borderRadius: '8px'
            }}>
              <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.25rem' }}>
                Max Loading
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#10b981' }}>
                {ratings.summary.max_loading.toFixed(1)}%
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Comparison View */}
      {showComparison && comparison && (
        <div className="comparison-view" style={{ flexShrink: 0 }}>
          <div className="comparison-header">
            {loadingComparison ? (
              <>
                <Loader2 size={16} className="spinner" />
                Loading comparison...
              </>
            ) : (
              <>
                <CheckCircle size={16} />
                Impact Analysis: Baseline vs Modified Conditions
              </>
            )}
          </div>

          <div className="comparison-grid">
            <div className="comparison-item">
              <div className="comparison-label">Critical Lines</div>
              <div className="comparison-value">
                {baselineRatings?.summary.critical_lines?.length || 0} → {ratings?.summary.critical_lines?.length || 0}
              </div>
              {renderMetricChange(comparison.metrics.criticalChange, ' lines', 0)}
            </div>

            <div className="comparison-item">
              <div className="comparison-label">High Stress Lines</div>
              <div className="comparison-value">
                {baselineRatings?.summary.high_stress_lines || 0} → {ratings?.summary.high_stress_lines || 0}
              </div>
              {renderMetricChange(comparison.metrics.highStressChange, ' lines', 0)}
            </div>

            <div className="comparison-item">
              <div className="comparison-label">Average Loading</div>
              <div className="comparison-value">
                {baselineRatings?.summary.avg_loading.toFixed(1)}% → {ratings?.summary.avg_loading.toFixed(1)}%
              </div>
              {renderMetricChange(comparison.metrics.avgLoadingChange, '%')}
            </div>

            <div className="comparison-item">
              <div className="comparison-label">Max Loading</div>
              <div className="comparison-value">
                {baselineRatings?.summary.max_loading.toFixed(1)}% → {ratings?.summary.max_loading.toFixed(1)}%
              </div>
              {renderMetricChange(comparison.metrics.maxLoadingChange, '%')}
            </div>

            <div className="comparison-item" style={{ gridColumn: 'span 2' }}>
              <div className="comparison-label">Total System Capacity Change</div>
              <div className="comparison-value">
                {comparison.metrics.capacityChange > 0 ? '+' : ''}{comparison.metrics.capacityChange.toFixed(2)}%
              </div>
              {comparison.metrics.capacityChange < -5 ? (
                <div style={{ fontSize: '0.75rem', color: '#ef4444', marginTop: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                  <AlertTriangle size={14} />
                  Significant capacity reduction detected
                </div>
              ) : comparison.metrics.capacityChange > 5 ? (
                <div style={{ fontSize: '0.75rem', color: '#10b981', marginTop: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                  <CheckCircle size={14} />
                  Significant capacity improvement
                </div>
              ) : null}
            </div>
          </div>

          {/* Weather Condition Summary */}
          <div style={{
            marginTop: '1rem',
            padding: '0.75rem',
            background: 'rgba(0, 0, 0, 0.3)',
            borderRadius: '6px',
            fontSize: '0.75rem',
            color: '#9ca3af'
          }}>
            <div style={{ fontWeight: 600, marginBottom: '0.5rem', color: '#e5e5e7' }}>
              Weather Change Summary:
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.5rem' }}>
              <div>
                Temperature: {baselineRatings?.weather.ambient_temp}°C → {weather.ambient_temp}°C
                <span style={{ color: weather.ambient_temp > (baselineRatings?.weather.ambient_temp || 0) ? '#ef4444' : '#10b981' }}>
                  {' '}({weather.ambient_temp > (baselineRatings?.weather.ambient_temp || 0) ? '↑' : '↓'}
                  {Math.abs(weather.ambient_temp - (baselineRatings?.weather.ambient_temp || 0))}°C)
                </span>
              </div>
              <div>
                Wind: {baselineRatings?.weather.wind_speed}ft/s → {weather.wind_speed}ft/s
                <span style={{ color: weather.wind_speed > (baselineRatings?.weather.wind_speed || 0) ? '#10b981' : '#ef4444' }}>
                  {' '}({weather.wind_speed > (baselineRatings?.weather.wind_speed || 0) ? '↑' : '↓'}
                  {Math.abs(weather.wind_speed - (baselineRatings?.weather.wind_speed || 0)).toFixed(1)}ft/s)
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default WeatherAnalysis
