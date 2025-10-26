# BLACKOUT by hack ops

An intelligent web-based system for transmission planners to calculate and visualize real-time power line ratings, perform N-1 contingency analysis, predict daily load stress patterns, and leverage AI-powered recommendations. This system prevents grid blackouts by dynamically tracking line capacity, simulating outage scenarios, and identifying stress points before failures occur.

## Project Overview

This prototype answers three critical questions:
1. **Threshold Detection**: At what ambient temperature or wind conditions do lines exceed their safe limits?
2. **Stress Progression**: Which lines or areas show stress first as ambient temperature increases?
3. **Impact Assessment**: How significant is the stress on the system?

## Key Features

### 1. Interactive Geospatial Visualization
- Real-time interactive map displaying all transmission lines
- Color-coded lines by stress level (green=normal, yellow=caution, orange=high, red=critical)
- Hover tooltips showing line details
- Click for comprehensive line information including:
  - Current rating and loading percentage
  - Safe operating limits
  - Margin to overload
  - Weather conditions affecting the line

### 2. Weather-Based Dynamic Ratings
- Adjust ambient temperature, wind speed, and solar conditions
- Instant recalculation of line ratings using IEEE 738 standard
- Compare dynamic ratings vs static ratings
- Quick scenario buttons (Cool & Windy, Hot & Calm, Extreme Heat)

### 3. Threshold Analysis
- Find exact temperature where lines begin to overload
- Visualize loading progression with temperature changes
- Identify early warning indicators
- Graph showing stress development over temperature range

### 4. Alert & Insights Dashboard
- Prioritized list of top 10 lines approaching limits
- Real-time grid health status indicator
- Summary statistics (total lines, overloaded, high stress, caution)
- Actionable recommendations for operators
- System health classification

### 5. Transmission Line Outage Simulation (N-1 Contingency Analysis)
- Simulate single or multiple line outages
- AC/DC power flow analysis using PyPSA
- Identify cascading effects on remaining lines:
  - Newly overloaded lines
  - Loading changes for all active lines
  - Islanded buses (stranded substations)
  - Network stability metrics
- Visual outage maps showing before/after comparison
- Comprehensive impact reports with metrics

### 6. Daily Load Scaling Analysis
- 24-hour transmission system stress profiling
- Hourly power flow analysis with load variations
- Peak stress hour identification
- Load curve simulation (minimum at 6 AM, maximum at 6 PM)
- Convergence tracking for reliability assessment
- Most stressed lines by hour

### 7. AI-Powered Chatbot Assistant
- Natural language interface powered by Claude AI
- Context-aware responses using live grid data
- Capabilities:
  - Data explanation and technical guidance
  - Line status queries
  - Weather impact predictions
  - Variable impact analysis
  - Autonomous agent insights integration
- Suggested questions for quick analysis

### 8. Autonomous Grid Monitoring Agent
- Continuous grid state monitoring for anomalies
- Predictive alerts using weather forecasts
- Prioritized operator recommendations
- Learning from operator feedback
- Persistent state management across sessions
- Decision audit logging for compliance

## Technical Architecture

### Backend (Python + Flask)
- **Dynamic Rating Engine**: IEEE 738 standard implementation
- **Data Processing**: Pandas & NumPy for CSV/GeoJSON handling
- **RESTful API**: Flask with CORS support
- **Power Flow Analysis**: PyPSA integration for contingency analysis
- **Load Profiling**: Daily load scaling analyzer with hourly resolution
- **Visualization**: Plotly for interactive network maps
- **AI Integration**: Anthropic Claude API for chatbot and autonomous agent
- **State Management**: Persistent JSON storage for agent learning

### Frontend (React + TypeScript)
- **Interactive Maps**: Plotly-based geospatial visualization with real-time updates
- **Modern UI**: React 18 with TypeScript and Hooks
- **Component Library**: Custom React components with Lucide icons
- **Build Tool**: Vite for fast development and optimized production builds
- **Dark Theme**: Professional dark mode interface
- **Responsive Design**: Mobile-friendly layout

### Calculations
- **IEEE 738 Standard**: Thermal rating calculations
- **Weather Parameters**: Temperature, wind speed, solar radiation
- **Conductor Properties**: Resistance, diameter, MOT (Maximum Operating Temperature)
- **MVA Conversion**: √3 × I × V × 10⁻⁶

## Project Structure

```
AEPhacks/
├── backend/
│   ├── app.py                      # Flask API server (port 5001)
│   ├── data_loader.py              # CSV/GeoJSON data loader
│   ├── rating_calculator.py        # IEEE 738 rating engine
│   ├── ieee738.py                  # IEEE 738 thermal calculations
│   ├── map_generator.py            # Plotly interactive map generation
│   ├── chatbot_service.py          # Claude AI chatbot integration
│   ├── agent.py                    # Autonomous monitoring agent
│   ├── outage_simulator.py         # N-1 contingency analysis
│   ├── load_scaling_analyzer.py    # Daily load profiling
│   ├── requirements.txt            # Python dependencies
│   └── data/
│       ├── lines.csv               # Transmission line data
│       ├── buses.csv               # Substation data
│       ├── generators.csv          # Generation units
│       ├── loads.csv               # Load points
│       ├── conductor_library.csv   # Conductor specs (IEEE 738)
│       ├── oneline_lines.geojson   # Line geographic coordinates
│       └── oneline_busses.geojson  # Bus locations
│
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── AlertDashboard.tsx          # Real-time alerts
    │   │   ├── NetworkMap.tsx              # Plotly network visualization
    │   │   ├── WeatherAnalysis.tsx         # Weather controls & comparison
    │   │   ├── WeatherControlsAdvanced.tsx # Advanced weather inputs
    │   │   ├── OutageAnalysis.tsx          # Outage simulation UI
    │   │   ├── LoadScalingAnalysis.tsx     # Daily load profiling UI
    │   │   ├── Chatbot.tsx                 # AI assistant interface
    │   │   └── ThresholdAnalysis.tsx       # Temperature threshold charts
    │   ├── services/
    │   │   └── api.ts                      # Backend API client
    │   ├── App.tsx                         # Main application
    │   └── main.tsx
    ├── package.json
    └── vite.config.ts
```

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- Node.js 18 or higher
- npm or yarn

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python app.py
```

Backend API will be available at `http://localhost:5001`

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at `http://localhost:5173`

## Usage

### Live Grid Map

1. Open the application in your browser
2. The map displays all transmission lines color-coded by stress level
3. **Adjust Weather**: Use the controls in the right sidebar to modify:
   - Ambient Temperature (-10°C to 50°C)
   - Wind Speed (0 to 10 ft/s)
   - Time of Day (0-23 hours)
4. **Quick Scenarios**: Try preset weather scenarios
5. **Explore Lines**:
   - Hover over lines to see quick info
   - Click lines for detailed information panel

### Threshold Analysis

1. Click the "Threshold Analysis" tab
2. Set temperature range to analyze (e.g., 20°C to 50°C)
3. Set wind speed conditions
4. Click "Run Analysis"
5. View:
   - First overload temperature
   - Progressive stress charts
   - Operational recommendations

### API Endpoints

#### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/grid/topology` | Get grid topology (lines & buses) |
| `POST` | `/api/lines/ratings` | Calculate line ratings for weather conditions |
| `POST` | `/api/lines/threshold` | Find temperature threshold for overloads |
| `GET` | `/api/lines/<id>` | Get specific line details |

#### Outage Simulation Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/outage/available-lines` | List all lines for simulation |
| `POST` | `/api/outage/simulate` | Simulate line outage(s) with N-1 analysis |
| `POST` | `/api/contingency/n1` | Legacy N-1 contingency analysis |

#### Load Scaling Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/load-scaling/daily?hours=24` | 24-hour load profile analysis |
| `GET` | `/api/load-scaling/hour/<hour>` | Analyze specific hour (0-23) |
| `GET` | `/api/load-scaling/profile` | Get load profile without analysis |

#### AI & Agent Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chatbot` | AI chatbot with grid context |
| `POST` | `/api/chatbot/analyze-impact` | Variable impact analysis |
| `GET` | `/api/agent/status` | Autonomous agent status |
| `POST` | `/api/agent/predict` | Predict future grid states |
| `POST` | `/api/agent/recommendations` | Get AI recommendations |
| `POST` | `/api/agent/feedback` | Submit operator feedback |

#### Map Generation Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/map/generate` | Generate interactive network map |
| `POST` | `/api/map/line/<id>` | Get line details for map |
| `POST` | `/api/map/outage` | Generate outage visualization map |

#### Example: Calculate Line Ratings

**Request:**
```bash
curl -X POST http://localhost:5001/api/lines/ratings \
  -H "Content-Type: application/json" \
  -d '{
    "ambient_temp": 35,
    "wind_speed": 2.0,
    "wind_angle": 90,
    "sun_time": 14,
    "date": "21 Jun"
  }'
```

**Response:**
```json
{
  "weather": {
    "Ta": 35,
    "WindVelocity": 2.0,
    "WindAngleDeg": 90,
    "SunTime": 14,
    "Date": "21 Jun"
  },
  "lines": [
    {
      "name": "L0",
      "branch_name": "ALOHA138 TO HONOLULU138 CKT 1",
      "rating_mva": 228.5,
      "flow_mva": 79.2,
      "loading_pct": 34.7,
      "stress_level": "normal",
      "margin_mva": 149.3,
      "voltage_kv": 138,
      "conductor": "ACSR 795"
    }
  ],
  "summary": {
    "total_lines": 186,
    "overloaded_lines": 3,
    "high_stress_lines": 12,
    "avg_loading": 45.3,
    "max_loading": 112.5
  }
}
```

#### Example: Simulate Outage

**Request:**
```bash
curl -X POST http://localhost:5001/api/outage/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "outage_lines": ["L48", "L49"],
    "use_lpf": false
  }'
```

**Response:**
```json
{
  "success": true,
  "outage_lines": ["L48", "L49"],
  "overloaded_lines": [...],
  "affected_lines": [...],
  "islanded_buses": [],
  "metrics": {
    "total_lines": 186,
    "outaged_lines_count": 2,
    "overloaded_count": 5,
    "max_loading_pct": 125.3,
    "max_loading_increase": 45.2
  }
}
```

## Data Sources

The system uses the **Hawaii40 synthetic grid** test case from Texas A&M Electric Grid Test Cases database.

**Data Files**:
- `osu_hackathon/hawaii40_osu/csv/lines.csv` - Line properties
- `osu_hackathon/hawaii40_osu/gis/oneline_lines.geojson` - Geographic data
- `osu_hackathon/ieee738/conductor_library.csv` - Conductor properties
- `osu_hackathon/hawaii40_osu/line_flows_nominal.csv` - Nominal power flows

## IEEE 738 Standard

The system implements the IEEE Standard 738-2006 for calculating the current-temperature relationship of bare overhead conductors.

**Key Parameters**:
- **Ambient Temperature (Ta)**: Air temperature in °C
- **Wind Speed (Vw)**: Wind velocity in ft/s
- **Solar Radiation**: Based on time of day and date
- **Conductor Properties**: Resistance, diameter, emissivity
- **Maximum Operating Temperature (MOT)**: Line-specific thermal limit

**Formula** (simplified):
```
Rating (Amps) = f(Ta, Vw, Solar, Conductor, MOT)
Rating (MVA) = √3 × I × V × 10⁻⁶
Loading (%) = (Flow / Rating) × 100
```

## Success Criteria

✅ **Accuracy**: Correct IEEE 738 calculations and overload detection
✅ **Usability**: Clear, intuitive visualization requiring minimal training
✅ **Actionability**: Specific insights and recommendations for operators
✅ **Innovation**: Real-time dynamic rating analysis with geographic context
✅ **Performance**: Sub-second response for rating recalculations
✅ **Practical Value**: Direct applicability to AEP operations

## Demo Highlights

1. **Normal Conditions** (25°C, 2 ft/s wind): All lines green, ~35-40% average loading
2. **Hot Day** (35°C, 1 ft/s wind): Some lines turn yellow/orange, approaching limits
3. **Extreme Heat** (40°C, 0.5 ft/s wind): Critical lines turn red, overloads detected
4. **Threshold Analysis**: Identify exact temperature (e.g., 37°C) where first overload occurs

## Configuration

### Environment Variables

Create a `backend/.env` file for optional features:

```env
# AI Chatbot (Optional - Claude API integration)
ANTHROPIC_API_KEY=your_api_key_here

# Autonomous Agent Configuration
AGENT_ENABLED=true
AGENT_STATE_PATH=backend/data/agent_state.json
AGENT_LOG_PATH=backend/data/agent_decisions.log
AGENT_PERSISTENCE=true

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=true
```

**Note:** The application works without the API key, but AI chatbot features will be disabled.

### Port Configuration

Default ports:
- **Backend**: `http://localhost:5001`
- **Frontend**: `http://localhost:5173`

To change ports:
- Backend: Edit `backend/app.py` line 1025
- Frontend API: Edit `frontend/src/services/api.ts` line 1

## Troubleshooting

### Port 5000 Conflict (macOS AirPlay)

**Issue:** macOS AirPlay Receiver uses port 5000 by default.

**Solution:** This app is configured to use port 5001 to avoid conflicts. If you still see port issues, verify:
- `backend/app.py:1025` uses `port=5001`
- `frontend/src/services/api.ts:1` uses `http://localhost:5001/api`

### Backend Won't Start

**Common solutions:**
- Install dependencies: `pip install -r requirements.txt`
- Verify data files exist in `backend/data/`
- Check Python version: `python --version` (requires 3.8+)
- Check port availability: `lsof -i :5001`

### Frontend API Errors

**Common solutions:**
- Ensure backend is running on port 5001
- Check browser console for CORS errors (Flask-CORS is enabled)
- Verify API endpoint URLs in `frontend/src/services/api.ts`

### Missing Data Files

Ensure these files exist in `backend/data/`:
- `lines.csv`, `buses.csv`, `generators.csv`, `loads.csv`
- `conductor_library.csv` (required for IEEE 738 calculations)
- `oneline_lines.geojson`, `oneline_busses.geojson` (required for maps)

## Future Enhancements

### Phase 2 (Potential Additions)
- **Real Weather API**: Integration with NOAA/weather services for live data
- **Historical Analysis**: Time-series tracking of grid performance
- **Alerts & Notifications**: Email/SMS for critical conditions
- **Export Reports**: PDF generation for compliance and documentation
- **Multi-Scenario Comparison**: Side-by-side analysis of multiple configurations

### Phase 3 (Advanced Features)
- **Load Forecasting**: ML models for demand prediction
- **Renewable Integration**: Solar/wind generation impact analysis
- **Multi-Utility Support**: Scale to multiple service territories
- **Mobile App**: iOS/Android native applications
- **Real-Time Streaming**: WebSocket integration for live grid updates

## Development Team

**BLACKOUT by hack ops** - Built for the **AEP Transmission Planning Hackathon**

**Technologies**: React 18, TypeScript, Python, Flask, Plotly, PyPSA, IEEE 738, Anthropic Claude API, Pandas, NumPy, Vite

**Key Capabilities:**
- ✅ Real-time dynamic line ratings (IEEE 738-2006)
- ✅ Interactive geospatial network visualization
- ✅ N-1 contingency analysis with cascading failure detection
- ✅ Daily load scaling analysis (24-hour profiling)
- ✅ AI-powered chatbot with Claude integration
- ✅ Autonomous monitoring agent with learning capabilities
- ✅ Weather impact analysis and threshold detection
- ✅ Comprehensive API with 20+ endpoints

## License

This is a prototype system developed for demonstration purposes.

## Support

For questions or issues, please refer to:
- IEEE Standard 738-2006 documentation
- OSU Hackathon resources in `osu_hackathon/` directory
- Backend API documentation in `backend/README.md`

---

**Remember**: The goal is not just to display data, but to provide transmission planners with clear, actionable intelligence that helps them maintain grid reliability and prevent overloads before they occur.
