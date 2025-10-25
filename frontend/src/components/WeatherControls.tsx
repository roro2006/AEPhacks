import { useState } from 'react'
import type { WeatherParams } from '../services/api'
import { CloudRain, Wind, Sun, RefreshCw } from 'lucide-react'
import './WeatherControls.css'

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

  const handleApply = () => {
    onChange(localWeather)
  }

  const handleReset = () => {
    const defaults: WeatherParams = {
      ambient_temp: 25,
      wind_speed: 2.0,
      wind_angle: 90,
      sun_time: 12,
      date: '12 Jun'
    }
    setLocalWeather(defaults)
    onChange(defaults)
  }

  const windSpeedMph = (localWeather.wind_speed * 0.681818).toFixed(1)
  const windSpeedKmh = (localWeather.wind_speed * 1.09728).toFixed(1)

  return (
    <div className="weather-controls">
      <div className="controls-header">
        <CloudRain size={20} />
        <h2>Weather Conditions</h2>
      </div>

      <div className="controls-body">
        <div className="control-group">
          <label>
            <Sun size={16} />
            <span>Ambient Temperature</span>
          </label>
          <div className="input-with-unit">
            <input
              type="range"
              min="-10"
              max="50"
              step="1"
              value={localWeather.ambient_temp}
              onChange={(e) => handleChange('ambient_temp', parseFloat(e.target.value))}
            />
            <div className="value-display">
              <strong>{localWeather.ambient_temp}°C</strong>
              <span className="value-alt">({(localWeather.ambient_temp * 9/5 + 32).toFixed(1)}°F)</span>
            </div>
          </div>
        </div>

        <div className="control-group">
          <label>
            <Wind size={16} />
            <span>Wind Speed</span>
          </label>
          <div className="input-with-unit">
            <input
              type="range"
              min="0"
              max="10"
              step="0.5"
              value={localWeather.wind_speed}
              onChange={(e) => handleChange('wind_speed', parseFloat(e.target.value))}
            />
            <div className="value-display">
              <strong>{localWeather.wind_speed.toFixed(1)} ft/s</strong>
              <span className="value-alt">({windSpeedMph} mph / {windSpeedKmh} km/h)</span>
            </div>
          </div>
        </div>

        <div className="control-group">
          <label>
            <Sun size={16} />
            <span>Time of Day</span>
          </label>
          <div className="input-with-unit">
            <input
              type="range"
              min="0"
              max="23"
              step="1"
              value={localWeather.sun_time}
              onChange={(e) => handleChange('sun_time', parseFloat(e.target.value))}
            />
            <div className="value-display">
              <strong>{localWeather.sun_time}:00</strong>
              <span className="value-alt">
                {localWeather.sun_time < 12 ? 'Morning' :
                 localWeather.sun_time < 17 ? 'Afternoon' : 'Evening'}
              </span>
            </div>
          </div>
        </div>

        <div className="control-actions">
          <button
            className="btn-secondary"
            onClick={handleReset}
            disabled={loading}
          >
            <RefreshCw size={16} />
            Reset to Defaults
          </button>

          <button
            className="btn-primary"
            onClick={handleApply}
            disabled={loading}
          >
            {loading ? 'Calculating...' : 'Apply Changes'}
          </button>
        </div>

        <div className="weather-scenarios">
          <h3>Quick Scenarios</h3>
          <div className="scenario-buttons">
            <button
              className="scenario-btn"
              onClick={() => {
                const scenario = { ambient_temp: 15, wind_speed: 2.5 }
                setLocalWeather({ ...localWeather, ...scenario })
                onChange(scenario)
              }}
            >
              Cool & Windy
            </button>
            <button
              className="scenario-btn"
              onClick={() => {
                const scenario = { ambient_temp: 35, wind_speed: 1.0 }
                setLocalWeather({ ...localWeather, ...scenario })
                onChange(scenario)
              }}
            >
              Hot & Calm
            </button>
            <button
              className="scenario-btn"
              onClick={() => {
                const scenario = { ambient_temp: 40, wind_speed: 0.5 }
                setLocalWeather({ ...localWeather, ...scenario })
                onChange(scenario)
              }}
            >
              Extreme Heat
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default WeatherControls
