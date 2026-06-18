import os
import uuid
import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from app.database import SessionLocal
from app.db_models import Patient, Checkup
from app.services.predict import predict_condition

router = APIRouter(prefix="", tags=["checkups"])
templates = Jinja2Templates(directory="app/templates")

UPLOAD_DIR = Path("app/static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ----------------------------------------------------------
# NEW CHECKUP PAGE
# ----------------------------------------------------------
@router.get("/new/{patient_id}", response_class=HTMLResponse)
async def new_checkup_page(request: Request, patient_id: int):
    # Require login
    if not request.cookies.get("username"):
        return RedirectResponse(url="/login", status_code=303)

    db = SessionLocal()
    try:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
    finally:
        db.close()

    if not patient:
        return templates.TemplateResponse(
            "new_checkup.html",
            {"request": request, "error": "patient_not_found", "patient": None},
        )

    return templates.TemplateResponse(
        "new_checkup.html",
        {"request": request, "patient": patient},
    )


# ----------------------------------------------------------
# CREATE CHECKUP (WITH PREDICTION)
# ----------------------------------------------------------
@router.post("/new/{patient_id}")
async def create_checkup(
    request: Request,
    patient_id: int,
    symptoms: str = Form(""),
    allergies: str = Form(""),
    notes: str = Form(""),
    image: UploadFile = File(None),
):
    # Require login
    if not request.cookies.get("username"):
        return RedirectResponse(url="/login", status_code=303)

    db = SessionLocal()
    try:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            return RedirectResponse("/?error=patient_not_found", status_code=302)

        img_public_path = None
        label: Optional[str] = None
        confidence: float = 0.0

        # SAVE UPLOADED IMAGE
        if image:
            ext = os.path.splitext(image.filename)[1].lower() or ".jpg"
            unique_name = f"{uuid.uuid4().hex}{ext}"
            save_path = UPLOAD_DIR / unique_name

            with open(save_path, "wb") as out:
                shutil.copyfileobj(image.file, out)

            image.file.close()
            img_public_path = f"/static/uploads/{unique_name}"

            # PREDICTION
            condition, conf, err = predict_condition(str(save_path))

            if err:
                print("Prediction failed:", err)
                label = None
                confidence = 0.0
            else:
                label = condition
                confidence = conf or 0.0

        # SAVE CHECKUP RECORD
        checkup = Checkup(
            patient_id=patient_id,
            image_path=img_public_path,
            symptoms=symptoms,
            predicted_condition=label,
            confidence=confidence,
            notes=notes,
            allergies=allergies,
        )

        db.add(checkup)
        db.commit()

    except Exception as e:
        db.rollback()
        print("Create checkup error:", e)
        return RedirectResponse(
            f"/checkups/new/{patient_id}?error=server_error", status_code=303
        )
    finally:
        db.close()

    return RedirectResponse(
        f"/patients/{patient_id}?success=checkup_added", status_code=303
    )
