"""
backend/app/api/contracts.py — Contract Performance module.

Every field here is a real CMS MSSP financial-settlement field (ABtotBnchmk, ABtotExp,
GenSaveLoss, EarnSaveLoss, FinalShareRate, FinalLossRate) or an application-computed score
already used elsewhere (Contract Health, ML risk). Nothing is invented: MSSP's actual
settlement mechanism is Gross Savings/Loss × Final Share/Loss Rate = Earned Savings/Loss —
a single multiplier step, not the multi-stage "quality/risk adjustment" waterfall sometimes
shown in illustrative dashboards. We show that one real step, not a fabricated one.
"""
from fastapi import APIRouter
from app.services.data_loader import load_all

router = APIRouter()


@router.get("/contracts")
def list_contracts():
    data = load_all()
    fin = data["financial"]
    qual = data["quality"][["ACO_ID", "QualScore", "quality_band"]]
    anomalies = data["anomalies"][["ACO_ID", "confidence_tier"]]
    health = data["contract_health"][["ACO_ID", "contract_health_score", "utilization_subscore", "ml_risk_score"]]

    merged = (fin.merge(qual, on="ACO_ID")
                 .merge(anomalies, on="ACO_ID")
                 .merge(health, on="ACO_ID"))

    records = []
    for r in merged.itertuples():
        records.append({
            "aco_id": r.ACO_ID,
            "aco_name": r.ACO_Name,
            "peer_group": r.peer_group,
            "peer_group_size": int(r.peer_group_size),
            "benchmark": round(float(r.ABtotBnchmk), 0),
            "actual_expenditure": round(float(r.ABtotExp), 0),
            "expenditure_gap_pct": round(float(r.expenditure_gap_pct), 2),
            "gross_savings_loss": round(float(r.GenSaveLoss), 0),
            "earned_savings_loss": round(float(r.EarnSaveLoss), 0),
            "share_rate": round(float(r.FinalShareRate), 1),
            "loss_rate": round(float(r.FinalLossRate), 1),
            "financial_status": r.financial_status,
            "quality_score": round(float(r.QualScore), 1),
            "quality_band": r.quality_band,
            "contract_health_score": round(float(r.contract_health_score), 1),
            "utilization_score": round(float(r.utilization_subscore), 1),
            "ml_risk_score": round(float(r.ml_risk_score), 1),
            "confidence_tier": r.confidence_tier,
        })

    n = len(records)
    return {
        "contracts": records,
        "total_contracts": n,
        "portfolio_avg_contract_health": round(sum(c["contract_health_score"] for c in records) / n, 1),
        "portfolio_avg_quality": round(sum(c["quality_score"] for c in records) / n, 1),
        "portfolio_avg_utilization": round(sum(c["utilization_score"] for c in records) / n, 1),
        "portfolio_total_benchmark": round(sum(c["benchmark"] for c in records), 0),
        "portfolio_total_expenditure": round(sum(c["actual_expenditure"] for c in records), 0),
        "portfolio_total_gross_savings_loss": round(sum(c["gross_savings_loss"] for c in records), 0),
        "portfolio_total_earned_savings_loss": round(sum(c["earned_savings_loss"] for c in records), 0),
    }
