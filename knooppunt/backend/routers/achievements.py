"""Endpoint voor het volledige achievement-overzicht."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Achievement
from schemas import AchievementOut

router = APIRouter(prefix="/api", tags=["achievements"])


@router.get("/achievements", response_model=list[AchievementOut])
def list_achievements(db: Session = Depends(get_db)):
    achievements = db.query(Achievement).order_by(Achievement.id.asc()).all()
    return [
        {
            "code": achievement.code,
            "title": achievement.title,
            "description": achievement.description,
            "icon": achievement.icon,
            "unlocked_at": achievement.unlocked_at,
        }
        for achievement in achievements
    ]
