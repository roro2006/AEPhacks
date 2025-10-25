# Power Grid Real-Time Rating Analysis System

An intelligent web-based system for AEP Transmission Planners to calculate and visualize real-time power line ratings based on weather conditions. This system prevents grid overloads by dynamically tracking line capacity and identifying stress points before failures occur.

![Grid Monitor Screenshot](docs/screenshot.png)

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

## Technical Architecture

### Backend (Python + Flask)
- **Dynamic Rating Engine**: IEEE 738 standard implementation
- **Data Processing**: Pandas for CSV/GeoJSON handling
- **RESTful API**: Flask with CORS support
- **Power Flow Analysis**: PyPSA integration (for contingency analysis)

### Frontend (React + TypeScript)
- **Interactive Maps**: Leaflet for geospatial visualization
- **Real-time Charts**: Recharts for threshold analysis
- **Modern UI**: React Hooks with TypeScript
- **Responsive Design**: Mobile-friendly layout

### Calculations
- **IEEE 738 Standard**: Thermal rating calculations
- **Weather Parameters**: Temperature, wind speed, solar radiation
- **Conductor Properties**: Resistance, diameter, MOT (Maximum Operating Temperature)
- **MVA Conversion**: √3 × I × V × 10⁻⁶

## Project Structure

```
grid-monitor/
├── backend/
│   ├── app.py                  # Flask API server
│   ├── data_loader.py          # CSV/GeoJSON data loader
│   ├── rating_calculator.py    # IEEE 738 rating engine
│   ├── requirements.txt        # Python dependencies
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── GridMap.tsx           # Leaflet map component
│   │   │   ├── WeatherControls.tsx   # Weather input panel
│   │   │   ├── AlertDashboard.tsx    # Alerts and insights
│   │   │   └── ThresholdAnalysis.tsx # Temperature threshold charts
│   │   ├── services/
│   │   │   └── api.ts                # Backend API client
│   │   ├── App.tsx                   # Main app component
│   │   └── main.tsx
│   ├── package.json
│   └── README.md
└── README.md (this file)
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

Backend API will be available at `http://localhost:5000`

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

#### GET `/api/health`
Health check endpoint

#### GET `/api/grid/topology`
Get grid topology (lines and buses GeoJSON)

#### POST `/api/lines/ratings`
Calculate line ratings for given weather conditions

Request body:
```json
{
  "ambient_temp": 25,
  "wind_speed": 2.0,
  "wind_angle": 90,
  "sun_time": 12,
  "date": "12 Jun"
}
```

Response:
```json
{
  "weather": {...},
  "lines": [
    {
      "name": "L0",
      "branch_name": "ALOHA138 TO HONOLULU138 CKT 1",
      "rating_mva": 228.5,
      "flow_mva": 79.2,
      "loading_pct": 34.7,
      "stress_level": "normal",
      ...
    }
  ],
  "summary": {
    "total_lines": 80,
    "overloaded_lines": 0,
    "avg_loading": 42.3,
    "max_loading": 87.2,
    ...
  }
}
```

#### POST `/api/lines/threshold`
Find temperature threshold for overloads

Request body:
```json
{
  "temp_range": [20, 50],
  "wind_speed": 2.0,
  "step": 1
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

## Future Enhancements

### Phase 2 (Recommended)
- **N-1 Contingency Analysis**: Full PyPSA integration for outage scenarios
- **Real Weather API**: Integration with NOAA/weather services
- **Historical Analysis**: Track patterns over time
- **Alerts & Notifications**: Email/SMS for critical conditions
- **Export Reports**: PDF generation for compliance

### Phase 3 (Advanced)
- **Load Forecasting**: ML models for demand prediction
- **Renewable Integration**: Solar/wind generation impact
- **Multi-Utility Support**: Scale to multiple service territories
- **Mobile App**: iOS/Android native applications

## Development Team

Built for the **AEP Transmission Planning Hackathon**

**Technologies**: React, TypeScript, Python, Flask, Leaflet, Recharts, IEEE 738, PyPSA

## License

This is a prototype system developed for demonstration purposes.

## Support

For questions or issues, please refer to:
- IEEE Standard 738-2006 documentation
- OSU Hackathon resources in `osu_hackathon/` directory
- Backend API documentation in `backend/README.md`

---

**Remember**: The goal is not just to display data, but to provide transmission planners with clear, actionable intelligence that helps them maintain grid reliability and prevent overloads before they occur.
