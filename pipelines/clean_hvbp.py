"""
Phase 1 — clean_hvbp.py
Cleans Hospital VBP Safety dataset per SRS Section 28.

Sentinel handling:
  'Not Available' -> true NaN + missingness indicator (measure not reported for that facility)
Measure Score fields ("5 out of 10") -> parsed to numeric 0-10 scale.
Facilities with zero usable measure scores across all 7 measures are flagged (not dropped —
kept for transparency, excluded downstream at feature-matrix build time per SRS Section 36).
"""

import sys as _sys
from pathlib import Path as _Path
_p = _Path(__file__).resolve()
while not (_p / "paths.py").exists():
    _p = _p.parent
_sys.path.insert(0, str(_p))
from paths import PROJECT_ROOT

import pandas as pd
import numpy as np
import re

RAW_PATH = f"{PROJECT_ROOT}/data/raw/hvbp/hvbp_safety__4_.csv"
OUT_PATH = f"{PROJECT_ROOT}/data/processed/hvbp_clean.parquet"

NA_TOKEN = "Not Available"
SCORE_COLS = [c for c in [
    'HAI-1 Measure Score', 'HAI-2 Measure Score', 'Combined SSI Measure Score',
    'HAI-3 Measure Score', 'HAI-4 Measure Score', 'HAI-5 Measure Score',
    'HAI-6 Measure Score', 'SEP-1 Measure Score'
]]
# "X out of Y" formatted columns are NOT limited to Measure Score — Achievement Points and
# Improvement Points use the identical text format in the raw file (Phase 9 discovery).
# All three groups must go through parse_score(), not plain pd.to_numeric().
OUT_OF_FORMAT_SUFFIXES = ['Measure Score', 'Achievement Points', 'Improvement Points']


def parse_score(val):
    """'5 out of 10' -> 5.0 ; 'Not Available' -> NaN"""
    if pd.isna(val) or val == NA_TOKEN:
        return np.nan
    m = re.match(r"(\d+)\s*out of\s*(\d+)", str(val))
    if m:
        return float(m.group(1))
    try:
        return float(val)
    except ValueError:
        return np.nan


def clean(df):
    df = df.copy()
    missingness_flags = {}

    # plain-numeric columns (Threshold, Benchmark, Baseline Rate, Performance Rate) — no "out of Y" text
    plain_numeric_cols = [c for c in df.columns if any(
        k in c for k in ['Threshold', 'Benchmark', 'Baseline Rate', 'Performance Rate']
    )]
    for c in plain_numeric_cols:
        s = df[c].astype(str)
        flag = (s == NA_TOKEN)
        s = s.where(~flag, np.nan)
        df[c] = pd.to_numeric(s, errors='coerce')
        if flag.any():
            missingness_flags[f"{c}_missing"] = flag.astype(int)

    # "X out of Y" formatted columns — Measure Score, Achievement Points, Improvement Points all alike
    out_of_format_cols = [c for c in df.columns if any(suf in c for suf in OUT_OF_FORMAT_SUFFIXES)]
    for c in out_of_format_cols:
        flag = df[c].astype(str) == NA_TOKEN
        df[c] = df[c].apply(parse_score)
        if flag.any():
            missingness_flags[f"{c}_missing"] = flag.astype(int)

    flags_df = pd.DataFrame(missingness_flags, index=df.index)
    df = pd.concat([df, flags_df], axis=1)

    # facility-level usability flag (Section 36 edge case)
    present_score_cols = [c for c in SCORE_COLS if c in df.columns]
    df['all_measures_unavailable'] = df[present_score_cols].isna().all(axis=1)

    return df, plain_numeric_cols + out_of_format_cols


if __name__ == "__main__":
    raw = pd.read_csv(RAW_PATH, low_memory=False)
    cleaned, numeric_cols = clean(raw)
    cleaned.to_parquet(OUT_PATH, engine="pyarrow", index=False)
    print(f"HVBP cleaned: {cleaned.shape} -> {OUT_PATH}")
    print(f"  numeric columns cleaned: {len(numeric_cols)}")
    print(f"  facilities with ALL measures unavailable: {cleaned['all_measures_unavailable'].sum()}")
