"""
Test script to verify contingency analysis JSON serialization fix
"""

import json
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_contingency_json_serialization():
    """Test that contingency analysis results can be JSON serialized"""
    print("\n" + "="*70)
    print("Testing Contingency Analysis JSON Serialization Fix")
    print("="*70)

    try:
        # Import after path is set
        from outage_simulator import OutageSimulator

        print("\n[1] Initializing OutageSimulator...")
        simulator = OutageSimulator()
        print("    [OK] Simulator initialized successfully")

        # Get available lines
        available_lines = simulator.get_available_lines()
        if not available_lines:
            print("    [X] No lines available for testing")
            return False

        # Pick first line for testing
        test_line = available_lines[0]['name']
        print(f"\n[2] Testing N-1 contingency for line: {test_line}")

        # Run contingency analysis
        result = simulator.simulate_outage([test_line])
        print(f"    [OK] Contingency simulation completed")
        print(f"    Success: {result.get('success')}")
        print(f"    Result keys: {list(result.keys())}")

        # Try to serialize to JSON
        print("\n[3] Testing JSON serialization...")
        try:
            json_str = json.dumps(result, indent=2)
            print("    [OK] JSON serialization successful!")

            # Verify it can be parsed back
            parsed = json.loads(json_str)
            print("    [OK] JSON deserialization successful!")

            # Show some key metrics
            if result.get('success'):
                metrics = result.get('metrics', {})
                print(f"\n[4] Contingency Results:")
                print(f"    Total lines: {metrics.get('total_lines', 0)}")
                print(f"    Outaged lines: {metrics.get('outaged_lines_count', 0)}")
                print(f"    Overloaded lines: {metrics.get('overloaded_count', 0)}")
                print(f"    High stress lines: {metrics.get('high_stress_count', 0)}")
                print(f"    Max loading: {metrics.get('max_loading_pct', 0):.2f}%")
                print(f"    Avg loading: {metrics.get('avg_loading_pct', 0):.2f}%")

                # Check power flow info types
                pf_info = result.get('power_flow_info', {})
                print(f"\n[5] Power Flow Info Types:")
                for key, value in pf_info.items():
                    print(f"    {key}: {type(value).__name__} = {value}")

            print("\n" + "="*70)
            print("TEST PASSED: Contingency analysis results are JSON serializable!")
            print("="*70)
            return True

        except TypeError as e:
            print(f"    [X] JSON serialization FAILED: {e}")
            print(f"\n    Error details:")
            print(f"    Type of result: {type(result)}")

            # Find problematic types
            def find_non_json_types(obj, path="root"):
                """Recursively find non-JSON-serializable types"""
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        find_non_json_types(value, f"{path}.{key}")
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        find_non_json_types(item, f"{path}[{i}]")
                else:
                    # Try to JSON serialize this value
                    try:
                        json.dumps(obj)
                    except TypeError:
                        print(f"    Non-serializable at {path}: {type(obj).__name__} = {obj}")

            print("\n    Scanning for non-serializable types:")
            find_non_json_types(result)

            print("\n" + "="*70)
            print("TEST FAILED: JSON serialization error")
            print("="*70)
            return False

    except Exception as e:
        print(f"\n[X] Test failed with error: {e}")
        import traceback
        print(f"\nTraceback:")
        print(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = test_contingency_json_serialization()
    sys.exit(0 if success else 1)
