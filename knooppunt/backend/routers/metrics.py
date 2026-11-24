"""Endpoint voor de zuinigheidsindicator (live jury-metrics)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from docs2md import get_usage_metric
from schemas import MetricsOut

router = APIRouter(prefix="/api", tags=["metrics"])


@router.get("/metrics", response_model=MetricsOut)
def get_metrics(db: Session = Depends(get_db)):
    metric = get_usage_metric(db)
    db.commit()
    return {
        "layer1_calls": metric.layer1_calls or 0,
        "layer3_calls": metric.layer3_calls or 0,
        "zero_ai_actions": metric.zero_ai_actions or 0,
        "tokens_saved_est": metric.tokens_saved_est or 0,
    }
