"""
Phase 1 — clean_physician.py
Ingests + aggregates the Medicare Physician & Other Practitioners by Provider and Service file
per SRS Section 28.2 / 8.1. Uses Polars lazy scan so the full (potentially multi-GB, tens-of-
millions-of-row) file is never materialized in memory — only the aggregated NPI-level result is.

Usage:
    python3 clean_physician.py <path_to_raw_csv> [--states CA,NY,TX]

If --states is omitted, aggregates the whole file (fine for a sample/test file; for the full
national file, always pass --states filtered to the states represented in the MSSP ACO data,
per Section 8.1's scope-reduction step).
"""

import sys as _sys
from pathlib import Path as _Path
_p = _Path(__file__).resolve()
while not (_p / "paths.py").exists():
    _p = _p.parent
_sys.path.insert(0, str(_p))
from paths import PROJECT_ROOT

import polars as pl
import argparse

OUT_PATH = f"{PROJECT_ROOT}/data/processed/provider_features.parquet"


def build_provider_features(raw_path: str, states: list[str] | None = None) -> pl.DataFrame:
    lf = pl.scan_csv(raw_path, infer_schema_length=10000)

    if states:
        lf = lf.filter(pl.col("Rndrng_Prvdr_State_Abrvtn").is_in(states))

    # E&M codes: 99xxx range: imaging/procedure categorization by HCPCS prefix is a simplification —
    # a full CPT/HCPCS category crosswalk should replace this in a later iteration if time allows.
    lf = lf.with_columns([
        pl.col("HCPCS_Cd").str.slice(0, 1).alias("_hcpcs_prefix"),
        (pl.col("Avg_Mdcr_Pymt_Amt") * pl.col("Tot_Srvcs")).alias("_line_payment"),
    ])

    agg = (
        lf.group_by("Rndrng_NPI")
        .agg([
            pl.col("Tot_Srvcs").sum().alias("total_services"),
            pl.col("Tot_Benes").sum().alias("total_beneficiaries"),
            pl.col("_line_payment").sum().alias("total_payment"),
            pl.col("HCPCS_Cd").n_unique().alias("service_diversity"),
            pl.col("Rndrng_Prvdr_Type").first().alias("specialty"),
            pl.col("Rndrng_Prvdr_State_Abrvtn").first().alias("state"),
            pl.col("Rndrng_Prvdr_RUCA_Desc").first().alias("rurality"),
            (pl.col("Place_Of_Srvc") == "F").sum().alias("_facility_lines"),  # F=facility, O=office (CMS coding)
            pl.len().alias("n_service_lines"),
        ])
    )

    df = agg.collect(engine="streaming")

    df = df.with_columns([
        (pl.col("total_payment") / pl.col("total_beneficiaries")).alias("avg_payment_per_beneficiary"),
        (pl.col("total_payment") / pl.col("total_services")).alias("avg_payment_per_service"),
        (pl.col("_facility_lines") / pl.col("n_service_lines")).alias("facility_share"),
        (1 - pl.col("_facility_lines") / pl.col("n_service_lines")).alias("office_share"),
    ]).drop(["_facility_lines", "n_service_lines"])

    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("raw_path")
    parser.add_argument("--states", default=None, help="comma-separated state abbreviations")
    args = parser.parse_args()

    states = args.states.split(",") if args.states else None
    result = build_provider_features(args.raw_path, states)
    result.write_parquet(OUT_PATH)
    print(f"Provider features: {result.shape} -> {OUT_PATH}")
    print(result.head(5))
