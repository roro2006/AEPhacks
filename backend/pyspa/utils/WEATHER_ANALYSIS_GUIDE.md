# Weather Analysis Feature - User Guide

## Overview

The Weather Analysis feature provides comprehensive IEEE 738-compliant weather parameter controls for analyzing transmission line thermal ratings under various environmental conditions. This tool allows grid operators to:

- Modify all IEEE 738 weather parameters
- Run what-if scenarios with preset conditions
- Compare baseline vs modified conditions
- Understand the impact of weather changes on system capacity

## Accessing the Feature

1. Navigate to the **Analysis** tab in the main application
2. Select **Weather Analysis** sub-tab
3. The weather controls panel will appear on the left with system metrics on the right

## Weather Parameters

### Temperature & Wind

#### Ambient Temperature
- **Range**: -20°C to 50°C
- **Default**: 25°C
- **Impact**: Higher temperature → Lower line ratings
- **Typical Change**: 10°C increase reduces ratings by 5-8%

Temperature is the most significant factor affecting line ratings. Hot conditions reduce the conductor's ability to dissipate heat, lowering safe current-carrying capacity.

#### Wind Speed
- **Range**: 0 to 20 ft/s
- **Default**: 2.0 ft/s
- **Impact**: Higher wind → Better cooling → Higher ratings
- **Typical Change**: Increase from 1 to 3 ft/s improves ratings by 10-15%

Wind cooling is critical for conductor thermal management. Perpendicular wind provides maximum cooling effect.

#### Wind Angle
- **Range**: 0° to 90°
- **Default**: 90° (perpendicular)
- **Impact**: 90° provides maximum cooling
- **Note**: 0° (parallel) provides minimal cooling

### Solar Conditions

#### Time of Day
- **Range**: 0 to 23 hours
- **Default**: 12 (noon)
- **Impact**: Solar radiation peaks around noon (12-14h)
- **Night Operation**: 0-6h and 20-23h have no solar heating

#### Date
- **Format**: DD MMM (e.g., "21 Jun")
- **Default**: "12 Jun"
- **Impact**: Affects solar angle calculations
- **Summer Peak**: June 21st has maximum solar radiation
- **Winter Low**: December 21st has minimum solar radiation

#### Surface Emissivity
- **Range**: 0.2 to 1.0
- **Default**: 0.8
- **Impact**: Heat radiation efficiency
- **Values**:
  - 0.9+: Weathered/aged conductors
  - 0.7-0.9: Normal conductors
  - <0.7: New/clean conductors

#### Solar Absorptivity
- **Range**: 0.2 to 1.0
- **Default**: 0.8
- **Impact**: Solar heat absorption
- **Values**:
  - 0.9+: Dark/aged conductors
  - 0.7-0.9: Normal conductors
  - <0.7: Reflective/new conductors

### Location & Atmospheric

#### Elevation
- **Range**: 0 to 5000 ft
- **Default**: 1000 ft
- **Impact**: Affects air density and cooling
- **Note**: Higher elevation = thinner air = less cooling

#### Latitude
- **Range**: 0° to 90°N
- **Default**: 27°
- **Impact**: Affects solar angle calculations
- **Zones**:
  - 0-23.5°: Tropical
  - 23.5-66.5°: Temperate
  - 66.5-90°: Polar

#### Line Orientation
- **Options**: East-West, North-South
- **Default**: East-West
- **Impact**: Affects solar heating patterns
- **Note**: East-West lines receive more solar heating at noon

#### Atmospheric Condition
- **Options**: Clear, Industrial
- **Default**: Clear
- **Impact**: Affects solar radiation and heat dissipation
- **Industrial**: More particulates can reduce solar heating

## Quick Scenarios

### Summer Peak
- Temperature: 40°C
- Wind: 1.0 ft/s
- Time: 14:00 (2 PM)
- Date: June 21st
- **Use Case**: Worst-case hot afternoon scenario

### Winter Low
- Temperature: 5°C
- Wind: 3.5 ft/s
- Time: 08:00 (8 AM)
- Date: December 21st
- **Use Case**: Best-case cold morning scenario

### High Wind
- Temperature: 25°C
- Wind: 8.0 ft/s (perpendicular)
- Time: 12:00 (noon)
- **Use Case**: Analyze cooling benefits of strong wind

### Night Operation
- Temperature: 15°C
- Wind: 2.0 ft/s
- Time: 00:00 (midnight)
- **Use Case**: No solar radiation scenario

### Extreme Heat
- Temperature: 48°C
- Wind: 0.5 ft/s
- Time: 13:00 (1 PM)
- Date: July 21st
- **Use Case**: Absolute worst-case scenario

### Optimal Cooling
- Temperature: 10°C
- Wind: 6.0 ft/s
- Time: 22:00 (10 PM)
- Date: January 12th
- **Use Case**: Maximum cooling capacity

## Using the Comparison View

### Activating Comparison
1. Modify weather parameters as desired
2. Click **"Compare with Baseline"** button
3. The comparison panel appears showing impact metrics

### Comparison Metrics

#### Critical Lines
Shows change in number of overloaded lines (>100% loading)
- **Green (↓)**: Improvement - fewer critical lines
- **Red (↑)**: Degradation - more critical lines

#### High Stress Lines
Shows change in lines at 90-100% loading
- Indicates lines approaching limits

#### Average Loading
Shows system-wide average loading percentage change
- Positive change = worse (higher loading)
- Negative change = better (lower loading)

#### Max Loading
Shows change in the most heavily loaded line
- Critical for identifying bottlenecks

#### Total System Capacity Change
Shows percentage change in aggregate system capacity
- **>5%**: Significant improvement (green indicator)
- **<-5%**: Significant reduction (red warning)

### Weather Change Summary
Displays the difference between baseline and modified conditions:
- Temperature change with color coding (red=hotter, green=cooler)
- Wind speed change (green=more wind, red=less wind)

## System Impact Summary

Real-time dashboard showing current system status:

### Critical (Red)
Number of lines operating above 100% of dynamic rating
- **Immediate action required**

### High Stress (Orange)
Number of lines at 90-100% of rating
- **Monitor closely, prepare contingency**

### Average Loading
System-wide average loading percentage
- **Target**: <60% for normal operation

### Max Loading
Highest line loading in the system
- **Critical threshold**: 100%

## Workflow Examples

### Example 1: Preparing for Heat Wave

**Objective**: Understand system impact of predicted 45°C temperatures

1. Navigate to Analysis → Weather Analysis
2. Click **"Extreme Heat"** preset (or manually set temp to 45°C)
3. Click **"Apply & Recalculate"**
4. Review System Impact Summary for critical lines
5. Click **"Compare with Baseline"** to see the delta
6. Check which lines moved from High Stress to Critical
7. Export or screenshot for contingency planning

**Expected Results**:
- 5-8% reduction in line ratings
- Increase in critical/high-stress line count
- May require load curtailment or generation re-dispatch

### Example 2: Analyzing Wind Benefits

**Objective**: Quantify rating improvement from forecasted wind

1. Start with current conditions (default)
2. Note baseline Average Loading
3. Click **"High Wind"** preset
4. Enable comparison view
5. Review Total System Capacity Change

**Expected Results**:
- 10-20% improvement in ratings with 8 ft/s wind
- Reduction in high-stress lines
- Possible deferment of planned outages

### Example 3: Night Operation Analysis

**Objective**: Determine if critical maintenance can be scheduled

1. Apply **"Night Operation"** preset
2. Check System Impact Summary
3. Compare with daytime peak (Summer Peak preset)
4. Identify lines with sufficient margin at night
5. Export comparison for maintenance planning

**Expected Results**:
- 3-5% rating improvement due to no solar heating
- Cooler temperatures provide additional margin
- May enable safe execution of critical work

## Tips and Best Practices

### For Grid Operators

1. **Start with Defaults**: Establish baseline before making changes
2. **Use Presets**: Quick scenarios cover 80% of analysis needs
3. **Compare Always**: Enable comparison view to quantify impact
4. **Check Extremes**: Test Summer Peak and Extreme Heat regularly
5. **Document Changes**: Screenshot or export comparison results

### For Planning Engineers

1. **Seasonal Analysis**: Run all four seasons (vary date and temperature)
2. **Probabilistic Scenarios**: Test multiple temperature/wind combinations
3. **Sensitivity Analysis**: Change one parameter at a time to understand individual impacts
4. **Validation**: Compare with historical data during known weather events
5. **Conductor Aging**: Increase emissivity (0.9+) for older conductors

### Understanding Weather Impact Patterns

| Temperature Change | Rating Impact | System Response |
|-------------------|---------------|-----------------|
| +10°C | -5 to -8% | Monitor closely |
| +20°C | -10 to -15% | Prepare curtailment |
| +30°C | -15 to -20% | Load shedding likely |

| Wind Speed | Rating Multiplier | Typical Benefit |
|------------|-------------------|-----------------|
| 0.5 ft/s | 0.85x | Worst case |
| 2.0 ft/s | 1.0x | Design basis |
| 5.0 ft/s | 1.15x | Significant gain |
| 10 ft/s | 1.25x | Maximum benefit |

### Common Scenarios

**Hot & Calm (Worst Case)**
- Temp: 40-48°C
- Wind: 0.5-1.0 ft/s
- Time: 13:00-15:00
- Impact: -20 to -25% capacity

**Cool & Windy (Best Case)**
- Temp: 5-15°C
- Wind: 5-8 ft/s
- Time: 0:00-6:00
- Impact: +15 to +25% capacity

**Typical Summer Day**
- Temp: 30-35°C
- Wind: 2-3 ft/s
- Time: 14:00
- Impact: -8 to -12% capacity

## Troubleshooting

### Controls Not Responding
- Ensure "Apply & Recalculate" button is clicked
- Check that backend server is running (port 5000)
- Verify no console errors in browser developer tools

### Comparison Shows No Change
- Ensure weather parameters actually changed from baseline
- Click "Reset to Defaults" then modify again
- Re-enable comparison view

### Unexpected Results
- Verify parameter values are in valid ranges
- Check that IEEE 738 assumptions match your system
- Conductor-specific parameters (emissivity, absorptivity) should match actual hardware

## Technical Notes

### IEEE 738 Standard Compliance

All calculations follow IEEE Std 738-2012: "Standard for Calculating the Current-Temperature Relationship of Bare Overhead Conductors"

Key assumptions:
- Steady-state thermal balance
- Uniform conductor temperature
- Standard atmospheric conditions at specified elevation
- Solar radiation based on ASHRAE clear sky model

### Calculation Frequency

- Ratings recalculate on "Apply & Recalculate" button click
- Baseline stored on first load (or can be reset)
- Comparison uses stored baseline vs current ratings

### Performance

- Typical calculation time: <1 second for 77 lines
- Real-time UI updates via React state management
- Backend caching for conductor properties

## API Integration

### Weather Parameters Structure

```typescript
interface WeatherParams {
  ambient_temp: number        // °C
  wind_speed: number          // ft/s
  wind_angle: number          // degrees (0-90)
  sun_time: number            // hour (0-23)
  date: string                // "DD MMM"
  elevation?: number          // ft
  latitude?: number           // degrees
  emissivity?: number         // 0.2-1.0
  absorptivity?: number       // 0.2-1.0
  direction?: 'EastWest' | 'NorthSouth'
  atmosphere?: 'Clear' | 'Industrial'
}
```

### Backend Endpoint

```
POST /api/lines/ratings
Content-Type: application/json

{
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
}
```

## Support and Feedback

For technical support or to report issues:
- Check browser console for errors
- Verify backend logs in terminal
- Ensure API key is configured (for chatbot features)
- Report issues on GitHub with screenshots and weather parameter values used

## Version History

**v1.0** (Current)
- Full IEEE 738 parameter support
- 6 preset scenarios
- Baseline comparison view
- Real-time system impact metrics
- Collapsible parameter sections
- Sub-tab integration in Analysis tab
