# IEEE-738 Integration — Overview

This document describes the integrated IEEE-738 steady-state thermal rating
pipeline added to the project. It explains CSV formats, assumptions, how to run
the calculation, and how to modify ambient conditions.

## Files added
- `backend/ieee738_integration.py` — main integration engine. Uses the existing
  `csv_data_loader` to read `lines.csv` and `data/conductor_library.csv`, maps
  parameters into `ieee738.ConductorParams`, computes ampacity, and writes a
  CSV with MVA ratings.
- `backend/run_ieee738.py` — simple runner script to execute the engine and
  write results to `backend/output/line_ratings_ieee738.csv`.

## Expected CSV formats

1) data/conductor_library.csv

Columns required:

- `ConductorName` — exact string that matches `lines.csv` conductor field
- `RES_25C` — resistance at 25°C in ohms/mile
- `RES_50C` — resistance at 50°C in ohms/mile
- `CDRAD_in` — conductor radius in inches

The integration converts `RES_*` from ohms/mile to ohms/ft by dividing by 5280
and converts radius to diameter via `Diameter = CDRAD_in * 2`.

2) lines.csv

Required (the project already expects these):

- `name` — line identifier
- `conductor` — conductor type string matching `ConductorName`
- `MOT` — maximum operating temperature (°C); if missing, an ambient default
  is used and values are clamped to 50–100°C.

## Calculation methodology & assumptions

- Uses the `ieee738` module's `ConductorParams` and `Conductor` class to
  compute the steady-state thermal rating in amps (I).
- Ambient/default weather parameters come from `AppConfig.get_default_weather_params()`;
  override by creating `IEEE738RatingEngine(ambient_defaults=...)`.
- The engine uses one conductor per bundle (`ConductorsPerBundle=1`) by default.

MVA conversions:

- rating_69kv_mva = √3 × I × 69,000 / 1e6
- rating_138kv_mva = √3 × I × 138,000 / 1e6

## How to run

From the repository root run (Windows PowerShell):

```powershell
python .\backend\run_ieee738.py
```

Output file: `backend/output/line_ratings_ieee738.csv` with columns:

- `line_name`, `conductor_type`, `mot_celsius`, `rating_amps`,
  `rating_69kv_mva`, `rating_138kv_mva`, `error`

`error` contains a text message when a line failed to process (missing
conductor, malformed data, etc.).

## How to change ambient conditions

Either edit defaults in `config.AppConfig.get_default_weather_params()` or
instantiate the engine with custom ambient parameters:

```python
from ieee738_integration import IEEE738RatingEngine

ambient = AppConfig.get_default_weather_params()
ambient['Ta'] = 30.0
ambient['WindVelocity'] = 4.0
engine = IEEE738RatingEngine(ambient_defaults=ambient)
engine.compute_all_line_ratings()
```

## Integration points

- `csv_data_loader.get_loader()` is used for robust access to `lines.csv`.
- The new engine writes output to `DataConfig.OUTPUT_DIR` which is created if
  missing.

## Notes & next steps

- The engine currently assumes `ConductorsPerBundle = 1`. If bundled
  conductor info is available in `lines.csv`, the engine can be extended to
  read and apply it per-line.
- Consider adding unit tests that validate a small set of known conductor
  values and their expected ampacity.
