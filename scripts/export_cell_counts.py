"""Aggregate the raw Kaggle CSV to day x hour cell counts.

The raw dataset is not committed (see .gitignore), so the headline-number tests
would have nothing to run against on a clean checkout. This script produces the
one small artifact they need: per test group, per day x hour cell, the number of
users, conversions, and impressions. Every figure quoted in README.md and
reports/report.md is recoverable from it.

Run from the repo root after placing marketing_AB.csv in data/raw/:

    python scripts/export_cell_counts.py
"""

from pathlib import Path

import pandas as pd

RAW = Path("data/raw/marketing_AB.csv")
OUT = Path("data/processed/cell_counts.csv")


def main() -> None:
    df = pd.read_csv(RAW).drop(columns=["Unnamed: 0"])

    cells = (
        df.groupby(["test group", "most ads day", "most ads hour"])
          .agg(n_users=("converted", "count"),
               n_converted=("converted", "sum"),
               n_impressions=("total ads", "sum"))
          .reset_index()
          .sort_values(["test group", "most ads day", "most ads hour"])
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    cells.to_csv(OUT, index=False)
    print(f"wrote {OUT} — {len(cells)} rows, {cells['n_users'].sum():,} users")


if __name__ == "__main__":
    main()
