from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.database import SessionLocal
from app.db_models import Patient
from sqlalchemy.orm import joinedload

router = APIRouter()

env = Environment(
    loader=FileSystemLoader("app/templates"),
    autoescape=select_autoescape(["html"])
)


# ---------------------------------------------
# SHOW PATIENT REGISTRATION FORM
# ---------------------------------------------
@router.get("/new", response_class=HTMLResponse)
async def new_patient(request: Request):
    # Require login (any user)
    if not request.cookies.get("username"):
        return RedirectResponse(url="/login", status_code=303)

    template = env.get_template("register.html")
    return HTMLResponse(template.render(request=request))


# ---------------------------------------------
# SAVE PATIENT RECORD
# ---------------------------------------------
@router.post("/", response_class=HTMLResponse)
async def save_patient(
    request: Request,
    name: str = Form(...),
    age: int = Form(None),
    gender: str = Form(None),
    email: str = Form(None),
    contact: str = Form(None),

    allergies: str = Form(""),
    medical_history: str = Form(""),
    current_treatments: str = Form(""),
    family_history: str = Form(""),

    emergency_name: str = Form(""),
    emergency_contact: str = Form(""),
    emergency_relation: str = Form(""),

    symptoms: list[str] = Form(None)
):
    # Require login
    if not request.cookies.get("username"):
        return RedirectResponse(url="/login", status_code=303)

    symptoms_str = ", ".join(symptoms) if symptoms else ""

    db = SessionLocal()
    try:
        patient = Patient(
            name=name,
            age=age,
            gender=gender,
            email=email,
            contact=contact,
            allergies=allergies,
            medical_history=medical_history,
            current_treatments=current_treatments,
            family_history=family_history,
            emergency_name=emergency_name,
            emergency_contact=emergency_contact,
            emergency_relation=emergency_relation,
            symptoms=symptoms_str
        )
        db.add(patient)
        db.commit()
    finally:
        db.close()

    template = env.get_template("patient_success.html")
    return HTMLResponse(
        template.render(
            request=request,
            patient_name=name
        )
    )


@router.get("/{patient_id}", response_class=HTMLResponse)
async def patient_detail(patient_id: int, request: Request, success: str = None):
    # Require login
    if not request.cookies.get("username"):
        return RedirectResponse(url="/login", status_code=303)

    db = SessionLocal()
    try:
        patient = (
            db.query(Patient)
            .options(joinedload(Patient.checkups))
            .filter(Patient.id == patient_id)
            .first()
        )
    finally:
        db.close()

    if not patient:
        return HTMLResponse("<h2>Patient Not Found</h2>", status_code=404)

    template = env.get_template("patient_detail.html")
    return HTMLResponse(
        template.render(
            request=request,
            patient=patient,
            success=success
        )
    )
