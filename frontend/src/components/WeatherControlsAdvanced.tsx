import { useState } from 'react'
import type { WeatherParams } from '../services/api'
import {
  CloudRain, Wind, Sun, RefreshCw, Thermometer,
  Compass, Mountain, Eye, Zap, Calendar
} from 'lucide-react'
import './WeatherControls.css'

interface WeatherControlsAdvancedProps {
  weather: WeatherParams
  onChange: (weather: Partial<WeatherParams>) => void
  loading: boolean
  onCompare?: () => void
  showComparison?: boolean
}

const DEFAULT_WEATHER: WeatherParams = {
  ambient_temp: 25,
  wind_speed: 2.0,
  wind_angle: 90,
  sun_time: 12,
  date: '12 Jun',
  elevation: 1000,
  latitude: 27,
  emissivity: 0.8,
  absorptivity: 0.8,
  direction: 'EastWest',
  atmosphere: 'Clear'
}

const PRESETS = {
  summerPeak: {
    name: 'Summer Peak',
    description: 'Hot afternoon, low wind, high solar',
    params: {
      ambient_temp: 40,
      wind_speed: 1.0,
      wind_angle: 45,
      sun_time: 14,
      date: '21 Jun'
    }
  },
  winterLow: {
    name: 'Winter Low',
    description: 'Cool morning, moderate wind',
    params: {
      ambient_temp: 5,
      wind_speed: 3.5,
      wind_angle: 90,
      sun_time: 8,
      date: '21 Dec'
    }
  },
  highWind: {
    name: 'High Wind',
    description: 'Normal temp, strong perpendicular wind',
    params: {
      ambient_temp: 25,
      wind_speed: 8.0,
      wind_angle: 90,
      sun_time: 12,
      date: '12 Jun'
    }
  },
  nightOperation: {
    name: 'Night Operation',
    description: 'Cool night, no solar radiation',
    params: {
      ambient_temp: 15,
      wind_speed: 2.0,
      wind_angle: 90,
      sun_time: 0,
      date: '12 Jun'
    }
  },
  extremeHeat: {
    name: 'Extreme Heat',
    description: 'Very hot, calm, worst-case scenario',
    params: {
      ambient_temp: 48,
      wind_speed: 0.5,
      wind_angle: 0,
      sun_time: 13,
      date: '21 Jul'
    }
  },
  optimal: {
    name: 'Optimal Cooling',
    description: 'Cool temp, strong wind, night',
    params: {
      ambient_temp: 10,
      wind_speed: 6.0,
      wind_angle: 90,
      sun_time: 22,
      date: '12 Jan'
    }
  }
}

const WeatherControlsAdvanced: React.FC<WeatherControlsAdvancedProps> = ({
  weather,
  onChange,
  loading,
  onCompare,
  showComparison = false
}) => {
  const [localWeather, setLocalWeather] = useState<WeatherParams>({
    ...DEFAULT_WEATHER,
    ...weather
  })
  const [expandedSection, setExpandedSection] = useState<string>('temperature')

  const handleChange = (key: keyof WeatherParams, value: number | string) => {
    const updated = { ...localWeather, [key]: value }
    setLocalWeather(updated)
  }

  const handleApply = () => {
    console.log('[WeatherControlsAdvanced] Applying weather:', localWeather)
    onChange(localWeather)
  }

  const handleReset = () => {
    setLocalWeather(DEFAULT_WEATHER)
    onChange(DEFAULT_WEATHER)
  }

  const applyPreset = (presetKey: keyof typeof PRESETS) => {
    const preset = PRESETS[presetKey]
    const updated = { ...localWeather, ...preset.params }
    setLocalWeather(updated)
    onChange(updated)
  }

  const toggleSection = (section: string) => {
    setExpandedSection(expandedSection === section ? '' : section)
  }

  const windSpeedMph = (localWeather.wind_speed * 0.681818).toFixed(1)
  const tempF = (localWeather.ambient_temp * 9/5 + 32).toFixed(1)

  return (
    <div className="weather-controls advanced">
      <div className="controls-header">
        <CloudRain size={20} />
        <h2>IEEE 738 Weather Parameters</h2>
      </div>

      <div className="controls-body">
        {/* Quick Presets */}
        <div className="preset-section">
          <h3 style={{
            fontSize: '0.875rem',
            fontWeight: 600,
            marginBottom: '0.75rem',
            color: '#9ca3af',
            textTransform: 'uppercase',
            letterSpacing: '0.05em'
          }}>
            Quick Scenarios
          </h3>
          <div className="preset-grid">
            {(Object.keys(PRESETS) as Array<keyof typeof PRESETS>).map((key) => {
              const preset = PRESETS[key]
              return (
                <button
                  key={key}
                  className="preset-card"
                  onClick={() => applyPreset(key)}
                  disabled={loading}
                  title={preset.description}
                >
                  <div className="preset-name">{preset.name}</div>
                  <div className="preset-desc">{preset.description}</div>
                </button>
              )
            })}
          </div>
        </div>

        {/* Temperature & Wind Section */}
        <div className="collapsible-section">
          <button
            className="section-header"
            onClick={() => toggleSection('temperature')}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Thermometer size={18} />
              <span>Temperature & Wind</span>
            </div>
            <span className="expand-icon">{expandedSection === 'temperature' ? '−' : '+'}</span>
          </button>

          {expandedSection === 'temperature' && (
            <div className="section-content">
              {/* Ambient Temperature */}
              <div className="control-group">
                <label>
                  <Thermometer size={16} />
                  <span>Ambient Temperature</span>
                  <span className="help-text">Higher temp = Lower rating</span>
                </label>
                <div className="input-with-unit">
                  <input
                    type="range"
                    min="-20"
                    max="50"
                    step="1"
                    value={localWeather.ambient_temp}
                    onChange={(e) => handleChange('ambient_temp', parseFloat(e.target.value))}
                  />
                  <div className="value-display">
                    <strong>{localWeather.ambient_temp}°C</strong>
                    <span className="value-alt">({tempF}°F)</span>
                  </div>
                </div>
              </div>

              {/* Wind Speed */}
              <div className="control-group">
                <label>
                  <Wind size={16} />
                  <span>Wind Speed</span>
                  <span className="help-text">Higher wind = Better cooling</span>
                </label>
                <div className="input-with-unit">
                  <input
                    type="range"
                    min="0"
                    max="20"
                    step="0.5"
                    value={localWeather.wind_speed}
                    onChange={(e) => handleChange('wind_speed', parseFloat(e.target.value))}
                  />
                  <div className="value-display">
                    <strong>{localWeather.wind_speed.toFixed(1)} ft/s</strong>
                    <span className="value-alt">({windSpeedMph} mph)</span>
                  </div>
                </div>
              </div>

              {/* Wind Angle */}
              <div className="control-group">
                <label>
                  <Compass size={16} />
                  <span>Wind Angle</span>
                  <span className="help-text">90° (perpendicular) cools best</span>
                </label>
                <div className="input-with-unit">
                  <input
                    type="range"
                    min="0"
                    max="90"
                    step="5"
                    value={localWeather.wind_angle}
                    onChange={(e) => handleChange('wind_angle', parseFloat(e.target.value))}
                  />
                  <div className="value-display">
                    <strong>{localWeather.wind_angle}°</strong>
                    <span className="value-alt">
                      {localWeather.wind_angle === 90 ? 'Perpendicular' :
                       localWeather.wind_angle === 0 ? 'Parallel' :
                       `${localWeather.wind_angle}° angle`}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Solar Conditions Section */}
        <div className="collapsible-section">
          <button
            className="section-header"
            onClick={() => toggleSection('solar')}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Sun size={18} />
              <span>Solar Conditions</span>
            </div>
            <span className="expand-icon">{expandedSection === 'solar' ? '−' : '+'}</span>
          </button>

          {expandedSection === 'solar' && (
            <div className="section-content">
              {/* Time of Day */}
              <div className="control-group">
                <label>
                  <Sun size={16} />
                  <span>Time of Day</span>
                  <span className="help-text">Solar peaks at noon</span>
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
                    <strong>{String(localWeather.sun_time).padStart(2, '0')}:00</strong>
                    <span className="value-alt">
                      {localWeather.sun_time < 6 ? 'Night' :
                       localWeather.sun_time < 12 ? 'Morning' :
                       localWeather.sun_time < 17 ? 'Afternoon' :
                       localWeather.sun_time < 20 ? 'Evening' : 'Night'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Date */}
              <div className="control-group">
                <label>
                  <Calendar size={16} />
                  <span>Date</span>
                  <span className="help-text">For solar angle calculations</span>
                </label>
                <div className="input-with-unit">
                  <input
                    type="text"
                    value={localWeather.date}
                    onChange={(e) => handleChange('date', e.target.value)}
                    placeholder="DD MMM (e.g., 21 Jun)"
                    style={{
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: '1px solid rgba(255, 255, 255, 0.2)',
                      borderRadius: '8px',
                      padding: '0.5rem 0.75rem',
                      color: '#f5f5f7',
                      fontSize: '0.875rem',
                      width: '100%'
                    }}
                  />
                </div>
              </div>

              {/* Emissivity */}
              <div className="control-group">
                <label>
                  <Zap size={16} />
                  <span>Surface Emissivity</span>
                  <span className="help-text">Heat radiation efficiency</span>
                </label>
                <div className="input-with-unit">
                  <input
                    type="range"
                    min="0.2"
                    max="1.0"
                    step="0.05"
                    value={localWeather.emissivity || 0.8}
                    onChange={(e) => handleChange('emissivity', parseFloat(e.target.value))}
                  />
                  <div className="value-display">
                    <strong>{(localWeather.emissivity || 0.8).toFixed(2)}</strong>
                    <span className="value-alt">
                      {(localWeather.emissivity || 0.8) >= 0.9 ? 'Weathered' :
                       (localWeather.emissivity || 0.8) >= 0.7 ? 'Normal' : 'New/Clean'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Absorptivity */}
              <div className="control-group">
                <label>
                  <Sun size={16} />
                  <span>Solar Absorptivity</span>
                  <span className="help-text">Solar heat absorption</span>
                </label>
                <div className="input-with-unit">
                  <input
                    type="range"
                    min="0.2"
                    max="1.0"
                    step="0.05"
                    value={localWeather.absorptivity || 0.8}
                    onChange={(e) => handleChange('absorptivity', parseFloat(e.target.value))}
                  />
                  <div className="value-display">
                    <strong>{(localWeather.absorptivity || 0.8).toFixed(2)}</strong>
                    <span className="value-alt">
                      {(localWeather.absorptivity || 0.8) >= 0.9 ? 'Dark/Aged' :
                       (localWeather.absorptivity || 0.8) >= 0.7 ? 'Normal' : 'Reflective'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Location & Atmospheric Section */}
        <div className="collapsible-section">
          <button
            className="section-header"
            onClick={() => toggleSection('location')}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Mountain size={18} />
              <span>Location & Atmospheric</span>
            </div>
            <span className="expand-icon">{expandedSection === 'location' ? '−' : '+'}</span>
          </button>

          {expandedSection === 'location' && (
            <div className="section-content">
              {/* Elevation */}
              <div className="control-group">
                <label>
                  <Mountain size={16} />
                  <span>Elevation</span>
                  <span className="help-text">Affects air density</span>
                </label>
                <div className="input-with-unit">
                  <input
                    type="range"
                    min="0"
                    max="5000"
                    step="100"
                    value={localWeather.elevation || 1000}
                    onChange={(e) => handleChange('elevation', parseFloat(e.target.value))}
                  />
                  <div className="value-display">
                    <strong>{localWeather.elevation || 1000} ft</strong>
                    <span className="value-alt">({((localWeather.elevation || 1000) * 0.3048).toFixed(0)} m)</span>
                  </div>
                </div>
              </div>

              {/* Latitude */}
              <div className="control-group">
                <label>
                  <Compass size={16} />
                  <span>Latitude</span>
                  <span className="help-text">For solar calculations</span>
                </label>
                <div className="input-with-unit">
                  <input
                    type="range"
                    min="0"
                    max="90"
                    step="1"
                    value={localWeather.latitude || 27}
                    onChange={(e) => handleChange('latitude', parseFloat(e.target.value))}
                  />
                  <div className="value-display">
                    <strong>{localWeather.latitude || 27}°N</strong>
                    <span className="value-alt">
                      {(localWeather.latitude || 27) < 23.5 ? 'Tropical' :
                       (localWeather.latitude || 27) < 66.5 ? 'Temperate' : 'Polar'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Line Direction */}
              <div className="control-group">
                <label>
                  <Compass size={16} />
                  <span>Line Orientation</span>
                  <span className="help-text">Affects solar heating</span>
                </label>
                <select
                  value={localWeather.direction || 'EastWest'}
                  onChange={(e) => handleChange('direction', e.target.value)}
                  style={{
                    background: 'rgba(255, 255, 255, 0.05)',
                    border: '1px solid rgba(255, 255, 255, 0.2)',
                    borderRadius: '8px',
                    padding: '0.5rem 0.75rem',
                    color: '#f5f5f7',
                    fontSize: '0.875rem',
                    width: '100%',
                    cursor: 'pointer'
                  }}
                >
                  <option value="EastWest">East-West</option>
                  <option value="NorthSouth">North-South</option>
                </select>
              </div>

              {/* Atmosphere */}
              <div className="control-group">
                <label>
                  <Eye size={16} />
                  <span>Atmospheric Condition</span>
                  <span className="help-text">Air clarity</span>
                </label>
                <select
                  value={localWeather.atmosphere || 'Clear'}
                  onChange={(e) => handleChange('atmosphere', e.target.value)}
                  style={{
                    background: 'rgba(255, 255, 255, 0.05)',
                    border: '1px solid rgba(255, 255, 255, 0.2)',
                    borderRadius: '8px',
                    padding: '0.5rem 0.75rem',
                    color: '#f5f5f7',
                    fontSize: '0.875rem',
                    width: '100%',
                    cursor: 'pointer'
                  }}
                >
                  <option value="Clear">Clear</option>
                  <option value="Industrial">Industrial</option>
                </select>
              </div>
            </div>
          )}
        </div>

        {/* Action Buttons */}
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
            {loading ? 'Recalculating...' : 'Apply & Recalculate'}
          </button>
        </div>

        {onCompare && (
          <button
            className="btn-compare"
            onClick={onCompare}
            style={{
              width: '100%',
              marginTop: '0.75rem',
              padding: '0.75rem',
              background: 'rgba(59, 130, 246, 0.1)',
              border: '1px solid rgba(59, 130, 246, 0.3)',
              borderRadius: '8px',
              color: '#60a5fa',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            {showComparison ? 'Hide Comparison' : 'Compare with Baseline'}
          </button>
        )}
      </div>
    </div>
  )
}

export default WeatherControlsAdvanced
