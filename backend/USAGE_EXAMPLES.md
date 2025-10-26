# Usage Examples - CSV Data Loading and Processing

This document provides practical examples for using the refactored CSV data loading infrastructure.

## Table of Contents

1. [Basic Data Loading](#basic-data-loading)
2. [Working with Transmission Lines](#working-with-transmission-lines)
3. [Data Validation](#data-validation)
4. [Error Handling](#error-handling)
5. [Configuration Management](#configuration-management)
6. [Integration with Rating Calculator](#integration-with-rating-calculator)
7. [Advanced Usage](#advanced-usage)

---

## Basic Data Loading

### Example 1: Load All Lines

```python
from csv_data_loader import CSVDataLoader

# Initialize the loader
loader = CSVDataLoader()

# Load all transmission lines (with validation)
lines = loader.get_all_lines(validate=True)

print(f"Loaded {len(lines)} transmission lines")

# Access first line
if lines:
    first_line = lines[0]
    print(f"Line: {first_line.name}")
    print(f"Capacity: {first_line.s_nom} MVA")
    print(f"Conductor: {first_line.conductor}")
```

### Example 2: Load Specific Line Data

```python
from csv_data_loader import CSVDataLoader

loader = CSVDataLoader()

# Get specific line by name
line = loader.get_line_data('L0')

if line:
    print(f"Line: {line.branch_name}")
    print(f"From: {line.bus0_name} To: {line.bus1_name}")
    print(f"Resistance: {line.r} Ohms")
    print(f"Reactance: {line.x} Ohms")
    print(f"Capacity: {line.s_nom} MVA")
else:
    print("Line not found")
```

### Example 3: Load Bus/Substation Data

```python
from csv_data_loader import CSVDataLoader

loader = CSVDataLoader()

# Load all buses
buses = loader.get_all_buses(validate=True)

print(f"Loaded {len(buses)} buses")

# Find specific bus
bus = loader.get_bus_data('ALOHA138')

if bus:
    print(f"Bus: {bus.BusName}")
    print(f"Voltage: {bus.v_nom} kV")
    print(f"Location: ({bus.y}, {bus.x})")  # (lat, lon)
```

### Example 4: Load Power Flow Data

```python
from csv_data_loader import CSVDataLoader

loader = CSVDataLoader()

# Get power flow for specific line
flow = loader.get_power_flow('L0')

if flow:
    print(f"Line: {flow.name}")
    print(f"Power Flow: {flow.p0_nominal} MW")
```

### Example 5: Load Conductor Parameters

```python
from csv_data_loader import CSVDataLoader

loader = CSVDataLoader()

# Get conductor parameters
conductor = loader.get_conductor_params('795 ACSR 26/7 DRAKE')

if conductor:
    print(f"Conductor: {conductor.ConductorName}")
    print(f"Max Temp: {conductor.MOT}°C")
    print(f"Rating (138kV): {conductor.RatingMVA_138} MVA")
    print(f"Rating (69kV): {conductor.RatingMVA_69} MVA")
```

---

## Working with Transmission Lines

### Example 6: Get Complete Line Information

```python
from csv_data_loader import CSVDataLoader

loader = CSVDataLoader()

# Get all information for a line
info = loader.get_complete_line_info('L0')

if info:
    line = info['line_data']
    flow = info['power_flow']
    conductor = info['conductor_params']
    geometry = info['geometry']

    print(f"=== Line {line.name} ===")
    print(f"Name: {line.branch_name}")
    print(f"Capacity: {line.s_nom} MVA")

    if flow:
        print(f"Flow: {flow.p0_nominal} MW")
        # Calculate approximate loading
        flow_mva = abs(flow.p0_nominal) / 0.95  # Assume PF = 0.95
        loading_pct = (flow_mva / line.s_nom) * 100
        print(f"Loading: {loading_pct:.1f}%")

    if conductor:
        print(f"Conductor: {conductor.ConductorName}")
        print(f"Rating: {conductor.RatingMVA_138} MVA @ 138kV")

    if geometry:
        print(f"Geographic data available: {geometry['type']}")
```

### Example 7: Find Overloaded Lines

```python
from csv_data_loader import CSVDataLoader

loader = CSVDataLoader()

# Load all data
lines = loader.get_all_lines(validate=False)
flows = loader.get_all_power_flows(validate=False)

# Create flow lookup
flow_dict = {f['name']: f['p0_nominal'] for f in flows}

# Find overloaded lines
overloaded = []

for line in lines:
    if line['name'] in flow_dict:
        flow_mw = flow_dict[line['name']]
        flow_mva = abs(flow_mw) / 0.95  # Approximate
        loading_pct = (flow_mva / line['s_nom']) * 100

        if loading_pct > 90:
            overloaded.append({
                'name': line['name'],
                'branch_name': line['branch_name'],
                'loading_pct': loading_pct,
                'capacity': line['s_nom'],
                'flow': flow_mva
            })

# Sort by loading percentage
overloaded.sort(key=lambda x: x['loading_pct'], reverse=True)

print(f"Found {len(overloaded)} lines with loading > 90%")
for line in overloaded[:5]:  # Top 5
    print(f"  {line['name']}: {line['loading_pct']:.1f}% "
          f"({line['flow']:.1f} / {line['capacity']:.1f} MVA)")
```

### Example 8: Calculate Line Statistics

```python
from csv_data_loader import CSVDataLoader
import statistics

loader = CSVDataLoader()

lines = loader.get_all_lines(validate=False)

# Calculate statistics
capacities = [line['s_nom'] for line in lines]
resistances = [line['r'] for line in lines]
reactances = [line['x'] for line in lines]
xr_ratios = [abs(line['x'] / line['r']) for line in lines if line['r'] > 0]

print("=== Line Statistics ===")
print(f"Total Lines: {len(lines)}")
print(f"\nCapacity (MVA):")
print(f"  Mean: {statistics.mean(capacities):.1f}")
print(f"  Median: {statistics.median(capacities):.1f}")
print(f"  Range: {min(capacities):.1f} - {max(capacities):.1f}")
print(f"\nX/R Ratio:")
print(f"  Mean: {statistics.mean(xr_ratios):.2f}")
print(f"  Median: {statistics.median(xr_ratios):.2f}")
```

---

## Data Validation

### Example 9: Validate All Data

```python
from csv_data_loader import CSVDataLoader
from data_validator import validate_csv_data_quality

loader = CSVDataLoader()

# Run comprehensive validation
is_valid, summary = validate_csv_data_quality(loader)

print(summary)

if is_valid:
    print("\n✓ All validation checks passed!")
else:
    print("\n✗ Validation failed - please review errors above")
```

### Example 10: Validate Individual Components

```python
from csv_data_loader import CSVDataLoader
from data_validator import DataValidator

loader = CSVDataLoader()

# Load data
lines = loader.get_all_lines(validate=True)
buses = loader.get_all_buses(validate=True)

# Validate individual line
line = lines[0]
result = DataValidator.validate_line_data(line)

print(f"Line {line.name} validation:")
print(f"  Valid: {result.is_valid}")
print(f"  Errors: {len(result.errors)}")
print(f"  Warnings: {len(result.warnings)}")

if result.errors:
    for error in result.errors:
        print(f"  ERROR: {error}")

if result.warnings:
    for warning in result.warnings:
        print(f"  WARNING: {warning}")
```

### Example 11: Check Data Coverage

```python
from csv_data_loader import CSVDataLoader

loader = CSVDataLoader()

# Get statistics
stats = loader.get_data_statistics()

print("=== Data Coverage ===")
print(f"Lines: {stats['line_count']}")
print(f"Buses: {stats['bus_count']}")
print(f"Power Flows: {stats['flow_count']}")
print(f"Conductors: {stats['conductor_count']}")

# Check file status
file_status = stats['data_files_status']
print("\n=== File Status ===")
for filename, exists in file_status.items():
    status = "✓" if exists else "✗"
    print(f"{status} {filename}")
```

---

## Error Handling

### Example 12: Handle Missing Files

```python
from csv_data_loader import CSVDataLoader
from data_models import DataLoadError
import logging

# Enable logging to see warnings
logging.basicConfig(level=logging.INFO)

try:
    loader = CSVDataLoader()
    lines = loader.get_all_lines(validate=True)
    print(f"Successfully loaded {len(lines)} lines")

except DataLoadError as e:
    print(f"Failed to load data: {e}")
    print("Please check that all required CSV files exist in backend/data/")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Example 13: Handle Validation Errors

```python
from csv_data_loader import CSVDataLoader
from data_models import DataValidationError

loader = CSVDataLoader()

try:
    # Load with validation enabled
    lines = loader.get_all_lines(validate=True)
    print(f"All {len(lines)} lines passed validation")

except DataValidationError as e:
    print(f"Validation failed: {e}")

    # Try loading without validation to see raw data
    print("\nLoading without validation...")
    lines_raw = loader.get_all_lines(validate=False)
    print(f"Loaded {len(lines_raw)} lines (unvalidated)")
```

### Example 14: Graceful Degradation

```python
from csv_data_loader import CSVDataLoader

loader = CSVDataLoader()

line_name = 'L0'

# Get line data with fallbacks
line = loader.get_line_data(line_name)
if not line:
    print(f"Line {line_name} not found")
    exit(1)

# Try to get optional data with fallbacks
flow = loader.get_power_flow(line_name)
flow_mw = flow.p0_nominal if flow else 0.0

conductor = loader.get_conductor_params(line.conductor)
if conductor:
    print(f"Conductor rating: {conductor.RatingAmps} A")
else:
    print(f"Conductor data not available for {line.conductor}")

print(f"Line {line_name}: {flow_mw} MW")
```

---

## Configuration Management

### Example 15: Check Configuration Status

```python
from config import DataConfig, APIConfig, print_configuration_status

# Print full configuration
print_configuration_status()
```

### Example 16: Validate File Paths

```python
from config import DataConfig

# Check which files are missing
missing = DataConfig.get_missing_files()

if missing:
    print("Missing required files:")
    for filename in missing:
        print(f"  - {filename}")
else:
    print("✓ All required data files present")

# Get file status
status = DataConfig.validate_required_files()
for filename, exists in status.items():
    print(f"{'✓' if exists else '✗'} {filename}")
```

### Example 17: Access Configuration Values

```python
from config import DataConfig, AppConfig

print(f"Data directory: {DataConfig.DATA_DIR}")
print(f"Lines CSV: {DataConfig.LINES_CSV}")
print(f"Output directory: {DataConfig.OUTPUT_DIR}")

print(f"\nStress thresholds:")
print(f"  Caution: {AppConfig.STRESS_THRESHOLD_CAUTION}%")
print(f"  High: {AppConfig.STRESS_THRESHOLD_HIGH}%")
print(f"  Critical: {AppConfig.STRESS_THRESHOLD_CRITICAL}%")

# Get default weather parameters
weather = AppConfig.get_default_weather_params()
print(f"\nDefault weather:")
print(f"  Temperature: {weather['Ta']}°C")
print(f"  Wind: {weather['WindVelocity']} ft/s")
```

---

## Integration with Rating Calculator

### Example 18: Calculate Line Ratings

```python
from data_loader import DataLoader
from rating_calculator import RatingCalculator

# Initialize (uses refactored data loader internally)
loader = DataLoader()
calculator = RatingCalculator(loader)

# Define weather conditions
weather = {
    'Ta': 35,                    # 35°C ambient temperature
    'WindVelocity': 2.0,         # 2 ft/s wind
    'WindAngleDeg': 90,
    'SunTime': 14,               # 2 PM
    'Date': '15 Jun',
    'Emissivity': 0.8,
    'Absorptivity': 0.8,
    'Direction': 'EastWest',
    'Atmosphere': 'Clear',
    'Elevation': 1000,
    'Latitude': 21
}

# Calculate ratings for all lines
result = calculator.calculate_all_line_ratings(weather)

# Print summary
summary = result['summary']
print(f"=== Rating Summary ===")
print(f"Total Lines: {summary['total_lines']}")
print(f"Overloaded: {summary['overloaded_lines']}")
print(f"High Stress: {summary['high_stress_lines']}")
print(f"Average Loading: {summary['avg_loading']:.1f}%")
print(f"Max Loading: {summary['max_loading']:.1f}%")

# Print top stressed lines
print(f"\nTop 5 Stressed Lines:")
for line in summary['critical_lines'][:5]:
    print(f"  {line['name']}: {line['loading_pct']:.1f}% "
          f"(margin: {line['margin_mva']:.1f} MVA)")
```

### Example 19: Find Temperature Threshold

```python
from data_loader import DataLoader
from rating_calculator import RatingCalculator

loader = DataLoader()
calculator = RatingCalculator(loader)

# Find temperature where overloads start
result = calculator.find_overload_threshold(
    temp_start=20,
    temp_end=50,
    wind_speed=2.0,
    step=2
)

print(f"=== Temperature Threshold Analysis ===")
print(f"Temperature range: {result['temperature_range']}")
print(f"Wind speed: {result['wind_speed']} ft/s")
print(f"First overload at: {result['first_overload_temp']}°C")

# Show progression
print(f"\nTemperature progression:")
for entry in result['progression'][::5]:  # Every 5th entry
    print(f"  {entry['temperature']}°C: "
          f"{entry['overloaded_lines']} overloaded, "
          f"avg loading {entry['avg_loading']:.1f}%")
```

---

## Advanced Usage

### Example 20: Use Global Singleton Loader

```python
from csv_data_loader import get_loader

# Get global loader instance (cached)
loader = get_loader()

# Use it anywhere in your application
lines = loader.get_all_lines()
print(f"Loaded {len(lines)} lines using global loader")
```

### Example 21: Custom Cache Configuration

```python
from csv_data_loader import CSVDataLoader

# Disable caching
loader_no_cache = CSVDataLoader(enable_cache=False)

# Custom cache TTL (10 minutes)
loader_long_cache = CSVDataLoader(cache_ttl=600)

# Clear cache when data changes
loader = CSVDataLoader()
loader.clear_cache()
```

### Example 22: Load GeoJSON for Mapping

```python
from csv_data_loader import CSVDataLoader

loader = CSVDataLoader()

# Load GeoJSON
lines_geojson = loader.get_lines_geojson()
buses_geojson = loader.get_buses_geojson()

# Process for visualization
for feature in lines_geojson['features']:
    line_name = feature['properties']['Name']
    coords = feature['geometry']['coordinates']
    print(f"Line {line_name}: {len(coords)} coordinate points")
```

### Example 23: Bulk Data Processing

```python
from csv_data_loader import CSVDataLoader
import pandas as pd

loader = CSVDataLoader()

# Load all data without validation for speed
lines = loader.get_all_lines(validate=False)
flows = loader.get_all_power_flows(validate=False)

# Convert to DataFrames for analysis
lines_df = pd.DataFrame(lines)
flows_df = pd.DataFrame(flows)

# Merge data
merged = pd.merge(lines_df, flows_df, on='name', how='left')

# Fill missing flows with 0
merged['p0_nominal'].fillna(0, inplace=True)

# Calculate loading
merged['flow_mva'] = merged['p0_nominal'].abs() / 0.95
merged['loading_pct'] = (merged['flow_mva'] / merged['s_nom']) * 100

# Analyze
print(f"=== Loading Distribution ===")
print(merged['loading_pct'].describe())

# Export results
merged.to_csv('line_loading_analysis.csv', index=False)
print("Exported to line_loading_analysis.csv")
```

### Example 24: Monitor Data Changes

```python
from csv_data_loader import CSVDataLoader
import time

loader = CSVDataLoader()

# Initial load
initial_stats = loader.get_data_statistics()
print(f"Initial: {initial_stats['line_count']} lines")

# Simulate data update
print("Waiting for data updates...")
time.sleep(5)

# Reload data
loader.reload_data()
updated_stats = loader.get_data_statistics()
print(f"After reload: {updated_stats['line_count']} lines")
```

---

## Testing Your Data

### Example 25: Quick Data Test

```python
#!/usr/bin/env python3
"""
Quick test script to verify CSV data loading works correctly.
Run this after setting up or updating CSV files.
"""

from csv_data_loader import CSVDataLoader
from data_validator import validate_csv_data_quality
from config import print_configuration_status

def test_data_loading():
    """Test basic data loading functionality."""
    print("\n" + "="*60)
    print("CSV DATA LOADING TEST")
    print("="*60)

    # 1. Check configuration
    print("\n[1/4] Checking configuration...")
    print_configuration_status()

    # 2. Load data
    print("\n[2/4] Loading CSV data...")
    try:
        loader = CSVDataLoader()
        stats = loader.get_data_statistics()

        print(f"✓ Lines: {stats['line_count']}")
        print(f"✓ Buses: {stats['bus_count']}")
        print(f"✓ Flows: {stats['flow_count']}")
        print(f"✓ Conductors: {stats['conductor_count']}")
    except Exception as e:
        print(f"✗ Error loading data: {e}")
        return False

    # 3. Validate data
    print("\n[3/4] Validating data quality...")
    is_valid, summary = validate_csv_data_quality(loader)
    print(summary)

    # 4. Test specific operations
    print("\n[4/4] Testing specific operations...")

    # Test line data
    line = loader.get_line_data('L0')
    if line:
        print(f"✓ Line data: {line.name} - {line.branch_name}")
    else:
        print("✗ Failed to load line L0")

    # Test complete info
    info = loader.get_complete_line_info('L0')
    if info:
        print(f"✓ Complete info: includes {len(info)} components")
    else:
        print("✗ Failed to get complete info")

    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60 + "\n")

    return is_valid

if __name__ == '__main__':
    success = test_data_loading()
    exit(0 if success else 1)
```

---

## See Also

- [DATA_SCHEMA.md](DATA_SCHEMA.md) - Complete data schema documentation
- [config.py](config.py) - Configuration management
- [csv_data_loader.py](csv_data_loader.py) - Data loader implementation
- [data_validator.py](data_validator.py) - Validation implementation
