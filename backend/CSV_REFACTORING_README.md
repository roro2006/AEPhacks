# CSV Data Loading Refactoring - Complete Guide

## Overview

This document describes the **production-ready CSV data loading infrastructure** that has been implemented for the Grid Real-Time Rating Monitor application. The refactoring provides:

- **Robust error handling** for missing files and malformed data
- **Data validation** using Pydantic models
- **Performance optimization** through intelligent caching
- **Centralized configuration** for easy path management
- **Backward compatibility** with existing code
- **Comprehensive documentation** and examples

---

## What Was Changed

### Before Refactoring

**Issues:**
- Hard-coded paths to external directories
- No error handling for missing files
- No data validation
- No logging or debugging support
- Path construction could fail on different operating systems
- Direct pandas DataFrame manipulation without type safety

### After Refactoring

**Improvements:**
- Centralized configuration in `config.py`
- Comprehensive error handling with custom exceptions
- Full data validation using Pydantic models
- Intelligent caching with configurable TTL
- Detailed logging for debugging
- Cross-platform path handling
- Type hints and documentation throughout
- Production-ready code quality

---

## New Components

### 1. `data_models.py` - Type-Safe Data Models

**Purpose:** Defines Pydantic models for all data structures with built-in validation.

**Models:**
- `LineData` - Transmission line parameters
- `BusData` - Bus/substation information
- `PowerFlow` - Power flow data
- `ConductorParams` - Conductor thermal ratings
- `WeatherParams` - Weather conditions for rating calculations
- `LineRatingResult` - Rating calculation results
- `RatingSummary` - Aggregated statistics

**Benefits:**
- Automatic data validation
- Type checking with IDE support
- Self-documenting code
- Runtime error prevention

**Example:**
```python
from data_models import LineData

line = LineData(
    name="L0",
    bus0="0",
    bus1="1",
    bus0_name="ALOHA138",
    bus1_name="HILL138",
    branch_name="ALOHA 138 - HILL 138 1",
    ckt="1",
    x=3.42,
    r=0.856,
    b=0.000115,
    s_nom=184.752,
    conductor="795 ACSR 26/7 DRAKE",
    MOT=100
)
```

---

### 2. `config.py` - Centralized Configuration

**Purpose:** Manages all configuration settings and file paths.

**Classes:**
- `DataConfig` - Data file paths and directories
- `APIConfig` - API and service configuration
- `AppConfig` - Application parameters and defaults

**Benefits:**
- Single source of truth for configuration
- Easy to change data locations
- Environment variable support
- Configuration validation

**Example:**
```python
from config import DataConfig, print_configuration_status

# Print current configuration
print_configuration_status()

# Access file paths
lines_path = DataConfig.LINES_CSV
data_dir = DataConfig.DATA_DIR

# Check for missing files
missing = DataConfig.get_missing_files()
```

---

### 3. `csv_data_loader.py` - Robust Data Loader

**Purpose:** Core data loading module with error handling and caching.

**Key Features:**
- Loads and validates CSV and GeoJSON files
- Implements caching for performance
- Comprehensive error handling
- Detailed logging
- Graceful degradation

**Benefits:**
- Consistent data access across application
- Automatic retry and fallback mechanisms
- Performance optimization
- Easy to test and maintain

**Example:**
```python
from csv_data_loader import CSVDataLoader

# Initialize loader
loader = CSVDataLoader()

# Load data with validation
lines = loader.get_all_lines(validate=True)

# Get specific line
line = loader.get_line_data('L0')

# Get complete information
info = loader.get_complete_line_info('L0')

# Clear cache when data changes
loader.clear_cache()
```

---

### 4. `data_validator.py` - Data Quality Validation

**Purpose:** Validates data against domain-specific rules and constraints.

**Features:**
- Individual record validation
- Cross-dataset consistency checks
- Physics-based validation rules
- Detailed error and warning messages

**Benefits:**
- Catch data errors early
- Ensure data integrity
- Provide actionable feedback
- Prevent calculation errors

**Example:**
```python
from csv_data_loader import CSVDataLoader
from data_validator import validate_csv_data_quality

loader = CSVDataLoader()
is_valid, summary = validate_csv_data_quality(loader)

print(summary)
# Shows errors, warnings, and info messages
```

---

### 5. `data_loader.py` - Refactored Legacy Wrapper

**Purpose:** Maintains backward compatibility while using new infrastructure.

**Changes:**
- Now uses `CSVDataLoader` internally
- Removed hard-coded external paths
- Added proper error handling
- Maintains same public API

**Benefits:**
- Existing code continues to work
- Gains all benefits of new infrastructure
- No breaking changes
- Smooth transition path

**Example:**
```python
from data_loader import DataLoader

# Works exactly like before
loader = DataLoader()
lines = loader.get_all_lines()
line_info = loader.get_line_info('L0')

# But now with better error handling and validation
```

---

## File Structure

```
backend/
├── config.py                      # Configuration management
├── data_models.py                 # Pydantic data models
├── csv_data_loader.py             # Core CSV loader
├── data_validator.py              # Data validation
├── data_loader.py                 # Legacy wrapper (refactored)
├── rating_calculator.py           # Rating calculations (unchanged)
├── map_generator.py               # Map visualization (unchanged)
├── app.py                         # Flask API server (unchanged)
│
├── DATA_SCHEMA.md                 # Complete data schema documentation
├── USAGE_EXAMPLES.md              # Usage examples and recipes
├── CSV_REFACTORING_README.md      # This file
├── test_csv_loading.py            # Comprehensive test suite
│
├── data/                          # Main data directory
│   ├── lines.csv                  # Transmission line data
│   ├── buses.csv                  # Bus/substation data
│   ├── oneline_lines.geojson      # Line geographic data
│   ├── oneline_busses.geojson     # Bus geographic data
│   └── ...                        # Other data files
│
├── conductor_ratings.csv          # Conductor thermal ratings
├── line_flows_nominal.csv         # Nominal power flows
└── output/                        # Generated files (maps, reports)
```

---

## How to Use

### Quick Start

1. **Run the test suite** to verify everything works:
   ```bash
   cd backend
   python test_csv_loading.py
   ```

2. **Check configuration**:
   ```python
   from config import print_configuration_status
   print_configuration_status()
   ```

3. **Load and validate data**:
   ```python
   from csv_data_loader import CSVDataLoader

   loader = CSVDataLoader()
   lines = loader.get_all_lines(validate=True)
   ```

### Common Tasks

#### Load All Lines
```python
from csv_data_loader import CSVDataLoader

loader = CSVDataLoader()
lines = loader.get_all_lines(validate=True)

for line in lines:
    print(f"{line.name}: {line.s_nom} MVA")
```

#### Get Complete Line Information
```python
loader = CSVDataLoader()
info = loader.get_complete_line_info('L0')

line_data = info['line_data']
power_flow = info['power_flow']
conductor = info['conductor_params']
```

#### Validate Data Quality
```python
from data_validator import validate_csv_data_quality

loader = CSVDataLoader()
is_valid, summary = validate_csv_data_quality(loader)

if is_valid:
    print("Data is valid!")
else:
    print(summary)  # Shows errors and warnings
```

#### Calculate Line Ratings (Existing Code)
```python
from data_loader import DataLoader
from rating_calculator import RatingCalculator

# Works exactly as before, but with improved error handling
loader = DataLoader()
calculator = RatingCalculator(loader)

weather = {...}  # Weather parameters
results = calculator.calculate_all_line_ratings(weather)
```

---

## Configuration

### Data Paths

Edit `config.py` to change data locations:

```python
class DataConfig:
    BACKEND_DIR = Path(__file__).resolve().parent
    DATA_DIR = BACKEND_DIR / 'data'

    # Customize paths as needed
    LINES_CSV = DATA_DIR / 'lines.csv'
    BUSES_CSV = DATA_DIR / 'buses.csv'
    # ...
```

### Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# Caching
ENABLE_CACHE=True
CACHE_TTL_SECONDS=300

# Logging
LOG_LEVEL=INFO

# API Configuration
ANTHROPIC_API_KEY=your_api_key_here
CLAUDE_MODEL=claude-3-5-sonnet-20240620
```

### Cache Configuration

```python
# Disable caching
loader = CSVDataLoader(enable_cache=False)

# Custom cache TTL (10 minutes)
loader = CSVDataLoader(cache_ttl=600)

# Clear cache manually
loader.clear_cache()
```

---

## Testing

### Run Full Test Suite

```bash
cd backend
python test_csv_loading.py
```

### Run Validation Only

```bash
python test_csv_loading.py --validate-only
```

### Run with Verbose Output

```bash
python test_csv_loading.py --verbose
```

### Test Individual Components

```bash
# Test configuration
python config.py

# Test data loading
python csv_data_loader.py

# Test validation
python data_validator.py
```

---

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `DataLoadError: CSV file not found` | File missing | Check path in config.py |
| `DataValidationError: Missing required columns` | Wrong CSV format | Check DATA_SCHEMA.md |
| `DataValidationError: validation errors` | Invalid data values | Review validation rules |
| `Referential integrity error` | Missing referenced data | Ensure all buses/conductors exist |

### Example Error Handling

```python
from csv_data_loader import CSVDataLoader
from data_models import DataLoadError, DataValidationError

try:
    loader = CSVDataLoader()
    lines = loader.get_all_lines(validate=True)

except DataLoadError as e:
    print(f"Failed to load CSV files: {e}")
    # Handle missing files

except DataValidationError as e:
    print(f"Data validation failed: {e}")
    # Handle invalid data

except Exception as e:
    print(f"Unexpected error: {e}")
    # Handle other errors
```

---

## Performance Considerations

### Caching

The loader implements intelligent caching to avoid re-reading CSV files:

- **Default TTL:** 5 minutes (300 seconds)
- **Cached items:** Lines, buses, flows, conductors, GeoJSON
- **Cache invalidation:** Automatic based on TTL or manual with `clear_cache()`

### Loading Strategies

**With Validation (Slower, Safer):**
```python
lines = loader.get_all_lines(validate=True)
```

**Without Validation (Faster, Riskier):**
```python
lines = loader.get_all_lines(validate=False)
```

**Best Practice:** Use validation during development and testing, disable for production if performance is critical and data is pre-validated.

---

## Migration Guide

### For Existing Code

**No changes required!** The refactored `DataLoader` maintains full backward compatibility:

```python
# Old code still works
from data_loader import DataLoader

loader = DataLoader()
lines = loader.get_all_lines()
line_info = loader.get_line_info('L0')
```

### For New Code

**Use the new infrastructure directly:**

```python
# New recommended approach
from csv_data_loader import CSVDataLoader

loader = CSVDataLoader()
lines = loader.get_all_lines(validate=True)
line = loader.get_line_data('L0')
```

### Gradual Migration

1. Keep using `DataLoader` for existing code
2. Use `CSVDataLoader` for new features
3. Gradually refactor as needed
4. No rush - both work identically!

---

## Documentation

### Complete Documentation Set

1. **[DATA_SCHEMA.md](DATA_SCHEMA.md)** - Comprehensive CSV file format and schema documentation
2. **[USAGE_EXAMPLES.md](USAGE_EXAMPLES.md)** - 25+ practical usage examples
3. **[CSV_REFACTORING_README.md](CSV_REFACTORING_README.md)** - This overview document

### Code Documentation

All modules include:
- Docstrings for all classes and functions
- Type hints for parameters and return values
- Example usage in docstrings
- Inline comments for complex logic

### Example:

```python
def get_line_data(self, line_name: str, validate: bool = True) -> Optional[LineData]:
    """
    Get data for a specific transmission line.

    Args:
        line_name: Line identifier (e.g., 'L0', 'L1')
        validate: Validate data using Pydantic model (default: True)

    Returns:
        LineData or None: Line data if found, None otherwise

    Example:
        >>> loader = CSVDataLoader()
        >>> line = loader.get_line_data('L0')
        >>> if line:
        ...     print(f"Capacity: {line.s_nom} MVA")
    """
```

---

## Future Enhancements

### Potential Improvements

1. **Database Integration**
   - Add optional database backend for large datasets
   - Keep CSV as primary format with DB as cache

2. **Data Export**
   - Export validated data to different formats
   - Generate summary reports

3. **Real-Time Updates**
   - Watch CSV files for changes
   - Auto-reload when data updates

4. **Advanced Caching**
   - Redis/Memcached support
   - Distributed caching for multi-process deployments

5. **Data Versioning**
   - Track changes to CSV files
   - Rollback capability

---

## Troubleshooting

### Problem: "CSV file not found"

**Solution:** Check configuration and file paths
```python
from config import DataConfig
print(f"Looking for files in: {DataConfig.DATA_DIR}")
missing = DataConfig.get_missing_files()
print(f"Missing: {missing}")
```

### Problem: Validation errors

**Solution:** Run validation to see specific errors
```python
from data_validator import validate_csv_data_quality
loader = CSVDataLoader()
is_valid, summary = validate_csv_data_quality(loader)
print(summary)
```

### Problem: Performance issues

**Solution:** Check cache status and adjust TTL
```python
stats = loader.get_data_statistics()
print(f"Cache enabled: {stats['cache_enabled']}")
print(f"Cached items: {stats['cached_items']}")

# Increase cache TTL
loader = CSVDataLoader(cache_ttl=1800)  # 30 minutes
```

### Problem: Legacy code breaks

**Solution:** The refactored code maintains full backward compatibility. If you encounter issues:

1. Check that you're importing from the right module
2. Verify CSV files are in the expected location
3. Run the test suite: `python test_csv_loading.py`
4. Enable verbose logging to see what's happening

---

## Support and Resources

### Getting Help

1. **Check documentation** - Start with DATA_SCHEMA.md and USAGE_EXAMPLES.md
2. **Run tests** - Use `test_csv_loading.py` to diagnose issues
3. **Enable logging** - Set `LOG_LEVEL=DEBUG` in .env file
4. **Review examples** - See USAGE_EXAMPLES.md for 25+ code examples

### Key Files to Review

- `config.py` - Configuration and paths
- `csv_data_loader.py` - Data loading implementation
- `data_models.py` - Data structure definitions
- `data_validator.py` - Validation rules
- `DATA_SCHEMA.md` - CSV file formats
- `USAGE_EXAMPLES.md` - Code examples

---

## Summary

The CSV data loading infrastructure has been completely refactored to provide:

✓ **Robust error handling** - Graceful failure recovery
✓ **Data validation** - Catch errors early
✓ **Performance optimization** - Intelligent caching
✓ **Clean architecture** - Separation of concerns
✓ **Comprehensive documentation** - Easy to understand and use
✓ **Backward compatibility** - Existing code keeps working
✓ **Production ready** - Tested and reliable

### Next Steps

1. Run `python test_csv_loading.py` to verify setup
2. Review `USAGE_EXAMPLES.md` for practical examples
3. Check `DATA_SCHEMA.md` for CSV file formats
4. Start using the new infrastructure in your code!

---

**Version:** 1.0
**Last Updated:** 2025-10-25
**Author:** Claude Code Refactoring Team
