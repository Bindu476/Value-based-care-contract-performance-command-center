"""
backend/app/api/providers.py — Section 25. Note Section 8.6: not attributed to any ACO.

/providers/stats  — full-dataset summary (score distribution, flagged %), computed once
                     over ALL rows regardless of pagination — this is what "complete
                     information" for the page should be sourced from, not a partial slice.
/providers        — paginated, MIXED order by default (random, fixed seed for reproducibility
                     per page) — NOT sorted by anomaly score, so the default view isn't
                     misleadingly skewed toward the extreme tail. Sorting is opt-in via sort_by.
"""
from fastapi import APIRouter, HTTPException, Query
from app.services.data_loader import load_all
import numpy as np

router = APIRouter()


@router.get("/providers/stats")
def provider_stats():
    prov = load_all()["provider_ml"]
    total = len(prov)
    flagged = int(prov["is_high_confidence_anomaly"].sum())

    # histogram of anomaly_score across the FULL dataset — cheap to compute, gives the
    # frontend a true picture of the distribution without transferring 1.2M rows
    counts, bin_edges = np.histogram(prov["anomaly_score"], bins=20)
    histogram = [{"bin_start": round(float(bin_edges[i]), 3), "bin_end": round(float(bin_edges[i+1]), 3),
                  "count": int(counts[i])} for i in range(len(counts))]

    # specialty aggregates over the FULL dataset — these feed the "Avg Payment by Specialty"
    # and "Specialty Mix" charts, which must reflect the true national pattern, not whatever
    # happens to be on the current paginated page
    specialty_group = prov.groupby("specialty").agg(
        avg_payment_per_beneficiary=("avg_payment_per_beneficiary", "mean"),
        count=("specialty", "size"),
    ).reset_index().sort_values("avg_payment_per_beneficiary", ascending=False)
    specialty_avg_payment = [
        {"specialty": r.specialty, "avg_payment_per_beneficiary": round(float(r.avg_payment_per_beneficiary), 2),
         "count": int(r.count)}
        for r in specialty_group.itertuples()
    ]

    specialty_counts = prov["specialty"].value_counts()
    top_specialties = specialty_counts.head(5)
    other_count = int(specialty_counts.iloc[5:].sum()) if len(specialty_counts) > 5 else 0
    specialty_mix = [{"name": name, "value": int(count)} for name, count in top_specialties.items()]
    if other_count > 0:
        specialty_mix.append({"name": "Other", "value": other_count})

    return {
        "total_providers": total,
        "flagged_count": flagged,
        "flagged_pct": round(flagged / total * 100, 2) if total else 0,
        "specialty_avg_payment": specialty_avg_payment,
        "specialty_mix": specialty_mix,
        "anomaly_score": {
            "mean": round(float(prov["anomaly_score"].mean()), 4),
            "std": round(float(prov["anomaly_score"].std()), 4),
            "min": round(float(prov["anomaly_score"].min()), 4),
            "max": round(float(prov["anomaly_score"].max()), 4),
            "p50": round(float(prov["anomaly_score"].quantile(0.50)), 4),
            "p90": round(float(prov["anomaly_score"].quantile(0.90)), 4),
            "p99": round(float(prov["anomaly_score"].quantile(0.99)), 4),
        },
        "histogram": histogram,
        "cluster_distribution": prov["cluster"].value_counts().to_dict(),
    }


@router.get("/providers")
def list_providers(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=2000),
    sort_by: str = Query("mixed", pattern="^(mixed|anomaly_desc|anomaly_asc|npi)$"),
    anomalies_only: bool = False,
    specialty: str | None = None,
    state: str | None = None,
):
    prov = load_all()["provider_ml"]
    is_sample = len(prov) < 100
    total_before_filter = len(prov)

    if anomalies_only:
        prov = prov[prov["is_high_confidence_anomaly"]]
    if specialty:
        prov = prov[prov["specialty"] == specialty]
    if state:
        prov = prov[prov["state"] == state]

    filtered_total = len(prov)

    if sort_by == "anomaly_desc":
        prov = prov.sort_values("anomaly_score", ascending=False)
    elif sort_by == "anomaly_asc":
        prov = prov.sort_values("anomaly_score", ascending=True)
    elif sort_by == "npi":
        prov = prov.sort_values("Rndrng_NPI")
    else:  # mixed — deterministic shuffle so pagination is stable across requests
        prov = prov.sample(frac=1, random_state=42)

    start = (page - 1) * page_size
    end = start + page_size
    page_df = prov.iloc[start:end]

    records = page_df[["Rndrng_NPI", "specialty", "state", "total_services", "total_beneficiaries",
                        "avg_payment_per_beneficiary", "cluster", "anomaly_score",
                        "is_high_confidence_anomaly"]].to_dict("records")

    return {
        "providers": records,
        "is_sample_scale": is_sample,
        "total_providers": total_before_filter,
        "filtered_total": filtered_total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, -(-filtered_total // page_size)),
        "sort_by": sort_by,
    }


@router.get("/providers/{provider_id}")
def get_provider(provider_id: str):
    prov = load_all()["provider_ml"]
    match = prov[prov.Rndrng_NPI.astype(str) == str(provider_id)]
    if len(match) == 0:
        raise HTTPException(status_code=404, detail=f"Provider {provider_id} not found")
    row = match.iloc[0].to_dict()
    return {**row, "attribution_note": "National context, not attributed to any specific ACO (Section 3.4)"}