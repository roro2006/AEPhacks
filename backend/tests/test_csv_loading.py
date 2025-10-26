#!/usr/bin/env python3
"""
CSV Data Loading Test Script

This script performs comprehensive testing of the CSV data loading infrastructure.
Run this to verify that all components are working correctly after setup or updates.

Usage:
    python test_csv_loading.py
    python test_csv_loading.py --verbose
    python test_csv_loading.py --validate-only
"""

import sys
import argparse
import logging
from typing import Tuple

# Import our modules
from csv_data_loader import CSVDataLoader
from data_validator import validate_csv_data_quality, DataValidator
from config import DataConfig, APIConfig, print_configuration_status
from data_models import DataLoadError, DataValidationError


def setup_logging(verbose: bool = False):
    """Configure logging for the test script."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def test_configuration() -> bool:
    """Test 1: Configuration and file paths."""
    print("\n" + "="*80)
    print("TEST 1: CONFIGURATION")
    print("="*80)

    try:
        # Print configuration
        print_configuration_status()

        # Check for missing files
        missing = DataConfig.get_missing_files()
        if missing:
            print(f"\n[!] WARNING: Missing {len(missing)} required files:")
            for f in missing:
                print(f"  - {f}")
            return False

        print("\n[OK] All required files present")
        return True

    except Exception as e:
        print(f"\n[X] Configuration test failed: {e}")
        return False


def test_basic_loading(loader: CSVDataLoader) -> bool:
    """Test 2: Basic CSV data loading."""
    print("\n" + "="*80)
    print("TEST 2: BASIC DATA LOADING")
    print("="*80)

    try:
        # Load lines
        print("\nLoading transmission lines...")
        lines = loader.get_all_lines(validate=False)
        print(f"[OK] Loaded {len(lines)} lines")

        if len(lines) == 0:
            print("[X] No lines loaded - check lines.csv")
            return False

        # Load buses
        print("\nLoading buses...")
        buses = loader.get_all_buses(validate=False)
        print(f"[OK] Loaded {len(buses)} buses")

        if len(buses) == 0:
            print("[X] No buses loaded - check buses.csv")
            return False

        # Load power flows
        print("\nLoading power flows...")
        flows = loader.get_all_power_flows(validate=False)
        print(f"[OK] Loaded {len(flows)} power flows")

        # Load conductors
        print("\nLoading conductor parameters...")
        conductors = loader.get_all_conductor_params(validate=False)
        print(f"[OK] Loaded {len(conductors)} conductor types")

        if len(conductors) == 0:
            print("[X] No conductors loaded - check conductor_ratings.csv")
            return False

        # Load GeoJSON
        print("\nLoading GeoJSON data...")
        try:
            lines_geojson = loader.get_lines_geojson()
            print(f"[OK] Loaded lines GeoJSON with {len(lines_geojson['features'])} features")
        except DataLoadError as e:
            print(f"[!] Could not load lines GeoJSON: {e}")

        try:
            buses_geojson = loader.get_buses_geojson()
            print(f"[OK] Loaded buses GeoJSON with {len(buses_geojson['features'])} features")
        except DataLoadError as e:
            print(f"[!] Could not load buses GeoJSON: {e}")

        return True

    except Exception as e:
        print(f"\n[X] Basic loading test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_validation(loader: CSVDataLoader) -> bool:
    """Test 3: Data validation with Pydantic models."""
    print("\n" + "="*80)
    print("TEST 3: DATA VALIDATION")
    print("="*80)

    try:
        # Validate lines
        print("\nValidating transmission lines...")
        lines = loader.get_all_lines(validate=True)
        print(f"[OK] {len(lines)} lines validated successfully")

        # Validate buses
        print("\nValidating buses...")
        buses = loader.get_all_buses(validate=True)
        print(f"[OK] {len(buses)} buses validated successfully")

        # Validate power flows
        print("\nValidating power flows...")
        flows = loader.get_all_power_flows(validate=True)
        print(f"[OK] {len(flows)} power flows validated successfully")

        # Validate conductors
        print("\nValidating conductor parameters...")
        conductors = loader.get_all_conductor_params(validate=True)
        print(f"[OK] {len(conductors)} conductor types validated successfully")

        return True

    except DataValidationError as e:
        print(f"\n[X] Validation failed: {e}")
        return False
    except Exception as e:
        print(f"\n[X] Validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_quality(loader: CSVDataLoader) -> bool:
    """Test 4: Comprehensive data quality validation."""
    print("\n" + "="*80)
    print("TEST 4: DATA QUALITY VALIDATION")
    print("="*80)

    try:
        is_valid, summary = validate_csv_data_quality(loader)
        print(summary)

        return is_valid

    except Exception as e:
        print(f"\n[X] Data quality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_specific_operations(loader: CSVDataLoader) -> bool:
    """Test 5: Specific data access operations."""
    print("\n" + "="*80)
    print("TEST 5: SPECIFIC OPERATIONS")
    print("="*80)

    try:
        # Test get_line_data
        print("\nTesting get_line_data('L0')...")
        line = loader.get_line_data('L0')
        if line:
            print(f"[OK] Line L0: {line.branch_name}")
            print(f"  Capacity: {line.s_nom} MVA")
            print(f"  Conductor: {line.conductor}")
        else:
            print("[X] Line L0 not found")
            return False

        # Test get_bus_data
        print("\nTesting get_bus_data...")
        all_buses = loader.get_all_buses(validate=False)
        if all_buses:
            first_bus_name = all_buses[0]['BusName']
            bus = loader.get_bus_data(first_bus_name)
            if bus:
                print(f"[OK] Bus {bus.BusName}: {bus.v_nom} kV")
            else:
                print(f"[X] Bus {first_bus_name} not found")
                return False

        # Test get_power_flow
        print("\nTesting get_power_flow('L0')...")
        flow = loader.get_power_flow('L0')
        if flow:
            print(f"[OK] Flow for L0: {flow.p0_nominal} MW")
        else:
            print("[!] No flow data for L0")

        # Test get_complete_line_info
        print("\nTesting get_complete_line_info('L0')...")
        info = loader.get_complete_line_info('L0')
        if info:
            print(f"[OK] Complete info retrieved:")
            print(f"  Line data: {info['line_data'].name}")
            print(f"  Power flow: {'Present' if info['power_flow'] else 'Missing'}")
            print(f"  Conductor: {'Present' if info['conductor_params'] else 'Missing'}")
            print(f"  Geometry: {'Present' if info['geometry'] else 'Missing'}")
        else:
            print("[X] Could not get complete info for L0")
            return False

        # Test get_data_statistics
        print("\nTesting get_data_statistics...")
        stats = loader.get_data_statistics()
        print(f"[OK] Statistics:")
        print(f"  Lines: {stats['line_count']}")
        print(f"  Buses: {stats['bus_count']}")
        print(f"  Flows: {stats['flow_count']}")
        print(f"  Conductors: {stats['conductor_count']}")
        print(f"  Cache enabled: {stats['cache_enabled']}")
        print(f"  Cached items: {stats['cached_items']}")

        return True

    except Exception as e:
        print(f"\n[X] Specific operations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling() -> bool:
    """Test 6: Error handling capabilities."""
    print("\n" + "="*80)
    print("TEST 6: ERROR HANDLING")
    print("="*80)

    try:
        loader = CSVDataLoader()

        # Test non-existent line
        print("\nTesting handling of non-existent line...")
        line = loader.get_line_data('NONEXISTENT')
        if line is None:
            print("[OK] Correctly returns None for non-existent line")
        else:
            print("[X] Should return None for non-existent line")
            return False

        # Test non-existent bus
        print("\nTesting handling of non-existent bus...")
        bus = loader.get_bus_data('NONEXISTENT')
        if bus is None:
            print("[OK] Correctly returns None for non-existent bus")
        else:
            print("[X] Should return None for non-existent bus")
            return False

        # Test cache operations
        print("\nTesting cache operations...")
        loader.clear_cache()
        print("[OK] Cache cleared successfully")

        stats_before = loader.get_data_statistics()
        print(f"  Cached items before reload: {stats_before['cached_items']}")

        # Reload data
        loader.get_all_lines()
        stats_after = loader.get_data_statistics()
        print(f"  Cached items after reload: {stats_after['cached_items']}")
        print("[OK] Cache operations working correctly")

        return True

    except Exception as e:
        print(f"\n[X] Error handling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration() -> bool:
    """Test 7: Integration with existing components."""
    print("\n" + "="*80)
    print("TEST 7: INTEGRATION WITH EXISTING COMPONENTS")
    print("="*80)

    try:
        # Test DataLoader (legacy wrapper)
        print("\nTesting legacy DataLoader wrapper...")
        from data_loader import DataLoader

        loader = DataLoader()
        lines = loader.get_all_lines()
        print(f"[OK] Legacy DataLoader loaded {len(lines)} lines")

        # Test specific methods
        line_info = loader.get_line_info('L0')
        if line_info:
            print(f"[OK] get_line_info working: {line_info['name']}")
        else:
            print("[X] get_line_info failed")
            return False

        # Test property accessors
        if loader.lines_df is not None and not loader.lines_df.empty:
            print(f"[OK] lines_df property: {len(loader.lines_df)} records")
        else:
            print("[X] lines_df property failed")
            return False

        print("\n[OK] All integration tests passed")
        return True

    except Exception as e:
        print(f"\n[X] Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_summary(results: dict):
    """Print test summary."""
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "[OK] PASSED" if result else "[X] FAILED"
        print(f"{status:10s} - {test_name}")

    print("\n" + "-"*80)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("="*80)
        print("SUCCESS: All tests passed! [OK]")
        print("="*80)
        return True
    else:
        print("="*80)
        print(f"FAILURE: {total - passed} test(s) failed [X]")
        print("="*80)
        return False


def main():
    """Run all tests."""
    parser = argparse.ArgumentParser(description='Test CSV data loading infrastructure')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose logging')
    parser.add_argument('--validate-only', action='store_true',
                        help='Only run validation tests')
    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    print("\n" + "="*80)
    print("CSV DATA LOADING - COMPREHENSIVE TEST SUITE")
    print("="*80)

    # Initialize loader
    try:
        loader = CSVDataLoader()
    except Exception as e:
        print(f"\n[X] FATAL: Could not initialize CSVDataLoader: {e}")
        return 1

    # Run tests
    results = {}

    if not args.validate_only:
        results['Configuration'] = test_configuration()
        results['Basic Loading'] = test_basic_loading(loader)
        results['Data Validation'] = test_data_validation(loader)

    results['Data Quality'] = test_data_quality(loader)

    if not args.validate_only:
        results['Specific Operations'] = test_specific_operations(loader)
        results['Error Handling'] = test_error_handling()
        results['Integration'] = test_integration()

    # Print summary
    success = print_summary(results)

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
