"""Integration layer connecting project CSV data to the IEEE-738 implementation.

This module reads `lines.csv` (via the project's CSV loader) and
`data/conductor_library.csv`, maps the conductor properties into the
`ieee738.ConductorParams` model, computes steady-state thermal ratings
and exports a CSV with MVA ratings at 69 kV and 138 kV.

Key behaviors:
- Converts RES_25C/RES_50C (ohms/mile) -> RLo/RHi (ohms/ft) by dividing by 5280
- Converts CDRAD_in (radius, inches) -> Diameter (inches) by multiplying by 2
- Uses ambient defaults from `AppConfig.get_default_weather_params()` unless
  alternate ambient_defaults are provided to the engine.
- Validates MOT (clamped to 50-100°C) and handles missing conductors with
  meaningful error messages recorded in the output CSV.
"""

from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from config import DataConfig, AppConfig
from csv_data_loader import get_loader
import ieee738

logger = logging.getLogger(__name__)


class IEEE738RatingEngine:
    """Engine to compute IEEE-738 steady state thermal ratings for lines.

    Typical usage:
        engine = IEEE738RatingEngine()
        df = engine.compute_all_line_ratings()
"""

    REQUIRED_CONDUCTOR_COLUMNS = {"ConductorName", "RES_25C", "RES_50C", "CDRAD_in"}

    def __init__(self, loader=None, ambient_defaults: Optional[Dict[str, Any]] = None):
        self.loader = loader or get_loader()
        self.ambient_defaults = ambient_defaults or AppConfig.get_default_weather_params()
        self._cond_df: Optional[pd.DataFrame] = None

    def _load_conductor_library(self) -> pd.DataFrame:
        path = DataConfig.DATA_DIR / "conductor_library.csv"
        if not path.exists():
            raise FileNotFoundError(f"Conductor library not found at: {path}")

        df = pd.read_csv(path)
        missing = self.REQUIRED_CONDUCTOR_COLUMNS - set(df.columns)
        if missing:
            raise ValueError(f"Missing columns in conductor_library.csv: {missing}")

        df["ConductorName"] = df["ConductorName"].astype(str).str.strip()
        self._cond_df = df
        return df

    def _get_conductor_row(self, conductor_name: str) -> Optional[pd.Series]:
        if self._cond_df is None:
            self._load_conductor_library()

        row = self._cond_df[self._cond_df["ConductorName"] == conductor_name]
        if row.empty:
            return None
        return row.iloc[0]

    def compute_line_rating(self, line_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Compute IEEE-738 rating for a single line dictionary.

        Args:
            line_dict: dict with at least 'name', 'conductor', and optional 'MOT'

        Returns:
            dict: result row with keys matching compute_all_line_ratings output
        """
        # support either pydantic model or dict
        ld = line_dict if isinstance(line_dict, dict) else line_dict.__dict__
        line_name = ld.get("name")
        conductor_type = ld.get("conductor")
        mot = ld.get("MOT")

        row_result: Dict[str, Any] = {
            "line_name": line_name,
            "conductor_type": conductor_type,
            "mot_celsius": None,
            "rating_amps": None,
            "rating_69kv_mva": None,
            "rating_138kv_mva": None,
            "error": None,
        }

        try:
            if not conductor_type or pd.isna(conductor_type):
                raise ValueError("Missing conductor type")

            cond_row = self._get_conductor_row(conductor_type)
            if cond_row is None:
                raise KeyError(f"Conductor '{conductor_type}' not found in conductor_library.csv")

            # Determine MOT
            if mot is None or pd.isna(mot):
                logger.warning(f"Line {line_name}: MOT missing, using ambient Ta default: {self.ambient_defaults.get('Ta')}")
                mot_val = float(self.ambient_defaults.get("Ta", 75.0))
            else:
                mot_val = float(mot)

            # Validate MOT range
            if mot_val < 50.0 or mot_val > 100.0:
                logger.warning(f"Line {line_name}: MOT {mot_val} outside expected range (50-100). Clamping.")
                mot_val = max(50.0, min(100.0, mot_val))

            row_result["mot_celsius"] = mot_val

            # Extract conductor properties
            res25 = float(cond_row["RES_25C"])  # ohms/mile
            res50 = float(cond_row["RES_50C"])  # ohms/mile
            crad_in = float(cond_row["CDRAD_in"])  # radius in inches

            # Convert units
            RLo = res25 / 5280.0
            RHi = res50 / 5280.0
            Diameter = crad_in * 2.0

            acsr = {
                "TLo": 25.0,
                "THi": 50.0,
                "RLo": RLo,
                "RHi": RHi,
                "Diameter": Diameter,
                "Tc": mot_val,
                "ConductorsPerBundle": 1,
            }

            params = {**self.ambient_defaults, **acsr}
            cp = ieee738.ConductorParams(**params)
            con = ieee738.Conductor(cp)

            rating_amps = con.steady_state_thermal_rating()
            row_result["rating_amps"] = float(rating_amps)
            row_result["rating_69kv_mva"] = (math.sqrt(3) * rating_amps * 69000.0) / 1e6
            row_result["rating_138kv_mva"] = (math.sqrt(3) * rating_amps * 138000.0) / 1e6

        except Exception as e:
            logger.exception(f"Failed to compute rating for line {line_name}: {e}")
            row_result["error"] = str(e)

        return row_result

    def compute_all_line_ratings(self, output_csv: Optional[Path] = None) -> pd.DataFrame:
        """Compute ratings for all lines and optionally write CSV.

        Returns:
            pd.DataFrame with columns: line_name, conductor_type, mot_celsius,
            rating_amps, rating_69kv_mva, rating_138kv_mva, error
        """
        lines = self.loader.get_all_lines(validate=False)
        results: List[Dict[str, Any]] = []

        for line in lines:
            # support either pydantic model or dict
            line_dict = line if isinstance(line, dict) else line.__dict__
            row_result = self.compute_line_rating(line_dict)
            results.append(row_result)

        df_out = pd.DataFrame(results)

        out_path = output_csv or (DataConfig.OUTPUT_DIR / "line_ratings_ieee738.csv")
        DataConfig.ensure_directories_exist()
        df_out.to_csv(out_path, index=False)
        logger.info(f"Wrote ratings to {out_path}")
        return df_out


def run_example():
    engine = IEEE738RatingEngine()
    df = engine.compute_all_line_ratings()
    print(df.head())
    return df


if __name__ == "__main__":
    run_example()
