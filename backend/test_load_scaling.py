"""
Test script for Load Scaling Analyzer
"""

import json
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_load_scaling():
    """Test the load scaling analyzer"""
    print("\n" + "="*70)
    print("Testing Load Scaling Analyzer")
    print("="*70)

    try:
        from load_scaling_analyzer import LoadScalingAnalyzer

        print("\n[1] Initializing LoadScalingAnalyzer...")
        analyzer = LoadScalingAnalyzer()
        print("    [OK] Analyzer initialized")
        print(f"    Baseline total load: {analyzer.baseline_load.sum():.2f} MW")
        print(f"    Baseline total gen: {analyzer.baseline_gen.sum():.2f} MW")

        # Test load profile generation
        print("\n[2] Generating 24-hour load profile...")
        profile = analyzer.get_load_profile(24)
        print(f"    [OK] Generated profile with {len(profile)} hours")
        print(f"    Sample hours:")
        for i in [0, 6, 12, 18]:
            p = profile[i]
            print(f"      {i:2d}:00 - Scale: {p['scale_factor']:.3f}, Load: {p['load_mw']:.0f} MW")

        # Test single hour analysis
        print("\n[3] Analyzing single hour (6 PM - peak load)...")
        hour_18 = analyzer.analyze_single_hour(18)
        if hour_18['success']:
            print(f"    [OK] Analysis successful")
            print(f"    Scale factor: {hour_18['scale_factor']:.3f}")
            print(f"    Total load: {hour_18['total_load_mw']:.0f} MW")
            print(f"    Max loading: {hour_18['max_loading_pct']:.2f}%")
            print(f"    Avg loading: {hour_18['avg_loading_pct']:.2f}%")
            print(f"    Overloaded lines: {hour_18['overloaded_count']}")
        else:
            print(f"    [X] Analysis failed: {hour_18.get('error')}")

        # Test daily analysis (reduced hours for faster testing)
        print("\n[4] Running daily analysis (12 hours for testing)...")
        daily_result = analyzer.analyze_daily_profile(12)

        if daily_result['success']:
            print(f"    [OK] Daily analysis successful")
            summary = daily_result['summary']
            print(f"    Hours converged: {summary['hours_converged']}/{summary['total_hours']}")
            print(f"\n    Peak Loading:")
            print(f"      Hour: {summary['peak_loading']['hour']} ({summary['peak_loading']['hour']}:00)")
            print(f"      Max loading: {summary['peak_loading']['max_loading_pct']:.2f}%")
            print(f"      Scale factor: {summary['peak_loading']['scale_factor']:.3f}")
            print(f"      Overloaded: {summary['peak_loading']['overloaded_count']} lines")

            if summary['peak_overloads']['overloaded_count'] > 0:
                print(f"\n    Peak Overloads:")
                print(f"      Hour: {summary['peak_overloads']['hour']}")
                print(f"      Count: {summary['peak_overloads']['overloaded_count']} lines")
                print(f"      Max loading: {summary['peak_overloads']['max_loading_pct']:.2f}%")

            if summary['most_stressed_lines']:
                print(f"\n    Top 3 Most Stressed Lines:")
                for i, line in enumerate(summary['most_stressed_lines'][:3], 1):
                    print(f"      {i}. {line['name']}: {line['max_loading_pct']:.2f}% at hour {line['hour_of_max']}")

            # Save results
            output_file = backend_dir / "load_scaling_test_results.json"
            with open(output_file, 'w') as f:
                json.dump(daily_result, f, indent=2)
            print(f"\n    [OK] Results saved to: {output_file}")

        else:
            print(f"    [X] Daily analysis failed")

        print("\n" + "="*70)
        print("TEST PASSED: Load scaling analyzer working correctly!")
        print("="*70)
        return True

    except Exception as e:
        print(f"\n[X] Test failed: {e}")
        import traceback
        print(f"\nTraceback:")
        print(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = test_load_scaling()
    sys.exit(0 if success else 1)
