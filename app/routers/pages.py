from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape
from datetime import datetime

from ..database import SessionLocal
from ..db_models import Patient, TreatmentPlan

router = APIRouter()

# Configure Jinja environment
env = Environment(
    loader=FileSystemLoader("app/templates"),
    autoescape=select_autoescape(["html", "xml"]),
)

# Auto update treatment progress based on date range
def auto_update_progress(db, treatment):
    if not treatment.start_date or not treatment.next_checkup_date:
        return

    total_days = (treatment.next_checkup_date - treatment.start_date).days
    days_elapsed = (datetime.utcnow() - treatment.start_date).days

    if total_days <= 0:
        treatment.progress_percent = 100
        treatment.cured = True
    else:
        progress = min(100, int((days_elapsed / total_days) * 100))
        treatment.progress_percent = progress
        treatment.cured = progress >= 100

    db.commit()
    db.refresh(treatment)

@router.get("/", response_class=HTMLResponse)
async def landing(request: Request) -> HTMLResponse:
    db = SessionLocal()

    # Get latest patient and latest treatment
    patient = db.query(Patient).order_by(Patient.id.desc()).first()
    latest_treatment = db.query(TreatmentPlan).order_by(TreatmentPlan.id.desc()).first()

    # Auto update progress each time home loads
    progress = 0
    if latest_treatment:
        auto_update_progress(db, latest_treatment)
        progress = latest_treatment.progress_percent

    template = env.get_template("landing.html")
    return HTMLResponse(
        template.render(
            request=request,
            patient=patient,
            progress=progress,
            latest_treatment=latest_treatment,
        )
    )
