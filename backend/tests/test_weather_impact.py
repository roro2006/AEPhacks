"""
Unit test to verify that weather parameters affect IEEE-738 rating calculations.

This test demonstrates that changing weather conditions (temperature, wind speed)
results in different line ratings as expected from IEEE 738 thermal calculations.
"""
import sys
import os

# Add ieee738 to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'osu_hackathon', 'ieee738'))

from data_loader import DataLoader
from rating_calculator import RatingCalculator


def test_temperature_affects_ratings():
    """
    Test that higher ambient temperature results in lower line ratings.

    IEEE 738 physics: Higher ambient temp reduces conductor cooling,
    lowering the maximum safe current capacity.
    """
    print("\n" + "="*70)
    print("TEST 1: Temperature Impact on Ratings")
    print("="*70)

    data_loader = DataLoader()
    calculator = RatingCalculator(data_loader)

    # Test with cool temperature (10°C)
    weather_cool = {
        'Ta': 10,  # Cool: 10°C
        'WindVelocity': 2.0,
        'WindAngleDeg': 90,
        'SunTime': 12,
        'Date': '12 Jun',
        'Emissivity': 0.8,
        'Absorptivity': 0.8,
        'Direction': 'EastWest',
        'Atmosphere': 'Clear',
        'Elevation': 1000,
        'Latitude': 27
    }

    # Test with hot temperature (40°C)
    weather_hot = {
        'Ta': 40,  # Hot: 40°C
        'WindVelocity': 2.0,
        'WindAngleDeg': 90,
        'SunTime': 12,
        'Date': '12 Jun',
        'Emissivity': 0.8,
        'Absorptivity': 0.8,
        'Direction': 'EastWest',
        'Atmosphere': 'Clear',
        'Elevation': 1000,
        'Latitude': 27
    }

    print(f"\nScenario A: Cool weather (Ta={weather_cool['Ta']}°C)")
    results_cool = calculator.calculate_all_line_ratings(weather_cool)

    print(f"Scenario B: Hot weather (Ta={weather_hot['Ta']}°C)")
    results_hot = calculator.calculate_all_line_ratings(weather_hot)

    # Extract ratings for comparison
    avg_loading_cool = results_cool['summary']['avg_loading']
    avg_loading_hot = results_hot['summary']['avg_loading']

    max_loading_cool = results_cool['summary']['max_loading']
    max_loading_hot = results_hot['summary']['max_loading']

    print(f"\nResults:")
    print(f"  Cool (10°C): Avg loading = {avg_loading_cool:.2f}%, Max loading = {max_loading_cool:.2f}%")
    print(f"  Hot (40°C):  Avg loading = {avg_loading_hot:.2f}%, Max loading = {max_loading_hot:.2f}%")

    # Higher temperature should result in higher loading % (because ratings are lower)
    # Loading % = Flow / Rating * 100
    # If rating decreases (due to heat), loading % increases
    loading_increase = avg_loading_hot - avg_loading_cool
    print(f"\n  Loading increase from heat: {loading_increase:.2f}%")

    # Assert that hot weather increases loading (ratings decrease)
    assert avg_loading_hot > avg_loading_cool, \
        f"Expected higher loading in hot weather, but got cool={avg_loading_cool:.2f}% vs hot={avg_loading_hot:.2f}%"

    # Assert the change is significant (at least 3% increase in loading)
    assert loading_increase >= 3.0, \
        f"Expected at least 3% loading increase, got {loading_increase:.2f}%"

    print(f"\n  ✓ PASS: Hot weather correctly increases loading (reduces ratings)")
    return True


def test_wind_speed_affects_ratings():
    """
    Test that higher wind speed results in higher line ratings.

    IEEE 738 physics: Higher wind speed improves convective cooling,
    increasing the maximum safe current capacity.
    """
    print("\n" + "="*70)
    print("TEST 2: Wind Speed Impact on Ratings")
    print("="*70)

    data_loader = DataLoader()
    calculator = RatingCalculator(data_loader)

    # Test with low wind (0.5 ft/s - calm conditions)
    weather_calm = {
        'Ta': 25,
        'WindVelocity': 0.5,  # Calm: 0.5 ft/s
        'WindAngleDeg': 90,
        'SunTime': 12,
        'Date': '12 Jun',
        'Emissivity': 0.8,
        'Absorptivity': 0.8,
        'Direction': 'EastWest',
        'Atmosphere': 'Clear',
        'Elevation': 1000,
        'Latitude': 27
    }

    # Test with high wind (10.0 ft/s - windy conditions)
    weather_windy = {
        'Ta': 25,
        'WindVelocity': 10.0,  # Windy: 10.0 ft/s
        'WindAngleDeg': 90,
        'SunTime': 12,
        'Date': '12 Jun',
        'Emissivity': 0.8,
        'Absorptivity': 0.8,
        'Direction': 'EastWest',
        'Atmosphere': 'Clear',
        'Elevation': 1000,
        'Latitude': 27
    }

    print(f"\nScenario A: Calm conditions (Wind={weather_calm['WindVelocity']} ft/s)")
    results_calm = calculator.calculate_all_line_ratings(weather_calm)

    print(f"Scenario B: Windy conditions (Wind={weather_windy['WindVelocity']} ft/s)")
    results_windy = calculator.calculate_all_line_ratings(weather_windy)

    # Extract ratings for comparison
    avg_loading_calm = results_calm['summary']['avg_loading']
    avg_loading_windy = results_windy['summary']['avg_loading']

    max_loading_calm = results_calm['summary']['max_loading']
    max_loading_windy = results_windy['summary']['max_loading']

    print(f"\nResults:")
    print(f"  Calm (0.5 ft/s):  Avg loading = {avg_loading_calm:.2f}%, Max loading = {max_loading_calm:.2f}%")
    print(f"  Windy (10.0 ft/s): Avg loading = {avg_loading_windy:.2f}%, Max loading = {max_loading_windy:.2f}%")

    # Higher wind should result in lower loading % (because ratings are higher)
    loading_decrease = avg_loading_calm - avg_loading_windy
    print(f"\n  Loading decrease from wind: {loading_decrease:.2f}%")

    # Assert that windy weather decreases loading (ratings increase)
    assert avg_loading_windy < avg_loading_calm, \
        f"Expected lower loading in windy weather, but got calm={avg_loading_calm:.2f}% vs windy={avg_loading_windy:.2f}%"

    # Assert the change is significant (at least 5% decrease in loading)
    assert loading_decrease >= 5.0, \
        f"Expected at least 5% loading decrease, got {loading_decrease:.2f}%"

    print(f"\n  ✓ PASS: High wind correctly decreases loading (increases ratings)")
    return True


def test_specific_line_rating_changes():
    """
    Test that a specific line's rating changes with different weather.
    """
    print("\n" + "="*70)
    print("TEST 3: Specific Line Rating Verification")
    print("="*70)

    data_loader = DataLoader()
    calculator = RatingCalculator(data_loader)

    weather_default = {
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
        'Latitude': 27
    }

    weather_extreme = {
        'Ta': 45,  # Very hot
        'WindVelocity': 0.5,  # Very calm
        'WindAngleDeg': 90,
        'SunTime': 14,
        'Date': '21 Jun',  # Summer peak
        'Emissivity': 0.8,
        'Absorptivity': 0.8,
        'Direction': 'EastWest',
        'Atmosphere': 'Clear',
        'Elevation': 1000,
        'Latitude': 27
    }

    print(f"\nScenario A: Default conditions (Ta=25°C, Wind=2.0 ft/s)")
    results_default = calculator.calculate_all_line_ratings(weather_default)

    print(f"Scenario B: Extreme heat (Ta=45°C, Wind=0.5 ft/s)")
    results_extreme = calculator.calculate_all_line_ratings(weather_extreme)

    # Find first line in both results
    if results_default['lines'] and results_extreme['lines']:
        line_default = results_default['lines'][0]
        line_extreme = results_extreme['lines'][0]

        print(f"\nLine: {line_default['name']}")
        print(f"  Default:  Rating = {line_default['rating_mva']:.2f} MVA, Loading = {line_default['loading_pct']:.2f}%")
        print(f"  Extreme:  Rating = {line_extreme['rating_mva']:.2f} MVA, Loading = {line_extreme['loading_pct']:.2f}%")

        rating_decrease = ((line_default['rating_mva'] - line_extreme['rating_mva']) / line_default['rating_mva']) * 100
        print(f"\n  Rating decrease: {rating_decrease:.1f}%")

        # Assert rating decreased in extreme heat
        assert line_extreme['rating_mva'] < line_default['rating_mva'], \
            "Expected lower rating in extreme heat"

        # Assert loading increased in extreme heat
        assert line_extreme['loading_pct'] > line_default['loading_pct'], \
            "Expected higher loading in extreme heat"

        print(f"\n  ✓ PASS: Line rating and loading correctly reflect weather changes")

    return True


def run_all_tests():
    """Run all weather impact tests."""
    print("\n" + "="*70)
    print("WEATHER PARAMETER IMPACT VERIFICATION TESTS")
    print("="*70)
    print("\nThese tests verify that weather parameters passed to the API")
    print("actually affect the IEEE 738 thermal rating calculations.")

    tests = [
        ("Temperature Impact", test_temperature_affects_ratings),
        ("Wind Speed Impact", test_wind_speed_affects_ratings),
        ("Specific Line Changes", test_specific_line_rating_changes),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n  ✗ FAIL: {e}")
            failed += 1
        except Exception as e:
            print(f"\n  ✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "="*70)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("="*70)

    if failed == 0:
        print("\n✓✓✓ ALL TESTS PASSED ✓✓✓")
        print("\nWeather parameters are correctly affecting IEEE 738 calculations!")
        return 0
    else:
        print(f"\n✗✗✗ {failed} TEST(S) FAILED ✗✗✗")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
