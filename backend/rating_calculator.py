"""
Line rating calculator using static ratings from conductor library

Note: This version uses static MVA ratings from conductor_ratings.csv.
For true dynamic IEEE 738 calculations, a detailed conductor library with
resistance and diameter parameters would be needed.
"""
import pandas as pd
import numpy as np
import logging
import math

logger = logging.getLogger(__name__)


class RatingCalculator:
    def __init__(self, data_loader):
        self.data_loader = data_loader
        # IEEE738 engine will be imported lazily to avoid hard dependency issues
        try:
            from ieee738_integration import IEEE738RatingEngine
            self._ieee_engine_cls = IEEE738RatingEngine
        except Exception:
            self._ieee_engine_cls = None

    def calculate_line_rating(self, line_data, weather_params):
        """
        Calculate rating for a single line using static conductor ratings

        Args:
            line_data: Dictionary with line information
            weather_params: Dictionary with weather conditions (currently not used for static ratings)

        Returns:
            Dictionary with rating information
        """
        # Try to compute dynamic rating using IEEE-738 engine (preferred)
        rating_amps = None
        rating_mva = None

        try:
            voltage_kv = self.data_loader.get_bus_voltage(line_data['bus0_name'])
            if voltage_kv is None:
                logger.warning(f"Line {line_data['name']}: Bus voltage for '{line_data['bus0_name']}' not found")
                return None

            # Try IEEE engine
            try:
                if self._ieee_engine_cls is not None:
                    # Merge defaults and per-request weather to ensure all keys present
                    from config import AppConfig
                    merged_weather = {**AppConfig.get_default_weather_params(), **(weather_params or {})}
                    engine = self._ieee_engine_cls(loader=self.data_loader, ambient_defaults=merged_weather)
                    ieee_result = engine.compute_line_rating(line_data)
                    if ieee_result and ieee_result.get('rating_amps') is not None:
                        rating_amps = float(ieee_result['rating_amps'])
                        # Compute MVA at the line's nominal voltage
                        rating_mva = (math.sqrt(3) * rating_amps * voltage_kv * 1000.0) / 1e6
                    else:
                        logger.debug(f"IEEE engine did not return rating for line {line_data['name']}: {ieee_result.get('error') if ieee_result else 'no result'}")
            except Exception as e:
                logger.warning(f"IEEE rating engine failed for line {line_data['name']}: {e}")
                rating_amps = None
                rating_mva = None

            # If IEEE dynamic rating not available, fall back to static conductor ratings
            if rating_amps is None:
                conductor_params = self.data_loader.get_conductor_params(line_data['conductor'])
                if conductor_params is None:
                    logger.warning(f"Line {line_data['name']}: Conductor '{line_data['conductor']}' not found")
                    return None

                if voltage_kv == 138.0:
                    rating_mva = conductor_params['RatingMVA_138']
                    rating_amps = conductor_params['RatingAmps']
                elif voltage_kv == 69.0:
                    rating_mva = conductor_params['RatingMVA_69']
                    rating_amps = conductor_params['RatingAmps']
                else:
                    # Interpolate or use closest voltage
                    logger.warning(f"Line {line_data['name']}: Unusual voltage {voltage_kv} kV, using 138kV rating")
                    rating_mva = conductor_params['RatingMVA_138']
                    rating_amps = conductor_params['RatingAmps']

            # Get nominal flow (in MW, convert to MVA)
            flow_mw = self.data_loader.get_line_flow(line_data['name'])
            # Approximate MVA assuming power factor of 0.95
            flow_mva = abs(flow_mw) / 0.95 if flow_mw != 0 else 0

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
                'branch_name': line_data.get('branch_name'),
                'conductor': line_data['conductor'],
                'MOT': line_data.get('MOT'),
                'voltage_kv': voltage_kv,
                'rating_amps': round(rating_amps, 2) if rating_amps is not None else None,
                'rating_mva': round(rating_mva, 2) if rating_mva is not None else None,
                'static_rating_mva': line_data.get('s_nom'),
                'flow_mva': round(flow_mva, 2),
                'loading_pct': round(loading_pct, 2),
                'margin_mva': round(rating_mva - flow_mva, 2) if rating_mva is not None else None,
                'stress_level': stress_level,
                'bus0': line_data.get('bus0_name'),
                'bus1': line_data.get('bus1_name')
            }

        except Exception as e:
            import traceback
            logger.error(f"Error calculating rating for {line_data.get('name')}: {str(e)}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return None

    def calculate_all_line_ratings(self, weather_params):
        """
        Calculate ratings for all lines

        Args:
            weather_params: Weather parameters (currently not used for static ratings)

        Returns:
            Dictionary with 'lines' and 'summary' keys
        """
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
            logger.warning(f"{failed_count} out of {len(lines)} lines failed to calculate")

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

    def analyze_contingency(self, outage_lines, weather_params=None):
        """
        Analyze N-1, N-2, or N-k contingency by removing one or more lines

        Args:
            outage_lines: Single line name (str) or list of line names to remove
            weather_params: Weather parameters (currently not used as flows are static)

        Returns:
            dict: Comprehensive contingency analysis results
        """
        try:
            # Import the outage simulator
            from outage_simulator import OutageSimulator

            # Convert single line to list
            if isinstance(outage_lines, str):
                outage_lines = [outage_lines]

            # Initialize simulator (will load network if not already loaded)
            simulator = OutageSimulator()

            # Run the outage simulation
            result = simulator.simulate_outage(outage_lines)

            return result

        except ImportError as e:
            logger.error(f"PyPSA not available: {e}")
            return {
                'success': False,
                'error': 'PyPSA not installed. Install with: pip install pypsa',
                'outage_lines': outage_lines
            }
        except Exception as e:
            logger.error(f"Contingency analysis failed: {e}")
            import traceback
            return {
                'success': False,
                'error': str(e),
                'trace': traceback.format_exc(),
                'outage_lines': outage_lines
            }
