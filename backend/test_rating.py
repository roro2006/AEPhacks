"""
Quick test script to see where the rating calculation fails
"""
import sys
import os

# Add ieee738 to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'osu_hackathon', 'ieee738'))

print("Step 1: Importing modules...")
try:
    from data_loader import DataLoader
    print("✓ DataLoader imported")
except Exception as e:
    print(f"✗ DataLoader import failed: {e}")
    sys.exit(1)

try:
    from rating_calculator import RatingCalculator
    print("✓ RatingCalculator imported")
except Exception as e:
    print(f"✗ RatingCalculator import failed: {e}")
    sys.exit(1)

print("\nStep 2: Loading data...")
try:
    data_loader = DataLoader()
    print(f"✓ Data loaded: {len(data_loader.lines_df)} lines")
except Exception as e:
    print(f"✗ Data loading failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nStep 3: Creating calculator...")
try:
    calculator = RatingCalculator(data_loader)
    print("✓ Calculator created")
except Exception as e:
    print(f"✗ Calculator creation failed: {e}")
    sys.exit(1)

print("\nStep 4: Calculating ratings...")
weather_params = {
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

try:
    results = calculator.calculate_all_line_ratings(weather_params)
    print(f"✓ Ratings calculated: {len(results['lines'])} lines")
    print(f"✓ Summary: {results['summary']['total_lines']} total, {results['summary']['overloaded_lines']} overloaded")
    print("\n✓✓✓ All tests passed! ✓✓✓")
except Exception as e:
    print(f"✗ Rating calculation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
