"""
pipelines/build_scorecards.py — Phase 2, SRS Section 14.
Builds financial, quality, and utilization scorecards from cleaned MSSP data and saves them
to data/analytical/. This is the baseline that ML (Phases 3+) is validated against — must run
before any downstream pipeline script.
"""
import sys as _sys
from pathlib import Path as _Path
_p = _Path(__file__).resolve()
while not (_p / "paths.py").exists():
    _p = _p.parent
_sys.path.insert(0, str(_p))
from paths import PROJECT_ROOT, DATA_PROCESSED, DATA_ANALYTICAL

_sys.path.insert(0, f"{PROJECT_ROOT}/backend")

import pandas as pd
from app.analytics.peer_benchmark import assign_peer_groups
from app.analytics.financial import financial_scorecard
from app.analytics.quality import quality_scorecard
from app.analytics.utilization import utilization_scorecard

if __name__ == "__main__":
    df = pd.read_parquet(f"{DATA_PROCESSED}/mssp_clean.parquet")
    df = assign_peer_groups(df)

    fin = financial_scorecard(df)
    qual = quality_scorecard(df)
    util = utilization_scorecard(df)

    fin.to_parquet(f"{DATA_ANALYTICAL}/financial_scorecard.parquet", index=False)
    qual.to_parquet(f"{DATA_ANALYTICAL}/quality_scorecard.parquet", index=False)
    util.to_parquet(f"{DATA_ANALYTICAL}/utilization_scorecard.parquet", index=False)

    print(f"Financial scorecard: {fin.shape} -> financial_scorecard.parquet")
    print(f"Quality scorecard: {qual.shape} -> quality_scorecard.parquet")
    print(f"Utilization scorecard: {util.shape} -> utilization_scorecard.parquet")
    print(f"\nFinancial status distribution:\n{fin.financial_status.value_counts()}")
