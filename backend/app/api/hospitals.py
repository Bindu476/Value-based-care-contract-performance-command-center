"""backend/app/api/hospitals.py — Section 25. Not attributed to any ACO (Section 3.4)."""
from fastapi import APIRouter, HTTPException
from app.services.data_loader import load_all

router = APIRouter()


@router.get("/hospitals")
def list_hospitals(flagged_only: bool = False, limit: int = 100):
    hosp = load_all()["hospital_ml"]
    if flagged_only:
        hosp = hosp[hosp.is_high_confidence_anomaly]
    hosp = hosp.sort_values("anomaly_score", ascending=False).head(limit)
    return {
        "hospitals": hosp[["Facility ID", "Facility Name", "State", "cluster_name",
                           "HAI_mean_score", "anomaly_score", "is_high_confidence_anomaly"]].to_dict("records"),
        "cluster_distribution": load_all()["hospital_ml"].cluster_name.value_counts().to_dict(),
        "total_flagged": int(load_all()["hospital_ml"].is_high_confidence_anomaly.sum()),
        "total_facilities": len(load_all()["hospital_ml"]),
    }


@router.get("/hospitals/{hospital_id}")
def get_hospital(hospital_id: str):
    hosp = load_all()["hospital_ml"]
    match = hosp[hosp["Facility ID"].astype(str) == str(hospital_id)]
    if len(match) == 0:
        raise HTTPException(status_code=404, detail=f"Hospital {hospital_id} not found")
    row = match.iloc[0].to_dict()
    return {**row, "attribution_note": "National context, not attributed to any specific ACO (Section 3.4)"}
