"""
backend/app/services/data_loader.py
Loads and caches the precomputed analytical artifacts (Phases 2-11) at process startup.
No recomputation happens per-request — this is a serving layer, not a pipeline.
"""

import sys as _sys
from pathlib import Path as _Path
_p = _Path(__file__).resolve()
while not (_p / "paths.py").exists():
    _p = _p.parent
_sys.path.insert(0, str(_p))
from paths import PROJECT_ROOT

import pandas as pd
from functools import lru_cache

DATA_DIR = f"{PROJECT_ROOT}/data/analytical"


@lru_cache(maxsize=1)
def load_all():
    return {
        "financial": pd.read_parquet(f"{DATA_DIR}/financial_scorecard.parquet"),
        "quality": pd.read_parquet(f"{DATA_DIR}/quality_scorecard.parquet"),
        "utilization": pd.read_parquet(f"{DATA_DIR}/utilization_scorecard.parquet"),
        "contract_health": pd.read_parquet(f"{DATA_DIR}/contract_health_scores.parquet"),
        "clusters": pd.read_parquet(f"{DATA_DIR}/aco_cluster_assignments.parquet"),
        "anomalies": pd.read_parquet(f"{DATA_DIR}/aco_anomaly_scores.parquet"),
        "anomaly_explanations": pd.read_csv(f"{DATA_DIR}/anomaly_explanations.csv"),
        "drivers": pd.read_parquet(f"{DATA_DIR}/aco_driver_candidates.parquet"),
        "top_drivers": pd.read_csv(f"{DATA_DIR}/top_driver_per_aco.csv"),
        "opportunities": pd.read_csv(f"{DATA_DIR}/opportunity_ranking.csv"),
        "cluster_profiles": pd.read_csv(f"{DATA_DIR}/cluster_profile_report.csv"),
        "pca_labels": pd.read_csv(f"{DATA_DIR}/pca_component_labels.csv"),
        "recs_aco": pd.read_csv(f"{DATA_DIR}/recommendations_aco.csv"),
        "recs_hospital": pd.read_csv(f"{DATA_DIR}/recommendations_hospital.csv"),
        "hospital_ml": pd.read_parquet(f"{DATA_DIR}/hospital_ml_results.parquet"),
        "provider_ml": pd.read_parquet(f"{DATA_DIR}/provider_ml_results.parquet"),
    }


def get_aco_row(aco_id: str, key: str):
    df = load_all()[key]
    match = df[df.ACO_ID == aco_id]
    return match.iloc[0].to_dict() if len(match) else None
