"""analytics/utilization.py — Section 14.3. Per-category raw value, peer median, percentile, deviation."""
import pandas as pd
from app.analytics.peer_benchmark import peer_percentile

UTILIZATION_METRICS = {
    "P_EDV_Vis": "ED Visits",
    "P_EDV_Vis_HOSP": "ED Visits (Hospital)",
    "P_CT_VIS": "CT Imaging",
    "P_MRI_VIS": "MRI Imaging",
    "P_EM_Total": "E&M Total",
    "P_EM_PCP_Vis": "PCP Visits",
    "P_EM_SP_Vis": "Specialist Visits",
    "P_SNF_ADM": "SNF Admissions",
    "SNF_LOS": "SNF Length of Stay",
    "ADM": "Inpatient Admissions",
}


def utilization_scorecard(df: pd.DataFrame) -> pd.DataFrame:
    out_cols = ["ACO_ID", "ACO_Name", "peer_group"]
    result = df[out_cols].copy()
    for col, label in UTILIZATION_METRICS.items():
        if col not in df.columns:
            continue
        result[f"{col}_value"] = df[col]
        peer_median = df.groupby("peer_group")[col].transform("median")
        result[f"{col}_peer_median"] = peer_median
        result[f"{col}_deviation_pct"] = ((df[col] - peer_median) / peer_median.replace(0, pd.NA)) * 100
        result[f"{col}_percentile"] = peer_percentile(df, col)
    return result
