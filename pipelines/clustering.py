"""
pipelines/clustering.py — Phase 5, SRS Section 7.5-7.6.
Final model: KMeans k=2 (selected via silhouette + Davies-Bouldin + stability check,
see k_selection_report.csv). Cluster names generated from actual centroid inspection,
not hardcoded in advance.
"""

import sys as _sys
from pathlib import Path as _Path
_p = _Path(__file__).resolve()
while not (_p / "paths.py").exists():
    _p = _p.parent
_sys.path.insert(0, str(_p))
from paths import PROJECT_ROOT

import pandas as pd
from sklearn.cluster import KMeans

K_FINAL = 2


def fit_final_clustering():
    pca_df = pd.read_parquet(f"{PROJECT_ROOT}/data/analytical/pca_scores_all_blocks.parquet")
    feature_cols = [c for c in pca_df.columns if c != "ACO_ID"]
    X = pca_df[feature_cols].values

    km = KMeans(n_clusters=K_FINAL, n_init=10, random_state=42)
    pca_df["cluster"] = km.fit_predict(X)

    fin = pd.read_parquet(f"{PROJECT_ROOT}/data/analytical/financial_scorecard.parquet")
    qual = pd.read_parquet(f"{PROJECT_ROOT}/data/analytical/quality_scorecard.parquet")
    util = pd.read_parquet(f"{PROJECT_ROOT}/data/analytical/utilization_scorecard.parquet")

    merged = (pca_df[["ACO_ID", "cluster"] + feature_cols]
              .merge(fin, on="ACO_ID")
              .merge(qual[["ACO_ID", "QualScore", "quality_peer_percentile", "quality_band"]], on="ACO_ID")
              .merge(util[["ACO_ID", "P_EDV_Vis_value", "P_SNF_ADM_value", "SNF_LOS_value"]], on="ACO_ID"))

    return merged, km, feature_cols


def name_cluster(row) -> str:
    """Auto-generate cluster name from its centroid characteristics vs. the other cluster."""
    if row["utilization_PC1_rel"] > 0.5 and row["QualScore_rel"] < -0.5:
        return "High Utilization / Below-Peer Quality"
    if row["utilization_PC1_rel"] < -0.5 and row["QualScore_rel"] > 0.5:
        return "Low Utilization / Strong Quality"
    if row["utilization_PC1_rel"] > 0.5:
        return "High Utilization Profile"
    return "Standard/Mainstream Profile"


def build_cluster_report(merged):
    summary = merged.groupby("cluster").agg(
        n_acos=("ACO_ID", "count"),
        avg_gen_save_loss=("GenSaveLoss", "mean"),
        median_gen_save_loss=("GenSaveLoss", "median"),
        pct_savings=("financial_status", lambda s: (s == "SAVINGS").mean() * 100),
        avg_quality=("QualScore", "mean"),
        avg_ed_visits=("P_EDV_Vis_value", "mean"),
        avg_snf_admissions=("P_SNF_ADM_value", "mean"),
        avg_snf_los=("SNF_LOS_value", "mean"),
        avg_utilization_pc1=("utilization_PC1", "mean"),
        avg_financial_pc1=("financial_PC1", "mean"),
    ).reset_index()

    # relative (z-like) comparison for auto-naming
    summary["utilization_PC1_rel"] = (summary["avg_utilization_pc1"] - summary["avg_utilization_pc1"].mean()) / summary["avg_utilization_pc1"].std()
    summary["QualScore_rel"] = (summary["avg_quality"] - summary["avg_quality"].mean()) / summary["avg_quality"].std()
    summary["cluster_name"] = summary.apply(name_cluster, axis=1)
    summary["recommended_review_focus"] = summary["cluster_name"].apply(
        lambda n: "Acute/post-acute utilization review recommended" if "High Utilization" in n
        else "No elevated-utilization review signal at cluster level"
    )
    return summary


if __name__ == "__main__":
    merged, km, feature_cols = fit_final_clustering()
    report = build_cluster_report(merged)

    merged.to_parquet(f"{PROJECT_ROOT}/data/analytical/aco_cluster_assignments.parquet", index=False)
    report.to_csv(f"{PROJECT_ROOT}/data/analytical/cluster_profile_report.csv", index=False)

    print(report[["cluster", "cluster_name", "n_acos", "avg_gen_save_loss", "pct_savings",
                   "avg_quality", "avg_ed_visits", "avg_snf_admissions", "recommended_review_focus"]].to_string(index=False))
