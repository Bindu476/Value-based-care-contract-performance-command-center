"""backend/app/api/opportunities.py — Section 25, Section 19 Page 7."""
from fastapi import APIRouter
from app.services.data_loader import load_all

router = APIRouter()


@router.get("/opportunities")
def list_opportunities(limit: int = 50):
    opps = load_all()["opportunities"]
    return opps.head(limit).to_dict("records")
