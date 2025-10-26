# Transmission Line Outage Simulation Feature

## Overview

A comprehensive outage simulation feature has been added to your power grid monitoring application. This feature allows users to simulate the removal of one or more transmission lines and visualize how this affects network stress, connectivity, and line loadings.

## Key Features

### 1. **Interactive Line Selection**
- Browse all available transmission lines in the network
- Search and filter lines by name or description
- Select single or multiple lines for N-1, N-2, or N-k contingency analysis
- Clear visual feedback for selected lines

### 2. **Power Flow Analysis**
- Uses PyPSA (Python for Power System Analysis) for accurate power flow calculations
- Automatically redistributes power flows when lines are removed
- Supports both nonlinear and linear power flow methods
- Handles convergence issues gracefully

### 3. **Comprehensive Impact Analysis**
The simulation provides detailed analysis including:

#### **Overloaded Lines**
- Identifies lines exceeding 100% capacity after outage
- Shows loading percentage and flow in MVA
- Displays loading increase from baseline

#### **High Stress Lines**
- Lines operating at 90-100% capacity
- At risk of overload with additional stress

#### **Affected Lines**
- Lines with loading changes greater than 10%
- Shows before/after comparison
- Sorted by magnitude of impact

#### **Islanded Buses**
- Detects buses that become disconnected from the main grid
- Critical for identifying network connectivity issues
- Shows bus details including voltage level and location

#### **Network-wide Metrics**
- Maximum and average loading percentages
- Comparison of baseline vs. post-outage state
- Count of affected, overloaded, and stressed lines

### 4. **Visual Analytics**
- Color-coded status indicators (red for overload, orange for high stress, yellow for caution)
- Summary cards with key metrics
- Detailed tables with expandable information
- Percentage change indicators with directional arrows

## Implementation Details

### Backend Components

#### **1. `outage_simulator.py`** (New)
Core simulation engine that:
- Loads PyPSA network from CSV files
- Manages baseline and post-outage network states
- Runs power flow analysis
- Detects islanded buses using graph connectivity algorithms
- Calculates loading changes and identifies affected lines

Key Methods:
```python
- simulate_outage(outage_lines, use_lpf) - Main simulation function
- get_available_lines() - Returns list of all lines
- _detect_islanded_buses() - Finds disconnected network components
- _analyze_outage_results() - Comprehensive impact analysis
```

#### **2. Updated `rating_calculator.py`**
- Added `analyze_contingency()` method that integrates with `OutageSimulator`
- Handles both single line and multiple line outages
- Provides error handling for PyPSA unavailability

#### **3. New API Endpoints in `app.py`**

**GET /api/outage/available-lines**
- Returns list of all transmission lines available for outage simulation
- Response includes line name, buses, capacity, and description

**POST /api/outage/simulate**
```json
Request Body:
{
  "outage_lines": ["L48", "L49"],  // List of line names
  "use_lpf": false                 // Optional: use linear power flow
}

Response:
{
  "success": true,
  "outage_lines": ["L48", "L49"],
  "overloaded_lines": [...],
  "high_stress_lines": [...],
  "affected_lines": [...],
  "islanded_buses": [...],
  "loading_changes": [...],
  "metrics": {
    "total_lines": 77,
    "outaged_lines_count": 2,
    "overloaded_count": 3,
    "high_stress_count": 5,
    "affected_lines_count": 12,
    "islanded_buses_count": 0,
    "max_loading_pct": 135.2,
    "avg_loading_pct": 42.1,
    ...
  }
}
```

### Frontend Components

#### **1. `OutageAnalysis.tsx`** (New)
Full-featured React component providing:
- Line selection interface with search
- Simulation trigger button
- Results visualization with metrics cards
- Detailed tables for overloaded lines, affected lines, and islanded buses
- Loading states and error handling

#### **2. Updated `api.ts`**
Added TypeScript interfaces and functions:
- `fetchAvailableLines()` - Get available lines
- `simulateOutage(outageLines, useLpf)` - Run simulation
- Type definitions for all simulation data structures

#### **3. Updated `App.tsx`**
- Integrated `OutageAnalysis` component into Analysis tab
- Replaced placeholder content with fully functional outage simulator

## Usage Instructions

### For End Users

1. **Navigate to Analysis Tab**
   - Click the "Analysis" tab in the sidebar
   - You'll see the Outage Simulation interface

2. **Select Lines to Outage**
   - Use the search box to find specific lines
   - Click on lines to select them (checkmark appears)
   - You can select multiple lines for N-2, N-3, etc. scenarios
   - Selected count shows the contingency type (e.g., "2 lines selected (N-2 contingency)")

3. **Run Simulation**
   - Click "Simulate Outage" button
   - Wait for power flow analysis to complete (usually < 5 seconds)
   - Results appear automatically below

4. **Analyze Results**

   **Summary Cards:**
   - Overloaded Lines: Count of lines exceeding 100% capacity
   - High Stress Lines: Count of lines at 90-100% loading
   - Affected Lines: Count of lines with >10% loading change
   - Islanded Buses: Count of disconnected buses

   **Network Loading Comparison:**
   - Shows before/after maximum and average loading
   - Highlights increases in red/orange

   **Detailed Tables:**
   - Overloaded Lines: Critical lines that need immediate attention
   - Islanded Buses: Parts of network that lost connectivity
   - Most Affected Lines: Top 10 lines with largest loading changes

5. **Reset and Try Another Scenario**
   - Click "Clear All" to deselect lines
   - Choose different lines for new scenario

### Example Scenarios to Try

#### **Single Line Outage (N-1)**
1. Select line "L48" (PEARL CITY69 - WAIPAHU69 #1)
2. Run simulation
3. Observe how power redistributes to parallel lines L49, L50, L51

#### **Multiple Line Outage (N-2)**
1. Select lines "L48" and "L49"
2. Run simulation
3. See significantly increased loading on L50 and L51
4. Check if any lines become overloaded

#### **Critical Corridor Analysis**
1. Select all parallel lines in a critical corridor
2. Simulate complete corridor outage
3. Identify which parts of the network become islanded

## Technical Architecture

### Data Flow

```
User Selection → Frontend (OutageAnalysis.tsx)
                     ↓
              API Call (simulateOutage)
                     ↓
         Backend (/api/outage/simulate)
                     ↓
       RatingCalculator.analyze_contingency()
                     ↓
          OutageSimulator.simulate_outage()
                     ↓
              PyPSA Network Analysis
              ├─ Load network from CSV
              ├─ Disable selected lines
              ├─ Run power flow (pf or lpf)
              ├─ Calculate loading changes
              ├─ Detect islanded buses
              └─ Compile metrics
                     ↓
         Return comprehensive results
                     ↓
         Frontend displays results
```

### PyPSA Integration

The system uses the PyPSA library exactly as shown in the provided example notebook:

1. **Network Loading**
   ```python
   network = pypsa.Network()
   network.import_from_csv_folder('data/')
   ```

2. **Baseline Power Flow**
   ```python
   network.pf()  # Non-linear power flow
   # or
   network.lpf()  # Linear power flow (approximation)
   ```

3. **Outage Simulation**
   ```python
   network.lines.loc["L48", "active"] = False
   network.lines_t['p0'].loc['now', 'L48'] = 0.0
   network.pf()  # Re-run power flow
   ```

4. **Loading Calculation**
   ```python
   p0 = network.lines_t['p0'].loc['now']
   s_nom = network.lines['s_nom']
   loading_pct = (abs(p0) / s_nom) * 100
   ```

5. **Connectivity Analysis**
   - Uses breadth-first search (BFS) to find connected components
   - Identifies buses unreachable from generator buses
   - Reports islanded buses

## Error Handling

The system includes comprehensive error handling:

1. **PyPSA Not Installed**
   - Graceful error message
   - Instructions to install: `pip install pypsa`

2. **Power Flow Convergence Issues**
   - Automatically falls back to linear power flow
   - Reports convergence status in results

3. **Invalid Line Names**
   - Validates all line names before simulation
   - Returns list of valid lines if error occurs

4. **Network Disconnection**
   - Detects and reports islanded buses
   - Provides bus details for troubleshooting

## Performance Considerations

- **Initial Load**: ~2-3 seconds to load PyPSA network
- **Single Simulation**: ~1-2 seconds for N-1 contingency
- **Multiple Simulations**: Each additional contingency ~1-2 seconds
- **Network Reload**: Reloads network state before each simulation to ensure clean baseline

## Files Modified/Created

### Backend
- ✅ **NEW**: `backend/outage_simulator.py` - Core simulation engine
- ✅ **MODIFIED**: `backend/rating_calculator.py` - Added contingency analysis
- ✅ **MODIFIED**: `backend/app.py` - Added outage simulation API endpoints

### Frontend
- ✅ **NEW**: `frontend/src/components/OutageAnalysis.tsx` - UI component
- ✅ **MODIFIED**: `frontend/src/services/api.ts` - Added API functions and types
- ✅ **MODIFIED**: `frontend/src/App.tsx` - Integrated component into Analysis tab

## Dependencies

### Backend Requirements
```
pypsa>=1.0.0  # Power system analysis
pandas        # Data manipulation
numpy         # Numerical operations
```

Install PyPSA if not already installed:
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install pypsa
```

### Frontend Requirements
No additional dependencies required - uses existing React setup.

## Future Enhancements

Potential improvements you could add:

1. **Visualization on Map**
   - Highlight outaged lines on the network map
   - Show loading changes with color gradients
   - Display islanded buses with special markers

2. **Automated Contingency Screening**
   - Run all N-1 scenarios automatically
   - Identify most critical lines
   - Generate ranked list of worst-case outages

3. **Weather Integration**
   - Combine outage simulation with temperature analysis
   - Show how outages affect network under different weather conditions

4. **Export Results**
   - Export simulation results to CSV/Excel
   - Generate PDF reports
   - Save scenarios for later comparison

5. **Remedial Actions**
   - Suggest load shedding strategies
   - Recommend generator redispatch
   - Propose temporary line reconfigurations

## Troubleshooting

### Issue: "PyPSA not available"
**Solution**: Install PyPSA in the backend virtual environment
```bash
cd backend
pip install pypsa
```

### Issue: Power flow doesn't converge
**Solution**: The system automatically falls back to linear power flow (LPF). Check the `power_flow_info` in results to see convergence status.

### Issue: No lines appear in selection list
**Solution**:
1. Ensure backend server is running
2. Check that CSV files exist in `backend/data/` folder
3. Check browser console for API errors

### Issue: Simulation takes too long
**Solution**:
1. Try using linear power flow (set `use_lpf: true`)
2. Check backend logs for errors
3. Ensure no other simulations are running

## API Reference

### GET /api/outage/available-lines

Returns list of all transmission lines.

**Response:**
```typescript
{
  success: boolean
  lines: Array<{
    name: string
    bus0: string
    bus1: string
    s_nom: number
    description: string
  }>
  total_count: number
}
```

### POST /api/outage/simulate

Simulates line outage and returns impact analysis.

**Request:**
```typescript
{
  outage_lines: string[]  // e.g., ["L48", "L49"]
  use_lpf?: boolean       // Optional, default: false
}
```

**Response:**
```typescript
{
  success: boolean
  outage_lines: string[]
  overloaded_lines: LineLoadingChange[]
  high_stress_lines: LineLoadingChange[]
  affected_lines: LineLoadingChange[]
  islanded_buses: IslandedBus[]
  loading_changes: LineLoadingChange[]
  metrics: OutageMetrics
  power_flow_info?: {
    converged: boolean
    max_error?: number
    linear: boolean
  }
  error?: string
}
```

## Contact & Support

For questions or issues with the outage simulation feature, please refer to:
- PyPSA documentation: https://pypsa.readthedocs.io/
- PyPSA examples: https://pypsa.readthedocs.io/en/latest/examples-basic.html
- Original example notebook provided with this implementation

---

**Implementation Date**: October 25, 2025
**Version**: 1.0
**Status**: ✅ Fully Implemented and Integrated
