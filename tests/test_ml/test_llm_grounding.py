"""tests/test_ml/test_llm_grounding.py — Section 37. Validators must catch corrupted LLM output."""

import sys as _sys
from pathlib import Path as _Path
_p = _Path(__file__).resolve()
while not (_p / "paths.py").exists():
    _p = _p.parent
_sys.path.insert(0, str(_p))
from paths import PROJECT_ROOT

import sys
sys.path.insert(0, f"{PROJECT_ROOT}/backend")
from app.services.llm_service import validate_number_grounding, validate_provider_phrasing

EVIDENCE = {
    "aco_id": "A2973",
    "financial": {"status": "SAVINGS", "gross_savings_loss": 66307311, "expenditure_gap_pct": 20.17},
    "quality": {"score": 77.2, "peer_percentile": 12.9},
}


def test_grounded_narrative_passes():
    text = "This ACO recorded SAVINGS of $66,307,311, a gap of 20.17%. Quality score 77.2."
    ok, ungrounded = validate_number_grounding(text, EVIDENCE)
    assert ok, f"Unexpected ungrounded numbers: {ungrounded}"


def test_fabricated_number_is_caught():
    text = "This ACO recorded SAVINGS of $999,999,999 this year."
    ok, ungrounded = validate_number_grounding(text, EVIDENCE)
    assert not ok
    assert "999999999" in ungrounded


def test_trailing_sentence_period_does_not_cause_false_positive():
    """Regression test for the bug found during Phase 13 build."""
    text = "This ACO recorded SAVINGS of $66,307,311."
    ok, ungrounded = validate_number_grounding(text, EVIDENCE)
    assert ok, f"False positive on trailing period: {ungrounded}"


def test_forbidden_provider_attribution_phrase_is_caught():
    text = "This ACO's providers are driving the pattern within this contract."
    ok, found = validate_provider_phrasing(text)
    assert not ok
    assert len(found) > 0


def test_clean_narrative_passes_phrasing_check():
    text = "Providers nationally in this specialty show elevated utilization, as general context."
    ok, found = validate_provider_phrasing(text)
    assert ok
    assert found == []


def test_grounded_answer_passes():
    """Phase 14 Q&A: same validators apply to answer text, mirroring narrative grounding."""
    text = "This ACO recorded SAVINGS of $66,307,311, a gap of 20.17%."
    ok, ungrounded = validate_number_grounding(text, EVIDENCE)
    assert ok, f"Unexpected ungrounded numbers: {ungrounded}"


def test_fabricated_number_in_answer_is_caught():
    text = "This ACO's quality score is 999.9, well above peers."
    ok, ungrounded = validate_number_grounding(text, EVIDENCE)
    assert not ok
    assert "999.9" in ungrounded


def test_forbidden_provider_attribution_phrase_in_answer_is_caught():
    text = "Yes — this ACO's providers are the reason for the anomaly, within this contract."
    ok, found = validate_provider_phrasing(text)
    assert not ok
    assert len(found) > 0
