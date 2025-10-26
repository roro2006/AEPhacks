#!/usr/bin/env python3
"""
Data models for grid monitoring application using Pydantic for validation.

This module defines strongly-typed data models for:
- Transmission lines
- Buses/substations
- Conductors
- Power flows
- Weather parameters
- Rating results

All models include validation rules to ensure data integrity.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field, validator, confloat, conint
from datetime import datetime


class LineData(BaseModel):
    """
    Transmission line data model.

    Represents a single transmission line with electrical properties
    and physical characteristics.
    """
    name: str = Field(..., description="Unique line identifier (e.g., 'L0', 'L1')")
    bus0: str = Field(..., description="From bus identifier")
    bus1: str = Field(..., description="To bus identifier")
    bus0_name: str = Field(..., description="From bus name")
    bus1_name: str = Field(..., description="To bus name")
    branch_name: str = Field(..., description="Full descriptive name of the line")
    ckt: str = Field(..., description="Circuit identifier")

    @validator('bus0', 'bus1', 'bus0_name', 'bus1_name', 'ckt', 'branch_name', pre=True)
    def convert_to_string(cls, v):
        """Convert values to strings and handle NaN."""
        import math
        if v is None or (isinstance(v, float) and math.isnan(v)):
            return ""
        return str(v)

    # Electrical parameters
    x: confloat(ge=0) = Field(..., description="Reactance in Ohms")
    r: confloat(ge=0) = Field(..., description="Resistance in Ohms")
    b: float = Field(..., description="Susceptance in Siemens")
    s_nom: confloat(gt=0) = Field(..., description="Nominal power capacity in MVA")

    # Physical properties
    conductor: str = Field(..., description="Conductor type (e.g., '795 ACSR 26/7 DRAKE')")
    MOT: conint(ge=0, le=150) = Field(..., description="Maximum Operating Temperature in Celsius")

    # Operating limits
    v_ang_min: Optional[float] = Field(None, description="Minimum voltage angle in degrees")
    v_ang_max: Optional[float] = Field(None, description="Maximum voltage angle in degrees")
    status: Optional[int] = Field(1, description="Line status (1=in service, 0=out of service)")
    original_index: Optional[int] = Field(None, description="Original index from source data")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "L0",
                "bus0": "0",
                "bus1": "1",
                "bus0_name": "ALOHA138",
                "bus1_name": "HILL138",
                "branch_name": "ALOHA 138 - HILL 138 1",
                "ckt": "1",
                "x": 3.42,
                "r": 0.856,
                "b": 0.000115,
                "s_nom": 184.752,
                "conductor": "795 ACSR 26/7 DRAKE",
                "MOT": 100,
                "v_ang_min": -60.0,
                "v_ang_max": 60.0,
                "status": 1,
                "original_index": 0
            }
        }


class BusData(BaseModel):
    """
    Bus/substation data model.

    Represents a node in the power grid with voltage and load information.
    """
    name: str = Field(..., description="Unique bus identifier")
    BusName: str = Field(..., description="Descriptive bus name")
    v_nom: confloat(gt=0) = Field(..., description="Nominal voltage in kV (69.0 or 138.0)")

    @validator('name', pre=True)
    def convert_name_to_string(cls, v):
        """Convert bus name to string."""
        if v is not None:
            return str(v)
        return v

    # Geographic coordinates
    x: float = Field(..., description="Longitude coordinate")
    y: float = Field(..., description="Latitude coordinate")

    # Voltage control parameters
    v_mag_pu_set: confloat(ge=0.9, le=1.1) = Field(1.0, description="Voltage magnitude setpoint in per-unit")
    v_mag_pu_min: confloat(ge=0.8, le=1.0) = Field(0.95, description="Minimum voltage magnitude in per-unit")
    v_mag_pu_max: confloat(ge=1.0, le=1.2) = Field(1.05, description="Maximum voltage magnitude in per-unit")
    control: Literal['PQ', 'PV', 'Slack'] = Field('PQ', description="Control type")

    # Load parameters
    Pd: float = Field(0.0, description="Active power demand in MW")
    Qd: float = Field(0.0, description="Reactive power demand in MVAr")

    # Shunt parameters
    Gs: float = Field(0.0, description="Shunt conductance in per-unit")
    Bs: float = Field(0.0, description="Shunt susceptance in per-unit")

    # Zone information
    area: Optional[int] = Field(None, description="Area number")
    zone: Optional[int] = Field(None, description="Zone number")
    v_ang_set: Optional[float] = Field(None, description="Voltage angle setpoint in degrees")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "0",
                "BusName": "ALOHA138",
                "v_nom": 138.0,
                "x": -157.936,
                "y": 21.345,
                "v_mag_pu_set": 1.0,
                "v_mag_pu_min": 0.95,
                "v_mag_pu_max": 1.05,
                "control": "PV",
                "Pd": 0.0,
                "Qd": 0.0,
                "Gs": 0.0,
                "Bs": 0.0,
                "area": 1,
                "zone": 1,
                "v_ang_set": 0.0
            }
        }


class ConductorParams(BaseModel):
    """
    Conductor library parameters.

    Contains thermal and electrical ratings for different conductor types.
    """
    ConductorName: str = Field(..., description="Conductor type identifier")
    MOT: conint(ge=0, le=150) = Field(..., description="Maximum Operating Temperature in Celsius")
    RatingAmps: confloat(gt=0) = Field(..., description="Static thermal rating in Amperes")
    RatingMVA_69: confloat(gt=0) = Field(..., description="Static rating at 69kV in MVA")
    RatingMVA_138: confloat(gt=0) = Field(..., description="Static rating at 138kV in MVA")

    class Config:
        json_schema_extra = {
            "example": {
                "ConductorName": "795 ACSR 26/7 DRAKE",
                "MOT": 100,
                "RatingAmps": 900.0,
                "RatingMVA_69": 107.6,
                "RatingMVA_138": 215.1
            }
        }


class PowerFlow(BaseModel):
    """
    Power flow data for a transmission line.

    Contains real power flow for nominal operating conditions.
    """
    name: str = Field(..., description="Line identifier matching LineData.name")
    p0_nominal: float = Field(..., description="Nominal active power flow in MW")

    @validator('p0_nominal')
    def validate_power_flow(cls, v):
        """Validate power flow is within reasonable bounds."""
        if abs(v) > 1000:  # 1000 MW is a very high flow for this system
            raise ValueError(f"Power flow {v} MW seems unreasonably high")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "name": "L0",
                "p0_nominal": 45.2
            }
        }


class WeatherParams(BaseModel):
    """
    Weather parameters for dynamic line rating calculations.

    Used in IEEE 738 thermal rating calculations.
    """
    Ta: float = Field(..., ge=-50, le=60, description="Ambient temperature in Celsius")
    WindVelocity: confloat(ge=0, le=100) = Field(..., description="Wind speed in feet/second")
    WindAngleDeg: confloat(ge=0, le=360) = Field(90, description="Wind angle relative to line in degrees")
    SunTime: conint(ge=0, le=24) = Field(12, description="Hour of day (0-24)")
    Date: str = Field("12 Jun", description="Date string for solar calculations")
    Emissivity: confloat(ge=0, le=1) = Field(0.8, description="Conductor emissivity coefficient")
    Absorptivity: confloat(ge=0, le=1) = Field(0.8, description="Solar absorptivity coefficient")
    Direction: Literal['EastWest', 'NorthSouth'] = Field('EastWest', description="Line orientation")
    Atmosphere: Literal['Clear', 'Industrial'] = Field('Clear', description="Atmospheric condition")
    Elevation: confloat(ge=0, le=15000) = Field(1000, description="Elevation in feet")
    Latitude: confloat(ge=-90, le=90) = Field(21, description="Latitude in degrees")

    class Config:
        json_schema_extra = {
            "example": {
                "Ta": 25,
                "WindVelocity": 2.0,
                "WindAngleDeg": 90,
                "SunTime": 12,
                "Date": "12 Jun",
                "Emissivity": 0.8,
                "Absorptivity": 0.8,
                "Direction": "EastWest",
                "Atmosphere": "Clear",
                "Elevation": 1000,
                "Latitude": 21
            }
        }


class LineRatingResult(BaseModel):
    """
    Result of line rating calculation.

    Contains all computed values for a transmission line including
    thermal ratings, power flows, and stress levels.
    """
    name: str = Field(..., description="Line identifier")
    branch_name: str = Field(..., description="Full line description")
    conductor: str = Field(..., description="Conductor type")
    MOT: int = Field(..., description="Maximum Operating Temperature")
    voltage_kv: confloat(gt=0) = Field(..., description="Line voltage in kV")

    # Rating values
    rating_amps: confloat(ge=0) = Field(..., description="Dynamic thermal rating in Amperes")
    rating_mva: confloat(ge=0) = Field(..., description="Dynamic thermal rating in MVA")
    static_rating_mva: confloat(ge=0) = Field(..., description="Static thermal rating in MVA")

    # Flow and loading
    flow_mva: float = Field(..., description="Current power flow in MVA")
    loading_pct: confloat(ge=0) = Field(..., description="Loading percentage")
    margin_mva: float = Field(..., description="Available capacity margin in MVA")

    # Status
    stress_level: Literal['normal', 'caution', 'high', 'critical'] = Field(
        ...,
        description="Stress level classification"
    )

    # Bus connections
    bus0: str = Field(..., description="From bus name")
    bus1: str = Field(..., description="To bus name")

    @validator('stress_level', pre=True, always=True)
    def determine_stress_level(cls, v, values):
        """Auto-calculate stress level based on loading percentage."""
        if 'loading_pct' in values:
            loading = values['loading_pct']
            if loading < 60:
                return 'normal'
            elif loading < 90:
                return 'caution'
            elif loading < 100:
                return 'high'
            else:
                return 'critical'
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "name": "L0",
                "branch_name": "ALOHA 138 - HILL 138 1",
                "conductor": "795 ACSR 26/7 DRAKE",
                "MOT": 100,
                "voltage_kv": 138.0,
                "rating_amps": 900.0,
                "rating_mva": 215.1,
                "static_rating_mva": 215.1,
                "flow_mva": 45.2,
                "loading_pct": 21.0,
                "margin_mva": 169.9,
                "stress_level": "normal",
                "bus0": "ALOHA138",
                "bus1": "HILL138"
            }
        }


class RatingSummary(BaseModel):
    """
    Summary statistics for all line ratings.

    Provides aggregated information about grid stress levels.
    """
    total_lines: conint(ge=0) = Field(..., description="Total number of lines analyzed")
    overloaded_lines: conint(ge=0) = Field(..., description="Lines at or above 100% loading")
    high_stress_lines: conint(ge=0) = Field(..., description="Lines between 90-100% loading")
    caution_lines: conint(ge=0) = Field(..., description="Lines between 60-90% loading")
    normal_lines: conint(ge=0) = Field(..., description="Lines below 60% loading")

    avg_loading: confloat(ge=0) = Field(..., description="Average loading percentage across all lines")
    max_loading: confloat(ge=0) = Field(..., description="Maximum loading percentage")
    min_loading: confloat(ge=0) = Field(..., description="Minimum loading percentage")

    timestamp: datetime = Field(default_factory=datetime.now, description="Time of calculation")

    class Config:
        json_schema_extra = {
            "example": {
                "total_lines": 77,
                "overloaded_lines": 0,
                "high_stress_lines": 5,
                "caution_lines": 12,
                "normal_lines": 60,
                "avg_loading": 35.2,
                "max_loading": 98.5,
                "min_loading": 2.1,
                "timestamp": "2025-10-25T10:30:00"
            }
        }


class DataValidationError(Exception):
    """Custom exception for data validation errors."""
    pass


class DataLoadError(Exception):
    """Custom exception for data loading errors."""
    pass


class ConfigurationError(Exception):
    """Custom exception for configuration errors."""
    pass
