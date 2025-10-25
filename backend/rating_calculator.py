"""
Dynamic line rating calculator using IEEE 738 standard
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'osu_hackathon', 'ieee738'))

import ieee738
from ieee738 import ConductorParams
import pandas as pd
import numpy as np

class RatingCalculator:
    def __init__(self, data_loader):
        self.data_loader = data_loader

    def calculate_line_rating(self, line_data, weather_params):
        """
        Calculate dynamic rating for a single line

        Args:
            line_data: Dictionary with line information
            weather_params: Dictionary with weather conditions

        Returns:
            Dictionary with rating information
        """
        # Get conductor parameters
        conductor_params = self.data_loader.get_conductor_params(line_data['conductor'])
        if conductor_params is None:
            print(f"Line {line_data['name']}: Conductor '{line_data['conductor']}' not found")
            return None

        # Get voltage
        voltage_kv = self.data_loader.get_bus_voltage(line_data['bus0_name'])
        if voltage_kv is None:
            print(f"Line {line_data['name']}: Bus voltage for '{line_data['bus0_name']}' not found")
            return None

        # Prepare IEEE738 parameters
        # Resistance is in Ohms/Mi, need to convert to Ohms/ft
        ieee_params = {
            'TLo': 25,
            'THi': 50,
            'RLo': conductor_params['RES_25C'] / 5280,  # Convert from Ohms/Mi to Ohms/ft
            'RHi': conductor_params['RES_50C'] / 5280,
            'Diameter': conductor_params['CDRAD_in'] * 2,  # Diameter = 2 * radius
            'Tc': line_data['MOT']  # Maximum Operating Temperature
        }

        # Combine with weather parameters
        all_params = {**weather_params, **ieee_params}

        # Calculate rating
        try:
            cp = ConductorParams(**all_params)
            conductor = ieee738.Conductor(cp)
            rating_amps = conductor.steady_state_thermal_rating()

            # Convert to MVA
            voltage_v = voltage_kv * 1000
            rating_mva = np.sqrt(3) * rating_amps * voltage_v / 1e6

            # Get nominal flow
            flow_mva = self.data_loader.get_line_flow(line_data['name'])

            # Calculate loading percentage
            loading_pct = (flow_mva / rating_mva * 100) if rating_mva > 0 else 0

            # Determine stress level
            if loading_pct >= 100:
                stress_level = 'critical'
            elif loading_pct >= 90:
                stress_level = 'high'
            elif loading_pct >= 60:
                stress_level = 'caution'
            else:
                stress_level = 'normal'

            return {
                'name': line_data['name'],
                'branch_name': line_data['branch_name'],
                'conductor': line_data['conductor'],
                'MOT': line_data['MOT'],
                'voltage_kv': voltage_kv,
                'rating_amps': round(rating_amps, 2),
                'rating_mva': round(rating_mva, 2),
                'static_rating_mva': line_data['s_nom'],
                'flow_mva': round(flow_mva, 2),
                'loading_pct': round(loading_pct, 2),
                'margin_mva': round(rating_mva - flow_mva, 2),
                'stress_level': stress_level,
                'bus0': line_data['bus0_name'],
                'bus1': line_data['bus1_name']
            }

        except Exception as e:
            import traceback
            print(f"Error calculating rating for {line_data['name']}: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return None

    def calculate_all_line_ratings(self, weather_params):
        """Calculate ratings for all lines"""
        lines = self.data_loader.get_all_lines()
        results = []
        failed_count = 0

        for line in lines:
            rating = self.calculate_line_rating(line, weather_params)
            if rating is not None:
                results.append(rating)
            else:
                failed_count += 1

        if failed_count > 0:
            print(f"Warning: {failed_count} out of {len(lines)} lines failed to calculate")

        # Calculate summary statistics
        if len(results) == 0:
            summary = {
                'total_lines': 0,
                'overloaded_lines': 0,
                'high_stress_lines': 0,
                'caution_lines': 0,
                'avg_loading': 0,
                'max_loading': 0,
                'critical_lines': []
            }
        else:
            df = pd.DataFrame(results)

            summary = {
                'total_lines': len(results),
                'overloaded_lines': len(df[df['loading_pct'] >= 100]),
                'high_stress_lines': len(df[df['loading_pct'] >= 90]),
                'caution_lines': len(df[df['loading_pct'] >= 60]),
                'avg_loading': round(df['loading_pct'].mean(), 2),
                'max_loading': round(df['loading_pct'].max(), 2),
                'critical_lines': df.nlargest(10, 'loading_pct')[
                    ['name', 'branch_name', 'loading_pct', 'margin_mva']
                ].to_dict('records')
            }

        return {
            'lines': results,
            'summary': summary
        }

    def find_overload_threshold(self, temp_start, temp_end, wind_speed, step=1):
        """
        Find the temperature threshold where lines start to overload

        Args:
            temp_start: Starting temperature (Celsius)
            temp_end: Ending temperature (Celsius)
            wind_speed: Wind speed (ft/sec)
            step: Temperature increment

        Returns:
            Dictionary with threshold information
        """
        temps = np.arange(temp_start, temp_end + step, step)
        results = []

        for temp in temps:
            weather_params = {
                'Ta': temp,
                'WindVelocity': wind_speed,
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

            ratings_result = self.calculate_all_line_ratings(weather_params)

            results.append({
                'temperature': temp,
                'overloaded_lines': ratings_result['summary']['overloaded_lines'],
                'high_stress_lines': ratings_result['summary']['high_stress_lines'],
                'avg_loading': ratings_result['summary']['avg_loading'],
                'max_loading': ratings_result['summary']['max_loading']
            })

        # Find first temperature where overloads occur
        first_overload_temp = None
        for r in results:
            if r['overloaded_lines'] > 0:
                first_overload_temp = r['temperature']
                break

        return {
            'temperature_range': [temp_start, temp_end],
            'wind_speed': wind_speed,
            'first_overload_temp': first_overload_temp,
            'progression': results
        }

    def analyze_contingency(self, outage_line, weather_params):
        """
        Analyze N-1 contingency by removing a line

        NOTE: This is a simplified version. Full implementation would require
        running a power flow solver (PyPSA) to redistribute flows.

        For now, we'll return the current state with the line marked as out of service.
        """
        try:
            # Import PyPSA for power flow analysis
            import pypsa

            # Load PyPSA network (would need to be implemented)
            # This is a placeholder for the actual implementation

            return {
                'outage_line': outage_line,
                'message': 'Full contingency analysis requires PyPSA integration',
                'status': 'not_implemented'
            }

        except ImportError:
            return {
                'error': 'PyPSA not available for contingency analysis',
                'outage_line': outage_line
            }
