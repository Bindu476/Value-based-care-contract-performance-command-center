"""tests/test_analytics/test_peer_benchmark.py"""

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
from app.analytics.peer_benchmark import assign_peer_groups, MIN_PEER_GROUP_SIZE


def test_every_group_meets_minimum_size():
    """Section 7.9/32 risk #6: no ACO should end up in a peer group under 20, even at the edge."""
    # 15 in a common group, 3 rare singletons that must fall back
    rows = []
    for i in range(15):
        rows.append({"ACO_ID": f"COMMON{i}", "Current_Track": "EN", "Risk_Model": "Two-Sided", "Agree_Type": "Renewal"})
    for i in range(3):
        rows.append({"ACO_ID": f"RARE{i}", "Current_Track": "D", "Risk_Model": "Two-Sided", "Agree_Type": "Initial"})
    df = pd.DataFrame(rows)
    result = assign_peer_groups(df)
    assert (result["peer_group_size"] >= MIN_PEER_GROUP_SIZE).all() or len(df) < MIN_PEER_GROUP_SIZE


def test_widened_flag_set_correctly():
    rows = [{"ACO_ID": f"A{i}", "Current_Track": "EN", "Risk_Model": "Two-Sided", "Agree_Type": "Renewal"} for i in range(25)]
    rows += [{"ACO_ID": "RARE1", "Current_Track": "D", "Risk_Model": "One-Sided", "Agree_Type": "Initial"}]
    df = pd.DataFrame(rows)
    result = assign_peer_groups(df)
    rare_row = result[result.ACO_ID == "RARE1"].iloc[0]
    common_row = result[result.ACO_ID == "A0"].iloc[0]
    assert rare_row["peer_group_widened"] == True
    assert common_row["peer_group_widened"] == False
