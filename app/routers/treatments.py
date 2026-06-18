from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from app.database import get_db
from app.db_models import TreatmentPlan, Checkup, Patient

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

UPLOAD_FOLDER = "app/static/uploads/treatments"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------------- New Treatment ----------------------
@router.get("/treatment/new/{checkup_id}", response_class=HTMLResponse)
def new_treatment_page(request: Request, checkup_id: int, db: Session = Depends(get_db)):
    checkup = db.query(Checkup).filter(Checkup.id == checkup_id).first()
    if not checkup:
        return RedirectResponse(url="/", status_code=303)

    patient = db.query(Patient).filter(Patient.id == checkup.patient_id).first()
    return templates.TemplateResponse("treatment_new.html", {
        "request": request,
        "checkup": checkup,
        "patient": patient
    })

# ---------------------- Save Treatment ----------------------
@router.post("/treatment/new/{checkup_id}")
async def save_treatment(
    request: Request,
    checkup_id: int,
    remedy_name: str = Form(...),
    medicines: str = Form(""),
    dosage: str = Form(""),
    notes: str = Form(""),
    next_checkup_date: str = Form(""),
    db: Session = Depends(get_db)
):
    # Fetch the related checkup and patient
    checkup = db.query(Checkup).filter(Checkup.id == checkup_id).first()
    if not checkup:
        return RedirectResponse(url="/", status_code=303)
    patient = db.query(Patient).filter(Patient.id == checkup.patient_id).first()

    # Automatically use analyzed image from checkup as after_image
    analyzed_image_path = checkup.image_path if checkup and checkup.image_path else None

    # Create treatment plan
    treatment = TreatmentPlan(
        patient_id=patient.id,
        checkup_id=checkup.id,
        disease_name=checkup.predicted_condition,
        remedy_name=remedy_name,
        medicines=medicines,
        dosage=dosage,
        notes=notes,
        next_checkup_date=datetime.strptime(next_checkup_date, "%Y-%m-%d") if next_checkup_date else None,
        before_image_path=checkup.image_path,      # before = same analyzed image
        after_image_path=analyzed_image_path       # after = same analyzed image
    )

    db.add(treatment)
    db.commit()

    return RedirectResponse(url=f"/treatment/report/{treatment.id}", status_code=303)


# ---------------------- Treatment Report ----------------------
@router.get("/treatment/report/{plan_id}", response_class=HTMLResponse)
def treatment_report(request: Request, plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(TreatmentPlan).filter(TreatmentPlan.id == plan_id).first()
    if not plan:
        return RedirectResponse(url="/", status_code=303)

    # Auto-progress calculation
    if plan.auto_progress and plan.next_checkup_date and plan.start_date:
        total_days = (plan.next_checkup_date - plan.start_date).days
        elapsed_days = (datetime.utcnow() - plan.start_date).days
        progress = min(int((elapsed_days / total_days) * 100), 100) if total_days > 0 else 0

        if progress != plan.progress_percent:
            plan.progress_percent = progress
            if progress >= 100:
                plan.cured = True
            db.commit()

    return templates.TemplateResponse("treatment_report.html", {"request": request, "plan": plan})


# ---------------------- Update Progress ----------------------
@router.post("/treatment/update_progress/{plan_id}")
async def update_progress(plan_id: int, progress_percent: int = Form(...), db: Session = Depends(get_db)):
    plan = db.query(TreatmentPlan).filter(TreatmentPlan.id == plan_id).first()
    if plan:
        plan.progress_percent = min(progress_percent, 100)
        if plan.progress_percent >= 100:
            plan.cured = True
        plan.auto_progress = False
        db.commit()
    return RedirectResponse(url=f"/treatment/report/{plan.id}", status_code=303)


# ---------------------- Generate PDF Report ----------------------
@router.get("/treatment/report/pdf/{plan_id}")
def generate_pdf(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(TreatmentPlan).filter(TreatmentPlan.id == plan_id).first()
    if not plan:
        return RedirectResponse(url="/", status_code=303)

    pdf_path = f"app/static/reports/treatment_{plan.id}.pdf"
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)

    c = canvas.Canvas(pdf_path, pagesize=A4)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(100, 800, "DermaSkin Cure - Treatment Report")

    c.setFont("Helvetica", 12)
    y = 760
    lines = [
        f"Patient ID: {plan.patient_id}",
        f"Disease: {plan.disease_name}",
        f"Remedy: {plan.remedy_name}",
        f"Medicines: {plan.medicines}",
        f"Dosage: {plan.dosage}",
        f"Progress: {plan.progress_percent}%",
        f"Cured: {'Yes' if plan.cured else 'No'}",
        f"Next Checkup: {plan.next_checkup_date.strftime('%d %b %Y') if plan.next_checkup_date else 'N/A'}"
    ]

    for line in lines:
        c.drawString(80, y, line)
        y -= 20

    # ✅ Include analyzed image in the PDF (fixed path handling)
    if plan.after_image_path:
        image_path = plan.after_image_path

        # Remove leading slashes and convert to full path
        if image_path.startswith("/"):
            image_path = image_path.lstrip("/")

        # Convert relative path to actual full path
        full_path = os.path.join("app", image_path) if not os.path.exists(image_path) else image_path

        if os.path.exists(full_path):
            try:
                c.drawImage(full_path, 80, y - 300, width=300, height=250)
                y -= 280  # space below image
            except Exception as e:
                print(f"⚠️ Error adding image: {e}")
        else:
            print(f"⚠️ Image not found: {full_path}")

    c.save()
    return FileResponse(pdf_path, filename=f"TreatmentReport_{plan.id}.pdf")


# ---------------------- Auto-update Progress Utility ----------------------
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
