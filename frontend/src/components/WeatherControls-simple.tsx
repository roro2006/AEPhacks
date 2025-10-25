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
    <div style={{ background: 'white', padding: '1rem', borderRadius: '8px' }}>
      <h2>Weather Controls (Simplified)</h2>
      <div>
        <label>Temperature: {localWeather.ambient_temp}°C</label>
        <input
          type="range"
          min="-10"
          max="50"
          value={localWeather.ambient_temp}
          onChange={(e) => handleChange('ambient_temp', parseFloat(e.target.value))}
        />
      </div>
      <div>
        <label>Wind Speed: {localWeather.wind_speed} ft/s</label>
        <input
          type="range"
          min="0"
          max="10"
          step="0.5"
          value={localWeather.wind_speed}
          onChange={(e) => handleChange('wind_speed', parseFloat(e.target.value))}
        />
      </div>
      <button onClick={() => onChange(localWeather)}>Apply</button>
    </div>
  )
}

export default WeatherControls
