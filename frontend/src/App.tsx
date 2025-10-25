import { useState, useEffect } from 'react'
import './App.css'
import { Activity, Loader2, Map, Table } from 'lucide-react'
import { fetchLineRatings, type WeatherParams, type RatingResponse } from './services/api'
import WeatherControls from './components/WeatherControls-simple'
import AlertDashboard from './components/AlertDashboard-simple'
import Chatbot from './components/Chatbot'
import NetworkMap from './components/NetworkMap'

type ViewTab = 'table' | 'map'

function App() {
  const [activeTab, setActiveTab] = useState<ViewTab>('map')
  const [weather, setWeather] = useState<WeatherParams>({
    ambient_temp: 25,
    wind_speed: 2.0,
    wind_angle: 90,
    sun_time: 12,
    date: '12 Jun'
  })

  const [ratings, setRatings] = useState<RatingResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadRatings()
  }, [])

  const loadRatings = async (weatherParams?: WeatherParams) => {
    const params = weatherParams || weather
    setLoading(true)
    setError(null)

    try {
      const data = await fetchLineRatings(params)
      setRatings(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load ratings. Make sure backend is running on http://localhost:5000')
    } finally {
      setLoading(false)
    }
  }

  const handleWeatherChange = (newWeather: Partial<WeatherParams>) => {
    const updated = { ...weather, ...newWeather }
    setWeather(updated)
    loadRatings(updated)
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-content">
          <div className="header-title">
            <Activity size={32} className="header-icon" />
            <div>
              <h1>Grid Real-Time Rating Monitor</h1>
              <p className="header-subtitle">AEP Transmission Planning System</p>
            </div>
          </div>
        </div>
      </header>

      {error && (
        <div style={{
          background: '#fee2e2',
          color: '#991b1b',
          padding: '1rem 2rem',
          borderLeft: '4px solid #dc2626'
        }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      <main className="main-content">
        <div className="grid-layout">
          <div className="map-section">
            {/* Tab Selector */}
            <div style={{
              display: 'flex',
              gap: '0.5rem',
              marginBottom: '1rem',
              background: 'white',
              padding: '0.5rem',
              borderRadius: '12px'
            }}>
              <button
                onClick={() => setActiveTab('map')}
                style={{
                  flex: 1,
                  padding: '0.75rem 1.5rem',
                  background: activeTab === 'map' ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : 'transparent',
                  color: activeTab === 'map' ? 'white' : '#6b7280',
                  border: 'none',
                  borderRadius: '8px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem',
                  transition: 'all 0.2s'
                }}
              >
                <Map size={18} />
                Interactive Map
              </button>
              <button
                onClick={() => setActiveTab('table')}
                style={{
                  flex: 1,
                  padding: '0.75rem 1.5rem',
                  background: activeTab === 'table' ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : 'transparent',
                  color: activeTab === 'table' ? 'white' : '#6b7280',
                  border: 'none',
                  borderRadius: '8px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem',
                  transition: 'all 0.2s'
                }}
              >
                <Table size={18} />
                Data Table
              </button>
            </div>

            {/* Map View */}
            {activeTab === 'map' && (
              <NetworkMap weather={weather} />
            )}

            {/* Table View */}
            {activeTab === 'table' && (
              <div style={{ padding: '2rem', background: 'white', height: '100%', borderRadius: '12px' }}>
                <h2 style={{ marginBottom: '1rem' }}>Transmission Line Analysis</h2>

              {loading && (
                <div style={{ textAlign: 'center', padding: '4rem', color: '#6b7280' }}>
                  <Loader2 size={48} style={{ animation: 'spin 1s linear infinite', margin: '0 auto' }} />
                  <p style={{ marginTop: '1rem' }}>Calculating line ratings...</p>
                </div>
              )}

              {!loading && ratings && (
                <div>
                  <div style={{
                    padding: '1.5rem',
                    background: '#f0fdf4',
                    borderRadius: '8px',
                    marginBottom: '1.5rem',
                    border: '2px solid #86efac'
                  }}>
                    <h3 style={{ marginBottom: '0.5rem' }}>Current Conditions</h3>
                    <p>Temperature: <strong>{weather.ambient_temp}°C</strong> ({(weather.ambient_temp * 9/5 + 32).toFixed(1)}°F)</p>
                    <p>Wind Speed: <strong>{weather.wind_speed} ft/s</strong> ({(weather.wind_speed * 0.681818).toFixed(1)} mph)</p>
                    <p>Time: <strong>{weather.sun_time}:00</strong></p>
                  </div>

                  <div style={{
                    maxHeight: '500px',
                    overflowY: 'auto',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px'
                  }}>
                    <table style={{ width: '100%', fontSize: '0.875rem', borderCollapse: 'collapse' }}>
                      <thead style={{ position: 'sticky', top: 0, background: '#f9fafb', zIndex: 1 }}>
                        <tr>
                          <th style={{ padding: '0.75rem', textAlign: 'left', borderBottom: '2px solid #e5e7eb' }}>Line</th>
                          <th style={{ padding: '0.75rem', textAlign: 'right', borderBottom: '2px solid #e5e7eb' }}>Loading</th>
                          <th style={{ padding: '0.75rem', textAlign: 'right', borderBottom: '2px solid #e5e7eb' }}>Rating</th>
                          <th style={{ padding: '0.75rem', textAlign: 'right', borderBottom: '2px solid #e5e7eb' }}>Flow</th>
                          <th style={{ padding: '0.75rem', textAlign: 'center', borderBottom: '2px solid #e5e7eb' }}>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {ratings.lines.map(line => (
                          <tr key={line.name} style={{
                            borderBottom: '1px solid #e5e7eb',
                            background: line.loading_pct >= 100 ? '#fef2f2' :
                                       line.loading_pct >= 90 ? '#fff7ed' :
                                       line.loading_pct >= 60 ? '#fefce8' : 'white'
                          }}>
                            <td style={{ padding: '0.75rem' }}>
                              <div style={{ fontWeight: 600 }}>{line.name}</div>
                              <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>{line.branch_name}</div>
                            </td>
                            <td style={{
                              padding: '0.75rem',
                              textAlign: 'right',
                              fontWeight: 700,
                              color: line.loading_pct >= 100 ? '#dc2626' :
                                     line.loading_pct >= 90 ? '#ea580c' :
                                     line.loading_pct >= 60 ? '#ca8a04' : '#16a34a'
                            }}>
                              {line.loading_pct.toFixed(1)}%
                            </td>
                            <td style={{ padding: '0.75rem', textAlign: 'right' }}>{line.rating_mva.toFixed(1)} MVA</td>
                            <td style={{ padding: '0.75rem', textAlign: 'right' }}>{line.flow_mva.toFixed(1)} MVA</td>
                            <td style={{ padding: '0.75rem', textAlign: 'center' }}>
                              <span style={{
                                padding: '0.25rem 0.5rem',
                                borderRadius: '4px',
                                fontSize: '0.75rem',
                                fontWeight: 600,
                                background: line.stress_level === 'critical' ? '#fee2e2' :
                                           line.stress_level === 'high' ? '#ffedd5' :
                                           line.stress_level === 'caution' ? '#fef9c3' : '#dcfce7',
                                color: line.stress_level === 'critical' ? '#991b1b' :
                                       line.stress_level === 'high' ? '#9a3412' :
                                       line.stress_level === 'caution' ? '#854d0e' : '#166534'
                              }}>
                                {line.stress_level.toUpperCase()}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {!loading && !ratings && !error && (
                <div style={{ textAlign: 'center', padding: '4rem', color: '#6b7280' }}>
                  <p>Loading grid data...</p>
                </div>
              )}
              </div>
            )}
          </div>

          <aside className="sidebar">
            <WeatherControls
              weather={weather}
              onChange={handleWeatherChange}
              loading={loading}
            />

            <AlertDashboard ratings={ratings} loading={loading} />
          </aside>
        </div>
      </main>

      {/* Chatbot Component */}
      <Chatbot weather={weather} />
    </div>
  )
}

export default App
