"""tests/test_recommendations/test_rules.py — Section 37. Each rule tested with a triggering and non-triggering input."""

import sys as _sys
from pathlib import Path as _Path
_p = _Path(__file__).resolve()
while not (_p / "paths.py").exists():
    _p = _p.parent
_sys.path.insert(0, str(_p))
from paths import PROJECT_ROOT

import pandas as pd
import sys
sys.path.insert(0, f"{PROJECT_ROOT}")
from pipelines.build_recommendations import apply_aco_rules


def make_row(**overrides):
    base = {
        "ACO_ID": "TEST1", "financial_status": "SAVINGS", "utilization_PC1": 0.0,
        "ADM_percentile": 50.0, "P_EDV_Vis_percentile": 50.0,
        "P_SNF_ADM_percentile": 50.0, "SNF_LOS_percentile": 50.0,
    }
    base.update(overrides)
    return base


def _triggered_rules_for(result: pd.DataFrame, aco_id: str) -> list:
    """Empty-safe helper: apply_aco_rules returns a columnless DataFrame when nothing triggers."""
    if "ACO_ID" not in result.columns:
        return []
    return result[result.ACO_ID == aco_id].rule.tolist()


def test_rule_a_triggers_on_loss_plus_high_acute_plus_high_pca():
    df = pd.DataFrame([make_row(
        financial_status="LOSS", ADM_percentile=95.0, utilization_PC1=10.0
    ), make_row(ACO_ID="OTHER", utilization_PC1=-5.0)])  # second row pulls quantile down so first is "high"
    result = apply_aco_rules(df)
    assert "A" in _triggered_rules_for(result, "TEST1")


def test_rule_a_does_not_trigger_on_savings_status():
    df = pd.DataFrame([make_row(
        financial_status="SAVINGS", ADM_percentile=95.0, utilization_PC1=10.0
    ), make_row(ACO_ID="OTHER", utilization_PC1=-5.0)])
    result = apply_aco_rules(df)
    assert "A" not in _triggered_rules_for(result, "TEST1")


def test_rule_c_triggers_on_snf_admission_p90():
    df = pd.DataFrame([make_row(P_SNF_ADM_percentile=95.0)])
    result = apply_aco_rules(df)
    assert "C" in _triggered_rules_for(result, "TEST1")


def test_rule_c_triggers_on_snf_los_p90_alone():
    df = pd.DataFrame([make_row(SNF_LOS_percentile=92.0)])  # OR condition — only LOS elevated
    result = apply_aco_rules(df)
    assert "C" in _triggered_rules_for(result, "TEST1")


def test_rule_c_does_not_trigger_below_threshold():
    df = pd.DataFrame([make_row(P_SNF_ADM_percentile=50.0, SNF_LOS_percentile=50.0)])
    result = apply_aco_rules(df)
    assert "C" not in _triggered_rules_for(result, "TEST1")
