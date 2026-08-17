"""backend/app/api/dashboard.py — GET /api/dashboard, Section 19 Page 1 data."""
from fastapi import APIRouter
from app.services.data_loader import load_all
import math

router = APIRouter()


def clean(v):
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v


@router.get("/dashboard")
def get_dashboard():
    data = load_all()
    fin = data["financial"]
    qual = data["quality"]
    clusters = data["clusters"]
    anomalies = data["anomalies"]
    opportunities = data["opportunities"]
    health = data["contract_health"]
    cluster_profiles = data["cluster_profiles"]

    total_acos = len(fin)
    savings_acos = int((fin.financial_status == "SAVINGS").sum())
    loss_acos = int((fin.financial_status == "LOSS").sum())
    total_net = float(fin.GenSaveLoss.sum())
    avg_quality = float(qual.QualScore.mean())
    anomalous_count = int((anomalies.confidence_tier != "NOT FLAGGED").sum())
    avg_contract_health = float(health.contract_health_score.mean())
    avg_ml_risk = float(health.ml_risk_score.mean())

    cluster_name_by_id = cluster_profiles.set_index("cluster")["cluster_name"].to_dict()
    cluster_dist_raw = clusters.cluster.value_counts().to_dict()
    cluster_dist = {cluster_name_by_id.get(k, str(k)): v for k, v in cluster_dist_raw.items()}

    bubble_data = (fin[["ACO_ID", "ACO_Name", "GenSaveLoss", "expenditure_gap_pct"]]
                   .merge(qual[["ACO_ID", "QualScore"]], on="ACO_ID")
                   .merge(anomalies[["ACO_ID", "confidence_tier"]], on="ACO_ID")
                   .merge(health[["ACO_ID", "contract_health_score"]], on="ACO_ID"))
    bubble_records = [
        {"aco_id": r.ACO_ID, "name": r.ACO_Name, "financial_pct": clean(round(r.expenditure_gap_pct, 2)),
         "quality": clean(round(r.QualScore, 1)), "anomaly": r.confidence_tier,
         "contract_health_score": clean(round(r.contract_health_score, 1))}
        for r in bubble_data.itertuples()
    ]

    top_opps = opportunities.head(10)[["priority_rank", "ACO_ID", "ACO_Name", "opportunity_priority",
                                        "driver_name", "financial_status", "confidence"]].to_dict("records")

    return {
        "kpis": {
            "total_acos": total_acos, "savings_acos": savings_acos, "loss_acos": loss_acos,
            "total_net_savings_loss": round(total_net, 0), "avg_quality": round(avg_quality, 1),
            "anomalous_aco_count": anomalous_count,
            "avg_contract_health": round(avg_contract_health, 1),
            "avg_ml_risk": round(avg_ml_risk, 1),
        },
        "cluster_distribution": cluster_dist,
        "financial_quality_bubbles": bubble_records,
        "top_opportunities": top_opps,
    }
