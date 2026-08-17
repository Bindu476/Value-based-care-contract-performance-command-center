"""analytics/financial.py — Section 14.1. Uses published MSSP fields as-is, no CMS methodology recreated."""
import pandas as pd
from app.analytics.peer_benchmark import peer_percentile


def financial_scorecard(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["expenditure_gap"] = df["ABtotBnchmk"] - df["ABtotExp"]
    df["expenditure_gap_pct"] = (df["expenditure_gap"] / df["ABtotBnchmk"]) * 100
    df["financial_status"] = df["GenSaveLoss"].apply(lambda x: "SAVINGS" if x >= 0 else "LOSS")
    df["expenditure_gap_pct_peer_percentile"] = peer_percentile(df, "expenditure_gap_pct")
    df["gen_save_loss_peer_percentile"] = peer_percentile(df, "GenSaveLoss")
    return df[["ACO_ID", "ACO_Name", "peer_group", "peer_group_size", "peer_group_widened",
               "ABtotBnchmk", "ABtotExp", "expenditure_gap", "expenditure_gap_pct",
               "GenSaveLoss", "EarnSaveLoss", "FinalShareRate", "FinalLossRate",
               "financial_status", "expenditure_gap_pct_peer_percentile", "gen_save_loss_peer_percentile"]]
