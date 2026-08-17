"""backend/app/api/acos.py — ACO list + detail endpoints, Sections 19 Pages 2-4, 25."""
from fastapi import APIRouter, HTTPException
from app.services.data_loader import load_all, get_aco_row

router = APIRouter()


@router.get("/acos")
def list_acos():
    data = load_all()
    fin = data["financial"]
    qual = data["quality"][["ACO_ID", "QualScore", "quality_band"]]
    anomalies = data["anomalies"][["ACO_ID", "confidence_tier"]]
    health = data["contract_health"][["ACO_ID", "contract_health_score"]]
    merged = fin[["ACO_ID", "ACO_Name", "financial_status", "GenSaveLoss"]].merge(
        qual, on="ACO_ID").merge(anomalies, on="ACO_ID").merge(health, on="ACO_ID")
    return merged.to_dict("records")


@router.get("/acos/{aco_id}")
def get_aco(aco_id: str):
    fin = get_aco_row(aco_id, "financial")
    if fin is None:
        raise HTTPException(status_code=404, detail=f"ACO {aco_id} not found")
    qual = get_aco_row(aco_id, "quality")
    cluster = get_aco_row(aco_id, "clusters")
    anomaly = get_aco_row(aco_id, "anomalies")
    health = get_aco_row(aco_id, "contract_health")
    cluster_profile = load_all()["cluster_profiles"]
    cluster_name = cluster_profile[cluster_profile.cluster == cluster["cluster"]]["cluster_name"].iloc[0]

    return {
        "aco_id": aco_id, "aco_name": fin["ACO_Name"],
        "financial": {"status": fin["financial_status"], "gen_save_loss": fin["GenSaveLoss"],
                      "expenditure_gap_pct": round(fin["expenditure_gap_pct"], 2),
                      "peer_group": fin["peer_group"], "peer_group_widened": bool(fin["peer_group_widened"])},
        "quality": {"score": qual["QualScore"], "band": qual["quality_band"],
                    "peer_percentile": round(qual["quality_peer_percentile"], 1)},
        "ml_profile": {"cluster": cluster_name, "anomaly_score": round(anomaly["anomaly_score"], 3),
                       "confidence_tier": anomaly["confidence_tier"]},
        "scores": {
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
    }


@router.get("/acos/{aco_id}/financial")
def get_aco_financial(aco_id: str):
    row = get_aco_row(aco_id, "financial")
    if row is None:
        raise HTTPException(status_code=404, detail=f"ACO {aco_id} not found")
    return row


@router.get("/acos/{aco_id}/quality")
def get_aco_quality(aco_id: str):
    row = get_aco_row(aco_id, "quality")
    if row is None:
        raise HTTPException(status_code=404, detail=f"ACO {aco_id} not found")
    return row


@router.get("/acos/{aco_id}/utilization")
def get_aco_utilization(aco_id: str):
    row = get_aco_row(aco_id, "utilization")
    if row is None:
        raise HTTPException(status_code=404, detail=f"ACO {aco_id} not found")
    metrics = ["P_EDV_Vis", "P_CT_VIS", "P_MRI_VIS", "P_EM_Total", "P_EM_PCP_Vis",
               "P_EM_SP_Vis", "P_SNF_ADM", "SNF_LOS", "ADM"]
    structured = []
    for m in metrics:
        if f"{m}_value" in row:
            structured.append({
                "metric": m,
                "value": row[f"{m}_value"],
                "peer_median": round(row[f"{m}_peer_median"], 1) if row.get(f"{m}_peer_median") is not None else None,
                "deviation_pct": round(row[f"{m}_deviation_pct"], 1) if row.get(f"{m}_deviation_pct") is not None else None,
                "percentile": round(row[f"{m}_percentile"], 1) if row.get(f"{m}_percentile") is not None else None,
            })
    return {"aco_id": aco_id, "metrics": structured}


@router.get("/acos/{aco_id}/ml-profile")
def get_aco_ml_profile(aco_id: str):
    cluster = get_aco_row(aco_id, "clusters")
    anomaly = get_aco_row(aco_id, "anomalies")
    if cluster is None:
        raise HTTPException(status_code=404, detail=f"ACO {aco_id} not found")
    pca_labels = load_all()["pca_labels"]
    components = [{"component": k.replace(f"_", " "), "value": round(cluster[k], 3)}
                  for k in cluster if k.endswith(("PC1", "PC2", "PC3", "PC4"))]
    return {"aco_id": aco_id, "cluster": cluster["cluster"], "anomaly_score": anomaly["anomaly_score"],
            "confidence_tier": anomaly["confidence_tier"], "pca_components": components}


@router.get("/acos/{aco_id}/anomalies")
def get_aco_anomalies(aco_id: str):
    anomaly = get_aco_row(aco_id, "anomalies")
    if anomaly is None:
        raise HTTPException(status_code=404, detail=f"ACO {aco_id} not found")
    explanations = load_all()["anomaly_explanations"]
    match = explanations[explanations.ACO_ID == aco_id]
    explanation = match.iloc[0]["peer_deviation_explanation"] if len(match) else None
    return {**anomaly, "explanation": explanation}


@router.get("/acos/{aco_id}/drivers")
def get_aco_drivers(aco_id: str):
    drivers = load_all()["drivers"]
    match = drivers[drivers.ACO_ID == aco_id].sort_values("driver_score", ascending=False)
    if len(match) == 0:
        raise HTTPException(status_code=404, detail=f"ACO {aco_id} not found")
    return match.to_dict("records")


@router.get("/acos/{aco_id}/opportunities")
def get_aco_opportunities(aco_id: str):
    opps = load_all()["opportunities"]
    match = opps[opps.ACO_ID == aco_id]
    if len(match) == 0:
        raise HTTPException(status_code=404, detail=f"ACO {aco_id} not found")
    return match.to_dict("records")[0]
