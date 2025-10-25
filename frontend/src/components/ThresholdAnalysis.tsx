import { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { fetchThresholdAnalysis, WeatherParams, ThresholdResponse } from '../services/api'
import { TrendingUp, Loader2, AlertTriangle } from 'lucide-react'
import './ThresholdAnalysis.css'

interface ThresholdAnalysisProps {
  weather: WeatherParams
}

const ThresholdAnalysis: React.FC<ThresholdAnalysisProps> = ({ weather }) => {
  const [data, setData] = useState<ThresholdResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [tempRange, setTempRange] = useState<[number, number]>([20, 50])
  const [windSpeed, setWindSpeed] = useState(weather.wind_speed)

  useEffect(() => {
    runAnalysis()
  }, [])

  const runAnalysis = async () => {
    setLoading(true)
    setError(null)

    try {
      const result = await fetchThresholdAnalysis(tempRange, windSpeed, 1)
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze thresholds')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="threshold-analysis">
      <div className="analysis-header">
        <TrendingUp size={24} />
        <div>
          <h2>Temperature Threshold Analysis</h2>
          <p>Identify at what ambient conditions lines begin to exceed safe limits</p>
        </div>
      </div>

      <div className="analysis-controls">
        <div className="control-group-inline">
          <label>Temperature Range (°C):</label>
          <input
            type="number"
            value={tempRange[0]}
            onChange={(e) => setTempRange([parseInt(e.target.value), tempRange[1]])}
            min="-10"
            max="50"
          />
          <span>to</span>
          <input
            type="number"
            value={tempRange[1]}
            onChange={(e) => setTempRange([tempRange[0], parseInt(e.target.value)])}
            min="0"
            max="60"
          />
        </div>

        <div className="control-group-inline">
          <label>Wind Speed (ft/s):</label>
          <input
            type="number"
            value={windSpeed}
            onChange={(e) => setWindSpeed(parseFloat(e.target.value))}
            min="0"
            max="10"
            step="0.5"
          />
        </div>

        <button
          className="btn-primary"
          onClick={runAnalysis}
          disabled={loading}
        >
          {loading ? 'Analyzing...' : 'Run Analysis'}
        </button>
      </div>

      {loading && (
        <div className="analysis-loading">
          <Loader2 className="spin" size={48} />
          <p>Running threshold analysis...</p>
        </div>
      )}

      {error && (
        <div className="analysis-error">
          <AlertTriangle size={24} />
          <p>{error}</p>
        </div>
      )}

      {data && !loading && (
        <>
          <div className="threshold-summary">
            {data.first_overload_temp !== null ? (
              <div className="summary-card critical">
                <AlertTriangle size={32} />
                <div>
                  <div className="summary-label">First Overload Temperature</div>
                  <div className="summary-value">
                    {data.first_overload_temp}°C
                    <span className="summary-alt">
                      ({(data.first_overload_temp * 9/5 + 32).toFixed(1)}°F)
                    </span>
                  </div>
                  <div className="summary-note">
                    Lines begin to overload at this temperature with wind speed of {windSpeed} ft/s
                  </div>
                </div>
              </div>
            ) : (
              <div className="summary-card normal">
                <div className="summary-label">No Overloads Detected</div>
                <div className="summary-note">
                  All lines remain below 100% loading across the entire temperature range
                </div>
              </div>
            )}
          </div>

          <div className="chart-container">
            <h3>Loading Progression with Temperature</h3>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={data.progression}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="temperature"
                  label={{ value: 'Ambient Temperature (°C)', position: 'insideBottom', offset: -5 }}
                />
                <YAxis
                  label={{ value: 'Lines Count / Loading %', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      return (
                        <div className="custom-tooltip">
                          <p className="label">{`Temperature: ${payload[0].payload.temperature}°C`}</p>
                          <p className="desc">{`Overloaded Lines: ${payload[0].payload.overloaded_lines}`}</p>
                          <p className="desc">{`High Stress Lines: ${payload[0].payload.high_stress_lines}`}</p>
                          <p className="desc">{`Avg Loading: ${payload[0].payload.avg_loading.toFixed(1)}%`}</p>
                          <p className="desc">{`Max Loading: ${payload[0].payload.max_loading.toFixed(1)}%`}</p>
                        </div>
                      )
                    }
                    return null
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="overloaded_lines"
                  stroke="#dc2626"
                  strokeWidth={2}
                  name="Overloaded Lines"
                  dot={{ r: 3 }}
                />
                <Line
                  type="monotone"
                  dataKey="high_stress_lines"
                  stroke="#ea580c"
                  strokeWidth={2}
                  name="High Stress Lines (>90%)"
                  dot={{ r: 3 }}
                />
                <Line
                  type="monotone"
                  dataKey="max_loading"
                  stroke="#ca8a04"
                  strokeWidth={2}
                  name="Maximum Loading %"
                  dot={{ r: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="insights-section">
            <h3>Key Insights</h3>
            <div className="insights-grid">
              <div className="insight-card">
                <div className="insight-label">Temperature Range Tested</div>
                <div className="insight-value">
                  {tempRange[0]}°C to {tempRange[1]}°C
                </div>
              </div>
              <div className="insight-card">
                <div className="insight-label">Wind Condition</div>
                <div className="insight-value">
                  {windSpeed} ft/s ({(windSpeed * 0.681818).toFixed(1)} mph)
                </div>
              </div>
              <div className="insight-card">
                <div className="insight-label">Critical Threshold</div>
                <div className="insight-value">
                  {data.first_overload_temp !== null
                    ? `${data.first_overload_temp}°C`
                    : 'Not reached'
                  }
                </div>
              </div>
            </div>

            {data.first_overload_temp !== null && (
              <div className="recommendations-box">
                <h4>Operational Recommendations</h4>
                <ul>
                  <li>Monitor forecasts when temperatures approach {data.first_overload_temp - 5}°C</li>
                  <li>Prepare load reduction or generation redispatch plans</li>
                  <li>Consider pre-emptive switching operations to redistribute load</li>
                  <li>Alert operations staff when temperature exceeds {data.first_overload_temp - 3}°C</li>
                </ul>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}

export default ThresholdAnalysis
