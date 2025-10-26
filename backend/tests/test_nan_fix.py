#!/usr/bin/env python3
"""
Test NaN Fix - Verify JSON responses don't contain NaN values
"""

from data_loader import DataLoader
from rating_calculator import RatingCalculator
import json
import sys


def test_nan_handling():
    """Test that NaN values are properly converted to null in JSON"""

    print("\n" + "="*60)
    print("NaN HANDLING TEST")
    print("="*60)

    try:
        # Initialize components
        loader = DataLoader()
        calculator = RatingCalculator(loader)

        # Test weather parameters
        weather = {
            'Ta': 25,
            'WindVelocity': 2.0,
            'WindAngleDeg': 90,
            'SunTime': 12,
            'Date': '12 Jun',
            'Emissivity': 0.8,
            'Absorptivity': 0.8,
            'Direction': 'EastWest',
            'Atmosphere': 'Clear',
            'Elevation': 1000,
            'Latitude': 21
        }

        # Calculate ratings
        result = calculator.calculate_all_line_ratings(weather)

        print(f"\n[OK] Calculated ratings for {len(result['lines'])} lines")

        # Test JSON serialization
        try:
            json_str = json.dumps(result)
            print("[OK] Full result serializes to valid JSON")

            # Check for NaN in the string
            if 'NaN' in json_str or 'nan' in json_str:
                print("[X] FAIL: JSON contains NaN values!")
                return False
            else:
                print("[OK] No NaN values in JSON")

        except TypeError as e:
            print(f"[X] FAIL: JSON serialization error: {e}")
            return False

        # Specifically check Line L23 (known to have NaN in bus1_name)
        line_23 = next((line for line in result['lines'] if line['name'] == 'L23'), None)

        if line_23:
            print(f"\n[OK] Found Line L23:")
            print(f"    bus0: {line_23.get('bus0')}")
            print(f"    bus1: {line_23.get('bus1')}")

            if line_23.get('bus1') is None:
                print("[OK] NaN value properly converted to None/null")
            else:
                print(f"[!] bus1 is: {line_23.get('bus1')} (type: {type(line_23.get('bus1'))})")

        # Parse JSON to verify it's valid
        try:
            parsed = json.loads(json_str)
            print(f"\n[OK] JSON parses successfully")
            print(f"[OK] Parsed data has {len(parsed['lines'])} lines")

            # Check the parsed L23
            parsed_l23 = next((line for line in parsed['lines'] if line['name'] == 'L23'), None)
            if parsed_l23:
                if parsed_l23.get('bus1') is None:
                    print("[OK] Parsed L23.bus1 is null (not NaN)")
                else:
                    print(f"[!] Parsed L23.bus1 is: {parsed_l23.get('bus1')}")

        except json.JSONDecodeError as e:
            print(f"[X] FAIL: JSON parsing error: {e}")
            return False

        print("\n" + "="*60)
        print("[OK] SUCCESS: All NaN values properly handled!")
        print("="*60)
        print("\nThe Flask API should now work correctly with the frontend.")
        print("No more 'Unexpected token NaN' errors should occur.")

        return True

    except Exception as e:
        print(f"\n[X] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_nan_handling()
    sys.exit(0 if success else 1)
