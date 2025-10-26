# Contingency Analysis JSON Serialization Fix

## Problem

When clicking "Simulate Outage" in the Analysis tab, the API returned a 500 Internal Server Error:

```
Error: API error: INTERNAL SERVER ERROR
```

**Root Cause**: The contingency analysis results contained numpy types (`numpy.bool_`, `numpy.int64`, `numpy.float64`) which are not JSON serializable by Python's default JSON encoder.

## Error Details

The specific error was:
```
TypeError: Object of type bool_ is not JSON serializable
```

This occurred because:
1. PyPSA's power flow analysis returns numpy types
2. The `_run_power_flow()` method returned `numpy.bool_` for convergence status
3. The `_analyze_outage_results()` method created dictionaries with `numpy.bool_` values
4. Flask's `jsonify()` cannot serialize these numpy types

## Solution

### 1. Added Numpy Type Converter Function

Added a recursive converter function to `outage_simulator.py` that converts all numpy types to native Python types:

```python
def convert_numpy_types(obj):
    """
    Recursively convert numpy types to native Python types for JSON serialization.
    """
    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return convert_numpy_types(obj.tolist())
    elif isinstance(obj, (pd.Series, pd.DataFrame)):
        return convert_numpy_types(obj.to_dict())
    elif pd.isna(obj):
        return None
    else:
        return obj
```

### 2. Fixed Power Flow Method

Updated `_run_power_flow()` to explicitly convert numpy types to Python types:

**Before:**
```python
converged = info.converged.any().any()  # Returns numpy.bool_
max_error = info.error.max().max()      # Returns numpy.float64
```

**After:**
```python
converged = bool(info.converged.any().any())  # Returns native bool
max_error = float(info.error.max().max())     # Returns native float
```

### 3. Applied Conversion to Results

Updated `simulate_outage()` to convert all results before returning:

**Before:**
```python
return analysis
```

**After:**
```python
return convert_numpy_types(analysis)
```

## Testing

Created `test_contingency_fix.py` to verify the fix:

```bash
python test_contingency_fix.py
```

**Test Results:**
- [OK] JSON serialization successful
- [OK] JSON deserialization successful
- [OK] All types in power_flow_info are native Python types (bool, float)
- [OK] Contingency analysis produces valid JSON

## Verification

To verify the fix works in the API:

1. Start the Flask backend:
   ```bash
   python app.py
   ```

2. Test the contingency endpoint:
   ```bash
   curl http://localhost:5000/api/contingency/n1 \
     -H "Content-Type: application/json" \
     -d '{"lines": ["L0"]}'
   ```

3. Or use the frontend:
   - Navigate to the Analysis tab
   - Select a line from the dropdown
   - Click "Simulate Outage"
   - Should now show results without errors

## Files Modified

- `backend/outage_simulator.py`:
  - Added `convert_numpy_types()` function
  - Updated `_run_power_flow()` to return native Python types
  - Updated `simulate_outage()` to convert results before returning

## Impact

- Fixes 500 Internal Server Error on `/api/contingency/n1` endpoint
- Ensures all contingency analysis results are JSON serializable
- No functional changes to the analysis logic
- Backward compatible with existing code

## Related Issues

This fix is similar to the NaN JSON serialization fix (see `NAN_JSON_FIX.md`) but addresses numpy type serialization specifically in the contingency analysis module.

---

**Date**: 2025-10-26
**Status**: Fixed and tested
