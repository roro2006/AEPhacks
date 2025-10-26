#!/usr/bin/env python3
"""
CSV Data Loader Module - Production-Ready CSV Data Access Layer

This module provides a robust, centralized data loading system for the grid
monitoring application. It handles:

- CSV file loading with comprehensive error handling
- Data validation using Pydantic models
- Caching for performance optimization
- GeoJSON loading for geographic visualization
- Graceful error recovery and detailed logging

All data loading goes through this module to ensure consistency and reliability.

Example Usage:
    >>> from csv_data_loader import CSVDataLoader
    >>>
    >>> # Initialize the loader
    >>> loader = CSVDataLoader()
    >>>
    >>> # Load and validate line data
    >>> lines = loader.get_all_lines()
    >>>
    >>> # Get specific line information
    >>> line_info = loader.get_line_data('L0')
    >>> print(f"Line capacity: {line_info.s_nom} MVA")
"""

import pandas as pd
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from functools import lru_cache
from datetime import datetime, timedelta

from data_models import (
    LineData, BusData, ConductorParams, PowerFlow,
    DataValidationError, DataLoadError
)
from config import DataConfig, APIConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CSVDataLoader:
    """
    Centralized CSV data loader with validation and caching.

    This class provides methods to load, validate, and access grid data
    from CSV and GeoJSON files. It implements caching to improve performance
    and includes comprehensive error handling.

    Attributes:
        _cache: Internal cache for loaded data
        _cache_time: Timestamp of last cache refresh
        _cache_ttl: Time-to-live for cached data in seconds
    """

    def __init__(self, enable_cache: bool = None, cache_ttl: int = None):
        """
        Initialize the data loader.

        Args:
            enable_cache: Enable caching (default from config)
            cache_ttl: Cache time-to-live in seconds (default from config)
        """
        self._cache: Dict[str, Any] = {}
        self._cache_time: Dict[str, datetime] = {}
        self._cache_enabled = enable_cache if enable_cache is not None else APIConfig.ENABLE_CACHE
        self._cache_ttl = cache_ttl if cache_ttl is not None else APIConfig.CACHE_TTL_SECONDS

        # Verify data files exist
        missing_files = DataConfig.get_missing_files()
        if missing_files:
            logger.warning(f"Missing data files: {', '.join(missing_files)}")

        logger.info("CSVDataLoader initialized")

    def _is_cache_valid(self, cache_key: str) -> bool:
        """
        Check if cached data is still valid.

        Args:
            cache_key: Cache key to check

        Returns:
            bool: True if cache is valid, False otherwise
        """
        if not self._cache_enabled:
            return False

        if cache_key not in self._cache_time:
            return False

        age = datetime.now() - self._cache_time[cache_key]
        return age.total_seconds() < self._cache_ttl

    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """
        Retrieve data from cache if valid.

        Args:
            cache_key: Cache key

        Returns:
            Cached data if valid, None otherwise
        """
        if self._is_cache_valid(cache_key):
            logger.debug(f"Cache hit: {cache_key}")
            return self._cache.get(cache_key)
        return None

    def _set_cache(self, cache_key: str, data: Any):
        """
        Store data in cache.

        Args:
            cache_key: Cache key
            data: Data to cache
        """
        if self._cache_enabled:
            self._cache[cache_key] = data
            self._cache_time[cache_key] = datetime.now()
            logger.debug(f"Cache set: {cache_key}")

    def clear_cache(self):
        """Clear all cached data."""
        self._cache.clear()
        self._cache_time.clear()
        logger.info("Cache cleared")

    def _load_csv(
        self,
        file_path: Path,
        required_columns: Optional[List[str]] = None,
        strip_whitespace: bool = True
    ) -> pd.DataFrame:
        """
        Load CSV file with error handling and validation.

        Args:
            file_path: Path to CSV file
            required_columns: List of required column names (optional)
            strip_whitespace: Strip whitespace from string columns

        Returns:
            pd.DataFrame: Loaded data

        Raises:
            DataLoadError: If file cannot be loaded or required columns are missing
        """
        try:
            # Check if file exists
            if not file_path.exists():
                raise DataLoadError(f"CSV file not found: {file_path}")

            # Read CSV
            logger.debug(f"Loading CSV: {file_path}")
            df = pd.read_csv(file_path)

            # Check if empty
            if df.empty:
                logger.warning(f"CSV file is empty: {file_path}")
                return df

            # Strip whitespace from string columns
            if strip_whitespace:
                for col in df.select_dtypes(include=['object']).columns:
                    df[col] = df[col].str.strip() if df[col].dtype == 'object' else df[col]

            # Validate required columns
            if required_columns:
                missing_cols = set(required_columns) - set(df.columns)
                if missing_cols:
                    raise DataLoadError(
                        f"Missing required columns in {file_path.name}: {missing_cols}"
                    )

            logger.info(f"Loaded {len(df)} records from {file_path.name}")
            return df

        except pd.errors.EmptyDataError:
            raise DataLoadError(f"CSV file is empty: {file_path}")
        except pd.errors.ParserError as e:
            raise DataLoadError(f"Error parsing CSV {file_path}: {str(e)}")
        except Exception as e:
            raise DataLoadError(f"Error loading CSV {file_path}: {str(e)}")

    def _load_geojson(self, file_path: Path) -> Dict[str, Any]:
        """
        Load GeoJSON file with error handling.

        Args:
            file_path: Path to GeoJSON file

        Returns:
            dict: Parsed GeoJSON data

        Raises:
            DataLoadError: If file cannot be loaded or is invalid
        """
        try:
            if not file_path.exists():
                raise DataLoadError(f"GeoJSON file not found: {file_path}")

            logger.debug(f"Loading GeoJSON: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate GeoJSON structure
            if 'type' not in data:
                raise DataLoadError(f"Invalid GeoJSON: missing 'type' field in {file_path}")

            logger.info(f"Loaded GeoJSON from {file_path.name}")
            return data

        except json.JSONDecodeError as e:
            raise DataLoadError(f"Invalid JSON in {file_path}: {str(e)}")
        except Exception as e:
            raise DataLoadError(f"Error loading GeoJSON {file_path}: {str(e)}")

    def get_all_lines(self, validate: bool = True) -> List[LineData]:
        """
        Get all transmission lines with validation.

        Args:
            validate: Validate data using Pydantic models (default: True)

        Returns:
            List[LineData]: List of validated line data objects

        Raises:
            DataLoadError: If data cannot be loaded
            DataValidationError: If validation fails

        Example:
            >>> loader = CSVDataLoader()
            >>> lines = loader.get_all_lines()
            >>> print(f"Found {len(lines)} transmission lines")
        """
        cache_key = 'all_lines'
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        try:
            # Load CSV
            required_cols = ['name', 'bus0', 'bus1', 's_nom', 'conductor', 'MOT']
            df = self._load_csv(DataConfig.LINES_CSV, required_columns=required_cols)

            if df.empty:
                logger.warning("No line data found")
                return []

            # Convert to list of dictionaries
            line_dicts = df.to_dict('records')

            # Validate if requested
            if validate:
                validated_lines = []
                errors = []

                for i, line_dict in enumerate(line_dicts):
                    try:
                        line_data = LineData(**line_dict)
                        validated_lines.append(line_data)
                    except Exception as e:
                        errors.append(f"Line {i} ({line_dict.get('name', 'unknown')}): {str(e)}")

                if errors:
                    error_msg = "Validation errors in line data:\n" + "\n".join(errors[:5])
                    if len(errors) > 5:
                        error_msg += f"\n... and {len(errors) - 5} more errors"
                    logger.error(error_msg)
                    raise DataValidationError(error_msg)

                self._set_cache(cache_key, validated_lines)
                return validated_lines
            else:
                # Return raw dictionaries without validation
                self._set_cache(cache_key, line_dicts)
                return line_dicts

        except (DataLoadError, DataValidationError):
            raise
        except Exception as e:
            raise DataLoadError(f"Unexpected error loading line data: {str(e)}")

    def get_line_data(self, line_name: str, validate: bool = True):
        """
        Get data for a specific transmission line.

        Args:
            line_name: Line identifier (e.g., 'L0', 'L1')
            validate: Validate data using Pydantic model (default: True)

        Returns:
            LineData or dict or None: Line data if found, None otherwise

        Example:
            >>> loader = CSVDataLoader()
            >>> line = loader.get_line_data('L0')
            >>> if line:
            ...     print(f"Capacity: {line.s_nom} MVA")
        """
        all_lines = self.get_all_lines(validate=validate)

        for line in all_lines:
            # Check name regardless of type (LineData object or dict)
            name = line.name if hasattr(line, 'name') else line.get('name')
            if name == line_name:
                return line

        logger.warning(f"Line not found: {line_name}")
        return None

    def get_all_buses(self, validate: bool = True) -> List[BusData]:
        """
        Get all bus/substation data with validation.

        Args:
            validate: Validate data using Pydantic models (default: True)

        Returns:
            List[BusData]: List of validated bus data objects

        Raises:
            DataLoadError: If data cannot be loaded
            DataValidationError: If validation fails
        """
        cache_key = 'all_buses'
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        try:
            required_cols = ['name', 'BusName', 'v_nom']
            df = self._load_csv(DataConfig.BUSES_CSV, required_columns=required_cols)

            if df.empty:
                logger.warning("No bus data found")
                return []

            bus_dicts = df.to_dict('records')

            if validate:
                validated_buses = []
                errors = []

                for i, bus_dict in enumerate(bus_dicts):
                    try:
                        bus_data = BusData(**bus_dict)
                        validated_buses.append(bus_data)
                    except Exception as e:
                        errors.append(f"Bus {i} ({bus_dict.get('name', 'unknown')}): {str(e)}")

                if errors:
                    error_msg = "Validation errors in bus data:\n" + "\n".join(errors[:5])
                    if len(errors) > 5:
                        error_msg += f"\n... and {len(errors) - 5} more errors"
                    logger.error(error_msg)
                    raise DataValidationError(error_msg)

                self._set_cache(cache_key, validated_buses)
                return validated_buses
            else:
                self._set_cache(cache_key, bus_dicts)
                return bus_dicts

        except (DataLoadError, DataValidationError):
            raise
        except Exception as e:
            raise DataLoadError(f"Unexpected error loading bus data: {str(e)}")

    def get_bus_data(self, bus_name: str, validate: bool = True):
        """
        Get data for a specific bus.

        Args:
            bus_name: Bus identifier or name
            validate: Validate data using Pydantic model

        Returns:
            BusData or dict or None: Bus data if found, None otherwise
        """
        all_buses = self.get_all_buses(validate=validate)

        for bus in all_buses:
            # Check name regardless of type (BusData object or dict)
            name = bus.name if hasattr(bus, 'name') else bus.get('name')
            bus_name_field = bus.BusName if hasattr(bus, 'BusName') else bus.get('BusName')
            if name == bus_name or bus_name_field == bus_name:
                return bus

        logger.warning(f"Bus not found: {bus_name}")
        return None

    def get_all_power_flows(self, validate: bool = True) -> List[PowerFlow]:
        """
        Get all power flow data.

        Args:
            validate: Validate data using Pydantic models

        Returns:
            List[PowerFlow]: List of power flow objects

        Raises:
            DataLoadError: If data cannot be loaded
        """
        cache_key = 'all_flows'
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        try:
            required_cols = ['name', 'p0_nominal']
            df = self._load_csv(DataConfig.LINE_FLOWS_CSV, required_columns=required_cols)

            if df.empty:
                logger.warning("No power flow data found")
                return []

            flow_dicts = df.to_dict('records')

            if validate:
                validated_flows = []
                errors = []

                for i, flow_dict in enumerate(flow_dicts):
                    try:
                        flow_data = PowerFlow(**flow_dict)
                        validated_flows.append(flow_data)
                    except Exception as e:
                        errors.append(f"Flow {i} ({flow_dict.get('name', 'unknown')}): {str(e)}")

                if errors and len(errors) > len(flow_dicts) * 0.5:
                    # Only raise error if more than 50% of flows are invalid
                    error_msg = "Too many validation errors in power flow data:\n" + "\n".join(errors[:5])
                    logger.error(error_msg)
                    raise DataValidationError(error_msg)
                elif errors:
                    logger.warning(f"{len(errors)} validation warnings in power flow data")

                self._set_cache(cache_key, validated_flows)
                return validated_flows
            else:
                self._set_cache(cache_key, flow_dicts)
                return flow_dicts

        except (DataLoadError, DataValidationError):
            raise
        except Exception as e:
            raise DataLoadError(f"Unexpected error loading power flow data: {str(e)}")

    def get_power_flow(self, line_name: str, validate: bool = True):
        """
        Get power flow for a specific line.

        Args:
            line_name: Line identifier
            validate: Validate data using Pydantic model

        Returns:
            PowerFlow or dict or None: Power flow data if found, None otherwise
        """
        all_flows = self.get_all_power_flows(validate=validate)

        for flow in all_flows:
            # Check name regardless of type (PowerFlow object or dict)
            name = flow.name if hasattr(flow, 'name') else flow.get('name')
            if name == line_name:
                return flow

        logger.debug(f"No power flow data for line: {line_name}")
        return None

    def get_all_conductor_params(self, validate: bool = True) -> List[ConductorParams]:
        """
        Get all conductor library parameters.

        Args:
            validate: Validate data using Pydantic models

        Returns:
            List[ConductorParams]: List of conductor parameter objects

        Raises:
            DataLoadError: If data cannot be loaded
        """
        cache_key = 'all_conductors'
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        try:
            required_cols = ['ConductorName', 'MOT', 'RatingAmps', 'RatingMVA_69', 'RatingMVA_138']
            df = self._load_csv(DataConfig.CONDUCTOR_RATINGS_CSV, required_columns=required_cols)

            if df.empty:
                logger.warning("No conductor rating data found")
                return []

            conductor_dicts = df.to_dict('records')

            if validate:
                validated_conductors = []
                errors = []

                for i, cond_dict in enumerate(conductor_dicts):
                    try:
                        cond_data = ConductorParams(**cond_dict)
                        validated_conductors.append(cond_data)
                    except Exception as e:
                        errors.append(f"Conductor {i} ({cond_dict.get('ConductorName', 'unknown')}): {str(e)}")

                if errors:
                    error_msg = "Validation errors in conductor data:\n" + "\n".join(errors[:5])
                    logger.error(error_msg)
                    raise DataValidationError(error_msg)

                self._set_cache(cache_key, validated_conductors)
                return validated_conductors
            else:
                self._set_cache(cache_key, conductor_dicts)
                return conductor_dicts

        except (DataLoadError, DataValidationError):
            raise
        except Exception as e:
            raise DataLoadError(f"Unexpected error loading conductor data: {str(e)}")

    def get_conductor_params(self, conductor_name: str, validate: bool = True):
        """
        Get parameters for a specific conductor type.

        Args:
            conductor_name: Conductor type name
            validate: Validate data using Pydantic model

        Returns:
            ConductorParams or dict or None: Conductor parameters if found, None otherwise
        """
        all_conductors = self.get_all_conductor_params(validate=validate)

        for conductor in all_conductors:
            # Check name regardless of type (ConductorParams object or dict)
            name = conductor.ConductorName if hasattr(conductor, 'ConductorName') else conductor.get('ConductorName')
            if name == conductor_name:
                return conductor

        logger.warning(f"Conductor not found: {conductor_name}")
        return None

    def get_lines_geojson(self) -> Dict[str, Any]:
        """
        Get GeoJSON data for transmission lines.

        Returns:
            dict: GeoJSON FeatureCollection

        Raises:
            DataLoadError: If GeoJSON cannot be loaded
        """
        cache_key = 'lines_geojson'
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        geojson = self._load_geojson(DataConfig.LINES_GEOJSON)
        self._set_cache(cache_key, geojson)
        return geojson

    def get_buses_geojson(self) -> Dict[str, Any]:
        """
        Get GeoJSON data for buses/substations.

        Returns:
            dict: GeoJSON FeatureCollection

        Raises:
            DataLoadError: If GeoJSON cannot be loaded
        """
        cache_key = 'buses_geojson'
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        geojson = self._load_geojson(DataConfig.BUSES_GEOJSON)
        self._set_cache(cache_key, geojson)
        return geojson

    def get_complete_line_info(self, line_name: str) -> Optional[Dict[str, Any]]:
        """
        Get complete information for a line including flows, conductor, and geometry.

        Args:
            line_name: Line identifier

        Returns:
            dict or None: Complete line information if found

        Example:
            >>> loader = CSVDataLoader()
            >>> info = loader.get_complete_line_info('L0')
            >>> print(f"Line: {info['line_data'].branch_name}")
            >>> print(f"Flow: {info['power_flow'].p0_nominal} MW")
        """
        line_data = self.get_line_data(line_name)
        if not line_data:
            return None

        power_flow = self.get_power_flow(line_name)
        conductor_params = self.get_conductor_params(line_data.conductor)

        # Find geometry in GeoJSON
        try:
            geojson = self.get_lines_geojson()
            geometry = None

            for feature in geojson.get('features', []):
                if feature.get('properties', {}).get('Name') == line_name:
                    geometry = feature.get('geometry')
                    break
        except DataLoadError:
            geometry = None

        return {
            'line_data': line_data,
            'power_flow': power_flow,
            'conductor_params': conductor_params,
            'geometry': geometry
        }

    def get_data_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about loaded data.

        Returns:
            dict: Data statistics including record counts and validation status

        Example:
            >>> loader = CSVDataLoader()
            >>> stats = loader.get_data_statistics()
            >>> print(f"Total lines: {stats['line_count']}")
        """
        try:
            lines = self.get_all_lines(validate=False)
            buses = self.get_all_buses(validate=False)
            flows = self.get_all_power_flows(validate=False)
            conductors = self.get_all_conductor_params(validate=False)

            return {
                'line_count': len(lines),
                'bus_count': len(buses),
                'flow_count': len(flows),
                'conductor_count': len(conductors),
                'cache_enabled': self._cache_enabled,
                'cache_ttl': self._cache_ttl,
                'cached_items': len(self._cache),
                'data_files_status': DataConfig.validate_required_files()
            }
        except Exception as e:
            logger.error(f"Error getting data statistics: {str(e)}")
            return {
                'error': str(e),
                'data_files_status': DataConfig.validate_required_files()
            }


# Global singleton instance for convenient access
_loader_instance: Optional[CSVDataLoader] = None


def get_loader() -> CSVDataLoader:
    """
    Get global CSVDataLoader singleton instance.

    Returns:
        CSVDataLoader: Global loader instance

    Example:
        >>> from csv_data_loader import get_loader
        >>> loader = get_loader()
        >>> lines = loader.get_all_lines()
    """
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = CSVDataLoader()
    return _loader_instance


if __name__ == '__main__':
    # Demo usage
    print("\n" + "=" * 80)
    print("CSV DATA LOADER - DEMO")
    print("=" * 80)

    try:
        loader = CSVDataLoader()

        # Get statistics
        stats = loader.get_data_statistics()
        print("\n[DATA STATISTICS]")
        print(f"Lines:      {stats['line_count']}")
        print(f"Buses:      {stats['bus_count']}")
        print(f"Flows:      {stats['flow_count']}")
        print(f"Conductors: {stats['conductor_count']}")
        print(f"Cache:      {'Enabled' if stats['cache_enabled'] else 'Disabled'}")

        # Load some sample data
        print("\n[SAMPLE LINE DATA]")
        lines = loader.get_all_lines()
        if lines:
            sample_line = lines[0]
            print(f"Line ID:    {sample_line.name}")
            print(f"Name:       {sample_line.branch_name}")
            print(f"Capacity:   {sample_line.s_nom} MVA")
            print(f"Conductor:  {sample_line.conductor}")

        # Check for missing files
        missing = DataConfig.get_missing_files()
        if missing:
            print(f"\n[!] WARNING: Missing files: {', '.join(missing)}")
        else:
            print("\n[OK] All required data files present")

    except Exception as e:
        print(f"\n[X] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80 + "\n")
