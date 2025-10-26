#!/usr/bin/env python3
"""
Configuration module for grid monitoring application.

This module provides centralized configuration management for:
- Data file paths
- API settings
- Application parameters
- Environment variable handling

All file paths are resolved relative to the backend directory to ensure
portability across different environments.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class DataConfig:
    """
    Configuration for data file paths and directories.

    All paths are resolved relative to the backend directory to ensure
    the application works correctly regardless of where it's run from.
    """

    # Get the backend directory (parent of this config.py file)
    BACKEND_DIR = Path(__file__).resolve().parent

    # Main data directory
    DATA_DIR = BACKEND_DIR / 'data'

    # CSV data files
    LINES_CSV = DATA_DIR / 'lines.csv'
    BUSES_CSV = DATA_DIR / 'buses.csv'
    GENERATORS_CSV = DATA_DIR / 'generators.csv'
    GENERATORS_STATUS_CSV = DATA_DIR / 'generators-status.csv'
    LOADS_CSV = DATA_DIR / 'loads.csv'
    TRANSFORMERS_CSV = DATA_DIR / 'transformers.csv'
    SHUNT_IMPEDANCES_CSV = DATA_DIR / 'shunt_impedances.csv'
    SNAPSHOTS_CSV = DATA_DIR / 'snapshots.csv'
    INVESTMENT_PERIODS_CSV = DATA_DIR / 'investment_periods.csv'
    NETWORK_CSV = DATA_DIR / 'network.csv'

    # GeoJSON data files
    LINES_GEOJSON = DATA_DIR / 'oneline_lines.geojson'
    BUSES_GEOJSON = DATA_DIR / 'oneline_busses.geojson'

    # Conductor ratings and flow data
    CONDUCTOR_RATINGS_CSV = BACKEND_DIR / 'conductor_ratings.csv'
    LINE_FLOWS_CSV = BACKEND_DIR / 'line_flows_nominal.csv'

    # Output directory for generated files
    OUTPUT_DIR = BACKEND_DIR / 'output'

    @classmethod
    def ensure_directories_exist(cls):
        """
        Create necessary directories if they don't exist.

        Creates:
        - DATA_DIR: Main data storage directory
        - OUTPUT_DIR: Directory for generated maps and reports
        """
        cls.DATA_DIR.mkdir(exist_ok=True, parents=True)
        cls.OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

    @classmethod
    def validate_required_files(cls) -> dict[str, bool]:
        """
        Check which required data files exist.

        Returns:
            dict: Dictionary mapping file paths to existence status (True/False)

        Example:
            >>> status = DataConfig.validate_required_files()
            >>> if not status[DataConfig.LINES_CSV]:
            ...     print("Missing lines.csv file!")
        """
        required_files = {
            'lines.csv': cls.LINES_CSV,
            'buses.csv': cls.BUSES_CSV,
            'conductor_ratings.csv': cls.CONDUCTOR_RATINGS_CSV,
            'line_flows_nominal.csv': cls.LINE_FLOWS_CSV,
            'oneline_lines.geojson': cls.LINES_GEOJSON,
            'oneline_busses.geojson': cls.BUSES_GEOJSON,
        }

        return {name: path.exists() for name, path in required_files.items()}

    @classmethod
    def get_missing_files(cls) -> list[str]:
        """
        Get list of required files that are missing.

        Returns:
            list: Names of missing required files

        Example:
            >>> missing = DataConfig.get_missing_files()
            >>> if missing:
            ...     print(f"Missing files: {', '.join(missing)}")
        """
        status = cls.validate_required_files()
        return [name for name, exists in status.items() if not exists]

    @classmethod
    def get_data_summary(cls) -> dict:
        """
        Get summary of data configuration and file status.

        Returns:
            dict: Summary containing paths and file existence status

        Example:
            >>> summary = DataConfig.get_data_summary()
            >>> print(f"Data directory: {summary['data_dir']}")
            >>> print(f"All files present: {summary['all_files_present']}")
        """
        file_status = cls.validate_required_files()
        missing_files = cls.get_missing_files()

        return {
            'backend_dir': str(cls.BACKEND_DIR),
            'data_dir': str(cls.DATA_DIR),
            'output_dir': str(cls.OUTPUT_DIR),
            'file_status': file_status,
            'all_files_present': len(missing_files) == 0,
            'missing_files': missing_files,
            'total_required_files': len(file_status),
            'files_found': sum(1 for exists in file_status.values() if exists)
        }


class APIConfig:
    """
    Configuration for API settings and external services.

    Reads configuration from environment variables with sensible defaults.
    """

    # Flask configuration
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    # Claude API configuration
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
    CLAUDE_MODEL = os.getenv('CLAUDE_MODEL', 'claude-3-5-sonnet-20240620')
    MAX_TOKENS = int(os.getenv('MAX_TOKENS', '1024'))
    TEMPERATURE = float(os.getenv('TEMPERATURE', '0.7'))

    # CORS configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')

    # Caching configuration
    ENABLE_CACHE = os.getenv('ENABLE_CACHE', 'True').lower() == 'true'
    CACHE_TTL_SECONDS = int(os.getenv('CACHE_TTL_SECONDS', '300'))  # 5 minutes default

    @classmethod
    def is_claude_configured(cls) -> bool:
        """Check if Claude API is properly configured."""
        return bool(cls.ANTHROPIC_API_KEY and cls.ANTHROPIC_API_KEY.strip())

    @classmethod
    def validate_configuration(cls) -> dict[str, bool]:
        """
        Validate API configuration.

        Returns:
            dict: Validation results for different configuration aspects

        Example:
            >>> config_status = APIConfig.validate_configuration()
            >>> if not config_status['claude_api']:
            ...     print("Warning: Claude API not configured")
        """
        return {
            'claude_api': cls.is_claude_configured(),
            'flask_port_valid': 1 <= cls.FLASK_PORT <= 65535,
            'temperature_valid': 0 <= cls.TEMPERATURE <= 1,
            'max_tokens_valid': cls.MAX_TOKENS > 0,
        }

    @classmethod
    def get_api_summary(cls) -> dict:
        """Get summary of API configuration."""
        validation = cls.validate_configuration()
        return {
            'flask_host': cls.FLASK_HOST,
            'flask_port': cls.FLASK_PORT,
            'flask_debug': cls.FLASK_DEBUG,
            'claude_model': cls.CLAUDE_MODEL,
            'claude_configured': validation['claude_api'],
            'cache_enabled': cls.ENABLE_CACHE,
            'cache_ttl': cls.CACHE_TTL_SECONDS,
            'all_valid': all(validation.values())
        }


class AppConfig:
    """
    General application configuration parameters.

    Defines default values and limits for various application features.
    """

    # Stress level thresholds (percentage loading)
    STRESS_THRESHOLD_CAUTION = 60.0
    STRESS_THRESHOLD_HIGH = 90.0
    STRESS_THRESHOLD_CRITICAL = 100.0

    # Map visualization settings
    MAP_CENTER_LAT = 21.4
    MAP_CENTER_LON = -157.95
    MAP_ZOOM_LEVEL = 9.5
    MAP_STYLE = 'open-street-map'

    # Rating calculation defaults
    DEFAULT_AMBIENT_TEMP = 25.0  # Celsius
    DEFAULT_WIND_SPEED = 2.0  # feet/second
    DEFAULT_WIND_ANGLE = 90.0  # degrees
    DEFAULT_ELEVATION = 1000.0  # feet
    DEFAULT_LATITUDE = 21.0  # degrees (Hawaii)

    # Data validation limits
    MAX_VOLTAGE_KV = 500.0
    MIN_VOLTAGE_KV = 10.0
    MAX_POWER_FLOW_MW = 1000.0
    MAX_LINE_LOADING_PCT = 200.0  # Allow up to 200% for emergency conditions

    # Logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    @classmethod
    def get_stress_level(cls, loading_pct: float) -> str:
        """
        Determine stress level from loading percentage.

        Args:
            loading_pct: Loading percentage (0-100+)

        Returns:
            str: Stress level ('normal', 'caution', 'high', 'critical')

        Example:
            >>> AppConfig.get_stress_level(45.0)
            'normal'
            >>> AppConfig.get_stress_level(95.0)
            'high'
        """
        if loading_pct < cls.STRESS_THRESHOLD_CAUTION:
            return 'normal'
        elif loading_pct < cls.STRESS_THRESHOLD_HIGH:
            return 'caution'
        elif loading_pct < cls.STRESS_THRESHOLD_CRITICAL:
            return 'high'
        else:
            return 'critical'

    @classmethod
    def get_stress_color(cls, loading_pct: float) -> str:
        """
        Get color code for stress visualization.

        Args:
            loading_pct: Loading percentage (0-100+)

        Returns:
            str: Hex color code

        Example:
            >>> AppConfig.get_stress_color(45.0)
            '#22c55e'  # Green
        """
        stress_level = cls.get_stress_level(loading_pct)
        color_map = {
            'normal': '#22c55e',    # Green
            'caution': '#eab308',   # Yellow
            'high': '#f97316',      # Orange
            'critical': '#ef4444'   # Red
        }
        return color_map.get(stress_level, '#9ca3af')  # Gray as fallback

    @classmethod
    def get_default_weather_params(cls) -> dict:
        """
        Get default weather parameters for rating calculations.

        Returns:
            dict: Default weather parameters

        Example:
            >>> weather = AppConfig.get_default_weather_params()
            >>> weather['Ta']
            25.0
        """
        return {
            'Ta': cls.DEFAULT_AMBIENT_TEMP,
            'WindVelocity': cls.DEFAULT_WIND_SPEED,
            'WindAngleDeg': cls.DEFAULT_WIND_ANGLE,
            'SunTime': 12,
            'Date': '12 Jun',
            'Emissivity': 0.8,
            'Absorptivity': 0.8,
            'Direction': 'EastWest',
            'Atmosphere': 'Clear',
            'Elevation': cls.DEFAULT_ELEVATION,
            'Latitude': cls.DEFAULT_LATITUDE
        }


def print_configuration_status():
    """
    Print comprehensive configuration status to console.

    Useful for debugging and verifying configuration on startup.
    """
    print("\n" + "=" * 80)
    print("GRID MONITORING APPLICATION - CONFIGURATION STATUS")
    print("=" * 80)

    # Data configuration
    print("\n[DATA CONFIGURATION]")
    data_summary = DataConfig.get_data_summary()
    print(f"Backend Directory: {data_summary['backend_dir']}")
    print(f"Data Directory:    {data_summary['data_dir']}")
    print(f"Output Directory:  {data_summary['output_dir']}")
    print(f"\nRequired Files: {data_summary['files_found']}/{data_summary['total_required_files']}")

    if data_summary['missing_files']:
        print(f"\n! WARNING: Missing files:")
        for filename in data_summary['missing_files']:
            print(f"  - {filename}")
    else:
        print("[OK] All required data files found")

    # API configuration
    print("\n[API CONFIGURATION]")
    api_summary = APIConfig.get_api_summary()
    print(f"Flask Host:        {api_summary['flask_host']}")
    print(f"Flask Port:        {api_summary['flask_port']}")
    print(f"Debug Mode:        {api_summary['flask_debug']}")
    print(f"Claude Model:      {api_summary['claude_model']}")
    print(f"Claude API:        {'[OK] Configured' if api_summary['claude_configured'] else '[X] Not Configured'}")
    print(f"Cache Enabled:     {api_summary['cache_enabled']}")

    if not api_summary['all_valid']:
        print("\n! WARNING: Some API configuration values are invalid")

    # App configuration
    print("\n[APPLICATION SETTINGS]")
    print(f"Stress Thresholds: Caution={AppConfig.STRESS_THRESHOLD_CAUTION}%, "
          f"High={AppConfig.STRESS_THRESHOLD_HIGH}%, "
          f"Critical={AppConfig.STRESS_THRESHOLD_CRITICAL}%")
    print(f"Map Center:        ({AppConfig.MAP_CENTER_LAT}, {AppConfig.MAP_CENTER_LON})")
    print(f"Log Level:         {AppConfig.LOG_LEVEL}")

    print("\n" + "=" * 80 + "\n")


if __name__ == '__main__':
    # When run directly, print configuration status
    print_configuration_status()

    # Optionally create required directories
    print("Creating required directories...")
    DataConfig.ensure_directories_exist()
    print("[OK] Directories created/verified")
