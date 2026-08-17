"""
backend/app/api/review.py — POST /api/acos/{aco_id}/review-brief, Section 25, Section 17.
Phase 12 scope: assembles the structured Evidence JSON only. LLM narrative generation
(Section 18) is added in Phase 13 — this endpoint is what the LLM will be fed.
Phase 14 adds free-text Q&A (POST /acos/{aco_id}/ask) grounded in the same evidence JSON.
"""
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from app.services.data_loader import load_all, get_aco_row
from app.services.llm_service import generate_narrative, ask_question

router = APIRouter()


def build_aco_evidence(aco_id: str) -> dict | None:
    """Assembles the structured Evidence JSON for an ACO. Returns None if aco_id is unknown."""
    fin = get_aco_row(aco_id, "financial")
    if fin is None:
        return None
    qual = get_aco_row(aco_id, "quality")
    cluster = get_aco_row(aco_id, "clusters")
    anomaly = get_aco_row(aco_id, "anomalies")
    health = get_aco_row(aco_id, "contract_health")

    data = load_all()
    cluster_profile = data["cluster_profiles"]
    cluster_name = cluster_profile[cluster_profile.cluster == cluster["cluster"]]["cluster_name"].iloc[0]

    drivers = data["drivers"]
    top_drivers = (drivers[drivers.ACO_ID == aco_id]
                   .sort_values("driver_score", ascending=False).head(3))
    driver_list = [
        {"name": r.driver_name, "priority": round(r.driver_score, 1), "confidence": r.confidence_label,
         "evidence": [f"{r.driver_name} at {r.peer_percentile:.0f}th percentile"]}
        for r in top_drivers.itertuples()
    ]

    explanations = data["anomaly_explanations"]
    match = explanations[explanations.ACO_ID == aco_id]
    anomaly_explanation = match.iloc[0]["peer_deviation_explanation"] if len(match) else None

    recs_aco = data["recs_aco"]
    aco_recs = recs_aco[recs_aco.ACO_ID == aco_id]["recommendation"].tolist()

    hospital_flagged_count = int(data["hospital_ml"].is_high_confidence_anomaly.sum())

    evidence = {
        "aco_id": aco_id,
        "aco_name": fin["ACO_Name"],
        "financial": {
            "status": fin["financial_status"],
            "gross_savings_loss": round(fin["GenSaveLoss"], 0),
            "benchmark": round(fin["ABtotBnchmk"], 0),
            "actual_expenditure": round(fin["ABtotExp"], 0),
            "expenditure_gap_pct": round(fin["expenditure_gap_pct"], 2),
        },
        "quality": {
            "score": round(qual["QualScore"], 1),
            "peer_percentile": round(qual["quality_peer_percentile"], 1),
            "band": qual["quality_band"],
        },
        "ml": {
            "cluster": cluster_name,
            "anomaly_score": round(anomaly["anomaly_score"], 3),
            "confidence_tier": anomaly["confidence_tier"],
            "anomaly_explanation": anomaly_explanation,
        },
        "contract_health": {
            "contract_health": health["contract_health_score"],
            "ml_risk": health["ml_risk_score"],
            "breakdown": {
                "financial_subscore": round(health["financial_subscore"], 1),
                "quality_subscore": round(health["quality_subscore"], 1),
                "utilization_subscore": round(health["utilization_subscore"], 1),
                "ml_risk_score": round(health["ml_risk_score"], 1),
                "weights": {"financial": 0.40, "quality": 0.25, "utilization": 0.15, "ml_risk": 0.20},
                "trend_status": health["trend_status"],
            },
            "disclosure": "Application-defined score, weights configurable — not a CMS score.",
        },
        "drivers": driver_list,
        "providers": {
            "note": "National context only — no verified ACO-provider attribution exists (Section 3.4/8.6). "
                    "Not included as ACO-specific findings.",
        },
        "hospital_context": {
            "note": "General portfolio context — not attributed to this ACO (Section 3.4).",
            "n_facilities_flagged_nationally": hospital_flagged_count,
        },
        "recommendations": aco_recs if aco_recs else ["No rule-triggered recommendation for this ACO at this time."],
        "limitations": [
            "ML identifies statistical patterns, not causality.",
            "Cluster and anomaly labels are application-generated interpretations, not CMS classifications.",
            "Provider and hospital signals are national context, not attributed to this specific ACO.",
        ],
    }

    return evidence


class AskRequest(BaseModel):
    question: str


@router.post("/acos/{aco_id}/review-brief")
def generate_review_brief(aco_id: str):
    evidence = build_aco_evidence(aco_id)
    if evidence is None:
        raise HTTPException(status_code=404, detail=f"ACO {aco_id} not found")

    evidence["narrative"] = None  # populated below by Phase 13 LLM layer
    llm_result = generate_narrative(evidence)
    evidence["narrative"] = llm_result["narrative"]
    evidence["narrative_status"] = llm_result["status"]
    if llm_result["status"] != "ok":
        evidence["narrative_note"] = llm_result.get("reason")

    return evidence


@router.post("/acos/{aco_id}/ask")
def ask_about_aco(aco_id: str, body: AskRequest):
    evidence = build_aco_evidence(aco_id)
    if evidence is None:
        raise HTTPException(status_code=404, detail=f"ACO {aco_id} not found")

    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question must not be empty")
    if len(question) > 500:
        raise HTTPException(status_code=400, detail="Question must be 500 characters or fewer")

    result = ask_question(evidence, question)
    return {
        "question": question,
        "answer": result["answer"],
        "status": result["status"],
        "reason": result.get("reason"),
    }
