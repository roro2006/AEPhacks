import { useState } from 'react'
import type { WeatherParams } from '../services/api'
import { CloudRain, Wind, Sun } from 'lucide-react'

interface WeatherControlsProps {
  weather: WeatherParams
  onChange: (weather: Partial<WeatherParams>) => void
  loading: boolean
}

const WeatherControls: React.FC<WeatherControlsProps> = ({ weather, onChange, loading }) => {
  const [localWeather, setLocalWeather] = useState(weather)

  const handleChange = (key: keyof WeatherParams, value: number | string) => {
    const updated = { ...localWeather, [key]: value }
    setLocalWeather(updated)
  }

  return (
    <div style={{
      background: 'white',
      borderRadius: '12px',
      boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
      padding: '1.5rem'
    }}>
      <h2 style={{
        fontSize: '1.25rem',
        fontWeight: 600,
        marginBottom: '1.5rem',
        color: '#111827'
      }}>Weather Controls</h2>

      <div style={{ marginBottom: '1.5rem' }}>
        <label style={{
          display: 'block',
          marginBottom: '0.5rem',
          color: '#374151',
          fontSize: '0.875rem',
          fontWeight: 500
        }}>
          Temperature: {localWeather.ambient_temp}°C
        </label>
        <input
          type="range"
          min="-10"
          max="50"
          value={localWeather.ambient_temp}
          onChange={(e) => handleChange('ambient_temp', parseFloat(e.target.value))}
          style={{ width: '100%' }}
        />
      </div>

      <div style={{ marginBottom: '1.5rem' }}>
        <label style={{
          display: 'block',
          marginBottom: '0.5rem',
          color: '#374151',
          fontSize: '0.875rem',
          fontWeight: 500
        }}>
          Wind Speed: {localWeather.wind_speed} ft/s
        </label>
        <input
          type="range"
          min="0"
          max="10"
          step="0.5"
          value={localWeather.wind_speed}
          onChange={(e) => handleChange('wind_speed', parseFloat(e.target.value))}
          style={{ width: '100%' }}
        />
      </div>

      <button
        onClick={() => onChange(localWeather)}
        disabled={loading}
        style={{
          width: '100%',
          padding: '0.75rem 1.5rem',
          background: loading ? '#9ca3af' : '#3b82f6',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          fontWeight: 600,
          cursor: loading ? 'not-allowed' : 'pointer'
        }}
      >
        {loading ? 'Calculating...' : 'Apply Changes'}
      </button>
    </div>
  )
}

export default WeatherControls
