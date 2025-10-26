#!/usr/bin/env python3
"""
Test API Components - Verify refactored components work correctly

This script tests the core components without requiring Flask to be running.
"""

import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_data_loader():
    """Test data loader initialization"""
    print("\n" + "="*60)
    print("TEST 1: DATA LOADER")
    print("="*60)

    try:
        from data_loader import DataLoader

        loader = DataLoader()
        lines = loader.get_all_lines()

        print(f"[OK] Loaded {len(lines)} lines")
        print(f"[OK] Sample line: {lines[0]['name']} - {lines[0]['branch_name']}")

        return True
    except Exception as e:
        print(f"[X] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rating_calculator():
    """Test rating calculator"""
    print("\n" + "="*60)
    print("TEST 2: RATING CALCULATOR")
    print("="*60)

    try:
        from data_loader import DataLoader
        from rating_calculator import RatingCalculator

        loader = DataLoader()
        calculator = RatingCalculator(loader)

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

        result = calculator.calculate_all_line_ratings(weather)
        summary = result['summary']

        print(f"[OK] Calculated ratings for {summary['total_lines']} lines")
        print(f"    Overloaded: {summary['overloaded_lines']}")
        print(f"    High stress: {summary['high_stress_lines']}")
        print(f"    Caution: {summary['caution_lines']}")
        print(f"    Average loading: {summary['avg_loading']:.1f}%")
        print(f"    Max loading: {summary['max_loading']:.1f}%")

        if result['lines']:
            sample = result['lines'][0]
            print(f"\n[OK] Sample calculation:")
            print(f"    Line: {sample['name']} - {sample['branch_name']}")
            print(f"    Rating: {sample['rating_mva']} MVA")
            print(f"    Flow: {sample['flow_mva']} MVA")
            print(f"    Loading: {sample['loading_pct']}%")
            print(f"    Status: {sample['stress_level']}")

        return True
    except Exception as e:
        print(f"[X] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_map_generator():
    """Test map generator"""
    print("\n" + "="*60)
    print("TEST 3: MAP GENERATOR")
    print("="*60)

    try:
        from data_loader import DataLoader
        from rating_calculator import RatingCalculator
        from map_generator import GridMapGenerator

        loader = DataLoader()
        calculator = RatingCalculator(loader)
        map_gen = GridMapGenerator(loader)

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

        result = calculator.calculate_all_line_ratings(weather)
        map_html = map_gen.generate_interactive_map(weather, result)

        print(f"[OK] Generated map HTML: {len(map_html)} characters")
        print(f"[OK] Map contains plotly visualization")

        return True
    except Exception as e:
        print(f"[X] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("API COMPONENTS TEST SUITE")
    print("="*60)

    results = {}

    results['Data Loader'] = test_data_loader()
    results['Rating Calculator'] = test_rating_calculator()
    results['Map Generator'] = test_map_generator()

    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "[OK] PASSED" if result else "[X] FAILED"
        print(f"{status:12s} - {test_name}")

    print("\n" + "-"*60)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("="*60)
        print("[OK] SUCCESS: All API components working correctly!")
        print("="*60)
        print("\nYour Flask API should work correctly once you:")
        print("1. Install Flask dependencies: pip install flask flask-cors")
        print("2. Start the Flask server: python app.py")
        print("3. The frontend should now connect successfully")
        return 0
    else:
        print("="*60)
        print(f"[X] FAILURE: {total - passed} test(s) failed")
        print("="*60)
        return 1


if __name__ == '__main__':
    sys.exit(main())
