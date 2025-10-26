"""
Load Scaling Analyzer

Analyzes how load/generation changes throughout the day stress the transmission system.
Based on pypsa_load_scale.ipynb - uses sine wave to approximate daily load variations.

Assumptions:
- Load min/max at 6am/6pm
- Values in model are nominal - peaks are 10% below/above nominal
- Generation scales proportionally with load to maintain power balance
"""

import pypsa
import numpy as np
import logging
from typing import Dict, List, Any
from pathlib import Path
from config import DataConfig

logger = logging.getLogger(__name__)


def convert_numpy_types(obj):
    """
    Recursively convert numpy types to native Python types for JSON serialization.
    """
    import pandas as pd

    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return convert_numpy_types(obj.tolist())
    elif isinstance(obj, (pd.Series, pd.DataFrame)):
        return convert_numpy_types(obj.to_dict())
    elif pd.isna(obj):
        return None
    else:
        return obj


class LoadScalingAnalyzer:
    """
    Analyzes transmission system stress under varying load/generation conditions
    throughout the day.
    """

    def __init__(self):
        """Initialize the load scaling analyzer with PyPSA network."""
        self.network = None
        self.baseline_load = None
        self.baseline_gen = None
        self._load_network()

    def _load_network(self):
        """Load PyPSA network from CSV files."""
        try:
            logger.info("Loading PyPSA network for load scaling analysis...")
            self.network = pypsa.Network()

            # Import from CSV folder
            csv_folder = str(DataConfig.DATA_DIR)
            self.network.import_from_csv_folder(csv_folder)

            logger.info(
                f"Network loaded: {len(self.network.lines)} lines, "
                f"{len(self.network.buses)} buses, "
                f"{len(self.network.generators)} generators, "
                f"{len(self.network.loads)} loads"
            )

            # Store baseline values
            self.baseline_load = self.network.loads['p_set'].copy()
            self.baseline_gen = self.network.generators['p_set'].copy()

            logger.info(f"Baseline total load: {self.baseline_load.sum():.2f} MW")
            logger.info(f"Baseline total gen: {self.baseline_gen.sum():.2f} MW")

        except Exception as e:
            logger.error(f"Error loading PyPSA network: {e}")
            raise RuntimeError(f"Failed to load PyPSA network: {e}")

    def _generate_daily_profile(self, hours: int = 24) -> List[float]:
        """
        Generate daily load profile using sine wave.

        Args:
            hours: Number of hours in the profile (default 24)

        Returns:
            List of scaling factors (0.9 to 1.1)
        """
        # Generate time points
        x = np.arange(hours)
        f = 1 / hours  # Frequency for one cycle per day

        # Sine wave parameters
        offset = 1.0   # Nominal value
        A = 0.1        # Amplitude (±10%)
        C = 2 * np.pi / 2  # Phase shift (min at 6am, max at 6pm)

        # Generate profile
        profile = A * np.sin(2 * np.pi * f * x + C) + offset

        return profile.tolist()

    def _run_power_flow(self) -> Dict[str, Any]:
        """
        Run power flow analysis.

        Returns:
            dict: Power flow convergence info
        """
        try:
            info = self.network.pf()
            converged = bool(info.converged.any().any())
            max_error = float(info.error.max().max())

            logger.debug(f"Power flow converged: {converged}, max error: {max_error:.2e}")

            return {
                'converged': converged,
                'max_error': max_error
            }
        except Exception as e:
            logger.error(f"Power flow failed: {e}")
            raise

    def _scale_network(self, scale_factor: float):
        """
        Scale loads and generators by the given factor.

        Args:
            scale_factor: Multiplier for load/gen (e.g., 1.1 = 110% of nominal)
        """
        # Reset to baseline
        self.network.loads['p_set'] = self.baseline_load.copy()
        self.network.loads['q_set'] = 0.0  # Reactive power set to 0 in base case
        self.network.generators['p_set'] = self.baseline_gen.copy()
        self.network.generators['q_set'] = 0.0

        # Apply scaling
        self.network.loads['p_set'] = scale_factor * self.network.loads['p_set']
        self.network.loads['q_set'] = scale_factor * self.network.loads['q_set']
        self.network.generators['p_set'] = scale_factor * self.network.generators['p_set']
        self.network.generators['q_set'] = scale_factor * self.network.generators['q_set']

    def _analyze_hour(self, hour: int, scale_factor: float) -> Dict[str, Any]:
        """
        Analyze network at a specific hour with given scaling.

        Args:
            hour: Hour of day (0-23)
            scale_factor: Load/gen scaling factor

        Returns:
            dict: Analysis results for this hour
        """
        # Scale network
        self._scale_network(scale_factor)

        # Run power flow
        pf_info = self._run_power_flow()

        if not pf_info['converged']:
            logger.warning(f"Power flow did not converge for hour {hour} (scale={scale_factor:.3f})")
            return {
                'hour': hour,
                'scale_factor': scale_factor,
                'converged': False,
                'error': 'Power flow did not converge'
            }

        # Get line flows and calculate loading
        flows = self.network.lines_t['p0'].loc['now', :]
        line_data = []

        for line_name, line in self.network.lines.iterrows():
            flow_mw = abs(flows[line_name])
            s_nom = line['s_nom']

            # Convert MW to MVA (approximate with power factor 0.95)
            flow_mva = flow_mw / 0.95 if flow_mw != 0 else 0
            loading_pct = (flow_mva / s_nom * 100) if s_nom > 0 else 0

            # Determine status
            if loading_pct >= 100:
                status = 'overloaded'
            elif loading_pct >= 90:
                status = 'high_stress'
            elif loading_pct >= 60:
                status = 'caution'
            else:
                status = 'normal'

            line_data.append({
                'name': line_name,
                'flow_mw': float(flow_mw),
                'flow_mva': float(flow_mva),
                'loading_pct': float(loading_pct),
                'status': status
            })

        # Calculate statistics
        loadings = [ld['loading_pct'] for ld in line_data]

        total_load_solved = float(self.network.loads_t['p'].sum(axis=1).iloc[0])
        total_gen_solved = float(self.network.generators_t['p'].sum(axis=1).iloc[0])

        return {
            'hour': hour,
            'scale_factor': float(scale_factor),
            'converged': True,
            'total_load_mw': float(self.network.loads['p_set'].sum()),
            'total_gen_mw': float(self.network.generators['p_set'].sum()),
            'total_load_solved_mw': total_load_solved,
            'total_gen_solved_mw': total_gen_solved,
            'max_loading_pct': float(max(loadings)),
            'avg_loading_pct': float(np.mean(loadings)),
            'overloaded_count': sum(1 for ld in line_data if ld['status'] == 'overloaded'),
            'high_stress_count': sum(1 for ld in line_data if ld['status'] == 'high_stress'),
            'caution_count': sum(1 for ld in line_data if ld['status'] == 'caution'),
            'lines': line_data,
            'power_flow_info': pf_info
        }

    def analyze_daily_profile(self, hours: int = 24) -> Dict[str, Any]:
        """
        Analyze network stress throughout a full day.

        Args:
            hours: Number of hours to analyze (default 24)

        Returns:
            dict: Complete daily analysis results
        """
        logger.info(f"Analyzing daily load profile ({hours} hours)...")

        # Generate load profile
        profile = self._generate_daily_profile(hours)

        # Analyze each hour
        hourly_results = []
        for hour, scale in enumerate(profile):
            logger.debug(f"Analyzing hour {hour} (scale={scale:.3f})")
            result = self._analyze_hour(hour, scale)
            hourly_results.append(result)

        # Find peak stress conditions
        max_loading_hour = max(hourly_results, key=lambda x: x.get('max_loading_pct', 0))
        max_overload_hour = max(hourly_results, key=lambda x: x.get('overloaded_count', 0))

        # Calculate summary
        summary = {
            'total_hours': hours,
            'hours_converged': sum(1 for r in hourly_results if r.get('converged', False)),
            'hours_failed': sum(1 for r in hourly_results if not r.get('converged', False)),
            'peak_loading': {
                'hour': max_loading_hour['hour'],
                'max_loading_pct': max_loading_hour.get('max_loading_pct', 0),
                'scale_factor': max_loading_hour['scale_factor'],
                'overloaded_count': max_loading_hour.get('overloaded_count', 0)
            },
            'peak_overloads': {
                'hour': max_overload_hour['hour'],
                'overloaded_count': max_overload_hour.get('overloaded_count', 0),
                'max_loading_pct': max_overload_hour.get('max_loading_pct', 0),
                'scale_factor': max_overload_hour['scale_factor']
            },
            'load_profile': [{'hour': i, 'scale': s} for i, s in enumerate(profile)]
        }

        # Find most stressed lines throughout the day
        line_max_loadings = {}
        for hour_result in hourly_results:
            if hour_result.get('converged'):
                for line in hour_result.get('lines', []):
                    line_name = line['name']
                    loading_pct = line['loading_pct']
                    if line_name not in line_max_loadings or loading_pct > line_max_loadings[line_name]['max_loading_pct']:
                        line_max_loadings[line_name] = {
                            'name': line_name,
                            'max_loading_pct': loading_pct,
                            'hour_of_max': hour_result['hour'],
                            'scale_at_max': hour_result['scale_factor']
                        }

        # Get top 10 most stressed lines
        top_lines = sorted(
            line_max_loadings.values(),
            key=lambda x: x['max_loading_pct'],
            reverse=True
        )[:10]

        summary['most_stressed_lines'] = top_lines

        result = {
            'success': True,
            'summary': summary,
            'hourly_results': hourly_results
        }

        # Convert numpy types to native Python
        return convert_numpy_types(result)

    def analyze_single_hour(self, hour: int) -> Dict[str, Any]:
        """
        Analyze network at a specific hour.

        Args:
            hour: Hour of day (0-23)

        Returns:
            dict: Analysis results for the specified hour
        """
        if hour < 0 or hour >= 24:
            return {
                'success': False,
                'error': f'Invalid hour: {hour}. Must be 0-23.'
            }

        # Generate profile and get scale for this hour
        profile = self._generate_daily_profile(24)
        scale = profile[hour]

        result = self._analyze_hour(hour, scale)
        result['success'] = result.get('converged', False)

        return convert_numpy_types(result)

    def get_load_profile(self, hours: int = 24) -> List[Dict[str, float]]:
        """
        Get the daily load profile without running analysis.

        Args:
            hours: Number of hours (default 24)

        Returns:
            list: Load profile data points
        """
        profile = self._generate_daily_profile(hours)
        return [
            {
                'hour': i,
                'scale_factor': float(s),
                'load_mw': float(self.baseline_load.sum() * s),
                'gen_mw': float(self.baseline_gen.sum() * s)
            }
            for i, s in enumerate(profile)
        ]
