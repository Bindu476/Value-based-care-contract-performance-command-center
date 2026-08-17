"""tests/test_api/test_endpoints.py — Section 37. Uses FastAPI's TestClient, no live server needed."""

import sys as _sys
from pathlib import Path as _Path
_p = _Path(__file__).resolve()
while not (_p / "paths.py").exists():
    _p = _p.parent
_sys.path.insert(0, str(_p))
from paths import PROJECT_ROOT

import sys
sys.path.insert(0, f"{PROJECT_ROOT}/backend")
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_dashboard_returns_expected_shape():
    r = client.get("/api/dashboard")
    assert r.status_code == 200
    data = r.json()
    assert "kpis" in data
    assert data["kpis"]["total_acos"] == 476


def test_acos_list():
    r = client.get("/api/acos")
    assert r.status_code == 200
    assert len(r.json()) == 476


def test_acos_list_includes_contract_health_score():
    r = client.get("/api/acos")
    assert r.status_code == 200
    data = r.json()
    assert "contract_health_score" in data[0]
    assert isinstance(data[0]["contract_health_score"], (int, float))


def test_valid_aco_detail():
    r = client.get("/api/acos/A2973")
    assert r.status_code == 200
    data = r.json()
    assert data["aco_id"] == "A2973"
    assert "scores" in data


def test_invalid_aco_returns_404():
    r = client.get("/api/acos/NOTREAL")
    assert r.status_code == 404


def test_aco_drivers():
    r = client.get("/api/acos/A2973/drivers")
    assert r.status_code == 200
    assert len(r.json()) > 0


def test_opportunities_list():
    r = client.get("/api/opportunities?limit=5")
    assert r.status_code == 200
    assert len(r.json()) == 5


def test_review_brief_returns_evidence_even_without_llm():
    """Section 36: LLM unavailable must not break the endpoint."""
    r = client.post("/api/acos/A2973/review-brief")
    assert r.status_code == 200
    data = r.json()
    assert "recommendations" in data
    assert data["narrative_status"] in ("ok", "unavailable", "validation_failed")


def test_review_brief_includes_contract_health():
    r = client.post("/api/acos/A2973/review-brief")
    assert r.status_code == 200
    data = r.json()
    assert "contract_health" in data
    assert "breakdown" in data["contract_health"]
    assert "disclosure" in data["contract_health"]


def test_provider_and_hospital_carry_non_attribution_note():
    r = client.get("/api/providers/1000000001")
    if r.status_code == 200:
        assert "not attributed" in r.json()["attribution_note"]


def test_ask_returns_well_formed_response_even_without_llm():
    """Section 36: LLM unavailable must not break the ask endpoint — status 'unavailable', not a 500."""
    r = client.post("/api/acos/A2973/ask", json={"question": "Why is this ACO flagged as an anomaly?"})
    assert r.status_code == 200
    data = r.json()
    assert data["question"] == "Why is this ACO flagged as an anomaly?"
    assert data["status"] in ("ok", "unavailable", "validation_failed")
    if data["status"] != "ok":
        assert data["answer"] is None


def test_ask_invalid_aco_returns_404():
    r = client.post("/api/acos/NOTREAL/ask", json={"question": "What is going on?"})
    assert r.status_code == 404


def test_ask_rejects_empty_question():
    r = client.post("/api/acos/A2973/ask", json={"question": "   "})
    assert r.status_code == 400


def test_ask_rejects_overlong_question():
    r = client.post("/api/acos/A2973/ask", json={"question": "x" * 501})
    assert r.status_code == 400
