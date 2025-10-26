"""Runner script for IEEE-738 rating integration.

Usage (from repo root):
    python backend\run_ieee738.py

This script will compute ratings for all lines and write CSV to
`backend/output/line_ratings_ieee738.csv` (creates output dir if needed).
"""

from pathlib import Path
import logging

from config import DataConfig
from ieee738_integration import IEEE738RatingEngine


def main():
    logging.basicConfig(level=logging.INFO)

    DataConfig.ensure_directories_exist()
    out_file = DataConfig.OUTPUT_DIR / "line_ratings_ieee738.csv"

    engine = IEEE738RatingEngine()
    df = engine.compute_all_line_ratings(output_csv=out_file)

    print("Computed ratings for {} lines".format(len(df)))
    errors = df[~df['error'].isna()]
    if not errors.empty:
        print(f"{len(errors)} lines had errors; see 'error' column in {out_file}")
    else:
        print(f"All lines processed successfully. Results written to {out_file}")


if __name__ == '__main__':
    main()
