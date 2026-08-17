"""
Phase 1 — clean_mssp.py
Cleans PY_Financial_and_Quality_Results (MSSP) per SRS Section 28.

Sentinel handling:
  '*'  -> true missing (CMS privacy suppression, small-cell) -> NaN + missingness indicator
  '-'  -> structural not-applicable (e.g. no loss when ACO had savings,
          or a quality measure reported via a different method) -> 0 + applicability flag
Categorical text columns (ACO_ID, Track, etc.) pass through unchanged.
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

RAW_PATH = f"{PROJECT_ROOT}/data/raw/mssp/PY_Financial_and_Quality_Results_2024_revised_2026_07_17.csv"
OUT_PATH = f"{PROJECT_ROOT}/data/processed/mssp_clean.parquet"

CATEGORICAL_COLS = ['ACO_ID', 'ACO_Name', 'Agree_Type', 'Current_Start_Date',
                     'Current_Track', 'Risk_Model', 'Assign_Type', 'FinalAdjCat', 'Rev_Exp_Cat']

# Mutually-exclusive quality reporting-method groups (Phase 0 finding) — coalesced, not dropped
REPORTING_METHOD_GROUPS = {
    'QualityID_134': ['QualityID_134_WI', 'QualityID_134_eCQM', 'QualityID_134_MIPSCQM', 'QualityID_134_MedicareCQM'],
    'QualityID_001': ['QualityID_001_WI', 'QualityID_001_eCQM', 'QualityID_001_MIPSCQM', 'QualityID_001_MedicareCQM'],
    'QualityID_236': ['QualityID_236_WI', 'QualityID_236_eCQM', 'QualityID_236_MIPSCQM', 'QualityID_236_MedicareCQM'],
}


def is_numeric_str(x):
    try:
        float(x)
        return True
    except (ValueError, TypeError):
        return False


def classify_columns(df):
    str_cols = [c for c in df.columns if str(df[c].dtype) in ('object', 'str')]
    star_dom, dash_dom = [], []
    for c in str_cols:
        if c in CATEGORICAL_COLS:
            continue
        vals = df[c].astype(str)
        star_pct = (vals == '*').mean()
        dash_pct = (vals == '-').mean()
        nonnum_other = any(v not in ('*', '-') and not is_numeric_str(v) for v in vals.unique())
        if nonnum_other:
            continue  # unexpected categorical, leave alone, flag in validation
        if dash_pct >= star_pct and dash_pct > 0:
            dash_dom.append(c)
        else:
            star_dom.append(c)
    return star_dom, dash_dom


def clean(df):
    df = df.copy()
    star_dom, dash_dom = classify_columns(df)

    missingness_flags = {}

    # '*' -> true NaN
    for c in star_dom:
        s = df[c].astype(str)
        flag = (s == '*')
        s = s.where(~flag, np.nan)
        df[c] = pd.to_numeric(s, errors='coerce')
        if flag.any():
            missingness_flags[f"{c}_missing"] = flag.astype(int)

    # '-' -> structural 0 + applicability flag
    for c in dash_dom:
        s = df[c].astype(str)
        flag = (s == '-')
        applicable = (~flag).astype(int)
        s = s.where(~flag, '0')
        df[c] = pd.to_numeric(s, errors='coerce')
        missingness_flags[f"{c}_applicable"] = applicable

    flags_df = pd.DataFrame(missingness_flags, index=df.index)
    df = pd.concat([df, flags_df], axis=1)

    # coalesce mutually-exclusive reporting-method groups
    for new_col, group_cols in REPORTING_METHOD_GROUPS.items():
        present = [c for c in group_cols if c in df.columns]
        df[new_col] = df[present].bfill(axis=1).iloc[:, 0]
        method_used = df[present].apply(
            lambda row: next((c.split('_')[-1] for c, v in zip(present, row) if v != 0), 'none'), axis=1
        )
        df[f"{new_col}_reporting_method"] = method_used

    return df, star_dom, dash_dom


if __name__ == "__main__":
    raw = pd.read_csv(RAW_PATH, low_memory=False)
    cleaned, star_dom, dash_dom = clean(raw)
    cleaned.to_parquet(OUT_PATH, engine="pyarrow", index=False)
    print(f"MSSP cleaned: {cleaned.shape} -> {OUT_PATH}")
    print(f"  star-dominant cols converted to NaN+flag: {len(star_dom)}")
    print(f"  dash-dominant cols converted to 0+applicability flag: {len(dash_dom)}")
    print(f"  reporting-method groups coalesced: {len(REPORTING_METHOD_GROUPS)}")
