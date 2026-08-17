"""
tests/test_ml/test_pipeline_regression.py — Section 37.
Fixed synthetic mini-dataset with a KNOWN, designed-in outlier. The pipeline must recover it —
this catches regressions that real-data-only testing can't, since real-data "correct" output
isn't independently known.
"""

import sys as _sys
from pathlib import Path as _Path
_p = _Path(__file__).resolve()
while not (_p / "paths.py").exists():
    _p = _p.parent
_sys.path.insert(0, str(_p))
from paths import PROJECT_ROOT

import numpy as np
from sklearn.preprocessing import RobustScaler
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.cluster import KMeans


def make_synthetic_dataset(seed=42):
    rng = np.random.default_rng(seed)
    n_normal = 40
    normal = rng.normal(loc=0, scale=1, size=(n_normal, 5))
    # one clear, designed-in outlier: 8 standard deviations out on every dimension
    outlier = np.full((1, 5), 8.0)
    X = np.vstack([normal, outlier])
    return X, n_normal  # index n_normal is the known outlier


def test_isolation_forest_recovers_designed_in_outlier():
    X, outlier_idx = make_synthetic_dataset()
    scaler = RobustScaler()
    X_scaled = scaler.fit_transform(X)

    flag_counts = np.zeros(len(X))
    for seed in range(10):
        iso = IsolationForest(contamination=0.05, random_state=seed, n_estimators=200)
        preds = iso.fit_predict(X_scaled)
        flag_counts += (preds == -1).astype(int)

    # the designed-in outlier must be flagged in every single rerun
    assert flag_counts[outlier_idx] == 10, f"Known outlier only flagged {flag_counts[outlier_idx]}/10 times"


def test_pca_preserves_outlier_separation():
    X, outlier_idx = make_synthetic_dataset()
    scaler = RobustScaler()
    X_scaled = scaler.fit_transform(X)
    pca = PCA(n_components=2, random_state=42)
    X_pca = pca.fit_transform(X_scaled)

    # the outlier's PC1 magnitude should be far larger than any normal point's
    outlier_pc1 = abs(X_pca[outlier_idx, 0])
    normal_pc1_max = np.abs(np.delete(X_pca[:, 0], outlier_idx)).max()
    assert outlier_pc1 > normal_pc1_max * 2, "PCA did not preserve outlier separation"


def test_clustering_does_not_collapse_to_single_cluster():
    """A degenerate pipeline (e.g. all-zero scaling bug) would collapse everything into one cluster."""
    X, _ = make_synthetic_dataset()
    scaler = RobustScaler()
    X_scaled = scaler.fit_transform(X)
    km = KMeans(n_clusters=2, n_init=10, random_state=42)
    labels = km.fit_predict(X_scaled)
    assert len(set(labels)) == 2, "Clustering collapsed to a single cluster — likely a preprocessing bug"


def test_outcome_variable_exclusion_enforced():
    """Section 6.2/28.7: regression guard against reintroducing outcome leakage."""
    import sys
    sys.path.insert(0, f"{PROJECT_ROOT}")
    from pipelines.build_ml_features import EXCLUDED_FROM_ML_INPUT, select_block_columns
    import pandas as pd

    fake_df = pd.DataFrame({
        "ACO_ID": ["A"], "ABtotBnchmk": [100], "GenSaveLoss": [10], "EarnSaveLoss": [8],
    })
    cols = select_block_columns(fake_df, ["ABtotBnchmk", "GenSaveLoss", "EarnSaveLoss"])
    assert "GenSaveLoss" not in cols
    assert "EarnSaveLoss" not in cols
    assert "ABtotBnchmk" in cols
