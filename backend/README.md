# Grid Monitor Backend

Python Flask API server for real-time power grid rating analysis.

## Setup

1. Create virtual environment:
```bash
python -m venv venv
```

2. Activate virtual environment:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

Server will start on http://localhost:5000

## API Endpoints

### GET /api/health
Health check

### GET /api/grid/topology
Get grid topology (lines and buses GeoJSON)

### POST /api/lines/ratings
Calculate line ratings for weather conditions

Body:
```json
{
  "ambient_temp": 25,
  "wind_speed": 2.0,
  "wind_angle": 90,
  "sun_time": 12,
  "date": "12 Jun"
}
```

### POST /api/lines/threshold
Find temperature threshold for overloads

Body:
```json
{
  "temp_range": [20, 50],
  "wind_speed": 2.0,
  "step": 1
}
```

### POST /api/contingency/n1
Perform N-1 contingency analysis

Body:
```json
{
  "outage_line": "L0",
  "ambient_temp": 25,
  "wind_speed": 2.0
}
```

### GET /api/lines/:line_id
Get details for a specific line
