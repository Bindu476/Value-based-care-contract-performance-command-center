"""
pipelines/build_ml_features.py
Builds the 5 ACO feature-block matrices for ML (PCA input, Phase 4).
Enforces Section 6.2/28.7: outcome variables (GenSaveLoss, EarnSaveLoss) are NEVER included
as ML inputs — they live only in the outcome table, joined back at the Driver Engine stage.
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
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import RobustScaler

RAW_PATH = f"{PROJECT_ROOT}/data/processed/mssp_clean.parquet"
OUT_DIR = f"{PROJECT_ROOT}/data/analytical"

EXCLUDED_FROM_ML_INPUT = ["GenSaveLoss", "EarnSaveLoss"]  # Section 28.7, enforced here

FEATURE_BLOCK_PREFIXES = {
    "financial": ['ABtotBnchmk', 'ABtotExp', 'FinalShareRate', 'FinalLossRate', 'Per_Capita_Exp'],
    "utilization": ['P_EDV', 'P_CT_VIS', 'P_MRI_VIS', 'P_EM_', 'P_Nurse_Vis', 'P_FQHC_RHC_Vis',
                     'P_SNF_ADM', 'SNF_LOS', 'SNF_PayperStay', 'ADM', 'CapAnn'],
    "risk": ['CMS_HCC_RiskScore', 'Demog_RiskScore', 'N_Ben', 'Perc_Dual', 'Perc_LTI'],
    "provider_composition": ['N_Hosp', 'N_PCP', 'N_Spec', 'N_NP', 'N_PA', 'N_CNS', 'N_FQHC',
                              'N_RHC', 'N_CAH', 'N_ETA', 'N_Fac_Other'],
    "quality": ['QualScore', 'CAHPS', 'Measure_', 'QualityID'],
}


def select_block_columns(df, prefixes):
    cols = [c for c in df.columns if any(c.startswith(p) for p in prefixes)
            and '_missing' not in c and '_applicable' not in c and '_reporting_method' not in c]
    # hard-enforce outcome exclusion even if a prefix accidentally matched
    cols = [c for c in cols if c not in EXCLUDED_FROM_ML_INPUT]
    return cols


def preprocess_block(df, cols, block_name):
    X = df[cols].copy()

    # skew correction on positive-valued numeric columns
    for c in cols:
        if X[c].min() >= 0 and X[c].skew(skipna=True) > 1.0:
            X[c] = np.log1p(X[c])

    # median impute + missingness indicator for any remaining NaN (post Phase-1 cleaning,
    # remaining NaN here represents true CMS privacy suppression, already flagged upstream —
    # this indicator is block-local, for the PCA input matrix specifically)
    imputer = SimpleImputer(strategy="median")
    missing_flags = X.isna().astype(int).add_suffix("_missing_block")
    X_imputed = pd.DataFrame(imputer.fit_transform(X), columns=cols, index=X.index)

    scaler = RobustScaler()
    X_scaled = pd.DataFrame(scaler.fit_transform(X_imputed), columns=[f"{c}_scaled" for c in cols], index=X.index)

    result = pd.concat([X_imputed.add_suffix("_raw"), X_scaled, missing_flags], axis=1)
    result.insert(0, "ACO_ID", df["ACO_ID"].values)
    return result, scaler


if __name__ == "__main__":
    df = pd.read_parquet(RAW_PATH)

    summary = []
    for block_name, prefixes in FEATURE_BLOCK_PREFIXES.items():
        cols = select_block_columns(df, prefixes)
        result, scaler = preprocess_block(df, cols, block_name)
        out_path = f"{OUT_DIR}/ml_features_{block_name}.parquet"
        result.to_parquet(out_path, index=False)
        summary.append((block_name, len(cols), result.shape))
        print(f"{block_name}: {len(cols)} raw features -> {result.shape} -> {out_path}")

    # sanity: confirm outcome vars never appear in any block
    all_block_files = [f"{OUT_DIR}/ml_features_{b}.parquet" for b in FEATURE_BLOCK_PREFIXES]
    leaked = []
    for f in all_block_files:
        cols = pd.read_parquet(f, columns=None).columns.tolist()
        leaked += [c for c in cols if any(ex in c for ex in EXCLUDED_FROM_ML_INPUT)]
    print(f"\nOutcome-variable leakage check: {'FAIL - ' + str(leaked) if leaked else 'PASS - no leakage'}")
