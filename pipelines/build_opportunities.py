""""
pipelines/build_opportunities.py — Phase 10, SRS Section 15.
Ranks review opportunities per ACO by combining: driver score (Phase 7), ML anomaly status
(Phase 6), cluster membership (Phase 5), and financial/quality relevance (Phase 2).
"""

import sys as _sys
from pathlib import Path as _Path
_p = _Path(__file__).resolve()
while not (_p / "paths.py").exists():
    _p = _p.parent
_sys.path.insert(0, str(_p))
from paths import PROJECT_ROOT

import pandas as pd

CLUSTER_NAMES = {0: "Low Utilization / Strong Quality", 1: "High Utilization / Below-Peer Quality"}


def build_opportunities():
    drivers = pd.read_csv(f"{PROJECT_ROOT}/data/analytical/top_driver_per_aco.csv")
    anomaly = pd.read_parquet(f"{PROJECT_ROOT}/data/analytical/aco_anomaly_scores.parquet")
    cluster = pd.read_parquet(f"{PROJECT_ROOT}/data/analytical/aco_cluster_assignments.parquet")[["ACO_ID", "cluster"]]
    fin = pd.read_parquet(f"{PROJECT_ROOT}/data/analytical/financial_scorecard.parquet")
    qual = pd.read_parquet(f"{PROJECT_ROOT}/data/analytical/quality_scorecard.parquet")

    df = (drivers.merge(anomaly, on="ACO_ID")
                 .merge(cluster, on="ACO_ID")
                 .merge(fin[["ACO_ID", "ACO_Name", "financial_status", "GenSaveLoss", "expenditure_gap_pct"]], on="ACO_ID")
                 .merge(qual[["ACO_ID", "quality_band"]], on="ACO_ID"))

    df["cluster_name"] = df["cluster"].map(CLUSTER_NAMES)

    # opportunity priority: base driver score, boosted for confirmed ML anomalies, boosted for LOSS status
    anomaly_boost = df["confidence_tier"].map({"VERY HIGH": 15, "HIGH": 8, "NOT FLAGGED": 0})
    financial_boost = (df["financial_status"] == "LOSS") * 10
    df["opportunity_priority"] = (df["driver_score"] + anomaly_boost + financial_boost).clip(upper=100).round(1)

    df["ml_signal"] = df.apply(
        lambda r: f"{r.cluster_name} cluster" + (f", {r.confidence_tier} confidence anomaly" if r.confidence_tier != "NOT FLAGGED" else ""),
        axis=1
    )
    df["evidence"] = df.apply(
        lambda r: f"{r.driver_name} at {r.peer_percentile:.0f}th percentile", axis=1
    )
    df["confidence"] = df["confidence_label"]

    result = df[["ACO_ID", "ACO_Name", "opportunity_priority", "driver_name", "evidence",
                 "ml_signal", "financial_status", "GenSaveLoss", "quality_band", "confidence"]].copy()
    result = result.sort_values("opportunity_priority", ascending=False).reset_index(drop=True)
    result.insert(0, "priority_rank", result.index + 1)
    return result


if __name__ == "__main__":
    opportunities = build_opportunities()
    opportunities.to_csv(f"{PROJECT_ROOT}/data/analytical/opportunity_ranking.csv", index=False)

    print(f"Opportunities ranked: {len(opportunities)}")
    print("\nTop 10 portfolio-wide opportunities:")
    print(opportunities.head(10)[["priority_rank", "ACO_Name", "opportunity_priority", "driver_name",
                                    "financial_status", "confidence"]].to_string(index=False))
