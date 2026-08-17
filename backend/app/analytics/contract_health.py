"""
backend/app/analytics/contract_health.py — Section 14.4-14.5.
Application-defined composite scores, explicitly not CMS scores. Weights redistributed per
Section 14.4.1 (Trend inactive, single performance year — 10% moved into Financial +5% / ML Risk +5%).
Every sub-component is returned alongside the final score — no black-box number (Section 12.1 principle
applied here too).
"""

import sys as _sys
from pathlib import Path as _Path
_p = _Path(__file__).resolve()
while not (_p / "paths.py").exists():
    _p = _p.parent
_sys.path.insert(0, str(_p))
from paths import PROJECT_ROOT

import pandas as pd

WEIGHTS = {"financial": 0.40, "quality": 0.25, "utilization": 0.15, "ml_risk": 0.20}


def compute_contract_health():
    fin = pd.read_parquet(f"{PROJECT_ROOT}/data/analytical/financial_scorecard.parquet")
    qual = pd.read_parquet(f"{PROJECT_ROOT}/data/analytical/quality_scorecard.parquet")
    anomaly = pd.read_parquet(f"{PROJECT_ROOT}/data/analytical/aco_anomaly_scores.parquet")
    cluster = pd.read_parquet(f"{PROJECT_ROOT}/data/analytical/aco_cluster_assignments.parquet")

    df = fin.merge(qual, on="ACO_ID").merge(anomaly, on="ACO_ID").merge(
        cluster[["ACO_ID", "cluster"]], on="ACO_ID")

    # Financial sub-score: percentile of expenditure_gap_pct within full population (0-100)
    df["financial_subscore"] = df["expenditure_gap_pct_peer_percentile"]

    # Quality sub-score: direct peer percentile
    df["quality_subscore"] = df["quality_peer_percentile"]

    # Utilization sub-score: inverse of cluster risk — cluster 1 (High Util/Below-Peer Quality) scores lower
    df["utilization_subscore"] = df["cluster"].map({0: 80.0, 1: 35.0})

    # ML Risk sub-score (Section 14.5): anomaly score normalized 0-100, inverted so higher anomaly = higher risk
    min_a, max_a = df.anomaly_score.min(), df.anomaly_score.max()
    df["ml_risk_score"] = ((df.anomaly_score - min_a) / (max_a - min_a) * 100).round(1)

    df["contract_health_score"] = (
        WEIGHTS["financial"] * df["financial_subscore"] +
        WEIGHTS["quality"] * df["quality_subscore"] +
        WEIGHTS["utilization"] * df["utilization_subscore"] +
        WEIGHTS["ml_risk"] * (100 - df["ml_risk_score"])  # high ML risk drags health down
    ).round(1)

    df["trend_status"] = "Not available — requires multi-year data (weight=0, Section 14.4.1)"

    return df[["ACO_ID", "contract_health_score", "financial_subscore", "quality_subscore",
               "utilization_subscore", "ml_risk_score", "trend_status"]]


if __name__ == "__main__":
    result = compute_contract_health()
    result.to_parquet(f"{PROJECT_ROOT}/data/analytical/contract_health_scores.parquet", index=False)
    print(f"Contract Health computed for {len(result)} ACOs")
    print(result.describe())
    print("\nWeight sensitivity spot-check — top 5 by Contract Health:")
    print(result.sort_values("contract_health_score", ascending=False).head(5).to_string(index=False))
