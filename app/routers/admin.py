import os
import zipfile
import uuid
import shutil
from io import BytesIO
from pathlib import Path
from fastapi import APIRouter, Form, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..database import SessionLocal
from ..db_models import Disease, Remedy, DiseaseImage

router = APIRouter()

env = Environment(
    loader=FileSystemLoader("app/templates"),
    autoescape=select_autoescape(["html", "xml"]),
)

UPLOAD_DIR = Path("app/static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_ZIP_SIZE_BYTES = 500 * 1024 * 1024
ALLOWED_IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}


def _require_admin(request: Request):
    if request.cookies.get("is_admin") != "true":
        return False
    return True


# ----------------------------------------------------
# ADMIN HOME
# ----------------------------------------------------
@router.get("/", response_class=HTMLResponse)
async def admin_home(request: Request) -> HTMLResponse:
    if not _require_admin(request):
        return RedirectResponse(url="/login", status_code=303)

    db = SessionLocal()
    try:
        diseases = db.query(Disease).order_by(Disease.id).all()
        for d in diseases:
            d.images = db.query(DiseaseImage).filter(DiseaseImage.disease_id == d.id).all()

        success = request.query_params.get("success")
        error = request.query_params.get("error")

        template = env.get_template("admin.html")
        return HTMLResponse(template.render(
            request=request,
            diseases=diseases,
            success_msg=success,
            error_msg=error
        ))

    finally:
        db.close()


# ----------------------------------------------------
# ADD DISEASE
# ----------------------------------------------------
@router.post("/disease", response_class=RedirectResponse)
async def add_disease(
    request: Request,
    name: str = Form(...),
    description: str = Form("")
):
    if not _require_admin(request):
        return RedirectResponse(url="/login", status_code=303)

    db = SessionLocal()
    try:
        if not db.query(Disease).filter(Disease.name == name).first():
            db.add(Disease(name=name, description=description))
            db.commit()

        return RedirectResponse("/admin?success=disease_added", status_code=303)

    finally:
        db.close()


# ----------------------------------------------------
# DELETE DISEASE
# ----------------------------------------------------
@router.post("/disease/{disease_id}/delete", response_class=RedirectResponse)
async def delete_disease(disease_id: int, request: Request):
    if not _require_admin(request):
        return RedirectResponse(url="/login", status_code=303)

    db = SessionLocal()
    try:
        disease = db.query(Disease).filter(Disease.id == disease_id).first()
        
        if not disease:
            return RedirectResponse("/admin?error=disease_not_found", status_code=303)
        
        # Delete all associated images from filesystem
        images = db.query(DiseaseImage).filter(DiseaseImage.disease_id == disease_id).all()
        for img in images:
            if img.image_path:
                filename = img.image_path.split('/')[-1]
                file_path = UPLOAD_DIR / filename
                if file_path.exists():
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        print(f"Error deleting file {file_path}: {e}")
            db.delete(img)
        
        # Delete all associated remedies
        remedies = db.query(Remedy).filter(Remedy.disease_id == disease_id).all()
        for remedy in remedies:
            db.delete(remedy)
        
        # Delete the disease itself
        db.delete(disease)
        db.commit()
        
        return RedirectResponse("/admin?success=disease_deleted", status_code=303)
    
    except Exception as e:
        print(f"Error deleting disease: {e}")
        db.rollback()
        return RedirectResponse("/admin?error=delete_failed", status_code=303)
    
    finally:
        db.close()


# ----------------------------------------------------
# DELETE SINGLE DISEASE IMAGE
# ----------------------------------------------------
@router.post("/disease-image/{image_id}/delete", response_class=RedirectResponse)
async def delete_disease_image(image_id: int, request: Request):
    if not _require_admin(request):
        return RedirectResponse(url="/login", status_code=303)

    db = SessionLocal()
    try:
        image = db.query(DiseaseImage).filter(DiseaseImage.id == image_id).first()
        
        if not image:
            return RedirectResponse("/admin?error=image_not_found", status_code=303)
        
        # Delete file from filesystem
        if image.image_path:
            filename = image.image_path.split('/')[-1]
            file_path = UPLOAD_DIR / filename
            if file_path.exists():
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error deleting file {file_path}: {e}")
        
        # Delete from database
        db.delete(image)
        db.commit()
        
        return RedirectResponse("/admin?success=image_deleted", status_code=303)
    
    except Exception as e:
        print(f"Error deleting image: {e}")
        db.rollback()
        return RedirectResponse("/admin?error=delete_failed", status_code=303)
    
    finally:
        db.close()


# ----------------------------------------------------
# UPLOAD IMAGES TO DISEASE
# ----------------------------------------------------
@router.post("/disease/{disease_id}/images", response_class=RedirectResponse)
async def upload_images(
    disease_id: int,
    request: Request,
    images: list[UploadFile] = File(...),
    descriptions: list[str] = Form([])
):
    if not _require_admin(request):
        return RedirectResponse(url="/login", status_code=303)

    db = SessionLocal()
    try:
        if not db.query(Disease).get(disease_id):
            return RedirectResponse("/admin?error=disease_not_found", status_code=303)

        uploaded = 0

        for i, image in enumerate(images):
            ext = os.path.splitext(image.filename)[1].lower()
            if ext not in ALLOWED_IMAGE_EXTS:
                continue

            unique = f"{uuid.uuid4()}{ext}"
            dst = UPLOAD_DIR / unique

            with open(dst, "wb") as f:
                f.write(await image.read())

            desc = descriptions[i] if i < len(descriptions) else ""

            db.add(DiseaseImage(
                disease_id=disease_id,
                image_path=f"/static/uploads/{unique}",
                image_name=image.filename,
                description=desc
            ))

            uploaded += 1

        db.commit()
        return RedirectResponse(f"/admin?success=uploaded_{uploaded}", status_code=303)

    finally:
        db.close()


# ----------------------------------------------------
# ZIP UPLOAD TO SPECIFIC DISEASE
# ----------------------------------------------------
@router.post("/disease/{disease_id}/zip-upload", response_class=RedirectResponse)
async def zip_upload_single(
    disease_id: int,
    request: Request,
    zip_file: UploadFile = File(...),
    description_prefix: str = Form("")
):
    if not _require_admin(request):
        return RedirectResponse(url="/login", status_code=303)

    db = SessionLocal()
    try:
        if not db.query(Disease).get(disease_id):
            return RedirectResponse("/admin?error=disease_not_found", status_code=303)

        if not zip_file.filename.lower().endswith(".zip"):
            return RedirectResponse("/admin?error=invalid_zip", status_code=303)

        zip_bytes = await zip_file.read()
        
        if len(zip_bytes) > MAX_ZIP_SIZE_BYTES:
            return RedirectResponse("/admin?error=zip_too_large", status_code=303)
        
        zip_stream = BytesIO(zip_bytes)
        saved = 0

        try:
            with zipfile.ZipFile(zip_stream) as zf:
                for name in zf.namelist():
                    if name.endswith('/'):
                        continue
                        
                    ext = os.path.splitext(name)[1].lower()
                    if ext not in ALLOWED_IMAGE_EXTS:
                        continue

                    unique = f"{uuid.uuid4()}{ext}"
                    dst = UPLOAD_DIR / unique

                    with zf.open(name) as src, open(dst, "wb") as out:
                        shutil.copyfileobj(src, out)

                    db.add(DiseaseImage(
                        disease_id=disease_id,
                        image_path=f"/static/uploads/{unique}",
                        image_name=os.path.basename(name),
                        description=description_prefix
                    ))
                    saved += 1

            db.commit()
            return RedirectResponse(f"/admin?success=uploaded_{saved}", status_code=303)
        
        except zipfile.BadZipFile:
            return RedirectResponse("/admin?error=bad_zip", status_code=303)

    finally:
        db.close()


# ----------------------------------------------------
# ZIP UPLOAD WITH PROGRESS (TOP CARD)
# ----------------------------------------------------
@router.post("/disease/zip-upload-top", response_class=RedirectResponse)
async def zip_upload_top(
    request: Request,
    disease_id: int = Form(...),
    zip_file: UploadFile = File(...),
    description_prefix: str = Form("")
):
    if not _require_admin(request):
        return RedirectResponse(url="/login", status_code=303)

    db = SessionLocal()
    try:
        disease = db.query(Disease).filter(Disease.id == disease_id).first()
        if not disease:
            return RedirectResponse("/admin?error=disease_not_found", status_code=303)

        if not zip_file.filename.lower().endswith(".zip"):
            return RedirectResponse("/admin?error=invalid_zip", status_code=303)

        zip_bytes = await zip_file.read()
        
        if len(zip_bytes) > MAX_ZIP_SIZE_BYTES:
            return RedirectResponse("/admin?error=zip_too_large", status_code=303)
        
        zip_stream = BytesIO(zip_bytes)
        saved = 0

        try:
            with zipfile.ZipFile(zip_stream) as zf:
                for name in zf.namelist():
                    if name.endswith('/'):
                        continue
                        
                    ext = os.path.splitext(name)[1].lower()
                    if ext not in ALLOWED_IMAGE_EXTS:
                        continue

                    unique = f"{uuid.uuid4()}{ext}"
                    dst = UPLOAD_DIR / unique

                    with zf.open(name) as src, open(dst, "wb") as out:
                        shutil.copyfileobj(src, out)

                    db.add(DiseaseImage(
                        disease_id=disease_id,
                        image_path=f"/static/uploads/{unique}",
                        image_name=os.path.basename(name),
                        description=description_prefix
                    ))
                    saved += 1

            db.commit()
            return RedirectResponse(f"/admin?success=uploaded_{saved}", status_code=303)
        
        except zipfile.BadZipFile:
            return RedirectResponse("/admin?error=bad_zip", status_code=303)

    finally:
        db.close()


# ----------------------------------------------------
# ADD REMEDY
# ----------------------------------------------------
@router.post("/remedy", response_class=RedirectResponse)
async def add_remedy(
    request: Request,
    disease_id: int = Form(...),
    name: str = Form(...),
    ingredients: str = Form(""),
    preparation: str = Form(""),
    steps: str = Form(""),
    duration_days: int = Form(14),
    allergy_warnings: str = Form("")
):
    if not _require_admin(request):
        return RedirectResponse(url="/login", status_code=303)

    db = SessionLocal()
    try:
        disease = db.query(Disease).filter(Disease.id == disease_id).first()
        
        if not disease:
            return RedirectResponse("/admin?error=disease_not_found", status_code=303)
        
        remedy = Remedy(
            disease_id=disease_id,
            name=name,
            ingredients=ingredients,
            preparation=preparation,
            steps=steps,
            duration_days=duration_days,
            allergy_warnings=allergy_warnings
        )
        
        db.add(remedy)
        db.commit()
        
        return RedirectResponse("/admin?success=remedy_added", status_code=303)
    
    finally:
        db.close()


# ----------------------------------------------------
# SEED 10 CANONICAL DISEASES
# ----------------------------------------------------
@router.post("/seed-10-diseases", response_class=RedirectResponse)
async def seed_10(request: Request):
    if not _require_admin(request):
        return RedirectResponse(url="/login", status_code=303)

    canonical = [
        "Eczema",
        "Melanoma",
        "Atopic Dermatitis",
        "Basal Cell Carcinoma",
        "Melanocytic Nevi",
        "Benign Keratosis-like Lesions",
        "Psoriasis & Lichen Planus and Related Disorders",
        "Seborrheic Keratoses and Other Benign Tumours",
        "Tinea, Ringworm, Candidiasis & Other Fungal Conditions",
        "Warts, Molluscum, and Other Viral Infections"
    ]

    db = SessionLocal()
    try:
        for name in canonical:
            if not db.query(Disease).filter(Disease.name == name).first():
                db.add(Disease(name=name, description=""))

        db.commit()
        return RedirectResponse("/admin?success=seeded_10", status_code=303)

    finally:
        db.close()


# ----------------------------------------------------
# SEED DEMO DATA
# ----------------------------------------------------
@router.post("/seed-demo", response_class=RedirectResponse)
async def seed_demo(request: Request):
    if not _require_admin(request):
        return RedirectResponse(url="/login", status_code=303)

    db = SessionLocal()
    try:
        # Add any demo data logic here
        db.commit()
        return RedirectResponse("/admin?success=demo_seeded", status_code=303)
    finally:
        db.close()
