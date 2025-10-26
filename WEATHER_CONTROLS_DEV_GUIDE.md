# Weather Controls - Developer Guide

## Architecture Overview

The weather analysis feature is built with a modular React + TypeScript frontend and Flask backend architecture.

### Component Hierarchy

```
App.tsx
└── Analysis Tab
    ├── Weather Analysis Sub-tab
    │   └── WeatherAnalysis.tsx
    │       ├── WeatherControlsAdvanced.tsx
    │       ├── System Impact Summary
    │       └── Comparison View
    └── Outage Simulation Sub-tab
        └── OutageAnalysis.tsx
```

## File Structure

### Frontend Components

```
frontend/src/
├── components/
│   ├── WeatherControlsAdvanced.tsx     # Advanced weather parameter controls
│   ├── WeatherAnalysis.tsx             # Main analysis component with comparison
│   ├── WeatherControls-simple.tsx      # Simple controls for Map tab
│   └── WeatherControls.css             # Shared styles
├── services/
│   └── api.ts                          # API client with WeatherParams interface
└── App.tsx                             # Main app with tab routing
```

### Backend

```
backend/
├── app.py                              # Flask server with /api/lines/ratings endpoint
├── rating_calculator.py                # IEEE 738 calculation engine
└── chatbot_service.py                  # AI integration for weather impact analysis
```

## Key Components

### 1. WeatherControlsAdvanced.tsx

**Purpose**: Comprehensive IEEE 738 parameter controls with presets

**Props**:
```typescript
interface WeatherControlsAdvancedProps {
  weather: WeatherParams
  onChange: (weather: Partial<WeatherParams>) => void
  loading: boolean
  onCompare?: () => void
  showComparison?: boolean
}
```

**Key Features**:
- Collapsible sections (Temperature & Wind, Solar, Location)
- 6 preset scenarios
- Real-time value display with unit conversions
- Local state management before applying changes
- Help text for each parameter

**State Management**:
```typescript
const [localWeather, setLocalWeather] = useState<WeatherParams>({
  ...DEFAULT_WEATHER,
  ...weather
})
const [expandedSection, setExpandedSection] = useState<string>('temperature')
```

**Preset System**:
```typescript
const PRESETS = {
  summerPeak: { /* ... */ },
  winterLow: { /* ... */ },
  highWind: { /* ... */ },
  nightOperation: { /* ... */ },
  extremeHeat: { /* ... */ },
  optimal: { /* ... */ }
}
```

### 2. WeatherAnalysis.tsx

**Purpose**: Container for weather controls + system metrics + comparison

**Props**:
```typescript
interface WeatherAnalysisProps {
  weather: WeatherParams
  ratings: RatingResponse | null
  onWeatherChange: (weather: Partial<WeatherParams>) => void
  loading: boolean
}
```

**Key Features**:
- Baseline rating storage
- Comparison metric calculations
- System status dashboard
- Impact visualization

**Comparison Calculation**:
```typescript
const calculateComparison = () => {
  const metrics = {
    criticalChange: (current - baseline),
    highStressChange: (current - baseline),
    avgLoadingChange: (current - baseline),
    maxLoadingChange: (current - baseline),
    capacityChange: ((modified - baseline) / baseline) * 100
  }
}
```

### 3. API Integration

**TypeScript Interface** (api.ts:3-15):
```typescript
export interface WeatherParams {
  ambient_temp: number      // Ta: Ambient temperature (°C) - Range: -20 to 50
  wind_speed: number         // WindVelocity: Wind speed (ft/sec) - Range: 0 to 20
  wind_angle: number         // WindAngleDeg: Wind angle (degrees) - Range: 0 to 90
  sun_time: number           // SunTime: Hour of day - Range: 0 to 24
  date: string               // Date: Date for solar calculations - Format: 'DD MMM'
  elevation?: number         // Elevation (ft) - Range: 0 to 5000
  latitude?: number          // Latitude (degrees) - Range: 0 to 90
  emissivity?: number        // Surface emissivity - Range: 0.2 to 1.0
  absorptivity?: number      // Solar absorptivity - Range: 0.2 to 1.0
  direction?: 'EastWest' | 'NorthSouth'  // Line orientation
  atmosphere?: 'Clear' | 'Industrial'     // Atmospheric condition
}
```

**API Call** (api.ts:69-83):
```typescript
export async function fetchLineRatings(weather: WeatherParams): Promise<RatingResponse> {
  const response = await fetch(`${API_BASE}/lines/ratings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(weather),
  })
  return response.json()
}
```

## Backend Integration

### Flask Endpoint (app.py:86-132)

```python
@app.route('/api/lines/ratings', methods=['POST'])
def calculate_ratings():
    weather = request.json

    # Map frontend params to IEEE 738 params
    weather_params = {
        'Ta': weather.get('ambient_temp', 25),
        'WindVelocity': weather.get('wind_speed', 2.0),
        'WindAngleDeg': weather.get('wind_angle', 90),
        'SunTime': weather.get('sun_time', 12),
        'Date': weather.get('date', '12 Jun'),
        'Emissivity': weather.get('emissivity', 0.8),
        'Absorptivity': weather.get('absorptivity', 0.8),
        'Direction': weather.get('direction', 'EastWest'),
        'Atmosphere': weather.get('atmosphere', 'Clear'),
        'Elevation': weather.get('elevation', 1000),
        'Latitude': weather.get('latitude', 27)
    }

    # Calculate ratings for all lines
    results = calculator.calculate_all_line_ratings(weather_params)

    # Clean NaN values before sending to frontend
    return jsonify({
        "weather": weather_params,
        "lines": clean_nan_values(results['lines']),
        "summary": clean_nan_values(results['summary'])
    })
```

### IEEE 738 Calculation

The backend uses `rating_calculator.py` which implements IEEE 738-2012 standard:

1. **Heat Balance Equation**:
   ```
   q_c + q_r = q_s + I²R
   ```
   Where:
   - q_c: Convective heat loss
   - q_r: Radiative heat loss
   - q_s: Solar heat gain
   - I²R: Joule heating

2. **Convective Cooling** (depends on wind speed & angle):
   ```python
   q_c = K_angle * (T_conductor - T_ambient)^1.25  # Natural convection
   q_c = K_wind * sqrt(wind_speed) * (T_c - T_a)   # Forced convection
   ```

3. **Solar Heating** (depends on time, date, latitude, orientation):
   ```python
   q_s = absorptivity * solar_radiation * projected_area
   ```

## Styling

### CSS Architecture (WeatherControls.css)

**Base Styles**: Lines 1-181
- Standard weather controls for Map tab
- Light background, blue gradients

**Advanced Styles**: Lines 183-381
- Dark glassmorphism design for Analysis tab
- Collapsible sections
- Preset grid
- Comparison view

**Key Classes**:
```css
.weather-controls.advanced { /* Dark theme */ }
.collapsible-section { /* Expandable parameter groups */ }
.preset-grid { /* 2-column preset buttons */ }
.comparison-view { /* Impact analysis display */ }
```

## State Flow

### 1. User Modifies Parameter

```
User adjusts slider
  → handleChange() updates localWeather state
  → Value display shows new value
  → "Apply & Recalculate" button enabled
```

### 2. User Applies Changes

```
User clicks "Apply & Recalculate"
  → handleApply() called
  → onChange(localWeather) prop function
  → App.tsx handleWeatherChange()
  → loadRatings() API call
  → setRatings() with new data
  → WeatherAnalysis receives updated ratings
  → System Impact Summary updates
```

### 3. User Enables Comparison

```
User clicks "Compare with Baseline"
  → handleCompareToggle()
  → calculateComparison()
  → Metrics calculated (delta from baseline)
  → Comparison view rendered with changes
  → Color-coded indicators (green/red/neutral)
```

## Adding New Features

### Adding a New Weather Parameter

1. **Update TypeScript Interface** (api.ts):
```typescript
export interface WeatherParams {
  // ...existing params
  new_param?: number  // Description and range
}
```

2. **Add to Default Values** (WeatherControlsAdvanced.tsx):
```typescript
const DEFAULT_WEATHER: WeatherParams = {
  // ...existing defaults
  new_param: 0.5,
}
```

3. **Add UI Control** (WeatherControlsAdvanced.tsx):
```tsx
<div className="control-group">
  <label>
    <Icon size={16} />
    <span>New Parameter</span>
    <span className="help-text">What it affects</span>
  </label>
  <div className="input-with-unit">
    <input
      type="range"
      min="0"
      max="1"
      step="0.1"
      value={localWeather.new_param || 0.5}
      onChange={(e) => handleChange('new_param', parseFloat(e.target.value))}
    />
    <div className="value-display">
      <strong>{(localWeather.new_param || 0.5).toFixed(1)}</strong>
    </div>
  </div>
</div>
```

4. **Map to Backend** (app.py):
```python
weather_params = {
    # ...existing mappings
    'NewParam': weather.get('new_param', 0.5),
}
```

5. **Update IEEE 738 Calculator** (rating_calculator.py):
```python
def calculate_rating(self, weather_params):
    new_param = weather_params.get('NewParam', 0.5)
    # Use in thermal calculation
```

### Adding a New Preset Scenario

In WeatherControlsAdvanced.tsx:

```typescript
const PRESETS = {
  // ...existing presets
  myScenario: {
    name: 'My Scenario',
    description: 'Custom weather conditions',
    params: {
      ambient_temp: 30,
      wind_speed: 4.0,
      wind_angle: 90,
      sun_time: 10,
      date: '15 Aug'
    }
  }
}
```

Presets automatically appear in the grid (2 columns, responsive).

### Adding a New Comparison Metric

In WeatherAnalysis.tsx:

```typescript
const calculateComparison = () => {
  const metrics = {
    // ...existing metrics
    newMetric: calculateNewMetric(baseline, modified)
  }
}

// Add to comparison grid render:
<div className="comparison-item">
  <div className="comparison-label">New Metric</div>
  <div className="comparison-value">
    {comparison.metrics.newMetric.toFixed(2)}
  </div>
  {renderMetricChange(comparison.metrics.newMetric, ' units')}
</div>
```

## Testing

### Unit Testing Strategy

**Component Tests**:
```typescript
describe('WeatherControlsAdvanced', () => {
  test('renders all parameter controls', () => {})
  test('applies preset correctly', () => {})
  test('validates parameter ranges', () => {})
  test('calls onChange on apply', () => {})
})
```

**Integration Tests**:
```typescript
describe('Weather Analysis Flow', () => {
  test('updates ratings when weather changes', () => {})
  test('comparison calculates correct deltas', () => {})
  test('handles API errors gracefully', () => {})
})
```

### Manual Testing Checklist

- [ ] All sliders move smoothly
- [ ] Value displays update in real-time
- [ ] Presets apply correct values
- [ ] "Apply & Recalculate" triggers API call
- [ ] System metrics update after calculation
- [ ] Comparison view shows correct deltas
- [ ] Collapsible sections expand/collapse
- [ ] Reset button restores defaults
- [ ] Backend handles all parameter combinations
- [ ] No console errors in browser
- [ ] Loading states display correctly

### Backend Testing

```bash
# Test API endpoint
curl -X POST http://localhost:5000/api/lines/ratings \
  -H "Content-Type: application/json" \
  -d '{
    "ambient_temp": 40,
    "wind_speed": 1.0,
    "wind_angle": 90,
    "sun_time": 14,
    "date": "21 Jun",
    "elevation": 1000,
    "latitude": 27,
    "emissivity": 0.8,
    "absorptivity": 0.8,
    "direction": "EastWest",
    "atmosphere": "Clear"
  }'
```

Expected response:
```json
{
  "weather": { /* echoed params */ },
  "lines": [ /* array of line ratings */ ],
  "summary": {
    "total_lines": 77,
    "critical_lines": [ /* overloaded lines */ ],
    "avg_loading": 45.2,
    "max_loading": 98.7
  }
}
```

## Performance Considerations

### Frontend Optimization

1. **Local State for Sliders**: Prevents API calls on every slider movement
   ```typescript
   const [localWeather, setLocalWeather] = useState(weather)
   // Update local state immediately, call API on "Apply"
   ```

2. **Debounced Updates**: For auto-apply mode (if implemented)
   ```typescript
   const debouncedApply = useMemo(
     () => debounce(onChange, 500),
     [onChange]
   )
   ```

3. **Conditional Rendering**: Only render comparison when enabled
   ```typescript
   {showComparison && comparison && (
     <ComparisonView />
   )}
   ```

### Backend Optimization

1. **Caching**: Conductor properties cached in memory
2. **Vectorization**: NumPy/Pandas for bulk line calculations
3. **NaN Handling**: Clean data before JSON serialization

## Troubleshooting

### Common Issues

**Issue**: Sliders don't update values
- **Cause**: Local state not initialized
- **Fix**: Ensure `useState` includes spread of incoming weather prop

**Issue**: "Apply" doesn't trigger recalculation
- **Cause**: onChange prop not connected
- **Fix**: Verify onChange is passed from App.tsx to WeatherAnalysis to Controls

**Issue**: Comparison shows NaN
- **Cause**: Baseline ratings not set
- **Fix**: Ensure baselineRatings stored on first load

**Issue**: Backend returns 500 error
- **Cause**: Invalid parameter values
- **Fix**: Add validation in frontend and backend

### Debug Mode

Enable verbose logging:

**Frontend**:
```typescript
const handleApply = () => {
  console.log('Applying weather:', localWeather)
  onChange(localWeather)
}
```

**Backend**:
```python
logger.info(f"Received weather params: {weather_params}")
logger.info(f"Calculated ratings: {results}")
```

## Future Enhancements

### Planned Features

1. **Auto-Apply Mode**: Real-time updates without "Apply" button
2. **Scenario Saving**: Save custom weather scenarios to local storage
3. **Export/Import**: JSON export of weather conditions and results
4. **Time-Series Analysis**: Animate weather changes over time
5. **Probabilistic Analysis**: Monte Carlo with weather distributions
6. **Advanced Comparison**: Multi-scenario comparison (3+ scenarios)
7. **Weather Forecasting Integration**: Pull live forecast data
8. **Mobile Optimization**: Touch-friendly sliders and responsive layout

### Extension Points

**Custom Presets**:
```typescript
interface UserPreset {
  id: string
  name: string
  description: string
  params: WeatherParams
  createdAt: Date
}

const [userPresets, setUserPresets] = useState<UserPreset[]>([])
```

**Time-Series**:
```typescript
interface WeatherTimeSeries {
  timestamps: Date[]
  weather: WeatherParams[]
  ratings: RatingResponse[]
}
```

**Export**:
```typescript
const exportScenario = () => {
  const data = {
    weather: localWeather,
    ratings: ratings,
    comparison: comparison,
    timestamp: new Date().toISOString()
  }
  downloadJSON(data, 'weather-analysis.json')
}
```

## Code Style Guidelines

### TypeScript

- Use explicit types for all props and state
- Prefer interfaces over types for objects
- Use optional chaining for nullable values: `weather?.ambient_temp`
- Add JSDoc comments for complex functions

### React

- Functional components with hooks (no class components)
- Extract reusable logic into custom hooks
- Keep components focused (single responsibility)
- Use controlled components for form inputs

### CSS

- Follow BEM naming for complex components
- Use CSS variables for theme values
- Prefer flexbox/grid over absolute positioning
- Mobile-first responsive design

## API Documentation

### Request Format

```http
POST /api/lines/ratings HTTP/1.1
Host: localhost:5000
Content-Type: application/json

{
  "ambient_temp": 25,
  "wind_speed": 2.0,
  "wind_angle": 90,
  "sun_time": 12,
  "date": "12 Jun",
  "elevation": 1000,
  "latitude": 27,
  "emissivity": 0.8,
  "absorptivity": 0.8,
  "direction": "EastWest",
  "atmosphere": "Clear"
}
```

### Response Format

```json
{
  "weather": {
    "Ta": 25,
    "WindVelocity": 2.0,
    "WindAngleDeg": 90,
    "SunTime": 12,
    "Date": "12 Jun",
    "Elevation": 1000,
    "Latitude": 27,
    "Emissivity": 0.8,
    "Absorptivity": 0.8,
    "Direction": "EastWest",
    "Atmosphere": "Clear"
  },
  "lines": [
    {
      "name": "L0",
      "branch_name": "Bus 0 - Bus 1",
      "conductor": "ACSR_Drake",
      "voltage_kv": 138,
      "rating_amps": 1087.3,
      "rating_mva": 260.5,
      "static_rating_mva": 245.0,
      "flow_mva": 123.4,
      "loading_pct": 47.4,
      "margin_mva": 137.1,
      "stress_level": "normal",
      "bus0": "Bus 0",
      "bus1": "Bus 1"
    }
  ],
  "summary": {
    "total_lines": 77,
    "critical_count": 0,
    "high_stress_count": 2,
    "caution_count": 15,
    "normal_count": 60,
    "avg_loading": 45.2,
    "max_loading": 94.7,
    "max_loading_line": "L42",
    "critical_lines": []
  }
}
```

## Support

For development questions or contributions:
- Review existing code in `frontend/src/components/Weather*.tsx`
- Check backend logic in `backend/app.py` and `rating_calculator.py`
- Follow TypeScript/React best practices
- Add tests for new features
- Update this documentation when adding features
