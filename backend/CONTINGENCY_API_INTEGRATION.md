# Contingency Analysis API Integration Guide

## Overview

This guide explains how to integrate the PyPSA contingency analysis results with your frontend application. It covers the JSON payload structure, API endpoints, and code examples for sending and receiving data.

---

## Table of Contents

1. [JSON Payload Structure](#json-payload-structure)
2. [API Endpoints](#api-endpoints)
3. [Backend Code](#backend-code)
4. [Frontend Code](#frontend-code)
5. [Visualization Examples](#visualization-examples)
6. [Assumptions and Design Decisions](#assumptions-and-design-decisions)

---

## JSON Payload Structure

### Response Format

When you call `/api/outage/simulate`, the backend returns a comprehensive JSON object with the following structure:

```json
{
  "success": true,
  "outage_lines": ["L0"],
  "overloaded_lines": [...],
  "high_stress_lines": [...],
  "loading_changes": [...],
  "islanded_buses": [...],
  "affected_lines": [...],
  "metrics": {...},
  "power_flow_info": {...}
}
```

### Field Descriptions

#### 1. `outage_lines` (Array of strings)
Lines that were removed from service for this contingency analysis.

```json
"outage_lines": ["L0"]
```

#### 2. `overloaded_lines` (Array of objects)
Lines operating above 100% capacity after the outage.

```json
"overloaded_lines": [
  {
    "name": "L48",
    "bus0": "15",
    "bus1": "23",
    "s_nom": 215.0,
    "flow_mw": 220.5,
    "flow_mva": 232.1,
    "loading_pct": 107.9,
    "baseline_loading_pct": 85.2,
    "loading_change_pct": 22.7,
    "is_active": true,
    "is_outaged": false,
    "status": "overloaded"
  }
]
```

#### 3. `high_stress_lines` (Array of objects)
Lines operating at 90-100% capacity.

```json
"high_stress_lines": [
  {
    "name": "L12",
    "loading_pct": 94.5,
    "status": "high_stress"
    // ... same fields as overloaded_lines
  }
]
```

#### 4. `loading_changes` (Array of objects)
**ALL** lines (77 total) with before/after comparison. This is the complete dataset.

```json
"loading_changes": [
  {
    "name": "L0",
    "bus0": "1",
    "bus1": "5",
    "s_nom": 228.0,                      // Nominal capacity (MVA)
    "flow_mw": 0.0,                      // Post-outage active power flow (MW)
    "flow_mva": 0.0,                     // Post-outage apparent power flow (MVA)
    "loading_pct": 0.0,                  // Post-outage loading percentage
    "baseline_loading_pct": 34.72,       // Pre-outage loading percentage
    "loading_change_pct": -34.72,        // Change in loading (positive = increased)
    "is_active": false,                  // Whether line is in service
    "is_outaged": true,                  // Whether this is an outaged line
    "status": "outaged"                  // Status: outaged|overloaded|high_stress|caution|normal
  },
  {
    "name": "L1",
    "bus0": "1",
    "bus1": "5",
    "s_nom": 228.0,
    "flow_mw": 140.84,
    "flow_mva": 148.26,
    "loading_pct": 65.02,
    "baseline_loading_pct": 34.72,
    "loading_change_pct": 30.30,         // This line picked up load from L0
    "is_active": true,
    "is_outaged": false,
    "status": "caution"
  }
  // ... 75 more lines
]
```

#### 5. `islanded_buses` (Array of objects)
Buses that became disconnected from the main grid due to the outage.

```json
"islanded_buses": [
  {
    "bus_id": "8",
    "bus_name": "Bus 8",
    "voltage_kv": 138.0,
    "x": -97.5,
    "y": 30.2
  }
]
```

#### 6. `affected_lines` (Array of objects)
Lines with significant loading changes (>10% change from baseline).

```json
"affected_lines": [
  {
    "name": "L1",
    "loading_change_pct": 30.30,
    // ... same fields as loading_changes
  }
]
```

#### 7. `metrics` (Object)
Summary statistics for the contingency analysis.

```json
"metrics": {
  "total_lines": 77,
  "outaged_lines_count": 1,
  "active_lines_count": 76,
  "overloaded_count": 0,
  "high_stress_count": 0,
  "affected_lines_count": 1,
  "islanded_buses_count": 8,
  "max_loading_pct": 86.99,
  "avg_loading_pct": 42.01,
  "max_loading_increase": 30.30,
  "baseline_max_loading": 80.76,
  "baseline_avg_loading": 39.21
}
```

#### 8. `power_flow_info` (Object)
Information about the power flow solver convergence.

```json
"power_flow_info": {
  "converged": true,
  "max_error": 1.5378062556692385e-07,
  "linear": false
}
```

---

## API Endpoints

### 1. Get Available Lines

**Endpoint:** `GET /api/outage/available-lines`

**Description:** Get list of all transmission lines that can be outaged.

**Response:**
```json
{
  "success": true,
  "lines": [
    {
      "name": "L0",
      "bus0": "1",
      "bus1": "5",
      "s_nom": 228.0,
      "description": "L0 | 1 - 5"
    }
    // ... 76 more lines
  ],
  "total_count": 77
}
```

### 2. Simulate Outage

**Endpoint:** `POST /api/outage/simulate`

**Request Body:**
```json
{
  "outage_lines": ["L0"],     // Can be single string or array
  "use_lpf": false            // Optional: use linear power flow (faster)
}
```

**Response:** See [JSON Payload Structure](#json-payload-structure)

### 3. Generate Outage Map

**Endpoint:** `POST /api/map/outage`

**Request Body:**
```json
{
  "outage_result": {
    // The full result from /api/outage/simulate
  }
}
```

**Response:**
```json
{
  "map_html": "<div>...</div>",  // HTML for Folium map
  "summary": {
    "outage_lines": ["L0"],
    "overloaded_count": 0,
    "high_stress_count": 0
  }
}
```

---

## Backend Code

### Python: Running Contingency Analysis

```python
from outage_simulator import OutageSimulator

# Initialize simulator
simulator = OutageSimulator()

# Simulate single line outage (N-1)
result = simulator.simulate_outage(['L0'])

# Simulate multiple line outage (N-2)
result = simulator.simulate_outage(['L0', 'L1'])

# Use linear power flow (faster but less accurate)
result = simulator.simulate_outage(['L0'], use_lpf=True)

# Check results
if result['success']:
    print(f"Max loading: {result['metrics']['max_loading_pct']:.2f}%")
    print(f"Overloaded lines: {result['metrics']['overloaded_count']}")

    # Get lines that picked up load
    for line in result['affected_lines']:
        print(f"{line['name']}: {line['loading_change_pct']:+.2f}% change")
else:
    print(f"Analysis failed: {result['error']}")
```

### Python: API Request Using Requests Library

```python
import requests
import json

# API endpoint
API_BASE = "http://localhost:5000/api"

# Request contingency analysis
response = requests.post(
    f"{API_BASE}/outage/simulate",
    headers={"Content-Type": "application/json"},
    json={
        "outage_lines": ["L0"],
        "use_lpf": False
    }
)

# Parse response
if response.status_code == 200:
    result = response.json()

    # Display summary
    print(f"Analysis successful: {result['success']}")
    print(f"Outaged: {', '.join(result['outage_lines'])}")
    print(f"Max loading: {result['metrics']['max_loading_pct']:.2f}%")

    # Find most affected line
    affected = max(
        result['loading_changes'],
        key=lambda x: abs(x['loading_change_pct'])
    )
    print(f"Most affected: {affected['name']} ({affected['loading_change_pct']:+.2f}%)")

else:
    print(f"Error: {response.status_code}")
    print(response.text)
```

---

## Frontend Code

### TypeScript/JavaScript: API Client

```typescript
// src/services/api.ts

export interface OutageSimulationResult {
  success: boolean;
  outage_lines: string[];
  overloaded_lines: LineData[];
  high_stress_lines: LineData[];
  loading_changes: LineData[];
  islanded_buses: BusData[];
  affected_lines: LineData[];
  metrics: Metrics;
  power_flow_info: PowerFlowInfo;
}

export interface LineData {
  name: string;
  bus0: string;
  bus1: string;
  s_nom: number;
  flow_mw: number;
  flow_mva: number;
  loading_pct: number;
  baseline_loading_pct: number;
  loading_change_pct: number;
  is_active: boolean;
  is_outaged: boolean;
  status: 'outaged' | 'overloaded' | 'high_stress' | 'caution' | 'normal';
}

export interface BusData {
  bus_id: string;
  bus_name: string;
  voltage_kv: number;
  x: number;
  y: number;
}

export interface Metrics {
  total_lines: number;
  outaged_lines_count: number;
  active_lines_count: number;
  overloaded_count: number;
  high_stress_count: number;
  affected_lines_count: number;
  islanded_buses_count: number;
  max_loading_pct: number;
  avg_loading_pct: number;
  max_loading_increase: number;
  baseline_max_loading: number;
  baseline_avg_loading: number;
}

export interface PowerFlowInfo {
  converged: boolean;
  max_error: number;
  linear: boolean;
}

const API_BASE = 'http://localhost:5000/api';

export async function simulateOutage(
  outageLines: string[],
  useLpf: boolean = false
): Promise<OutageSimulationResult> {
  const response = await fetch(`${API_BASE}/outage/simulate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      outage_lines: outageLines,
      use_lpf: useLpf,
    }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

export async function fetchAvailableLines() {
  const response = await fetch(`${API_BASE}/outage/available-lines`);

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  const data = await response.json();
  return data.lines;
}
```

### React Component Example

```tsx
// src/components/OutageAnalysis.tsx

import React, { useState, useEffect } from 'react';
import { simulateOutage, fetchAvailableLines, OutageSimulationResult } from '../services/api';

const OutageAnalysis: React.FC = () => {
  const [availableLines, setAvailableLines] = useState<string[]>([]);
  const [selectedLines, setSelectedLines] = useState<string[]>([]);
  const [result, setResult] = useState<OutageSimulationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load available lines on mount
  useEffect(() => {
    fetchAvailableLines()
      .then(lines => setAvailableLines(lines.map(l => l.name)))
      .catch(err => setError(err.message));
  }, []);

  const runSimulation = async () => {
    if (selectedLines.length === 0) {
      setError('Please select at least one line');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const simulationResult = await simulateOutage(selectedLines, false);

      if (!simulationResult.success) {
        setError('Simulation failed');
        setResult(null);
      } else {
        setResult(simulationResult);
      }
    } catch (err) {
      setError(err.message);
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="outage-analysis">
      <h2>N-{selectedLines.length} Contingency Analysis</h2>

      {/* Line selection */}
      <select
        multiple
        value={selectedLines}
        onChange={(e) => {
          const selected = Array.from(e.target.selectedOptions, opt => opt.value);
          setSelectedLines(selected);
        }}
      >
        {availableLines.map(line => (
          <option key={line} value={line}>{line}</option>
        ))}
      </select>

      <button onClick={runSimulation} disabled={loading}>
        {loading ? 'Simulating...' : 'Simulate Outage'}
      </button>

      {/* Error display */}
      {error && <div className="error">{error}</div>}

      {/* Results */}
      {result && (
        <div className="results">
          <h3>Results</h3>

          {/* Metrics Summary */}
          <div className="metrics">
            <div>Outaged Lines: {result.metrics.outaged_lines_count}</div>
            <div>Overloaded Lines: {result.metrics.overloaded_count}</div>
            <div>High Stress Lines: {result.metrics.high_stress_count}</div>
            <div>Max Loading: {result.metrics.max_loading_pct.toFixed(2)}%</div>
            <div>Avg Loading: {result.metrics.avg_loading_pct.toFixed(2)}%</div>
            <div>Islanded Buses: {result.metrics.islanded_buses_count}</div>
          </div>

          {/* Overloaded Lines Table */}
          {result.overloaded_lines.length > 0 && (
            <div>
              <h4>Overloaded Lines</h4>
              <table>
                <thead>
                  <tr>
                    <th>Line</th>
                    <th>Loading</th>
                    <th>Change</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {result.overloaded_lines.map(line => (
                    <tr key={line.name}>
                      <td>{line.name}</td>
                      <td>{line.loading_pct.toFixed(2)}%</td>
                      <td>{line.loading_change_pct > 0 ? '+' : ''}{line.loading_change_pct.toFixed(2)}%</td>
                      <td>{line.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Most Affected Lines */}
          {result.affected_lines.length > 0 && (
            <div>
              <h4>Most Affected Lines</h4>
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
                        {line.loading_change_pct > 0 ? '+' : ''}{line.loading_change_pct.toFixed(2)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default OutageAnalysis;
```

---

## Visualization Examples

### 1. Loading Change Bar Chart

```typescript
import { Chart } from 'chart.js';

function createLoadingChangeChart(result: OutageSimulationResult) {
  // Filter to most affected lines (top 10 by absolute change)
  const topAffected = result.loading_changes
    .filter(line => !line.is_outaged)
    .sort((a, b) => Math.abs(b.loading_change_pct) - Math.abs(a.loading_change_pct))
    .slice(0, 10);

  const chartData = {
    labels: topAffected.map(line => line.name),
    datasets: [
      {
        label: 'Before Outage',
        data: topAffected.map(line => line.baseline_loading_pct),
        backgroundColor: 'rgba(54, 162, 235, 0.5)',
      },
      {
        label: 'After Outage',
        data: topAffected.map(line => line.loading_pct),
        backgroundColor: topAffected.map(line => {
          if (line.loading_pct >= 100) return 'rgba(255, 99, 132, 0.5)';
          if (line.loading_pct >= 90) return 'rgba(255, 206, 86, 0.5)';
          return 'rgba(75, 192, 192, 0.5)';
        }),
      }
    ]
  };

  new Chart(ctx, {
    type: 'bar',
    data: chartData,
    options: {
      responsive: true,
      scales: {
        y: {
          beginAtZero: true,
          title: { display: true, text: 'Loading (%)' }
        }
      }
    }
  });
}
```

### 2. Network Flow Diagram

```typescript
// Using D3.js or similar library
function visualizeFlowChanges(result: OutageSimulationResult) {
  // Create nodes for buses
  const nodes = new Set();
  result.loading_changes.forEach(line => {
    nodes.add(line.bus0);
    nodes.add(line.bus1);
  });

  // Create edges for lines with flow data
  const edges = result.loading_changes.map(line => ({
    source: line.bus0,
    target: line.bus1,
    flow: line.flow_mw,
    loading: line.loading_pct,
    change: line.loading_change_pct,
    status: line.status,
    isOutaged: line.is_outaged
  }));

  // Color code by status
  const colorScale = {
    'outaged': '#333333',
    'overloaded': '#ff4444',
    'high_stress': '#ffaa00',
    'caution': '#ffdd00',
    'normal': '#44ff44'
  };

  // Visualize with D3/Cytoscape/etc.
}
```

### 3. Heat Map of Loading Changes

```typescript
function createLoadingHeatmap(result: OutageSimulationResult) {
  // Group lines by bus connections
  const heatmapData = result.loading_changes.map(line => ({
    x: line.bus0,
    y: line.bus1,
    value: line.loading_change_pct,
    loading: line.loading_pct
  }));

  // Use a heatmap library to visualize
  // Higher positive values = lines picking up load
  // Negative values = lines shedding load
}
```

---

## Assumptions and Design Decisions

### 1. **Network Data Structure**

**Assumption:** PyPSA's `network.lines_t['p0']` contains active power flow in MW at a single snapshot ('now').

**Rationale:** The system analyzes a static snapshot of grid conditions rather than time-series data. This simplifies the analysis and focuses on steady-state contingencies.

### 2. **Power Factor Approximation**

**Assumption:** Power factor = 0.95 for converting MW to MVA.

```python
flow_mva = flow_mw / 0.95
```

**Rationale:** Without reactive power (Q) data, we approximate apparent power (S) from active power (P). A 0.95 power factor is typical for transmission systems.

**Impact:** Loading percentages may be slightly inaccurate (±5%), but trends and relative comparisons remain valid.

### 3. **Loading Status Thresholds**

**Defined as:**
- **Overloaded:** ≥100% loading
- **High Stress:** 90-100% loading
- **Caution:** 60-90% loading
- **Normal:** <60% loading

**Rationale:** Industry-standard thresholds for transmission line operation.

### 4. **Affected Lines Threshold**

**Assumption:** Lines with >10% loading change are considered "affected."

**Rationale:** Filters out minor fluctuations to focus on significant impacts.

### 5. **Graph Data Format**

**Decision:** Use native Python/NumPy types in JSON (not matplotlib objects).

**Rationale:** Frontend handles visualization separately. Backend provides raw data, allowing flexible visualization choices (Chart.js, D3, Plotly, etc.).

**Implication:** No pre-rendered graphs are sent. Frontend creates visualizations from `loading_changes` array.

### 6. **Island Detection**

**Assumption:** Buses disconnected from any generator are considered islanded.

**Rationale:** PyPSA doesn't inherently mark islanded buses. We use breadth-first search from generator buses to find connected components.

**Limitation:** Doesn't account for local generation on islanded buses.

### 7. **Baseline Comparison**

**Assumption:** The "baseline" is the network state with all lines active before the outage.

**Rationale:** Each simulation starts from a clean network state and applies the outage, allowing before/after comparison.

### 8. **JSON Serialization**

**Decision:** Convert all numpy types to native Python types before JSON serialization.

**Rationale:** Prevents `TypeError: Object of type bool_ is not JSON serializable`.

**Implementation:** The `convert_numpy_types()` function recursively converts:
- `numpy.bool_` → `bool`
- `numpy.int64` → `int`
- `numpy.float64` → `float`
- `numpy.nan` → `null`

### 9. **Network Reload for Each Simulation**

**Decision:** Reload the entire PyPSA network for each contingency scenario.

**Rationale:** Ensures clean state and prevents state leakage between simulations.

**Trade-off:** Slower (6-8 seconds per simulation) but more reliable.

### 10. **Linear vs. Nonlinear Power Flow**

**Default:** Nonlinear AC power flow (more accurate)

**Fallback:** Linear DC power flow if nonlinear doesn't converge

**Parameter:** `use_lpf=True` forces linear power flow (faster, less accurate)

**Rationale:** Accuracy is prioritized, but speed option is available for large-scale studies.

---

## Complete Example Workflow

### Backend (Python)

```python
from outage_simulator import OutageSimulator
import json

# Initialize
simulator = OutageSimulator()

# Run N-1 analysis
result = simulator.simulate_outage(['L0'])

# Save to file
with open('contingency_result.json', 'w') as f:
    json.dump(result, f, indent=2)

# Print summary
print(f"Outaged: {result['outage_lines']}")
print(f"Overloaded: {result['metrics']['overloaded_count']} lines")
print(f"Max loading: {result['metrics']['max_loading_pct']:.2f}%")
```

### Frontend (TypeScript/React)

```typescript
import { simulateOutage } from './services/api';

async function runContingency() {
  try {
    const result = await simulateOutage(['L0'], false);

    if (result.success) {
      // Update UI with results
      displayMetrics(result.metrics);
      displayOverloadedLines(result.overloaded_lines);
      createVisualization(result.loading_changes);
      updateMap(result);
    } else {
      console.error('Simulation failed');
    }
  } catch (error) {
    console.error('API error:', error);
  }
}
```

---

## Testing

### Sample JSON File

A complete sample payload is available in:
```
backend/sample_contingency_payload.json
```

### Test Script

Run the test to verify JSON structure:
```bash
python backend/test_network_output.py
```

### Sample API Request

```bash
curl -X POST http://localhost:5000/api/outage/simulate \
  -H "Content-Type: application/json" \
  -d '{"outage_lines": ["L0"], "use_lpf": false}'
```

---

## Troubleshooting

### Issue: "API error: INTERNAL SERVER ERROR"

**Cause:** Flask server hasn't been restarted after code changes.

**Solution:** Restart Flask server:
```bash
cd backend
python app.py
```

### Issue: JSON parsing errors

**Cause:** Numpy types not converted to native Python types.

**Solution:** Ensure `convert_numpy_types()` is applied in `outage_simulator.py`.

### Issue: Power flow doesn't converge

**Cause:** Network becomes infeasible after outage (too much load lost).

**Solution:** System automatically falls back to linear power flow. Check `power_flow_info.linear` field.

---

## Performance Considerations

- **Network reload:** ~2-3 seconds per simulation
- **Power flow solve:** ~3-5 seconds per simulation
- **JSON serialization:** <100ms
- **Total time:** 6-8 seconds per N-1 contingency

For batch analysis of multiple contingencies, consider:
1. Using `run_multiple_contingency_scenarios()` method
2. Enabling `use_lpf=True` for faster (but less accurate) results
3. Caching network topology if analyzing same network repeatedly

---

**Last Updated:** 2025-10-26
**Version:** 1.0
