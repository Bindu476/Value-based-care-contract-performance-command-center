"""
analytics/peer_benchmark.py
Peer grouping + percentile computation with minimum-group-size guard.
Decision from Phase 0: primary peer dimension = Current_Track x Risk_Model (only 10 ACOs,
~2%, fall under 20 at this level). Agree_Type is added as refinement only when the resulting
3-way group still clears MIN_PEER_GROUP_SIZE.
"""
import pandas as pd

MIN_PEER_GROUP_SIZE = 20
PRIMARY_GROUP_COLS = ["Current_Track", "Risk_Model"]
REFINEMENT_COL = "Agree_Type"


def assign_peer_groups(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    primary_sizes = df.groupby(PRIMARY_GROUP_COLS)[PRIMARY_GROUP_COLS[0]].transform("size")

    refined_key = df[PRIMARY_GROUP_COLS + [REFINEMENT_COL]].astype(str).agg("|".join, axis=1)
    refined_sizes = refined_key.map(refined_key.value_counts())

    use_refined = refined_sizes >= MIN_PEER_GROUP_SIZE
    df["peer_group"] = df[PRIMARY_GROUP_COLS].astype(str).agg("|".join, axis=1)
    df.loc[use_refined, "peer_group"] = refined_key[use_refined]
    df["peer_group_size"] = df["peer_group"].map(df["peer_group"].value_counts())
    df["peer_group_refined"] = use_refined

    # Final fallback tier: even the 2-way (Track x Risk_Model) group can be <20 for genuinely
    # rare tracks (C, D — 5 ACOs nationally each). Fall back to Risk_Model alone for these.
    still_small = df["peer_group_size"] < MIN_PEER_GROUP_SIZE
    risk_model_sizes = df["Risk_Model"].map(df["Risk_Model"].value_counts())
    df.loc[still_small, "peer_group"] = "RiskModelOnly|" + df.loc[still_small, "Risk_Model"]
    df["peer_group_size"] = df["peer_group"].map(df["peer_group"].value_counts())
    df["peer_group_widened"] = still_small  # UI must show "Compared against broader peer group"

    return df


def peer_percentile(df: pd.DataFrame, metric_col: str) -> pd.Series:
    """Percentile rank of metric_col within each ACO's assigned peer_group."""
    return df.groupby("peer_group")[metric_col].rank(pct=True) * 100
