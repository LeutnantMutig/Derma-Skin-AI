from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from passlib.hash import argon2 as bcrypt


from app.database import SessionLocal
from app.db_models import User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# -----------------------------
# HELPER
# -----------------------------
def _get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------------
# LOGIN PAGE
# -----------------------------
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    username = request.cookies.get("username")
    if username:
        # Already logged in – redirect based on role
        is_admin = request.cookies.get("is_admin") == "true"
        target = "/admin" if is_admin else "/patients/new"
        return RedirectResponse(url=target, status_code=303)

    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user or not bcrypt.verify(password, user.password_hash):
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "error": "Invalid username or password"
                },
                status_code=400
            )

        # Success – set cookies
        response = RedirectResponse(
            url="/admin" if user.is_admin else "/patients/new",
            status_code=303
        )
        response.set_cookie(
            key="username",
            value=user.username,
            httponly=True,
            samesite="lax",
        )
        response.set_cookie(
            key="is_admin",
            value="true" if user.is_admin else "false",
            httponly=True,
            samesite="lax",
        )
        return response
    finally:
        db.close()


# -----------------------------
# LOGOUT
# -----------------------------
@router.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("username")
    response.delete_cookie("is_admin")
    return response


# -----------------------------
# REGISTER USER (ACCOUNT)
# -----------------------------
@router.get("/auth/register", response_class=HTMLResponse)
async def register_user_page(request: Request):
    return templates.TemplateResponse("register_user.html", {"request": request})


@router.post("/auth/register")
async def register_user(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
):
    db = SessionLocal()
    try:
        # Check duplicates
        existing = (
            db.query(User)
            .filter((User.username == username) | (User.email == email))
            .first()
        )
        if existing:
            return templates.TemplateResponse(
                "register_user.html",
                {
                    "request": request,
                    "error": "Username or email already exists"
                },
                status_code=400
            )

        # First user = admin (nice for demo)
        is_first = db.query(User).count() == 0

        user = User(
            username=username,
            email=email,
            password_hash=bcrypt.hash(password),
            is_admin=is_first,   # first account becomes admin
        )
        db.add(user)
        db.commit()

        return RedirectResponse(url="/login", status_code=303)
    finally:
        db.close()
