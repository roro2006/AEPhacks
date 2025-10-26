"""
Data loader for grid data from CSV and GeoJSON files

REFACTORED VERSION - Now uses the robust CSVDataLoader infrastructure
with proper error handling, validation, and caching.

This class maintains backward compatibility with existing code while
leveraging the new data loading infrastructure.
"""
import pandas as pd
import json
import os
import logging
from typing import Optional, Dict, Any, List

# Import new infrastructure
from csv_data_loader import CSVDataLoader
from data_models import DataLoadError
from config import DataConfig

logger = logging.getLogger(__name__)


class DataLoader:
    """
    Legacy data loader class - refactored to use new infrastructure.

    This class provides backward compatibility with existing code while
    using the new CSVDataLoader internally for robust data access.

    Args:
        data_path: Optional custom data path (deprecated - uses config by default)
    """

    def __init__(self, data_path: Optional[str] = None):
        """
        Initialize the data loader.

        Args:
            data_path: Optional custom data path (for backward compatibility)
                      If None, uses paths from DataConfig
        """
        # Use new CSV data loader
        self._csv_loader = CSVDataLoader()

        # Legacy path handling (for backward compatibility)
        if data_path is not None:
            logger.warning(
                "Custom data_path is deprecated. The loader now uses config.DataConfig "
                "for path management. Custom path will be ignored."
            )

        # Legacy attributes (for backward compatibility)
        # These are now populated on-demand from the CSV loader
        self._lines_df = None
        self._buses_df = None
        self._flows_df = None
        self._conductors_df = None
        self._lines_geojson = None
        self._buses_geojson = None

        # Load data
        self._load_data()

    def _load_data(self):
        """Load all data files using new infrastructure."""
        try:
            logger.info("Loading grid data using CSVDataLoader...")

            # Load data using the new loader (validates and caches automatically)
            lines = self._csv_loader.get_all_lines(validate=False)
            buses = self._csv_loader.get_all_buses(validate=False)
            flows = self._csv_loader.get_all_power_flows(validate=False)
            conductors = self._csv_loader.get_all_conductor_params(validate=False)

            # Convert to DataFrames for backward compatibility
            self._lines_df = pd.DataFrame(lines)
            self._buses_df = pd.DataFrame(buses)
            self._flows_df = pd.DataFrame(flows)
            self._conductors_df = pd.DataFrame(conductors)

            # Load GeoJSON
            try:
                self._lines_geojson = self._csv_loader.get_lines_geojson()
            except DataLoadError as e:
                logger.warning(f"Could not load lines GeoJSON: {e}")
                self._lines_geojson = None

            try:
                self._buses_geojson = self._csv_loader.get_buses_geojson()
            except DataLoadError as e:
                logger.warning(f"Could not load buses GeoJSON: {e}")
                self._buses_geojson = None

            logger.info(
                f"Loaded {len(self._lines_df)} lines, {len(self._buses_df)} buses, "
                f"{len(self._flows_df)} flows, {len(self._conductors_df)} conductors"
            )

        except DataLoadError as e:
            logger.error(f"Error loading data: {e}")
            # Initialize empty DataFrames for graceful degradation
            self._lines_df = pd.DataFrame()
            self._buses_df = pd.DataFrame()
            self._flows_df = pd.DataFrame()
            self._conductors_df = pd.DataFrame()
            self._lines_geojson = None
            self._buses_geojson = None
            raise

    # Legacy property accessors for backward compatibility
    @property
    def lines_df(self) -> pd.DataFrame:
        """Legacy accessor for lines DataFrame."""
        return self._lines_df

    @property
    def buses_df(self) -> pd.DataFrame:
        """Legacy accessor for buses DataFrame."""
        return self._buses_df

    @property
    def flows_df(self) -> pd.DataFrame:
        """Legacy accessor for flows DataFrame."""
        return self._flows_df

    @property
    def conductors_df(self) -> pd.DataFrame:
        """Legacy accessor for conductors DataFrame."""
        return self._conductors_df

    @property
    def lines_geojson(self) -> Optional[Dict]:
        """Legacy accessor for lines GeoJSON."""
        return self._lines_geojson

    @property
    def buses_geojson(self) -> Optional[Dict]:
        """Legacy accessor for buses GeoJSON."""
        return self._buses_geojson

    def get_lines_geojson(self) -> Optional[Dict[str, Any]]:
        """
        Return lines GeoJSON.

        Returns:
            dict: GeoJSON FeatureCollection or None if not available
        """
        return self._lines_geojson

    def get_buses_geojson(self) -> Optional[Dict[str, Any]]:
        """
        Return buses GeoJSON.

        Returns:
            dict: GeoJSON FeatureCollection or None if not available
        """
        return self._buses_geojson

    def get_line_data(self, line_name: str) -> Optional[Dict[str, Any]]:
        """
        Get line data by name.

        Args:
            line_name: Line identifier (e.g., 'L0', 'L1')

        Returns:
            dict: Line data or None if not found
        """
        if self._lines_df.empty:
            logger.warning("No line data available")
            return None

        line = self._lines_df[self._lines_df['name'] == line_name]
        if len(line) == 0:
            logger.debug(f"Line not found: {line_name}")
            return None

        return line.iloc[0].to_dict()

    def get_all_lines(self) -> List[Dict[str, Any]]:
        """
        Get all lines as list of dictionaries.

        Returns:
            list: List of line data dictionaries with NaN replaced by None
        """
        if self._lines_df.empty:
            logger.warning("No line data available")
            return []

        # Replace NaN with None for proper JSON serialization
        df_clean = self._lines_df.replace({pd.NA: None, float('nan'): None})
        return df_clean.where(pd.notna(df_clean), None).to_dict('records')

    def get_conductor_params(self, conductor_name: str) -> Optional[Dict[str, Any]]:
        """
        Get conductor parameters.

        Args:
            conductor_name: Conductor type name

        Returns:
            dict: Conductor parameters or None if not found
        """
        if self._conductors_df.empty:
            logger.warning("No conductor data available")
            return None

        conductor = self._conductors_df[
            self._conductors_df['ConductorName'] == conductor_name
        ]

        if len(conductor) == 0:
            logger.debug(f"Conductor not found: {conductor_name}")
            return None

        return conductor.iloc[0].to_dict()

    def get_line_flow(self, line_name: str) -> float:
        """
        Get nominal flow for a line.

        Args:
            line_name: Line identifier

        Returns:
            float: Nominal power flow in MW (0 if not found)
        """
        if self._flows_df.empty:
            logger.warning("No flow data available")
            return 0.0

        flow = self._flows_df[self._flows_df['name'] == line_name]

        if len(flow) == 0:
            logger.debug(f"No flow data for line: {line_name}")
            return 0.0

        return float(flow.iloc[0]['p0_nominal'])

    def get_bus_voltage(self, bus_name: str) -> Optional[float]:
        """
        Get bus voltage in kV.

        Args:
            bus_name: Bus name

        Returns:
            float: Voltage in kV or None if not found
        """
        if self._buses_df.empty:
            logger.warning("No bus data available")
            return None

        # Bus names are in 'BusName' column, not 'name' column
        bus = self._buses_df[self._buses_df['BusName'] == bus_name]

        if len(bus) == 0:
            logger.debug(f"Bus not found: {bus_name}")
            return None

        return float(bus.iloc[0]['v_nom'])

    def get_line_info(self, line_name: str) -> Optional[Dict[str, Any]]:
        """
        Get complete line information including flow and conductor data.

        Args:
            line_name: Line identifier

        Returns:
            dict: Complete line information or None if not found
        """
        line_data = self.get_line_data(line_name)
        if line_data is None:
            return None

        conductor_params = self.get_conductor_params(line_data['conductor'])
        flow = self.get_line_flow(line_name)
        voltage = self.get_bus_voltage(line_data['bus0_name'])

        return {
            **line_data,
            'conductor_params': conductor_params,
            'flow_nominal': flow,
            'voltage_kv': voltage
        }

    def reload_data(self):
        """
        Reload all data from CSV files.

        Useful when data files have been updated.
        """
        logger.info("Reloading data...")
        self._csv_loader.clear_cache()
        self._load_data()

    def get_data_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about loaded data.

        Returns:
            dict: Data statistics
        """
        return self._csv_loader.get_data_statistics()
