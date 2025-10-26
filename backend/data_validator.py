#!/usr/bin/env python3
"""
Data Validation Utilities Module

Provides comprehensive validation functions for grid data to ensure:
- Data integrity and consistency
- Proper ranges for electrical parameters
- Referential integrity between datasets
- Physics-based validation rules

This module complements Pydantic validation with domain-specific checks.
"""

import logging
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

from data_models import LineData, BusData, ConductorParams, PowerFlow
from config import AppConfig

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    info: List[str]

    def __bool__(self):
        """Validation passes if there are no errors."""
        return self.is_valid and len(self.errors) == 0

    def add_error(self, message: str):
        """Add an error message."""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)

    def add_info(self, message: str):
        """Add an info message."""
        self.info.append(message)

    def get_summary(self) -> str:
        """Get formatted summary of validation results."""
        parts = []
        if self.errors:
            parts.append(f"ERRORS ({len(self.errors)}):")
            parts.extend([f"  - {e}" for e in self.errors[:10]])
            if len(self.errors) > 10:
                parts.append(f"  ... and {len(self.errors) - 10} more errors")

        if self.warnings:
            parts.append(f"\nWARNINGS ({len(self.warnings)}):")
            parts.extend([f"  - {w}" for w in self.warnings[:10]])
            if len(self.warnings) > 10:
                parts.append(f"  ... and {len(self.warnings) - 10} more warnings")

        if self.info:
            parts.append(f"\nINFO ({len(self.info)}):")
            parts.extend([f"  - {i}" for i in self.info[:5]])

        return "\n".join(parts) if parts else "Validation passed - no issues found"


class DataValidator:
    """Validator for grid data with domain-specific rules."""

    @staticmethod
    def validate_line_data(line: LineData) -> ValidationResult:
        """
        Validate a single transmission line.

        Args:
            line: Line data to validate

        Returns:
            ValidationResult: Validation results
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[], info=[])

        # Check electrical parameters are positive
        if line.r <= 0:
            result.add_error(f"Line {line.name}: Resistance must be positive (got {line.r})")

        if line.x <= 0:
            result.add_warning(f"Line {line.name}: Reactance is zero or negative (got {line.x})")

        if line.s_nom <= 0:
            result.add_error(f"Line {line.name}: Capacity must be positive (got {line.s_nom})")

        # Check X/R ratio (typical range 2-15 for transmission lines)
        if line.r > 0:
            xr_ratio = abs(line.x / line.r)
            if xr_ratio < 1:
                result.add_warning(
                    f"Line {line.name}: Unusually low X/R ratio ({xr_ratio:.2f}), "
                    "typical for transmission is 2-15"
                )
            elif xr_ratio > 20:
                result.add_warning(
                    f"Line {line.name}: Unusually high X/R ratio ({xr_ratio:.2f})"
                )

        # Check MOT is reasonable
        if line.MOT < 50 or line.MOT > 150:
            result.add_warning(
                f"Line {line.name}: Unusual Maximum Operating Temperature ({line.MOT}°C), "
                "typical range is 50-150°C"
            )

        # Check voltage angle limits if present
        if line.v_ang_min is not None and line.v_ang_max is not None:
            if line.v_ang_min >= line.v_ang_max:
                result.add_error(
                    f"Line {line.name}: v_ang_min ({line.v_ang_min}) must be less than "
                    f"v_ang_max ({line.v_ang_max})"
                )

        # Check bus names are different
        if line.bus0 == line.bus1:
            result.add_error(f"Line {line.name}: From and to buses are the same ({line.bus0})")

        return result

    @staticmethod
    def validate_bus_data(bus: BusData) -> ValidationResult:
        """
        Validate a single bus/substation.

        Args:
            bus: Bus data to validate

        Returns:
            ValidationResult: Validation results
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[], info=[])

        # Check voltage is reasonable
        if bus.v_nom not in [69.0, 138.0]:
            result.add_warning(
                f"Bus {bus.name}: Unusual voltage level ({bus.v_nom} kV), "
                "this system typically uses 69kV or 138kV"
            )

        # Check voltage limits are properly ordered
        if bus.v_mag_pu_min >= bus.v_mag_pu_max:
            result.add_error(
                f"Bus {bus.name}: v_mag_pu_min ({bus.v_mag_pu_min}) must be less than "
                f"v_mag_pu_max ({bus.v_mag_pu_max})"
            )

        # Check voltage setpoint is within limits
        if bus.v_mag_pu_set < bus.v_mag_pu_min or bus.v_mag_pu_set > bus.v_mag_pu_max:
            result.add_warning(
                f"Bus {bus.name}: Voltage setpoint ({bus.v_mag_pu_set}) is outside limits "
                f"[{bus.v_mag_pu_min}, {bus.v_mag_pu_max}]"
            )

        # Check geographic coordinates are reasonable for Hawaii
        # Hawaii longitude: -160 to -154, latitude: 18 to 23
        if not (-161 < bus.x < -153):
            result.add_warning(
                f"Bus {bus.name}: Longitude ({bus.x}) is outside Hawaii range (-161 to -153)"
            )

        if not (18 < bus.y < 23):
            result.add_warning(
                f"Bus {bus.name}: Latitude ({bus.y}) is outside Hawaii range (18 to 23)"
            )

        # Check load values are reasonable
        if abs(bus.Pd) > 1000:
            result.add_warning(
                f"Bus {bus.name}: Very high active power demand ({bus.Pd} MW)"
            )

        if abs(bus.Qd) > 500:
            result.add_warning(
                f"Bus {bus.name}: Very high reactive power demand ({bus.Qd} MVAr)"
            )

        return result

    @staticmethod
    def validate_power_flow(flow: PowerFlow, line: LineData) -> ValidationResult:
        """
        Validate power flow data against line capacity.

        Args:
            flow: Power flow data
            line: Associated line data

        Returns:
            ValidationResult: Validation results
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[], info=[])

        # Check if flow exceeds line capacity (approximate check using active power)
        # Convert MW to MVA (approximate, assuming power factor ~0.95)
        apparent_power = abs(flow.p0_nominal) / 0.95

        if apparent_power > line.s_nom:
            result.add_error(
                f"Line {flow.name}: Power flow ({flow.p0_nominal:.1f} MW ≈ {apparent_power:.1f} MVA) "
                f"exceeds capacity ({line.s_nom:.1f} MVA)"
            )
        elif apparent_power > line.s_nom * 0.9:
            result.add_warning(
                f"Line {flow.name}: Power flow ({flow.p0_nominal:.1f} MW) is near capacity "
                f"({line.s_nom:.1f} MVA)"
            )

        # Check for very low utilization (might indicate data issue)
        if line.s_nom > 0 and apparent_power < line.s_nom * 0.01:
            result.add_info(
                f"Line {flow.name}: Very low utilization "
                f"({apparent_power/line.s_nom*100:.1f}%)"
            )

        return result

    @staticmethod
    def validate_conductor_params(conductor: ConductorParams) -> ValidationResult:
        """
        Validate conductor parameters.

        Args:
            conductor: Conductor parameters

        Returns:
            ValidationResult: Validation results
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[], info=[])

        # Check ratings are positive
        if conductor.RatingAmps <= 0:
            result.add_error(
                f"Conductor {conductor.ConductorName}: "
                f"Rating in amps must be positive (got {conductor.RatingAmps})"
            )

        if conductor.RatingMVA_69 <= 0 or conductor.RatingMVA_138 <= 0:
            result.add_error(
                f"Conductor {conductor.ConductorName}: MVA ratings must be positive"
            )

        # Check relationship between voltage levels
        # MVA_138 should be roughly 2x MVA_69 (138/69 = 2)
        if conductor.RatingMVA_69 > 0:
            ratio = conductor.RatingMVA_138 / conductor.RatingMVA_69
            expected_ratio = 138.0 / 69.0  # 2.0
            if abs(ratio - expected_ratio) > 0.3:
                result.add_warning(
                    f"Conductor {conductor.ConductorName}: "
                    f"Unexpected MVA ratio between voltage levels ({ratio:.2f}, expected ~{expected_ratio:.2f})"
                )

        # Check ampere rating vs MVA rating consistency
        # MVA = sqrt(3) * kV * kA = 1.732 * kV * I/1000
        expected_mva_69 = 1.732 * 69 * conductor.RatingAmps / 1000
        expected_mva_138 = 1.732 * 138 * conductor.RatingAmps / 1000

        if abs(conductor.RatingMVA_69 - expected_mva_69) > expected_mva_69 * 0.1:
            result.add_warning(
                f"Conductor {conductor.ConductorName}: "
                f"MVA rating at 69kV ({conductor.RatingMVA_69:.1f}) doesn't match "
                f"ampere rating ({expected_mva_69:.1f} expected)"
            )

        return result

    @staticmethod
    def validate_dataset_consistency(
        lines: List[LineData],
        buses: List[BusData],
        flows: List[PowerFlow],
        conductors: List[ConductorParams]
    ) -> ValidationResult:
        """
        Validate consistency across entire dataset.

        Args:
            lines: All transmission lines
            buses: All buses
            flows: All power flows
            conductors: All conductor types

        Returns:
            ValidationResult: Validation results
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[], info=[])

        # Create lookup sets
        bus_names = {bus.name for bus in buses}
        bus_full_names = {bus.BusName for bus in buses}
        all_bus_identifiers = bus_names | bus_full_names

        conductor_types = {cond.ConductorName for cond in conductors}
        flow_line_names = {flow.name for flow in flows}
        line_names = {line.name for line in lines}

        # Check referential integrity: lines reference valid buses
        for line in lines:
            if line.bus0_name not in all_bus_identifiers:
                result.add_error(
                    f"Line {line.name} references unknown from-bus: {line.bus0_name}"
                )
            if line.bus1_name not in all_bus_identifiers:
                result.add_error(
                    f"Line {line.name} references unknown to-bus: {line.bus1_name}"
                )

            # Check conductor type exists in library
            if line.conductor not in conductor_types:
                result.add_warning(
                    f"Line {line.name} uses unknown conductor type: {line.conductor}"
                )

        # Check coverage: all lines have flow data
        lines_without_flows = line_names - flow_line_names
        if lines_without_flows:
            result.add_warning(
                f"{len(lines_without_flows)} lines have no power flow data: "
                f"{list(lines_without_flows)[:5]}"
            )

        # Check for orphaned flows (flows without corresponding lines)
        orphaned_flows = flow_line_names - line_names
        if orphaned_flows:
            result.add_warning(
                f"{len(orphaned_flows)} power flows reference non-existent lines: "
                f"{list(orphaned_flows)[:5]}"
            )

        # Dataset statistics
        result.add_info(f"Total lines: {len(lines)}")
        result.add_info(f"Total buses: {len(buses)}")
        result.add_info(f"Total power flows: {len(flows)}")
        result.add_info(f"Total conductor types: {len(conductors)}")
        result.add_info(
            f"Data coverage: {len(flow_line_names)} of {len(line_names)} lines have flow data "
            f"({len(flow_line_names)/len(line_names)*100:.1f}%)"
        )

        return result

    @staticmethod
    def validate_all_data(
        lines: List[LineData],
        buses: List[BusData],
        flows: List[PowerFlow],
        conductors: List[ConductorParams],
        strict: bool = False
    ) -> ValidationResult:
        """
        Run comprehensive validation on all data.

        Args:
            lines: All transmission lines
            buses: All buses
            flows: All power flows
            conductors: All conductor types
            strict: If True, treat warnings as errors

        Returns:
            ValidationResult: Combined validation results
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[], info=[])

        # Validate individual lines
        for line in lines:
            line_result = DataValidator.validate_line_data(line)
            result.errors.extend(line_result.errors)
            result.warnings.extend(line_result.warnings)

        # Validate individual buses
        for bus in buses:
            bus_result = DataValidator.validate_bus_data(bus)
            result.errors.extend(bus_result.errors)
            result.warnings.extend(bus_result.warnings)

        # Validate conductors
        for conductor in conductors:
            cond_result = DataValidator.validate_conductor_params(conductor)
            result.errors.extend(cond_result.errors)
            result.warnings.extend(cond_result.warnings)

        # Validate power flows against lines
        flow_dict = {flow.name: flow for flow in flows}
        line_dict = {line.name: line for line in lines}

        for flow_name, flow in flow_dict.items():
            if flow_name in line_dict:
                flow_result = DataValidator.validate_power_flow(flow, line_dict[flow_name])
                result.errors.extend(flow_result.errors)
                result.warnings.extend(flow_result.warnings)

        # Validate dataset consistency
        consistency_result = DataValidator.validate_dataset_consistency(
            lines, buses, flows, conductors
        )
        result.errors.extend(consistency_result.errors)
        result.warnings.extend(consistency_result.warnings)
        result.info.extend(consistency_result.info)

        # If strict mode, treat warnings as errors
        if strict and result.warnings:
            result.errors.extend([f"STRICT MODE: {w}" for w in result.warnings])
            result.warnings = []

        # Update validation status
        result.is_valid = len(result.errors) == 0

        return result


def validate_csv_data_quality(
    csv_loader
) -> Tuple[bool, str]:
    """
    High-level validation function for CSV data quality.

    Args:
        csv_loader: CSVDataLoader instance

    Returns:
        Tuple of (is_valid, summary_message)

    Example:
        >>> from csv_data_loader import get_loader
        >>> from data_validator import validate_csv_data_quality
        >>>
        >>> loader = get_loader()
        >>> is_valid, message = validate_csv_data_quality(loader)
        >>> print(message)
    """
    try:
        # Load all data
        lines = csv_loader.get_all_lines(validate=True)
        buses = csv_loader.get_all_buses(validate=True)
        flows = csv_loader.get_all_power_flows(validate=True)
        conductors = csv_loader.get_all_conductor_params(validate=True)

        # Run validation
        result = DataValidator.validate_all_data(lines, buses, flows, conductors)

        summary = f"""
DATA VALIDATION SUMMARY
{'='*60}
Status: {'[OK] PASSED' if result.is_valid else '[X] FAILED'}

Errors:   {len(result.errors)}
Warnings: {len(result.warnings)}
Info:     {len(result.info)}

{result.get_summary()}
{'='*60}
"""
        return result.is_valid, summary

    except Exception as e:
        error_msg = f"Validation failed with exception: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


if __name__ == '__main__':
    # Demo validation
    from csv_data_loader import CSVDataLoader

    print("\n" + "=" * 80)
    print("DATA VALIDATOR - DEMO")
    print("=" * 80)

    try:
        loader = CSVDataLoader()
        is_valid, summary = validate_csv_data_quality(loader)
        print(summary)

        if is_valid:
            print("\n[OK] All data validation checks passed!")
        else:
            print("\n[X] Data validation found issues - please review above")

    except Exception as e:
        print(f"\n[X] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80 + "\n")
