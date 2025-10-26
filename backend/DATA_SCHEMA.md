# Data Schema Documentation

## Overview

This document describes the CSV file structure and data schemas for the Grid Real-Time Rating Monitor application. All CSV files are located in the `backend/data/` directory unless otherwise specified.

---

## Table of Contents

1. [CSV File Locations](#csv-file-locations)
2. [Transmission Lines Data](#transmission-lines-data)
3. [Bus/Substation Data](#bussubstation-data)
4. [Power Flow Data](#power-flow-data)
5. [Conductor Ratings Library](#conductor-ratings-library)
6. [GeoJSON Data](#geojson-data)
7. [Data Validation Rules](#data-validation-rules)
8. [Example CSV Files](#example-csv-files)
9. [Error Handling](#error-handling)

---

## CSV File Locations

### Primary Data Files

| File Name | Location | Description | Record Count |
|-----------|----------|-------------|--------------|
| `lines.csv` | `backend/data/` | Transmission line parameters | 77 lines |
| `buses.csv` | `backend/data/` | Bus/substation information | 37 buses |
| `line_flows_nominal.csv` | `backend/` | Nominal power flows | 77 flows |
| `conductor_ratings.csv` | `backend/` | Conductor thermal ratings library | 40 types |

### GeoJSON Files

| File Name | Location | Description |
|-----------|----------|-------------|
| `oneline_lines.geojson` | `backend/data/` | Line geographic coordinates |
| `oneline_busses.geojson` | `backend/data/` | Bus geographic locations |

### Supporting Data Files

Located in `backend/data/`:
- `generators.csv` - Generator parameters
- `generators-status.csv` - Generator operational status
- `loads.csv` - Load definitions
- `transformers.csv` - Transformer parameters
- `shunt_impedances.csv` - Shunt device parameters
- `snapshots.csv` - Time period definitions
- `investment_periods.csv` - Investment metadata
- `network.csv` - Network-level metadata

---

## Transmission Lines Data

### File: `backend/data/lines.csv`

Contains electrical and physical properties of transmission lines.

### Required Columns

| Column Name | Data Type | Units | Description | Example |
|-------------|-----------|-------|-------------|---------|
| `name` | String | - | Unique line identifier | `"L0"` |
| `bus0` | String | - | From bus ID | `"0"` |
| `bus1` | String | - | To bus ID | `"1"` |
| `bus0_name` | String | - | From bus name | `"ALOHA138"` |
| `bus1_name` | String | - | To bus name | `"HILL138"` |
| `branch_name` | String | - | Descriptive line name | `"ALOHA 138 - HILL 138 1"` |
| `ckt` | String | - | Circuit identifier | `"1"` |
| `x` | Float | Ohms | Line reactance | `3.42` |
| `r` | Float | Ohms | Line resistance | `0.856` |
| `b` | Float | Siemens | Line susceptance | `0.000115` |
| `s_nom` | Float | MVA | Nominal capacity (thermal limit) | `184.752` |
| `conductor` | String | - | Conductor type | `"795 ACSR 26/7 DRAKE"` |
| `MOT` | Integer | °C | Maximum Operating Temperature | `100` |

### Optional Columns

| Column Name | Data Type | Units | Description | Valid Range |
|-------------|-----------|-------|-------------|-------------|
| `v_ang_min` | Float | Degrees | Minimum voltage angle | `-60.0 to 0.0` |
| `v_ang_max` | Float | Degrees | Maximum voltage angle | `0.0 to 60.0` |
| `status` | Integer | - | Line status (1=in service, 0=out) | `0 or 1` |
| `original_index` | Integer | - | Source data index | Any integer |

### Data Constraints

- `r > 0` (Resistance must be positive)
- `x > 0` (Reactance should be positive)
- `s_nom > 0` (Capacity must be positive)
- `MOT` typically ranges from 50-150°C
- X/R ratio typically 2-15 for transmission lines
- `bus0` and `bus1` must reference valid buses in `buses.csv`
- `conductor` must match an entry in `conductor_ratings.csv`

### Example Record

```csv
name,bus0,bus1,bus0_name,bus1_name,branch_name,ckt,x,r,b,s_nom,conductor,MOT,v_ang_min,v_ang_max,status,original_index
L0,0,1,ALOHA138,HILL138,ALOHA 138 - HILL 138 1,1,3.42,0.856,0.000115,184.752,795 ACSR 26/7 DRAKE,100,-60.0,60.0,1,0
```

---

## Bus/Substation Data

### File: `backend/data/buses.csv`

Contains node/substation information for the power grid.

### Required Columns

| Column Name | Data Type | Units | Description | Example |
|-------------|-----------|-------|-------------|---------|
| `name` | String | - | Unique bus ID | `"0"` |
| `BusName` | String | - | Descriptive bus name | `"ALOHA138"` |
| `v_nom` | Float | kV | Nominal voltage | `138.0` or `69.0` |
| `x` | Float | Degrees | Longitude coordinate | `-157.936` |
| `y` | Float | Degrees | Latitude coordinate | `21.345` |

### Optional Columns

| Column Name | Data Type | Units | Description | Default | Valid Range |
|-------------|-----------|-------|-------------|---------|-------------|
| `v_mag_pu_set` | Float | p.u. | Voltage magnitude setpoint | `1.0` | `0.9 - 1.1` |
| `v_mag_pu_min` | Float | p.u. | Minimum voltage magnitude | `0.95` | `0.8 - 1.0` |
| `v_mag_pu_max` | Float | p.u. | Maximum voltage magnitude | `1.05` | `1.0 - 1.2` |
| `control` | String | - | Control type | `"PQ"` | `"PQ"`, `"PV"`, `"Slack"` |
| `Pd` | Float | MW | Active power demand | `0.0` | Any |
| `Qd` | Float | MVAr | Reactive power demand | `0.0` | Any |
| `Gs` | Float | p.u. | Shunt conductance | `0.0` | Any |
| `Bs` | Float | p.u. | Shunt susceptance | `0.0` | Any |
| `area` | Integer | - | Area number | - | Any |
| `zone` | Integer | - | Zone number | - | Any |
| `v_ang_set` | Float | Degrees | Voltage angle setpoint | `0.0` | `-180 to 180` |

### Data Constraints

- `v_nom` should be either 69.0 or 138.0 kV for this system
- `v_mag_pu_min < v_mag_pu_set < v_mag_pu_max`
- Longitude `x` should be in range -161 to -153 (Hawaii)
- Latitude `y` should be in range 18 to 23 (Hawaii)
- `Pd` and `Qd` should be reasonable (typically < 1000 MW, < 500 MVAr)

### Example Record

```csv
name,BusName,v_nom,x,y,v_mag_pu_set,v_mag_pu_min,v_mag_pu_max,control,Pd,Qd,Gs,Bs,area,zone,v_ang_set
0,ALOHA138,138.0,-157.936,21.345,1.0,0.95,1.05,PV,0.0,0.0,0.0,0.0,1,1,0.0
```

---

## Power Flow Data

### File: `backend/line_flows_nominal.csv`

Contains nominal active power flow for each transmission line.

### Required Columns

| Column Name | Data Type | Units | Description | Example |
|-------------|-----------|-------|-------------|---------|
| `name` | String | - | Line identifier (matches `lines.csv`) | `"L0"` |
| `p0_nominal` | Float | MW | Nominal active power flow | `45.2` |

### Data Constraints

- `name` must match a line in `lines.csv`
- `p0_nominal` should be reasonable (typically < 1000 MW for this system)
- Approximate MVA flow = `abs(p0_nominal) / 0.95` (assuming PF ≈ 0.95)
- Flow should not exceed line capacity (`s_nom` in `lines.csv`)

### Example Record

```csv
name,p0_nominal
L0,45.2
L1,-23.8
L2,102.5
```

**Note:** Negative values indicate power flowing in the opposite direction (from `bus1` to `bus0`).

---

## Conductor Ratings Library

### File: `backend/conductor_ratings.csv`

Contains thermal rating parameters for different conductor types.

### Required Columns

| Column Name | Data Type | Units | Description | Example |
|-------------|-----------|-------|-------------|---------|
| `ConductorName` | String | - | Conductor type identifier | `"795 ACSR 26/7 DRAKE"` |
| `MOT` | Integer | °C | Maximum Operating Temperature | `100` |
| `RatingAmps` | Float | Amperes | Static thermal rating (current) | `900.0` |
| `RatingMVA_69` | Float | MVA | Static rating at 69kV | `107.6` |
| `RatingMVA_138` | Float | MVA | Static rating at 138kV | `215.1` |

### Data Constraints

- `RatingAmps > 0`
- `RatingMVA_69 > 0` and `RatingMVA_138 > 0`
- Ratio `RatingMVA_138 / RatingMVA_69` should be approximately 2.0 (138/69)
- Relationship: `MVA = √3 × kV × kA = 1.732 × kV × I/1000`
- `ConductorName` should match conductor types in `lines.csv`

### Example Record

```csv
ConductorName,MOT,RatingAmps,RatingMVA_69,RatingMVA_138
795 ACSR 26/7 DRAKE,100,900.0,107.6,215.1
556.5 ACSR 26/7 PARTRIDGE,100,730.0,87.3,174.6
```

### Common Conductor Types

| Type | Description | Typical Rating (Amps) |
|------|-------------|----------------------|
| ACSR (Aluminum Conductor Steel Reinforced) | Standard transmission conductor | 400-1500 |
| AAAC (All Aluminum Alloy Conductor) | All-aluminum alloy | 300-1200 |
| ACAR (Aluminum Conductor Alloy Reinforced) | Aluminum with alloy core | 350-1000 |

---

## GeoJSON Data

### File: `backend/data/oneline_lines.geojson`

Geographic coordinates for transmission lines in GeoJSON format.

### Structure

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [-157.936, 21.345],
          [-157.892, 21.312]
        ]
      },
      "properties": {
        "Name": "L0",
        "LineName": "ALOHA 138 - HILL 138 1",
        "nomkv": 138.0
      }
    }
  ]
}
```

### Required Properties

- `Name`: Line identifier matching `lines.csv`
- `LineName`: Descriptive line name
- `nomkv`: Nominal voltage in kV

### File: `backend/data/oneline_busses.geojson`

Geographic locations for buses/substations.

### Structure

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [-157.936, 21.345]
      },
      "properties": {
        "Name": "ALOHA138",
        "nomkv": 138.0
      }
    }
  ]
}
```

---

## Data Validation Rules

### Cross-File Validation

The application performs the following cross-file validation checks:

1. **Referential Integrity**
   - All `bus0_name` and `bus1_name` in `lines.csv` must exist in `buses.csv`
   - All `conductor` types in `lines.csv` must exist in `conductor_ratings.csv`
   - All `name` values in `line_flows_nominal.csv` should match lines in `lines.csv`

2. **Capacity Checks**
   - Power flow should not exceed line capacity: `|p0_nominal| / 0.95 ≤ s_nom`
   - Loading percentage = `(flow_mva / s_nom) × 100%`
   - Warning if loading > 90%, critical if loading > 100%

3. **Physical Constraints**
   - X/R ratio should be in reasonable range (typically 2-15 for transmission)
   - Voltage levels should be consistent (69kV or 138kV)
   - Geographic coordinates should be valid for Hawaii

4. **Voltage Level Consistency**
   - If line connects buses at different voltages, it should have a transformer
   - Conductor ratings should match line voltage level

### Data Quality Checks

Run validation using:

```python
from csv_data_loader import CSVDataLoader
from data_validator import validate_csv_data_quality

loader = CSVDataLoader()
is_valid, summary = validate_csv_data_quality(loader)
print(summary)
```

---

## Example CSV Files

### Minimal lines.csv

```csv
name,bus0,bus1,bus0_name,bus1_name,branch_name,ckt,x,r,b,s_nom,conductor,MOT
L0,0,1,ALOHA138,HILL138,ALOHA 138 - HILL 138 1,1,3.42,0.856,0.000115,184.752,795 ACSR 26/7 DRAKE,100
L1,1,2,HILL138,KOKO138,HILL 138 - KOKO 138 1,1,2.15,0.537,7.24e-05,184.752,795 ACSR 26/7 DRAKE,100
```

### Minimal buses.csv

```csv
name,BusName,v_nom,x,y
0,ALOHA138,138.0,-157.936,21.345
1,HILL138,138.0,-157.892,21.312
2,KOKO138,138.0,-157.848,21.280
```

### Minimal line_flows_nominal.csv

```csv
name,p0_nominal
L0,45.2
L1,-23.8
```

### Minimal conductor_ratings.csv

```csv
ConductorName,MOT,RatingAmps,RatingMVA_69,RatingMVA_138
795 ACSR 26/7 DRAKE,100,900.0,107.6,215.1
556.5 ACSR 26/7 PARTRIDGE,100,730.0,87.3,174.6
```

---

## Error Handling

### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `CSV file not found` | File missing from expected location | Check file path in `config.py`, ensure file exists |
| `Missing required columns` | CSV missing critical columns | Add missing columns or fix column names |
| `Validation errors` | Data values out of range | Check data constraints in this document |
| `Referential integrity error` | Bus/conductor not found | Ensure all referenced entities exist in their respective files |
| `Empty CSV file` | File has no data rows | Add data or check export process |
| `Invalid JSON` | Malformed GeoJSON | Validate JSON structure using online tools |

### Loading with Error Handling

```python
from csv_data_loader import CSVDataLoader
from data_models import DataLoadError, DataValidationError

try:
    loader = CSVDataLoader()
    lines = loader.get_all_lines(validate=True)
    print(f"Successfully loaded {len(lines)} lines")
except DataLoadError as e:
    print(f"Failed to load data: {e}")
except DataValidationError as e:
    print(f"Data validation failed: {e}")
```

### Graceful Degradation

The application handles missing data gracefully:

- **Missing power flow data**: Line loading shown as 0%
- **Missing conductor data**: Rating calculation skipped for that line
- **Missing GeoJSON**: Map visualization unavailable but calculations still work
- **Missing optional columns**: Default values used

---

## Configuration

### Configuring Data Paths

Edit `backend/config.py` to customize data file locations:

```python
class DataConfig:
    DATA_DIR = Path(__file__).parent / 'data'
    LINES_CSV = DATA_DIR / 'lines.csv'
    BUSES_CSV = DATA_DIR / 'buses.csv'
    # ... other paths
```

### Environment Variables

Set in `.env` file:

```bash
# Data caching
ENABLE_CACHE=True
CACHE_TTL_SECONDS=300

# Logging
LOG_LEVEL=INFO
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-25 | Initial documentation with refactored CSV loader |

---

## Related Documentation

- [README.md](../README.md) - Project overview
- [config.py](config.py) - Configuration management
- [csv_data_loader.py](csv_data_loader.py) - Data loading implementation
- [data_models.py](data_models.py) - Pydantic data models
- [data_validator.py](data_validator.py) - Validation rules implementation

---

## Support

For questions or issues:
1. Check this documentation
2. Review example CSV files in `backend/data/`
3. Run validation: `python data_validator.py`
4. Check logs for detailed error messages
