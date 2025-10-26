"""
Transmission Line Outage Simulator using PyPSA

This module simulates the removal of one or more transmission lines from the power network
and analyzes the resulting impacts on grid stress, connectivity, and line loadings.

Based on the PyPSA power flow analysis approach, similar to the provided example notebook.
"""

import pandas as pd
import numpy as np
import pypsa
import logging
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
from config import DataConfig

logger = logging.getLogger(__name__)


class OutageSimulator:
    """
    Simulates transmission line outages and analyzes grid impacts.

    Uses PyPSA to load network topology from CSV files, remove specified lines,
    and re-run power flow to calculate the new network state.
    """

    def __init__(self):
        """Initialize the outage simulator with PyPSA network."""
        self.network = None
        self.baseline_flows = None
        self.baseline_loading = None
        self._load_network()

    def _load_network(self):
        """Load PyPSA network from CSV files."""
        try:
            logger.info("Loading PyPSA network from CSV files...")
            self.network = pypsa.Network()

            # Import from CSV folder (PyPSA format)
            csv_folder = str(DataConfig.DATA_DIR)
            self.network.import_from_csv_folder(csv_folder)

            logger.info(
                f"Network loaded: {len(self.network.lines)} lines, "
                f"{len(self.network.buses)} buses, "
                f"{len(self.network.generators)} generators"
            )

            # Run baseline power flow
            logger.info("Running baseline power flow...")
            self._run_power_flow()

            # Store baseline state
            self._store_baseline()

        except Exception as e:
            logger.error(f"Error loading PyPSA network: {e}")
            raise RuntimeError(f"Failed to load PyPSA network: {e}")

    def _run_power_flow(self, use_lpf=False):
        """
        Run power flow analysis.

        Args:
            use_lpf: If True, use linear power flow approximation (faster, less accurate)

        Returns:
            dict: Power flow convergence info
        """
        try:
            if use_lpf:
                self.network.lpf()
                return {'converged': True, 'linear': True}
            else:
                info = self.network.pf()
                converged = info.converged.any().any()
                max_error = info.error.max().max()

                logger.info(f"Power flow converged: {converged}, max error: {max_error:.2e}")

                return {
                    'converged': converged,
                    'max_error': float(max_error),
                    'linear': False
                }
        except Exception as e:
            logger.error(f"Power flow failed: {e}")
            raise

    def _store_baseline(self):
        """Store baseline flows and loading for comparison."""
        if self.network is None:
            return

        # Store baseline line flows (p0 = active power flow from bus0)
        self.baseline_flows = self.network.lines_t['p0'].copy()

        # Calculate baseline loading percentages
        self.baseline_loading = {}
        for line_name in self.network.lines.index:
            flow = abs(self.network.lines_t['p0'].loc['now', line_name])
            s_nom = self.network.lines.loc[line_name, 's_nom']
            if s_nom > 0:
                self.baseline_loading[line_name] = (flow / s_nom) * 100
            else:
                self.baseline_loading[line_name] = 0.0

    def reload_network(self):
        """Reload network from scratch (resets all outages)."""
        self._load_network()

    def simulate_outage(self, outage_lines: List[str], use_lpf: bool = False) -> Dict[str, Any]:
        """
        Simulate the outage of one or more transmission lines.

        Args:
            outage_lines: List of line names to remove (e.g., ['L48', 'L49'])
            use_lpf: Use linear power flow (faster but less accurate)

        Returns:
            dict: Comprehensive outage analysis results including:
                - outage_lines: Lines that were removed
                - converged: Whether power flow converged
                - overloaded_lines: Lines exceeding 100% capacity
                - high_stress_lines: Lines between 90-100%
                - islanded_buses: Buses that became disconnected
                - affected_lines: Lines with significant loading changes
                - loading_changes: Detailed before/after comparison
                - metrics: Summary statistics
        """
        # Reload network to ensure clean state
        self.reload_network()

        # Validate that all specified lines exist
        invalid_lines = [line for line in outage_lines if line not in self.network.lines.index]
        if invalid_lines:
            return {
                'success': False,
                'error': f"Invalid line names: {invalid_lines}",
                'valid_lines': list(self.network.lines.index)
            }

        logger.info(f"Simulating outage of lines: {outage_lines}")

        # Disable the outaged lines
        for line_name in outage_lines:
            self.network.lines.loc[line_name, "active"] = False
            # Clear old solve data for disabled lines
            self.network.lines_t['p0'].loc['now', line_name] = 0.0

        # Run power flow with outages
        try:
            pf_info = self._run_power_flow(use_lpf=use_lpf)
        except Exception as e:
            return {
                'success': False,
                'error': f"Power flow failed: {str(e)}",
                'outage_lines': outage_lines
            }

        if not pf_info['converged'] and not use_lpf:
            # Try again with linear power flow
            logger.warning("Nonlinear power flow did not converge, trying linear approximation...")
            try:
                pf_info = self._run_power_flow(use_lpf=True)
            except Exception as e:
                return {
                    'success': False,
                    'error': f"Both power flow methods failed: {str(e)}",
                    'outage_lines': outage_lines
                }

        # Analyze results
        analysis = self._analyze_outage_results(outage_lines)
        analysis['power_flow_info'] = pf_info
        analysis['success'] = True

        return analysis

    def _analyze_outage_results(self, outage_lines: List[str]) -> Dict[str, Any]:
        """
        Analyze the post-outage network state.

        Args:
            outage_lines: List of lines that were removed

        Returns:
            dict: Analysis results
        """
        results = {
            'outage_lines': outage_lines,
            'overloaded_lines': [],
            'high_stress_lines': [],
            'loading_changes': [],
            'islanded_buses': [],
            'affected_lines': [],
            'metrics': {}
        }

        # Get active lines (excluding outaged ones)
        active_lines = self.network.lines[self.network.lines['active']].index

        # Calculate loading for each active line
        loading_data = []
        for line_name in self.network.lines.index:
            flow_mw = abs(self.network.lines_t['p0'].loc['now', line_name])
            s_nom = self.network.lines.loc[line_name, 's_nom']
            is_active = self.network.lines.loc[line_name, 'active']

            # Convert to MVA (approximate with power factor 0.95)
            flow_mva = flow_mw / 0.95 if flow_mw != 0 else 0

            loading_pct = (flow_mva / s_nom * 100) if s_nom > 0 else 0
            baseline_pct = self.baseline_loading.get(line_name, 0)
            loading_change = loading_pct - baseline_pct

            line_result = {
                'name': line_name,
                'bus0': self.network.lines.loc[line_name, 'bus0'],
                'bus1': self.network.lines.loc[line_name, 'bus1'],
                's_nom': float(s_nom),
                'flow_mw': float(flow_mw),
                'flow_mva': float(flow_mva),
                'loading_pct': float(loading_pct),
                'baseline_loading_pct': float(baseline_pct),
                'loading_change_pct': float(loading_change),
                'is_active': bool(is_active),
                'is_outaged': line_name in outage_lines,
                'status': 'outaged' if line_name in outage_lines else (
                    'overloaded' if loading_pct >= 100 else
                    'high_stress' if loading_pct >= 90 else
                    'caution' if loading_pct >= 60 else
                    'normal'
                )
            }

            loading_data.append(line_result)

            # Categorize active lines
            if is_active and line_name not in outage_lines:
                if loading_pct >= 100:
                    results['overloaded_lines'].append(line_result)
                elif loading_pct >= 90:
                    results['high_stress_lines'].append(line_result)

                # Lines with significant loading change (>10%)
                if abs(loading_change) > 10:
                    results['affected_lines'].append(line_result)

        results['loading_changes'] = loading_data

        # Check for islanded buses (disconnected from main grid)
        results['islanded_buses'] = self._detect_islanded_buses(outage_lines)

        # Calculate summary metrics
        active_loading = [ld for ld in loading_data if ld['is_active'] and not ld['is_outaged']]
        if active_loading:
            loadings = [ld['loading_pct'] for ld in active_loading]
            baseline_loadings = [ld['baseline_loading_pct'] for ld in active_loading]

            results['metrics'] = {
                'total_lines': len(self.network.lines),
                'outaged_lines_count': len(outage_lines),
                'active_lines_count': len(active_loading),
                'overloaded_count': len(results['overloaded_lines']),
                'high_stress_count': len(results['high_stress_lines']),
                'affected_lines_count': len(results['affected_lines']),
                'islanded_buses_count': len(results['islanded_buses']),
                'max_loading_pct': float(max(loadings)),
                'avg_loading_pct': float(np.mean(loadings)),
                'max_loading_increase': float(max([ld['loading_change_pct'] for ld in active_loading], default=0)),
                'baseline_max_loading': float(max(baseline_loadings)),
                'baseline_avg_loading': float(np.mean(baseline_loadings)),
            }
        else:
            results['metrics'] = {
                'total_lines': len(self.network.lines),
                'outaged_lines_count': len(outage_lines),
                'active_lines_count': 0,
                'overloaded_count': 0,
                'high_stress_count': 0,
                'affected_lines_count': 0,
                'islanded_buses_count': len(results['islanded_buses']),
                'max_loading_pct': 0,
                'avg_loading_pct': 0,
                'max_loading_increase': 0,
                'baseline_max_loading': 0,
                'baseline_avg_loading': 0,
            }

        # Sort results by loading percentage
        results['overloaded_lines'].sort(key=lambda x: x['loading_pct'], reverse=True)
        results['high_stress_lines'].sort(key=lambda x: x['loading_pct'], reverse=True)
        results['affected_lines'].sort(key=lambda x: abs(x['loading_change_pct']), reverse=True)

        return results

    def _detect_islanded_buses(self, outage_lines: List[str]) -> List[Dict[str, Any]]:
        """
        Detect buses that have become islanded (disconnected) due to outages.

        Args:
            outage_lines: Lines that have been removed

        Returns:
            list: List of islanded bus information
        """
        # Build connectivity graph of active lines
        connected_buses = set()
        bus_connections = {bus: set() for bus in self.network.buses.index}

        # Add edges for active lines
        for line_name, line in self.network.lines.iterrows():
            if line['active']:
                bus0 = line['bus0']
                bus1 = line['bus1']
                bus_connections[bus0].add(bus1)
                bus_connections[bus1].add(bus0)

        # Find connected components using BFS from a generator bus
        if len(self.network.generators) > 0:
            # Start from first generator bus
            start_bus = self.network.generators.iloc[0]['bus']
            visited = set()
            queue = [start_bus]

            while queue:
                bus = queue.pop(0)
                if bus in visited:
                    continue
                visited.add(bus)
                connected_buses.add(bus)

                # Add connected buses to queue
                for neighbor in bus_connections.get(bus, []):
                    if neighbor not in visited:
                        queue.append(neighbor)

        # Buses not in connected component are islanded
        all_buses = set(self.network.buses.index)
        islanded = all_buses - connected_buses

        islanded_info = []
        for bus in islanded:
            bus_data = self.network.buses.loc[bus]
            islanded_info.append({
                'bus_id': bus,
                'bus_name': bus_data.get('name', bus),
                'voltage_kv': float(bus_data.get('v_nom', 0)),
                'x': float(bus_data.get('x', 0)),
                'y': float(bus_data.get('y', 0))
            })

        return islanded_info

    def get_available_lines(self) -> List[Dict[str, str]]:
        """
        Get list of all available lines that can be outaged.

        Returns:
            list: List of dictionaries with line information
        """
        if self.network is None:
            return []

        lines = []
        for line_name, line in self.network.lines.iterrows():
            lines.append({
                'name': line_name,
                'bus0': str(line['bus0']),
                'bus1': str(line['bus1']),
                's_nom': float(line['s_nom']),
                'description': f"{line_name} | {line['bus0']} - {line['bus1']}"
            })

        return sorted(lines, key=lambda x: x['name'])

    def run_multiple_contingency_scenarios(self, scenarios: List[List[str]]) -> List[Dict[str, Any]]:
        """
        Run multiple N-1, N-2, etc. contingency scenarios.

        Args:
            scenarios: List of outage scenarios, each containing list of line names

        Returns:
            list: Results for each scenario
        """
        results = []
        for i, outage_lines in enumerate(scenarios):
            logger.info(f"Running scenario {i+1}/{len(scenarios)}: {outage_lines}")
            result = self.simulate_outage(outage_lines)
            result['scenario_id'] = i + 1
            result['scenario_type'] = f"N-{len(outage_lines)}"
            results.append(result)

        return results
