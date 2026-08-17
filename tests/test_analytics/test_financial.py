"""tests/test_analytics/test_financial.py — Section 37 unit tests."""

import sys as _sys
from pathlib import Path as _Path
_p = _Path(__file__).resolve()
while not (_p / "paths.py").exists():
    _p = _p.parent
_sys.path.insert(0, str(_p))
from paths import PROJECT_ROOT

import pandas as pd
import sys
sys.path.insert(0, f"{PROJECT_ROOT}/backend")
from app.analytics.financial import financial_scorecard
from app.analytics.peer_benchmark import assign_peer_groups


def make_fixture():
    df = pd.DataFrame({
        "ACO_ID": ["X1", "X2", "X3"],
        "ACO_Name": ["Alpha", "Beta", "Gamma"],
        "Current_Track": ["A", "A", "B"],
        "Risk_Model": ["One-Sided", "One-Sided", "Two-Sided"],
        "Agree_Type": ["Initial", "Initial", "Renewal"],
        "ABtotBnchmk": [1_000_000, 2_000_000, 500_000],
        "ABtotExp": [900_000, 2_100_000, 500_000],
        "GenSaveLoss": [100_000, -100_000, 0],
        "EarnSaveLoss": [80_000, -100_000, 0],
        "FinalShareRate": [0.5, 0.5, 0.5],
        "FinalLossRate": [0.0, 0.5, 0.0],
    })
    return assign_peer_groups(df)


def test_expenditure_gap_hand_computed():
    df = make_fixture()
    result = financial_scorecard(df)
    # hand-computed: 1,000,000 - 900,000 = 100,000
    assert result.loc[result.ACO_ID == "X1", "expenditure_gap"].iloc[0] == 100_000
    # 2,000,000 - 2,100,000 = -100,000
    assert result.loc[result.ACO_ID == "X2", "expenditure_gap"].iloc[0] == -100_000


def test_expenditure_gap_pct_hand_computed():
    df = make_fixture()
    result = financial_scorecard(df)
    # 100,000 / 1,000,000 * 100 = 10.0
    val = result.loc[result.ACO_ID == "X1", "expenditure_gap_pct"].iloc[0]
    assert abs(val - 10.0) < 1e-9


def test_financial_status_matches_gen_save_loss_sign():
    df = make_fixture()
    result = financial_scorecard(df)
    assert result.loc[result.ACO_ID == "X1", "financial_status"].iloc[0] == "SAVINGS"
    assert result.loc[result.ACO_ID == "X2", "financial_status"].iloc[0] == "LOSS"
    assert result.loc[result.ACO_ID == "X3", "financial_status"].iloc[0] == "SAVINGS"  # 0 >= 0


def test_no_zero_or_negative_benchmark_produces_infinite_gap():
    df = make_fixture()
    result = financial_scorecard(df)
    import numpy as np
    assert not result["expenditure_gap_pct"].isin([np.inf, -np.inf]).any()
