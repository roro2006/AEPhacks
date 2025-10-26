# Summary: Network Output Integration Guide

## Overview

This document summarizes how to extract PyPSA `network.lines_t['p0']` data and send it to your frontend website for visualization.

---

## Quick Start

### 1. **Get Network Flow Data**

```python
from outage_simulator import OutageSimulator

# Initialize simulator
simulator = OutageSimulator()

# Access PyPSA network power flows (MW)
p0_data = simulator.network.lines_t['p0']  # DataFrame: snapshots x line_names

# Get flow for a specific line at 'now' snapshot
flow_L0 = p0_data.loc['now', 'L0']  # Returns: 79.1686 MW

# Get all flows at 'now' snapshot
all_flows = p0_data.loc['now', :]  # Returns: Series of 77 line flows
```

### 2. **Run Contingency Analysis**

```python
# Simulate outage and get comprehensive results
result = simulator.simulate_outage(['L0'])

# Result structure:
{
  "success": true,
  "outage_lines": ["L0"],
  "loading_changes": [77 line objects],  # ALL lines with before/after data
  "overloaded_lines": [],                # Lines >100% loading
  "high_stress_lines": [],               # Lines 90-100% loading
  "affected_lines": [1 line],            # Lines with >10% loading change
  "islanded_buses": [8 buses],           # Disconnected buses
  "metrics": {...},                      # Summary statistics
  "power_flow_info": {...}               # Convergence info
}
```

### 3. **Send to Frontend via API**

```python
import requests

# Call the API endpoint
response = requests.post(
    'http://localhost:5000/api/outage/simulate',
    json={
        "outage_lines": ["L0"],
        "use_lpf": False
    }
)

# Get results
if response.status_code == 200:
    result = response.json()
    print(f"Max loading: {result['metrics']['max_loading_pct']:.2f}%")
```

---

## Key Data Structures

### PyPSA Network Structure

```python
simulator.network.lines_t['p0']
# Type: pandas.DataFrame
# Shape: (1, 77)  # 1 snapshot ('now'), 77 lines
# Columns: ['L0', 'L1', 'L2', ..., 'L76']
# Index: ['now']
# Values: Active power flow in MW

# Example data:
#          L0       L1       L2       L3       L4
# now  79.1686  79.1686 -22.4497 -66.6941 -66.6941
```

### Contingency Result Structure

```json
{
  "loading_changes": [
    {
      "name": "L1",
      "bus0": "1",
      "bus1": "5",
      "s_nom": 228.0,
      "flow_mw": 140.84,
      "flow_mva": 148.26,
      "loading_pct": 65.02,
      "baseline_loading_pct": 34.72,
      "loading_change_pct": 30.30,
      "is_active": true,
      "is_outaged": false,
      "status": "caution"
    }
    // ... 76 more lines
  ]
}
```

---

## Assumptions and Key Points

### 1. **Power Flow Data**

**Source:** `network.lines_t['p0']` - Active power from bus0 to bus1 (MW)

**Snapshot:** Single snapshot named 'now' (static analysis, not time-series)

**Sign Convention:** Positive = flow from bus0 → bus1, Negative = reverse direction

### 2. **MVA Calculation**

**Formula:** `MVA = MW / 0.95`

**Assumption:** Power factor = 0.95 (typical for transmission systems)

**Why:** PyPSA provides active power (P), but line ratings are in apparent power (S). Without reactive power (Q), we approximate.

### 3. **Loading Percentage**

**Formula:** `Loading % = (Flow MVA / Rated MVA) × 100`

**Example:** Line with 148.26 MVA flow and 228 MVA rating = 65.02% loading

### 4. **Status Categories**

- **Outaged:** Line removed from service
- **Overloaded:** ≥100% loading (emergency condition)
- **High Stress:** 90-100% loading (caution)
- **Caution:** 60-90% loading (monitor)
- **Normal:** <60% loading

### 5. **Network Reload**

**Each simulation reloads the entire network from CSV files**

**Reason:** Ensures clean state, prevents contamination between scenarios

**Trade-off:** Slower (6-8 sec/simulation) but more reliable

---

## JSON Payload for Frontend

### Complete Payload

See `sample_contingency_payload.json` for full example (31,570 bytes)

### Optimized Visualization Data

See `visualization_data.json` for frontend-ready charts:

```json
{
  "bar_chart_loading_changes": [
    {"line": "L1", "before": 34.72, "after": 65.02, "change": 30.30},
    // ... top 10 affected lines
  ],
  "pie_chart_status": {
    "normal": 56,
    "caution": 20,
    "high_stress": 0,
    "overloaded": 0,
    "outaged": 1
  },
  "histogram_loading": [65.02, 11.79, 31.52, ...],
  "network_graph": {
    "nodes": ["1", "5", "22", ...],
    "edges": [
      {
        "source": "1",
        "target": "5",
        "flow": 140.84,
        "loading": 65.02,
        "status": "caution",
        "width": 2.8
      }
    ]
  },
  "dashboard_metrics": {
    "total_lines": 77,
    "outaged": 1,
    "overloaded": 0,
    "max_loading": 86.99,
    "avg_loading": 42.01
  }
}
```

---

## Generated Files

All example files have been generated in the `backend/` directory:

| File | Description | Size |
|------|-------------|------|
| `sample_contingency_payload.json` | Complete API response for L0 outage | 32 KB |
| `contingency_L0_result.json` | Detailed N-1 analysis for L0 | 32 KB |
| `batch_contingency_results.json` | Results for 5 N-1 scenarios | 156 KB |
| `visualization_data.json` | Frontend-ready chart data | 7 KB |

---

## API Endpoints

### 1. Simulate Outage

```
POST /api/outage/simulate
Content-Type: application/json

{
  "outage_lines": ["L0"],
  "use_lpf": false
}
```

**Response:** Complete contingency analysis results (see above)

### 2. Get Available Lines

```
GET /api/outage/available-lines
```

**Response:**
```json
{
  "success": true,
  "lines": [
    {"name": "L0", "bus0": "1", "bus1": "5", "s_nom": 228.0, "description": "L0 | 1 - 5"}
  ],
  "total_count": 77
}
```

### 3. Generate Map

```
POST /api/map/outage
Content-Type: application/json

{
  "outage_result": { /* full contingency result */ }
}
```

**Response:**
```json
{
  "map_html": "<div>...</div>",
  "summary": { "outage_lines": ["L0"], "overloaded_count": 0 }
}
```

---

## Code Examples

### Python: Direct Access to Flow Data

```python
from outage_simulator import OutageSimulator

simulator = OutageSimulator()

# Get all line flows
flows = simulator.network.lines_t['p0'].loc['now', :]

# Convert to dictionary
flow_dict = flows.to_dict()
# {'L0': 79.1686, 'L1': 79.1686, 'L2': -22.4497, ...}

# Find highest loaded line
line_data = []
for line_name, line in simulator.network.lines.iterrows():
    flow = abs(flows[line_name])
    s_nom = line['s_nom']
    loading = (flow / 0.95) / s_nom * 100
    line_data.append({
        'name': line_name,
        'flow_mw': flow,
        'loading_pct': loading
    })

# Sort by loading
line_data.sort(key=lambda x: x['loading_pct'], reverse=True)

# Top 5 most loaded lines
for line in line_data[:5]:
    print(f"{line['name']}: {line['loading_pct']:.2f}% loaded")
```

### JavaScript/TypeScript: Fetch from API

```typescript
async function getContingencyAnalysis(lines: string[]) {
  const response = await fetch('http://localhost:5000/api/outage/simulate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      outage_lines: lines,
      use_lpf: false
    })
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  const result = await response.json();
  return result;
}

// Usage
const result = await getContingencyAnalysis(['L0']);
console.log(`Max loading: ${result.metrics.max_loading_pct.toFixed(2)}%`);

// Create bar chart
const chartData = result.affected_lines.map(line => ({
  x: line.name,
  y: line.loading_pct,
  color: line.status === 'overloaded' ? 'red' : 'orange'
}));
```

### React Component: Display Results

```tsx
import React, { useState } from 'react';

function ContingencyResults({ result }) {
  if (!result) return <div>No analysis run yet</div>;

  return (
    <div>
      <h3>N-{result.outage_lines.length} Contingency Results</h3>

      {/* Metrics Dashboard */}
      <div className="metrics-grid">
        <MetricCard
          label="Outaged Lines"
          value={result.metrics.outaged_lines_count}
        />
        <MetricCard
          label="Overloaded Lines"
          value={result.metrics.overloaded_count}
          alert={result.metrics.overloaded_count > 0}
        />
        <MetricCard
          label="Max Loading"
          value={`${result.metrics.max_loading_pct.toFixed(2)}%`}
          alert={result.metrics.max_loading_pct >= 100}
        />
        <MetricCard
          label="Islanded Buses"
          value={result.metrics.islanded_buses_count}
          alert={result.metrics.islanded_buses_count > 0}
        />
      </div>

      {/* Affected Lines Table */}
      {result.affected_lines.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Line</th>
              <th>Before</th>
              <th>After</th>
              <th>Change</th>
            </tr>
          </thead>
          <tbody>
            {result.affected_lines.map(line => (
              <tr key={line.name}>
                <td>{line.name}</td>
                <td>{line.baseline_loading_pct.toFixed(2)}%</td>
                <td>{line.loading_pct.toFixed(2)}%</td>
                <td className={line.loading_change_pct > 0 ? 'increase' : 'decrease'}>
                  {line.loading_change_pct > 0 ? '+' : ''}
                  {line.loading_change_pct.toFixed(2)}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
```

---

## Visualization Examples

### 1. Loading Bar Chart (Chart.js)

```javascript
import Chart from 'chart.js/auto';

function createLoadingChart(result) {
  const topAffected = result.loading_changes
    .filter(l => !l.is_outaged)
    .sort((a, b) => Math.abs(b.loading_change_pct) - Math.abs(a.loading_change_pct))
    .slice(0, 10);

  new Chart(document.getElementById('loadingChart'), {
    type: 'bar',
    data: {
      labels: topAffected.map(l => l.name),
      datasets: [
        {
          label: 'Before Outage',
          data: topAffected.map(l => l.baseline_loading_pct),
          backgroundColor: 'rgba(54, 162, 235, 0.5)',
        },
        {
          label: 'After Outage',
          data: topAffected.map(l => l.loading_pct),
          backgroundColor: topAffected.map(l =>
            l.loading_pct >= 100 ? 'rgba(255, 99, 132, 0.5)' :
            l.loading_pct >= 90 ? 'rgba(255, 206, 86, 0.5)' :
            'rgba(75, 192, 192, 0.5)'
          ),
        }
      ]
    }
  });
}
```

### 2. Network Diagram (D3.js)

```javascript
import * as d3 from 'd3';

function createNetworkDiagram(result) {
  const nodes = [...new Set(
    result.loading_changes.flatMap(l => [l.bus0, l.bus1])
  )].map(id => ({ id }));

  const links = result.loading_changes.map(line => ({
    source: line.bus0,
    target: line.bus1,
    value: Math.abs(line.flow_mw),
    loading: line.loading_pct,
    status: line.status
  }));

  const simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id(d => d.id))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(400, 300));

  // ... SVG rendering code
}
```

### 3. Status Pie Chart

```javascript
function createStatusPieChart(result) {
  const statusCounts = {
    normal: result.loading_changes.filter(l => l.status === 'normal').length,
    caution: result.loading_changes.filter(l => l.status === 'caution').length,
    high_stress: result.loading_changes.filter(l => l.status === 'high_stress').length,
    overloaded: result.loading_changes.filter(l => l.status === 'overloaded').length,
    outaged: result.loading_changes.filter(l => l.status === 'outaged').length,
  };

  new Chart(document.getElementById('statusChart'), {
    type: 'pie',
    data: {
      labels: ['Normal', 'Caution', 'High Stress', 'Overloaded', 'Outaged'],
      datasets: [{
        data: Object.values(statusCounts),
        backgroundColor: [
          '#44ff44',  // normal - green
          '#ffdd00',  // caution - yellow
          '#ffaa00',  // high_stress - orange
          '#ff4444',  // overloaded - red
          '#333333'   // outaged - gray
        ]
      }]
    }
  });
}
```

---

## Testing

### Run Example Scripts

```bash
# Test network output structure
python backend/test_network_output.py

# Test API endpoint logic
python backend/test_api_endpoint.py

# Run integration examples
python backend/send_to_frontend.py

# Test contingency JSON serialization
python backend/test_contingency_fix.py
```

### Start Flask Server

```bash
cd backend
python app.py
```

Server runs on `http://localhost:5000`

### Test API with curl

```bash
# Get available lines
curl http://localhost:5000/api/outage/available-lines

# Simulate outage
curl -X POST http://localhost:5000/api/outage/simulate \
  -H "Content-Type: application/json" \
  -d '{"outage_lines": ["L0"], "use_lpf": false}'
```

---

## Important Notes

### 1. **Restart Flask After Code Changes**

The contingency analysis fix requires Flask to be restarted to load updated code.

```bash
# Stop Flask (Ctrl+C)
# Restart
python app.py
```

### 2. **JSON Serialization**

All numpy types are automatically converted to native Python types via `convert_numpy_types()` function.

### 3. **Performance**

- Single N-1 contingency: ~6-8 seconds
- Network reload: ~2-3 seconds
- Power flow solve: ~3-5 seconds

For faster results, use `use_lpf: true` (linear power flow).

### 4. **Data Quality**

- Power factor assumption (0.95) introduces ±5% error in MVA calculations
- Loading percentages are approximate but trends are accurate
- Island detection may miss buses with local generation

---

## Documentation Files

| File | Description |
|------|-------------|
| `CONTINGENCY_API_INTEGRATION.md` | Complete API integration guide (9,000+ words) |
| `CONTINGENCY_JSON_FIX.md` | JSON serialization fix documentation |
| `SUMMARY_NETWORK_OUTPUT_INTEGRATION.md` | This document (quick reference) |

---

## Support

For questions or issues:
1. Check the full documentation in `CONTINGENCY_API_INTEGRATION.md`
2. Run test scripts to verify setup
3. Check Flask server logs for errors

---

**Last Updated:** 2025-10-26
**Version:** 1.0
**Status:** Production Ready
