"""analytics/quality.py — Section 14.2. Quality bands are application-defined, not CMS classifications."""
import pandas as pd
from app.analytics.peer_benchmark import peer_percentile


def quality_band(pctile: float) -> str:
    if pctile >= 75:
        return "Excellent"
    if pctile >= 50:
        return "Strong"
    if pctile >= 25:
        return "Watch"
    return "At Risk"


def quality_scorecard(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["quality_peer_percentile"] = peer_percentile(df, "QualScore")
    df["quality_band"] = df["quality_peer_percentile"].apply(quality_band)
    return df[["ACO_ID", "ACO_Name", "peer_group", "QualScore",
               "quality_peer_percentile", "quality_band"]]
