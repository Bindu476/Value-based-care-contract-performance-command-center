"""
pipelines/provider_ml.py — Phase 8, SRS Section 8.
Provider-level PCA -> Clustering -> Isolation Forest, structurally identical to the ACO and
Hospital pipelines.

SCALE FIX #1: silhouette_score computes a full O(n^2) pairwise distance matrix by default —
infeasible at n>~1M. Above SILHOUETTE_SAMPLE_THRESHOLD, silhouette uses a subsample instead.

SCALE FIX #2: a PLAIN random subsample can miss a small minority cluster entirely (real
failure hit during development: an 8-point outlier cluster out of 1.2M provider rows was
absent from a random 10,000-row sample, causing sklearn's "Number of labels is 1" crash).
Fixed with a STRATIFIED sample — guarantees every cluster present in `labels` has at least
`min_per_cluster` representatives in the silhouette sample, regardless of how imbalanced the
clustering is. Verified against a deterministic 3-point-minority adversarial test case.

Also adds the same log1p skew correction used for ACO features (Section 7.2) — provider
payment/volume columns are heavily right-skewed and were previously scaled without this,
which was producing a near-degenerate PCA (99%+ variance in PC1 alone).

Progress is printed at every stage so a long real-data run is never silent.
"""

import sys as _sys
from pathlib import Path as _Path
_p = _Path(__file__).resolve()
while not (_p / "paths.py").exists():
    _p = _p.parent
_sys.path.insert(0, str(_p))
from paths import PROJECT_ROOT

import time
import pandas as pd
import numpy as np
from sklearn.preprocessing import RobustScaler
from sklearn.impute import SimpleImputer
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, adjusted_rand_score
from sklearn.ensemble import IsolationForest

FEATURE_COLS = ['total_services', 'total_beneficiaries', 'total_payment', 'service_diversity',
                'avg_payment_per_beneficiary', 'avg_payment_per_service', 'facility_share', 'office_share']
SKEW_CORRECT_COLS = ['total_services', 'total_beneficiaries', 'total_payment',
                      'avg_payment_per_beneficiary', 'avg_payment_per_service']

SILHOUETTE_SAMPLE_THRESHOLD = 20_000
SILHOUETTE_SAMPLE_SIZE = 10_000
MIN_PER_CLUSTER_IN_SAMPLE = 25


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def stratified_sample_indices(labels, sample_size, min_per_cluster=MIN_PER_CLUSTER_IN_SAMPLE, random_state=42):
    """Guarantees every cluster label has at least min_per_cluster (or all of it, if smaller)
    representatives in the returned index set — a plain random sample cannot do this when
    cluster sizes are wildly imbalanced (e.g. a few-point outlier cluster among 1M+ rows)."""
    rng = np.random.default_rng(random_state)
    labels = np.asarray(labels)
    n = len(labels)
    unique, counts = np.unique(labels, return_counts=True)

    idx_parts = []
    for lbl, cnt in zip(unique, counts):
        lbl_idx = np.where(labels == lbl)[0]
        proportional = int(round(sample_size * cnt / n))
        take = max(min_per_cluster, proportional)
        take = min(take, cnt)  # never sample more than exists in a tiny cluster
        idx_parts.append(rng.choice(lbl_idx, size=take, replace=False))

    idx = np.concatenate(idx_parts)
    rng.shuffle(idx)
    return idx


def safe_silhouette(X, labels, n):
    """Full computation for small/medium data; stratified subsample for large data."""
    if n <= SILHOUETTE_SAMPLE_THRESHOLD:
        return silhouette_score(X, labels)
    idx = stratified_sample_indices(labels, SILHOUETTE_SAMPLE_SIZE)
    labels_arr = np.asarray(labels)
    try:
        return silhouette_score(X[idx], labels_arr[idx])
    except ValueError as e:
        log(f"    (silhouette scoring failed even with stratified sample: {e} — scoring as -1)")
        return -1.0


def run_pipeline(min_rows_for_clustering=100):
    log("Loading provider_features.parquet...")
    df = pd.read_parquet(f"{PROJECT_ROOT}/data/processed/provider_features.parquet")
    n = len(df)
    is_sample_scale = n < min_rows_for_clustering
    log(f"Loaded {n:,} providers. Sample-scale: {is_sample_scale}")

    log("Skew correction (log1p on right-skewed payment/volume columns)...")
    df_feat = df.copy()
    for c in SKEW_CORRECT_COLS:
        if df_feat[c].min() >= 0 and df_feat[c].skew(skipna=True) > 1.0:
            df_feat[c] = np.log1p(df_feat[c])

    log("Imputing + scaling...")
    imputer = SimpleImputer(strategy="median")
    X_imp = imputer.fit_transform(df_feat[FEATURE_COLS])
    scaler = RobustScaler()
    X_scaled = scaler.fit_transform(X_imp)

    log("Running PCA...")
    n_components = min(4, X_scaled.shape[1], len(df) - 1)
    pca = PCA(n_components=n_components, random_state=42)
    X_pca = pca.fit_transform(X_scaled)
    loadings = pd.DataFrame(pca.components_.T, index=FEATURE_COLS,
                             columns=[f"PC{i+1}" for i in range(n_components)])
    log(f"PCA done. {n_components} components, {pca.explained_variance_ratio_.sum()*100:.1f}% variance explained "
        f"(PC1 alone: {pca.explained_variance_ratio_[0]*100:.1f}%).")

    df = df.copy()
    if is_sample_scale:
        log("Sample-scale: fitting single KMeans(k=2), no K-search.")
        km = KMeans(n_clusters=2, n_init=10, random_state=42)
        df['cluster'] = km.fit_predict(X_pca)
        stability = None
    else:
        if n > SILHOUETTE_SAMPLE_THRESHOLD:
            log(f"n={n:,} > {SILHOUETTE_SAMPLE_THRESHOLD:,} — silhouette will use a stratified "
                f"~{SILHOUETTE_SAMPLE_SIZE:,}-row sample per K (guarantees every cluster is represented).")

        best_k, best_sil = 2, -1
        k_range = range(2, min(9, len(df) // 10))
        for k in k_range:
            t0 = time.time()
            labels = KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(X_pca)
            sizes = pd.Series(labels).value_counts().to_dict()
            sil = safe_silhouette(X_pca, labels, n)
            log(f"  K={k}: silhouette={sil:.4f}  cluster sizes={sizes}  ({time.time()-t0:.1f}s)")
            if sil > best_sil:
                best_k, best_sil = k, sil
        log(f"Selected K={best_k} (silhouette={best_sil:.4f})")

        km = KMeans(n_clusters=best_k, n_init=10, random_state=42)
        labels_ref = km.fit_predict(X_pca)
        df['cluster'] = labels_ref

        log("Running stability check (5 reruns, ARI)...")
        aris = [adjusted_rand_score(labels_ref, KMeans(n_clusters=best_k, n_init=10, random_state=s).fit_predict(X_pca))
                for s in range(1, 6)]
        stability = np.mean(aris)
        log(f"Stability (mean ARI): {stability:.3f}")

    log(f"Running Isolation Forest (10-seed stability check)...")
    flag_counts = np.zeros(n)
    n_seeds = 10 if not is_sample_scale else 5
    for seed in range(n_seeds):
        t0 = time.time()
        iso = IsolationForest(contamination=min(0.10, max(1/n, 0.05)), random_state=seed, n_estimators=200, n_jobs=-1)
        preds = iso.fit_predict(X_pca)
        flag_counts += (preds == -1).astype(int)
        log(f"  seed {seed+1}/{n_seeds} done ({time.time()-t0:.1f}s)")
    threshold = int(np.ceil(0.8 * n_seeds))
    df['anomaly_flag_count'] = flag_counts.astype(int)
    df['is_high_confidence_anomaly'] = flag_counts >= threshold

    log("Computing final anomaly scores...")
    iso_ref = IsolationForest(contamination=min(0.10, max(1/n, 0.05)), random_state=42, n_estimators=200, n_jobs=-1)
    iso_ref.fit(X_pca)
    df['anomaly_score'] = -iso_ref.score_samples(X_pca)

    log("Pipeline complete.")
    return df, loadings, stability, is_sample_scale


if __name__ == "__main__":
    result, loadings, stability, is_sample = run_pipeline()

    print(f"\n{'SAMPLE-SCALE RUN (n=' + str(len(result)) + ', structural proof only)' if is_sample else 'FULL RUN'}")
    print(f"PCA loadings:\n{loadings}\n")
    print(f"Cluster sizes:\n{result.cluster.value_counts()}")
    if stability is not None:
        print(f"Cluster stability (ARI): {stability:.3f}")
    print(f"High-confidence anomalies: {result.is_high_confidence_anomaly.sum()} of {len(result)}")

    result.to_parquet(f"{PROJECT_ROOT}/data/analytical/provider_ml_results.parquet", index=False)
    loadings.to_csv(f"{PROJECT_ROOT}/data/analytical/provider_pca_loadings.csv")
    log(f"Saved to data/analytical/provider_ml_results.parquet")