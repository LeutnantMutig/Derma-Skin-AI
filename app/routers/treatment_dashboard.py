from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.db_models import TreatmentPlan, Patient

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/treatments/dashboard", response_class=HTMLResponse)
def treatment_dashboard(request: Request, db: Session = Depends(get_db)):
    treatments = db.query(TreatmentPlan).all()
    ongoing = [t for t in treatments if not t.cured]
    cured = [t for t in treatments if t.cured]

    # Stats
    total = len(treatments)
    cured_count = len(cured)
    ongoing_count = len(ongoing)
    cured_percent = (cured_count / total * 100) if total > 0 else 0

    # Next checkup reminders
    upcoming = [
        t for t in treatments 
        if t.next_checkup_date and t.next_checkup_date >= datetime.utcnow()
    ]
    upcoming.sort(key=lambda x: x.next_checkup_date)

    return templates.TemplateResponse("treatment_dashboard.html", {
        "request": request,
        "treatments": treatments,
        "ongoing": ongoing,
        "cured": cured,
        "cured_percent": round(cured_percent, 1),
        "upcoming": upcoming
    })
