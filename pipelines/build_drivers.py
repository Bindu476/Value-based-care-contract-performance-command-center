"""
pipelines/build_drivers.py — Phase 7, SRS Section 12.
Combines: raw metric deviation, PCA loading strength, anomaly strength, financial relevance,
quality relevance, confidence -> weighted driver_priority_score. Every component stored
alongside the final score (no black-box score, Section 12.1). Weights loaded from config,
never hardcoded. Includes the mandatory sensitivity check (Section 32 risk #4).
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
import yaml

CANDIDATE_METRICS = {
    "P_EDV_Vis": "ED Utilization",
    "P_CT_VIS": "CT Imaging Utilization",
    "P_MRI_VIS": "MRI Imaging Utilization",
    "P_EM_SP_Vis": "Specialist Visit Utilization",
    "P_SNF_ADM": "SNF Admission Utilization",
    "SNF_LOS": "SNF Length of Stay",
    "ADM": "Inpatient Admission Utilization",
}


def load_weights(path=f"{PROJECT_ROOT}/config/driver_weights.yaml"):
    with open(path) as f:
        return yaml.safe_load(f)


def compute_pca_strength_lookup():
    """Weighted loading magnitude per raw utilization metric, normalized 0-1 across the block."""
    loadings = pd.read_csv(f"{PROJECT_ROOT}/data/analytical/pca_loadings_utilization.csv", index_col=0)
    var_report = pd.read_csv(f"{PROJECT_ROOT}/data/analytical/pca_component_labels.csv")
    var_report = var_report[var_report.block == "utilization"].set_index("component")["variance_pct"] / 100

    weighted_strength = {}
    for raw_metric in loadings.index:
        val = sum(abs(loadings.loc[raw_metric, pc]) * var_report.get(pc, 0) for pc in loadings.columns)
        weighted_strength[raw_metric.replace("_raw", "")] = val

    vals = pd.Series(weighted_strength)
    return (vals / vals.max()).to_dict()


def build_driver_candidates(weights, pca_strength_lookup):
    fin = pd.read_parquet(f"{PROJECT_ROOT}/data/analytical/financial_scorecard.parquet")
    qual = pd.read_parquet(f"{PROJECT_ROOT}/data/analytical/quality_scorecard.parquet")
    util = pd.read_parquet(f"{PROJECT_ROOT}/data/analytical/utilization_scorecard.parquet")
    anomaly = pd.read_parquet(f"{PROJECT_ROOT}/data/analytical/aco_anomaly_scores.parquet")

    df = fin.merge(qual, on="ACO_ID").merge(util, on="ACO_ID").merge(anomaly, on="ACO_ID")

    anomaly_min, anomaly_max = df.anomaly_score.min(), df.anomaly_score.max()
    df["anomaly_strength_norm"] = (df.anomaly_score - anomaly_min) / (anomaly_max - anomaly_min)
    df["financial_relevance"] = np.where(
        df.financial_status == "LOSS", 1.0,
        np.clip(1 - df.expenditure_gap_pct / 20, 0, 1)
    )
    df["quality_relevance"] = 1 - (df.quality_peer_percentile / 100)
    df["confidence"] = np.minimum(df.peer_group_size / 100, 1.0)

    records = []
    for _, row in df.iterrows():
        for metric_col, metric_label in CANDIDATE_METRICS.items():
            pct_col = f"{metric_col}_percentile"
            if pct_col not in row.index or pd.isna(row[pct_col]):
                continue
            raw_deviation = abs(row[pct_col] - 50) / 50
            pca_strength = pca_strength_lookup.get(metric_col, 0)

            components = {
                "raw_deviation": raw_deviation,
                "pca_strength": pca_strength,
                "anomaly_strength": row["anomaly_strength_norm"],
                "financial_relevance": row["financial_relevance"],
                "quality_relevance": row["quality_relevance"],
                "confidence": row["confidence"],
            }
            driver_score = sum(weights[k] * v for k, v in components.items()) * 100

            records.append({
                "ACO_ID": row.ACO_ID, "driver_name": metric_label, "driver_metric": metric_col,
                "peer_percentile": row[pct_col], "driver_score": round(driver_score, 2),
                **{f"component_{k}": round(v, 3) for k, v in components.items()},
                "confidence_label": "HIGH" if components["confidence"] >= 0.8 else
                                     "MEDIUM" if components["confidence"] >= 0.5 else "LOW",
            })

    return pd.DataFrame(records)


def sensitivity_check(pca_strength_lookup):
    """Section 12.1: recompute with alternate weight sets, check ranking stability."""
    base_weights = load_weights()
    alt_weights_1 = {"raw_deviation": 0.40, "pca_strength": 0.15, "anomaly_strength": 0.20,
                      "financial_relevance": 0.10, "quality_relevance": 0.10, "confidence": 0.05}
    alt_weights_2 = {"raw_deviation": 0.20, "pca_strength": 0.20, "anomaly_strength": 0.10,
                      "financial_relevance": 0.25, "quality_relevance": 0.15, "confidence": 0.10}

    results = {}
    for name, w in [("base", base_weights), ("alt1_deviation_heavy", alt_weights_1),
                     ("alt2_financial_heavy", alt_weights_2)]:
        d = build_driver_candidates(w, pca_strength_lookup)
        top1_per_aco = d.loc[d.groupby("ACO_ID")["driver_score"].idxmax()][["ACO_ID", "driver_name"]]
        results[name] = top1_per_aco.set_index("ACO_ID")["driver_name"]

    agreement_base_alt1 = (results["base"] == results["alt1_deviation_heavy"]).mean()
    agreement_base_alt2 = (results["base"] == results["alt2_financial_heavy"]).mean()
    return agreement_base_alt1, agreement_base_alt2


if __name__ == "__main__":
    weights = load_weights()
    print("Driver weights (from config):", weights)

    pca_strength_lookup = compute_pca_strength_lookup()
    print("\nPCA strength per utilization metric (normalized 0-1):")
    for k, v in sorted(pca_strength_lookup.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v:.3f}")

    drivers = build_driver_candidates(weights, pca_strength_lookup)
    drivers.to_parquet(f"{PROJECT_ROOT}/data/analytical/aco_driver_candidates.parquet", index=False)

    top_drivers = drivers.loc[drivers.groupby("ACO_ID")["driver_score"].idxmax()].sort_values("driver_score", ascending=False)
    top_drivers.to_csv(f"{PROJECT_ROOT}/data/analytical/top_driver_per_aco.csv", index=False)

    print(f"\nTotal driver candidates scored: {len(drivers)} across {drivers.ACO_ID.nunique()} ACOs")
    print("\nTop 5 highest-priority drivers portfolio-wide:")
    print(top_drivers[["ACO_ID", "driver_name", "driver_score", "peer_percentile", "confidence_label"]].head(5).to_string(index=False))

    agree1, agree2 = sensitivity_check(pca_strength_lookup)
    print(f"\n--- Sensitivity check (Section 12.1) ---")
    print(f"Top-driver agreement, base vs deviation-heavy weights: {agree1*100:.1f}%")
    print(f"Top-driver agreement, base vs financial-heavy weights: {agree2*100:.1f}%")
