# Quick Reference: Contingency Analysis API

## TL;DR - Get Started in 30 Seconds

### Backend (Python)
```python
from outage_simulator import OutageSimulator

simulator = OutageSimulator()
result = simulator.simulate_outage(['L0'])

print(f"Max loading: {result['metrics']['max_loading_pct']:.2f}%")
```

### Frontend (TypeScript)
```typescript
const response = await fetch('http://localhost:5000/api/outage/simulate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ outage_lines: ['L0'], use_lpf: false })
});

const result = await response.json();
console.log(`Max loading: ${result.metrics.max_loading_pct}%`);
```

---

## JSON Response Structure

```json
{
  "success": true,
  "outage_lines": ["L0"],
  "loading_changes": [77 lines],      // ALL lines with before/after
  "overloaded_lines": [],             // Lines >100%
  "high_stress_lines": [],            // Lines 90-100%
  "affected_lines": [1 line],         // Lines with >10% change
  "metrics": {
    "max_loading_pct": 86.99,
    "avg_loading_pct": 42.01,
    "overloaded_count": 0,
    "islanded_buses_count": 8
  },
  "power_flow_info": {
    "converged": true,
    "max_error": 1.54e-07
  }
}
```

---

## Key Data Points

### Per-Line Data (in `loading_changes` array)

```json
{
  "name": "L1",
  "bus0": "1",
  "bus1": "5",
  "flow_mw": 140.84,                  // Active power (MW)
  "flow_mva": 148.26,                 // Apparent power (MVA)
  "loading_pct": 65.02,               // After outage
  "baseline_loading_pct": 34.72,      // Before outage
  "loading_change_pct": 30.30,        // Change (+/-)
  "status": "caution"                 // outaged|overloaded|high_stress|caution|normal
}
```

---

## Assumptions

| Item | Value | Note |
|------|-------|------|
| Power Factor | 0.95 | For MW→MVA conversion |
| Overloaded | ≥100% | Emergency threshold |
| High Stress | 90-100% | Caution threshold |
| Affected Line | >10% change | Significant impact |

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/outage/available-lines` | GET | List all lines |
| `/api/outage/simulate` | POST | Run N-k analysis |
| `/api/map/outage` | POST | Generate map HTML |

---

## Files Generated

- `sample_contingency_payload.json` - Full API response example
- `visualization_data.json` - Frontend-ready chart data
- `batch_contingency_results.json` - Multiple scenario results

---

## Common Tasks

### Get Most Affected Lines
```python
affected = sorted(
    result['loading_changes'],
    key=lambda x: abs(x['loading_change_pct']),
    reverse=True
)[:10]
```

### Find Overloaded Lines
```python
overloaded = [
    line for line in result['loading_changes']
    if line['loading_pct'] >= 100
]
```

### Get Network Flows
```python
flows = simulator.network.lines_t['p0'].loc['now', :]
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| 500 Internal Server Error | Restart Flask: `python app.py` |
| JSON parsing error | Check numpy types are converted |
| Power flow doesn't converge | Use `use_lpf: true` |
| Connection refused | Start Flask server first |

---

## Full Documentation

See `CONTINGENCY_API_INTEGRATION.md` for complete guide (9,000+ words)
