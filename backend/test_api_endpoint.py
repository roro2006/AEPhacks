"""
Test the /api/outage/simulate endpoint directly
"""

import json
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_outage_endpoint():
    """Test the outage simulation directly through the app endpoint logic"""
    print("\n" + "="*70)
    print("Testing /api/outage/simulate Endpoint Logic")
    print("="*70)

    try:
        # Import dependencies
        from rating_calculator import RatingCalculator
        from data_loader import DataLoader

        print("\n[1] Initializing components...")
        data_loader = DataLoader()
        calculator = RatingCalculator(data_loader)
        print("    [OK] Components initialized")

        # Test data
        outage_lines = ['L0']
        print(f"\n[2] Testing contingency analysis for lines: {outage_lines}")

        # This is what the endpoint calls
        result = calculator.analyze_contingency(outage_lines)

        print(f"    [OK] Analysis completed")
        print(f"    Success: {result.get('success')}")
        print(f"    Result keys: {list(result.keys())}")

        # Now try to clean NaN values (like the endpoint does)
        print("\n[3] Cleaning NaN values...")

        # Copy the clean_nan_values function from app.py
        import pandas as pd
        import numpy as np

        def clean_nan_values(obj):
            """Recursively replace NaN values with None"""
            if isinstance(obj, dict):
                return {k: clean_nan_values(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_nan_values(item) for item in obj]
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, (np.integer, np.int64, np.int32)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64, np.float32)):
                if pd.isna(obj) or np.isnan(obj) or np.isinf(obj):
                    return None
                return float(obj)
            elif isinstance(obj, float):
                if pd.isna(obj) or np.isnan(obj) or np.isinf(obj):
                    return None
                return obj
            else:
                return obj

        result_clean = clean_nan_values(result)
        print("    [OK] NaN cleaning completed")

        # Try to serialize to JSON (like jsonify does)
        print("\n[4] Testing JSON serialization...")
        try:
            json_str = json.dumps(result_clean, indent=2)
            print("    [OK] JSON serialization successful!")

            # Verify result structure
            if result_clean.get('success'):
                metrics = result_clean.get('metrics', {})
                print(f"\n[5] Results:")
                print(f"    Total lines: {metrics.get('total_lines', 0)}")
                print(f"    Outaged: {metrics.get('outaged_lines_count', 0)}")
                print(f"    Overloaded: {metrics.get('overloaded_count', 0)}")
                print(f"    Max loading: {metrics.get('max_loading_pct', 0):.2f}%")

                pf_info = result_clean.get('power_flow_info', {})
                print(f"\n[6] Power Flow Info:")
                for key, value in pf_info.items():
                    print(f"    {key}: {type(value).__name__} = {value}")

            print("\n" + "="*70)
            print("TEST PASSED: Endpoint logic works correctly!")
            print("="*70)
            return True

        except TypeError as e:
            print(f"    [X] JSON serialization FAILED: {e}")

            # Find problematic types
            def find_non_json_types(obj, path="root"):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        find_non_json_types(value, f"{path}.{key}")
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        find_non_json_types(item, f"{path}[{i}]")
                else:
                    try:
                        json.dumps(obj)
                    except TypeError:
                        print(f"    Non-serializable at {path}: {type(obj).__name__} = {obj}")

            print("\n    Scanning for non-serializable types:")
            find_non_json_types(result_clean)
            return False

    except Exception as e:
        print(f"\n[X] Test failed: {e}")
        import traceback
        print(f"\nTraceback:")
        print(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = test_outage_endpoint()
    sys.exit(0 if success else 1)
