# Daily Load Scaling Analysis Feature

## Overview

Added a new **"Daily Load Scaling"** analysis tab that shows how load/generation changes throughout the day stress the transmission system. This feature uses PyPSA to solve power flow at different loading levels based on a sine wave approximation of daily load variations.

---

## What It Does

- **Analyzes 24 hours** of grid operation with varying load/generation levels
- **Uses sine wave** to approximate daily load profile (±10% from nominal)
- **Min load at 6 AM**, **max load at 6 PM** (typical daily pattern)
- **Solves PyPSA power flow** for each hour to calculate line loadings
- **Identifies peak stress conditions** and most stressed lines
- **Interactive 24-hour timeline** showing stress levels throughout the day

---

## Implementation

### Backend

#### 1. **`load_scaling_analyzer.py`**

New analyzer class that:
- Loads PyPSA network from CSV files
- Generates daily load profile using sine wave
- Scales both loads and generators proportionally
- Runs power flow solver for each hour
- Tracks line loadings and identifies overloads

**Key Methods:**
```python
analyzer = LoadScalingAnalyzer()

# Run full 24-hour analysis
result = analyzer.analyze_daily_profile(hours=24)

# Analyze a specific hour
hour_result = analyzer.analyze_single_hour(hour=18)

# Get just the load profile
profile = analyzer.get_load_profile(hours=24)
```

#### 2. **API Endpoints** (in `app.py`)

Three new endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/load-scaling/daily` | GET | Full 24-hour analysis |
| `/api/load-scaling/hour/<hour>` | GET | Single hour analysis |
| `/api/load-scaling/profile` | GET | Load profile data only |

**Example Request:**
```bash
GET http://localhost:5000/api/load-scaling/daily?hours=24
```

**Response Structure:**
```json
{
  "success": true,
  "summary": {
    "total_hours": 24,
    "hours_converged": 24,
    "peak_loading": {
      "hour": 18,
      "max_loading_pct": 93.68,
      "scale_factor": 1.1,
      "overloaded_count": 0
    },
    "most_stressed_lines": [
      {
        "name": "L48",
        "max_loading_pct": 93.68,
        "hour_of_max": 18,
        "scale_at_max": 1.1
      }
    ]
  },
  "hourly_results": [
    {
      "hour": 0,
      "scale_factor": 1.0,
      "total_load_mw": 1136.29,
      "max_loading_pct": 85.13,
      "avg_loading_pct": 41.24,
      "overloaded_count": 0,
      "lines": [...]
    }
  ]
}
```

### Frontend

#### 1. **`LoadScalingAnalysis.tsx`**

New React component with:
- **Run Analysis Button** - Triggers 24-hour analysis
- **Summary Cards** - Shows peak loading and max overloads
- **24-Hour Timeline Grid** - Visual representation of all hours
  - Color-coded by stress level (green/yellow/orange/red)
  - Click any hour for detailed view
- **Hour Details Panel** - Shows specific metrics for selected hour
- **Most Stressed Lines List** - Top 5 lines with maximum 24-hour loading

**Styling:**
- Matches existing analysis tab design
- Same color scheme and component patterns
- Responsive grid layout
- Smooth transitions and hover effects

#### 2. **App.tsx Integration**

Added as third sub-tab in Analysis section:
```
Analysis Tab
├── Weather Analysis
├── Outage Simulation
└── Daily Load Scaling  ← NEW
```

---

## Load Profile Formula

Uses sine wave to approximate daily variations:

```python
x = hour (0-23)
f = 1/24 (one cycle per day)
offset = 1.0 (nominal/100%)
amplitude = 0.1 (±10%)
phase = π (min at 6AM, max at 6PM)

scale_factor = 0.1 * sin(2π * f * x + π) + 1.0
```

**Sample Profile:**
```
Hour   Scale   Load (MW)   Description
0:00   1.000   1136        Midnight (nominal)
6:00   0.900   1023        Morning minimum
12:00  1.000   1136        Noon (nominal)
18:00  1.100   1250        Evening peak
24:00  1.000   1136        Back to nominal
```

---

## Key Features

### 1. **Proportional Scaling**

Both loads and generators scale together to maintain power balance:
```python
network.loads['p_set'] *= scale_factor
network.generators['p_set'] *= scale_factor
```

This prevents solver failures due to power imbalance.

### 2. **PyPSA Power Flow**

Uses nonlinear AC power flow for accuracy:
- Newton-Raphson solver
- Converges to steady-state solution
- Calculates line flows, bus voltages, losses

### 3. **Line Status Classification**

Same thresholds as other analyses:
- **Normal**: <60% loading
- **Caution**: 60-90% loading
- **High Stress**: 90-100% loading
- **Overloaded**: ≥100% loading

### 4. **Interactive Timeline**

- 12x2 grid showing all 24 hours
- Color-coded borders indicate stress level
- Click to view detailed hour metrics
- Icons show peak times and overloads

---

## Testing

### Backend Test
```bash
python backend/test_load_scaling.py
```

**Results:**
```
[1] Initializing LoadScalingAnalyzer...
    [OK] Baseline total load: 1136.29 MW
    [OK] Baseline total gen: 1154.66 MW

[2] Generating 24-hour load profile...
    [OK] Generated profile with 24 hours

[3] Analyzing single hour (6 PM - peak load)...
    [OK] Scale factor: 1.100
    [OK] Max loading: 93.68%
    [OK] Overloaded lines: 0

[4] Running daily analysis (12 hours)...
    [OK] Hours converged: 12/12
    [OK] Peak Loading: Hour 9, 93.68%
    [OK] Top stressed: L48, L49, L50

TEST PASSED!
```

### Frontend Usage

1. Navigate to **Analysis** tab
2. Click **Daily Load Scaling** sub-tab
3. Click **Run Daily Analysis** button
4. View results:
   - Summary metrics
   - 24-hour timeline
   - Click any hour for details
   - See most stressed lines

---

## Performance

- **Single hour analysis**: ~1-2 seconds
- **24-hour analysis**: ~30-45 seconds
- **Network reload**: None (reuses loaded network)
- **Memory usage**: ~100MB for network data

Can be improved by:
- Using linear power flow (`use_lpf=True`) for faster solving
- Caching baseline network state
- Parallel hour analysis (if needed)

---

## Assumptions

1. **Daily Pattern**: Sine wave with min at 6 AM, max at 6 PM
2. **±10% Variation**: Amplitude chosen to match typical grid patterns
3. **Proportional Scaling**: Load and generation scale together
4. **Power Factor**: 0.95 used for MW→MVA conversion
5. **Static Topology**: No line switching or contingencies
6. **Weather**: Not considered (separate from weather analysis)

---

## Files Created/Modified

### New Files
```
backend/load_scaling_analyzer.py          - Core analyzer class
backend/test_load_scaling.py              - Test script
backend/LOAD_SCALING_FEATURE.md           - This documentation
frontend/src/components/LoadScalingAnalysis.tsx  - React component
```

### Modified Files
```
backend/app.py                            - Added 3 API endpoints
frontend/src/App.tsx                      - Added third sub-tab
```

---

## Example Use Cases

### 1. **Peak Demand Planning**

Identify when grid stress is highest:
```
Peak at 6 PM (hour 18):
- Max loading: 93.68%
- Most stressed: L48, L49, L50
- Action: Monitor these lines during evening peak
```

### 2. **Maintenance Scheduling**

Schedule line maintenance during low-stress hours:
```
Minimum at 6 AM (hour 6):
- Max loading: 76.62%
- Safest time: Early morning hours (4-8 AM)
```

### 3. **Capacity Planning**

Determine if system can handle 10% load growth:
```
At 110% load (18:00):
- Overloaded lines: 0
- Max loading: 93.68%
- Conclusion: System has headroom
```

---

## Future Enhancements

1. **Custom Profiles**
   - Upload real historical load data
   - Seasonal variations (summer/winter)
   - Weather-dependent patterns

2. **Renewable Integration**
   - Solar generation curve (peaks at noon)
   - Wind variability
   - Storage optimization

3. **Multi-Day Analysis**
   - Weekend vs. weekday patterns
   - Seasonal trends
   - Annual peak identification

4. **N-1 During Peak**
   - Combine with outage simulation
   - "What if line fails during peak hour?"
   - Cascading failure analysis

---

## Technical Notes

### PyPSA Network Loading

Network loads once and reuses for all hours:
```python
def __init__(self):
    self._load_network()
    self.baseline_load = network.loads['p_set'].copy()
    self.baseline_gen = network.generators['p_set'].copy()
```

### Scaling Reset

Each hour resets to baseline before scaling:
```python
def _scale_network(self, scale_factor):
    # Reset to baseline
    self.network.loads['p_set'] = self.baseline_load.copy()
    # Apply scaling
    self.network.loads['p_set'] *= scale_factor
```

### JSON Serialization

All numpy types converted to native Python:
```python
return convert_numpy_types(result)
```

Prevents `TypeError: Object of type bool_ is not JSON serializable`

---

## Integration with Existing Features

### Complements Weather Analysis
- Weather analysis: How temperature/wind affects ratings
- Load scaling: How demand level affects stress
- Combined: Peak demand on hot day

### Complements Outage Analysis
- Outage analysis: N-1 contingencies
- Load scaling: Normal daily operations
- Combined: Contingency during peak hour

### Uses Same Infrastructure
- Same PyPSA network data
- Same line stress thresholds
- Same color scheme and styling
- Same API patterns (Flask/React)

---

## Troubleshooting

### Issue: Power flow doesn't converge

**Symptom**: Some hours show "Power flow did not converge"

**Cause**: Network becomes infeasible at extreme loadings

**Solution**: Results still returned, but marked as not converged

### Issue: Slow performance

**Symptom**: 24-hour analysis takes >60 seconds

**Solutions**:
1. Reduce hours for testing: `?hours=12`
2. Use linear power flow (requires code change)
3. Ensure backend isn't in debug mode

### Issue: Incorrect load values

**Symptom**: Total load doesn't match expected values

**Check**:
1. Baseline loads: `analyzer.baseline_load.sum()`
2. Scale factors: Should range 0.9 to 1.1
3. Generator scaling: Must match load scaling

---

## References

- Original notebook: `backend/pypsa_load_scale.ipynb`
- PyPSA documentation: https://pypsa.readthedocs.io/
- Sine wave load profile based on: [EIA energy data](https://www.eia.gov/todayinenergy/detail.php?id=42915)

---

**Status**: ✅ Complete and tested
**Date**: 2025-10-26
**Version**: 1.0
