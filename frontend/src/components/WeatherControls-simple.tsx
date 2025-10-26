import { useState } from 'react'
import type { WeatherParams } from '../services/api'
import { CloudRain, Wind, Sun, RefreshCw } from 'lucide-react'

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
      background: 'rgba(20, 20, 22, 0.85)',
      backdropFilter: 'blur(10px)',
      WebkitBackdropFilter: 'blur(10px)',
      padding: '1.5rem',
      borderRadius: '14px',
      border: '1px solid rgba(255, 255, 255, 0.08)',
      boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
      color: '#f5f5f7'
    }}>
      <h2 style={{
        fontSize: '1.25rem',
        fontWeight: 600,
        marginBottom: '1.5rem',
        color: '#ffffff'
      }}>Weather Controls</h2>
      <div style={{ marginBottom: '1.5rem' }}>
        <label style={{
          display: 'block',
          marginBottom: '0.5rem',
          color: '#e5e5e7',
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
          color: '#e5e5e7',
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
        style={{
          width: '100%',
          padding: '0.75rem 1.5rem',
          background: 'rgba(255, 255, 255, 0.1)',
          color: '#f5f5f7',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          borderRadius: '8px',
          fontWeight: 600,
          cursor: 'pointer',
          transition: 'all 0.2s'
        }}
        onMouseOver={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.2)'}
        onMouseOut={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)'}
      >
        Apply Changes
      </button>
    </div>
  )
}

export default WeatherControls
