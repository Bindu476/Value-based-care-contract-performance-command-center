"""
pipelines/anomaly_detection.py — Phase 6, SRS Section 7.7-7.8, 29.4-29.5.
Final model: Isolation Forest, contamination=0.10, seed-stability validated (>=8/10 reruns).
Two-tier confidence: "very high" = also flagged at contamination=0.05 (nested nested set,
see phase6 sweep). Explanation: peer-deviation (primary) + decision-tree cross-check (secondary).
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
from sklearn.ensemble import IsolationForest
from sklearn.tree import DecisionTreeClassifier

CONTAMINATION_FINAL = 0.10
N_SEEDS = 10
STABILITY_THRESHOLD = 8  # of 10 reruns


def fit_final_anomaly_model():
    pca_df = pd.read_parquet(f"{PROJECT_ROOT}/data/analytical/pca_scores_all_blocks.parquet")
    feature_cols = [c for c in pca_df.columns if c != "ACO_ID"]
    X = pca_df[feature_cols].values
    n = len(pca_df)

    flag_counts = np.zeros(n)
    for seed in range(N_SEEDS):
        iso = IsolationForest(contamination=CONTAMINATION_FINAL, random_state=seed, n_estimators=200)
        preds = iso.fit_predict(X)
        flag_counts += (preds == -1).astype(int)

    pca_df["anomaly_flag_count"] = flag_counts.astype(int)
    pca_df["is_high_confidence_anomaly"] = flag_counts >= STABILITY_THRESHOLD

    # also compute the 5% (stricter) flag for the "very high confidence" tier
    flag_counts_05 = np.zeros(n)
    for seed in range(N_SEEDS):
        iso = IsolationForest(contamination=0.05, random_state=seed, n_estimators=200)
        preds = iso.fit_predict(X)
        flag_counts_05 += (preds == -1).astype(int)
    pca_df["is_very_high_confidence_anomaly"] = flag_counts_05 >= STABILITY_THRESHOLD

    pca_df["confidence_tier"] = np.select(
        [pca_df["is_very_high_confidence_anomaly"], pca_df["is_high_confidence_anomaly"]],
        ["VERY HIGH", "HIGH"], default="NOT FLAGGED"
    )

    # continuous anomaly score from a single reference fit, for ranking within tiers
    iso_ref = IsolationForest(contamination=CONTAMINATION_FINAL, random_state=42, n_estimators=200)
    iso_ref.fit(X)
    pca_df["anomaly_score"] = -iso_ref.score_samples(X)  # higher = more anomalous

    return pca_df, feature_cols, X


def secondary_explainability_check(pca_df, feature_cols, X):
    """Section 7.8/29.5: cross-check peer-deviation explanation with a model-based one."""
    y = pca_df["is_high_confidence_anomaly"].astype(int).values
    tree = DecisionTreeClassifier(max_depth=4, random_state=42, class_weight="balanced")
    tree.fit(X, y)
    importances = pd.Series(tree.feature_importances_, index=feature_cols).sort_values(ascending=False)
    return importances


def peer_deviation_explanation(aco_id, cluster_df, fin, qual, util, top_n=3):
    """Section 7.8: explain a flagged ACO via percentile deviation vs its peer group."""
    row_fin = fin[fin.ACO_ID == aco_id].iloc[0]
    row_qual = qual[qual.ACO_ID == aco_id].iloc[0]
    row_util = util[util.ACO_ID == aco_id].iloc[0]

    deviations = []
    for col in ["P_EDV_Vis", "P_CT_VIS", "P_MRI_VIS", "P_SNF_ADM", "SNF_LOS", "ADM"]:
        pct_col = f"{col}_percentile"
        if pct_col in row_util.index:
            deviations.append((col, row_util[pct_col]))
    deviations.append(("Quality (QualScore)", row_qual["quality_peer_percentile"]))
    deviations.append(("Expenditure Gap %", row_fin["expenditure_gap_pct_peer_percentile"]))

    # sort by distance from 50th percentile (most extreme first)
    deviations.sort(key=lambda x: abs(x[1] - 50), reverse=True)
    top = deviations[:top_n]
    explanation = "; ".join([f"{name} at {pct:.0f}th percentile" for name, pct in top])
    return explanation


if __name__ == "__main__":
    pca_df, feature_cols, X = fit_final_anomaly_model()

    print("Confidence tier distribution:")
    print(pca_df["confidence_tier"].value_counts())

    importances = secondary_explainability_check(pca_df, feature_cols, X)
    print("\nSecondary (decision-tree) explainability — top features distinguishing anomalies:")
    print(importances.head(8))

    fin = pd.read_parquet(f"{PROJECT_ROOT}/data/analytical/financial_scorecard.parquet")
    qual = pd.read_parquet(f"{PROJECT_ROOT}/data/analytical/quality_scorecard.parquet")
    util = pd.read_parquet(f"{PROJECT_ROOT}/data/analytical/utilization_scorecard.parquet")

    flagged = pca_df[pca_df.is_high_confidence_anomaly].copy()
    flagged["peer_deviation_explanation"] = flagged.ACO_ID.apply(
        lambda aid: peer_deviation_explanation(aid, pca_df, fin, qual, util)
    )

    out_cols = ["ACO_ID", "confidence_tier", "anomaly_score", "peer_deviation_explanation"]
    result = flagged[out_cols].sort_values("anomaly_score", ascending=False)
    result.to_csv(f"{PROJECT_ROOT}/data/analytical/anomaly_explanations.csv", index=False)
    pca_df[["ACO_ID", "anomaly_score", "anomaly_flag_count", "confidence_tier"]].to_parquet(
        f"{PROJECT_ROOT}/data/analytical/aco_anomaly_scores.parquet", index=False)
    importances.to_csv(f"{PROJECT_ROOT}/data/analytical/secondary_feature_importance.csv")

    print(f"\nTop 5 anomalies with explanations:")
    print(result.head(5).to_string(index=False))
