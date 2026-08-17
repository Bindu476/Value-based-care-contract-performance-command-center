"""
pipelines/hospital_ml.py — Phase 9, SRS Section 9.
Safety feature engineering -> RobustScaler -> PCA -> KMeans -> Isolation Forest,
same structural pattern and validation protocol as the ACO pipeline (Section 7).
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
from sklearn.preprocessing import RobustScaler
from sklearn.impute import SimpleImputer
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score
from sklearn.ensemble import IsolationForest

FEATURE_COLS = ['HAI_mean_score', 'HAI_median_score', 'measure_count',
                'poor_measure_count', 'achievement_mean', 'improvement_mean']


def build_hospital_features():
    df = pd.read_parquet(f"{PROJECT_ROOT}/data/processed/hvbp_clean.parquet")
    df = df[~df['all_measures_unavailable']].copy()  # Section 36 edge case: exclude unusable facilities

    def cols(substr):
        return [c for c in df.columns if substr in c and '_missing' not in c]

    score_cols, ach_cols, imp_cols = cols('Measure Score'), cols('Achievement Points'), cols('Improvement Points')
    df['HAI_mean_score'] = df[score_cols].mean(axis=1, skipna=True)
    df['HAI_median_score'] = df[score_cols].median(axis=1, skipna=True)
    df['measure_count'] = df[score_cols].notna().sum(axis=1)
    df['poor_measure_count'] = (df[score_cols] <= 3).sum(axis=1)
    df['achievement_mean'] = df[ach_cols].mean(axis=1, skipna=True)
    df['improvement_mean'] = df[imp_cols].mean(axis=1, skipna=True)

    return df[['Facility ID', 'Facility Name', 'State'] + FEATURE_COLS]


def run_pipeline(df):
    imputer = SimpleImputer(strategy="median")
    X_imp = imputer.fit_transform(df[FEATURE_COLS])
    scaler = RobustScaler()
    X_scaled = scaler.fit_transform(X_imp)

    pca = PCA(n_components=0.85, random_state=42)
    X_pca = pca.fit_transform(X_scaled)
    loadings = pd.DataFrame(pca.components_.T, index=FEATURE_COLS,
                             columns=[f"PC{i+1}" for i in range(X_pca.shape[1])])

    km = KMeans(n_clusters=2, n_init=10, random_state=42)
    labels = km.fit_predict(X_pca)

    # stability check (Section 9.2 / 7.5 protocol)
    aris = [adjusted_rand_score(labels, KMeans(n_clusters=2, n_init=10, random_state=s).fit_predict(X_pca))
            for s in range(1, 6)]
    stability = np.mean(aris)

    df = df.copy()
    df['cluster'] = labels
    perf_by_cluster = df.groupby('cluster')['HAI_mean_score'].mean()
    stronger = perf_by_cluster.idxmax()
    df['cluster_name'] = df['cluster'].map(
        lambda c: "Stronger Safety Performance" if c == stronger else "Weaker Safety Performance")

    # anomaly detection with seed-stability (Section 7.7 protocol)
    n = len(df)
    flag_counts = np.zeros(n)
    for seed in range(10):
        iso = IsolationForest(contamination=0.10, random_state=seed, n_estimators=200)
        preds = iso.fit_predict(X_pca)
        flag_counts += (preds == -1).astype(int)
    df['anomaly_flag_count'] = flag_counts.astype(int)
    df['is_high_confidence_anomaly'] = flag_counts >= 8

    iso_ref = IsolationForest(contamination=0.10, random_state=42, n_estimators=200)
    iso_ref.fit(X_pca)
    df['anomaly_score'] = -iso_ref.score_samples(X_pca)

    return df, loadings, stability


def explain_anomaly(row, peer_df):
    peer_pctile = lambda col: (peer_df[col] < row[col]).mean() * 100
    devs = [(c, peer_pctile(c)) for c in ['HAI_mean_score', 'poor_measure_count', 'achievement_mean']]
    devs.sort(key=lambda x: abs(x[1] - 50), reverse=True)
    return "; ".join([f"{c} at {p:.0f}th percentile" for c, p in devs[:2]])


if __name__ == "__main__":
    features = build_hospital_features()
    result, loadings, stability = run_pipeline(features)

    print(f"Cluster stability (ARI): {stability:.3f}")
    print(f"Cluster sizes:\n{result.cluster_name.value_counts()}")
    print(f"High-confidence anomalies: {result.is_high_confidence_anomaly.sum()} of {len(result)}")

    flagged = result[result.is_high_confidence_anomaly].copy()
    flagged['explanation'] = flagged.apply(lambda r: explain_anomaly(r, result), axis=1)

    result.to_parquet(f"{PROJECT_ROOT}/data/analytical/hospital_ml_results.parquet", index=False)
    flagged[['Facility ID', 'Facility Name', 'State', 'anomaly_score', 'explanation']].sort_values(
        'anomaly_score', ascending=False).to_csv(
        f"{PROJECT_ROOT}/data/analytical/hospital_anomaly_explanations.csv", index=False)
    loadings.to_csv(f"{PROJECT_ROOT}/data/analytical/hospital_pca_loadings.csv")

    print("\nTop 5 flagged hospitals:")
    print(flagged[['Facility Name', 'State', 'anomaly_score', 'explanation']].sort_values(
        'anomaly_score', ascending=False).head(5).to_string(index=False))
