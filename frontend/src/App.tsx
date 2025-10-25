import { useState, useEffect } from 'react'
import './App.css'
import { Activity, Loader2 } from 'lucide-react'
import { fetchLineRatings, type WeatherParams, type RatingResponse } from './services/api'
import WeatherControls from './components/WeatherControls-simple'
import AlertDashboard from './components/AlertDashboard-simple'
import Chatbot from './components/Chatbot'
import GridMap from './components/GridMap'

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
      </main>

      {/* Chatbot Component */}
      <Chatbot weather={weather} />
    </div>
  )
}

export default App
