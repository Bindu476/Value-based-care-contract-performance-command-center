"""
pipelines/pca.py — Phase 4, SRS Section 7.3.
Runs PCA per feature block, selects components by cumulative explained variance (~80-90%,
not forced), and generates human-readable interpretations from top-loading raw features.
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
from sklearn.decomposition import PCA

BLOCKS = ["financial", "utilization", "risk", "provider_composition", "quality"]
TARGET_CUM_VAR = 0.85
TOP_N_LOADINGS_FOR_LABEL = 4

# Human-readable interpretations, keyed by component. Kept here (not as a separate follow-up
# script) so a rerun of this file can never silently drop them again (Phase 15 regression found
# and fixed: an earlier version added these in a one-off shell step, and rerunning pca.py during
# folder migration wiped them out without any error).
HUMAN_LABELS = {
    "financial_PC1": "Aged/Non-Dual Per-Capita Cost Level",
    "financial_PC2": "Aged/Dual Per-Capita Cost Level",
    "financial_PC3": "Total Benchmark vs. Actual Expenditure Scale",
    "financial_PC4": "ESRD Benchmark/Expenditure Scale",
    "utilization_PC1": "Inpatient / Psychiatric Admission Intensity",
    "utilization_PC2": "Long-Term Inpatient & ED (Hospital) Intensity",
    "utilization_PC3": "PCP Visit & Outpatient (PB) Intensity",
    "utilization_PC4": "DME & SNF Stay-Length Intensity",
    "utilization_PC5": "Post-Acute (SNF/Rehab) Intensity",
    "utilization_PC6": "Ambulatory (PCP/Nurse/MRI) Visit Intensity",
    "risk_PC1": "Disabled-Population Clinical Risk Intensity",
    "risk_PC2": "Hispanic/CBA-Only Beneficiary Demographic Mix",
    "risk_PC3": "Dual-Eligible & Disabled Risk Composition",
    "risk_PC4": "Long-Term-Institutional & Hispanic Demographic Mix",
    "risk_PC5": "ESRD Risk Composition",
    "risk_PC6": "Long-Term-Institutional Risk Composition",
    "risk_PC7": "Hispanic/Native Demographic & ESRD Mix",
    "provider_composition_PC1": "Primary-Care/Community-Health Workforce Density (FQHC/NP/PCP/PA)",
    "provider_composition_PC2": "Specialist/Hospital-Facility Density",
    "provider_composition_PC3": "Critical-Access & Rural Health Facility Density",
    "quality_PC1": "Clinical Quality Measure Composite (QualityID 438/236)",
    "quality_PC2": "Patient Experience (CAHPS) Composite",
    "quality_PC3": "Preventive/Screening Measure Composite",
}
RISK_CAVEAT = "Demographic-count driven, not purely clinical risk"


def clean_feature_name(raw_col: str) -> str:
    return raw_col.replace("_raw", "").replace("_", " ")


def label_component(loadings: pd.Series, top_n=TOP_N_LOADINGS_FOR_LABEL) -> str:
    top = loadings.abs().sort_values(ascending=False).head(top_n)
    names = [clean_feature_name(idx) for idx in top.index]
    return " + ".join(names)


def run_pca_block(block_name: str):
    df = pd.read_parquet(f"{PROJECT_ROOT}/data/analytical/ml_features_{block_name}.parquet")
    scaled_cols = [c for c in df.columns if c.endswith("_scaled")]
    raw_names = [c.replace("_scaled", "_raw") for c in scaled_cols]
    X = df[scaled_cols].values

    pca_full = PCA(n_components=min(len(scaled_cols), len(df)), random_state=42)
    pca_full.fit(X)
    cum_var = pca_full.explained_variance_ratio_.cumsum()
    n_components = int((cum_var < TARGET_CUM_VAR).sum() + 1)
    n_components = min(n_components, len(scaled_cols))

    pca = PCA(n_components=n_components, random_state=42)
    pc_scores = pca.fit_transform(X)

    pc_cols = [f"{block_name}_PC{i+1}" for i in range(n_components)]
    scores_df = pd.DataFrame(pc_scores, columns=pc_cols, index=df.index)
    scores_df.insert(0, "ACO_ID", df["ACO_ID"].values)

    loadings = pd.DataFrame(pca.components_.T, index=raw_names, columns=pc_cols)

    labels = {pc: label_component(loadings[pc]) for pc in pc_cols}
    variance_explained = {pc: round(v * 100, 1) for pc, v in zip(pc_cols, pca.explained_variance_ratio_)}

    return {
        "block": block_name,
        "n_components": n_components,
        "cumulative_variance_pct": round(cum_var[n_components - 1] * 100, 1),
        "scores_df": scores_df,
        "loadings": loadings,
        "labels": labels,
        "variance_explained": variance_explained,
    }


if __name__ == "__main__":
    all_scores = []
    label_report = []

    for block in BLOCKS:
        result = run_pca_block(block)
        result["scores_df"].to_parquet(f"{PROJECT_ROOT}/data/analytical/pca_scores_{block}.parquet", index=False)
        result["loadings"].to_csv(f"{PROJECT_ROOT}/data/analytical/pca_loadings_{block}.csv")

        print(f"\n{block.upper()}: {result['n_components']} components, "
              f"{result['cumulative_variance_pct']}% cumulative variance")
        for pc, label in result["labels"].items():
            var = result["variance_explained"][pc]
            print(f"  {pc} ({var}%): {label}")
            label_report.append({"block": block, "component": pc, "variance_pct": var, "top_loadings": label})

        all_scores.append(result["scores_df"].set_index("ACO_ID"))

    combined = pd.concat(all_scores, axis=1).reset_index()
    combined.to_parquet(f"{PROJECT_ROOT}/data/analytical/pca_scores_all_blocks.parquet", index=False)

    label_df = pd.DataFrame(label_report)
    label_df["human_label"] = label_df["component"].map(HUMAN_LABELS)
    label_df["caveat"] = label_df["component"].apply(
        lambda pc: RISK_CAVEAT if pc.startswith("risk_PC") and pc != "risk_PC1" else "")
    label_df.to_csv(f"{PROJECT_ROOT}/data/analytical/pca_component_labels.csv", index=False)
    print(f"\nCombined PCA feature matrix: {combined.shape}")
