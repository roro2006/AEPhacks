import { useState, useEffect } from 'react'
import './App.css'
import GridMap from './components/GridMap'
import WeatherControls from './components/WeatherControls'
import AlertDashboard from './components/AlertDashboard'
import ThresholdAnalysis from './components/ThresholdAnalysis'
import { fetchLineRatings } from './services/api'
import type { WeatherParams, RatingResponse } from './services/api'
import { Activity } from 'lucide-react'

function App() {
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
  const [activeTab, setActiveTab] = useState<'map' | 'threshold'>('map')

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
      setError(err instanceof Error ? err.message : 'Failed to load ratings')
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

          <div className="header-tabs">
            <button
              className={`tab-button ${activeTab === 'map' ? 'active' : ''}`}
              onClick={() => setActiveTab('map')}
            >
              Live Grid Map
            </button>
            <button
              className={`tab-button ${activeTab === 'threshold' ? 'active' : ''}`}
              onClick={() => setActiveTab('threshold')}
            >
              Threshold Analysis
            </button>
          </div>
        </div>
      </header>

      {error && (
        <div className="error-banner">
          <strong>Error:</strong> {error}
        </div>
      )}

      <main className="main-content">
        {activeTab === 'map' ? (
          <div className="grid-layout">
            <div className="map-section">
              <GridMap ratings={ratings} loading={loading} />
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
        ) : (
          <div className="threshold-section">
            <ThresholdAnalysis weather={weather} />
          </div>
        )}
      </main>
    </div>
  )
}

export default App
