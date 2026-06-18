import os
import sys



# Ensure upload folders exist
os.makedirs("app/static/uploads/treatments", exist_ok=True)
os.makedirs("app/static/reports", exist_ok=True)


# ensure parent folder is on path when running `python app/main.py`
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# routers package must expose pages, patients, checkups, admin, auth
from app.routers import pages, patients, checkups, admin, auth, treatments, treatment_dashboard 
from app.database import init_db

app = FastAPI(title="DermaSkin Cure")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# mount static (css/js/images and uploaded images)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# include routers
app.include_router(auth.router, tags=["auth"])
app.include_router(pages.router)
app.include_router(patients.router, prefix="/patients", tags=["patients"])
app.include_router(checkups.router, prefix="/checkups", tags=["checkups"])
app.include_router(treatments.router)
app.include_router(treatment_dashboard.router)
app.include_router(admin.router, prefix="/admin", tags=["admin"])


@app.on_event("startup")
async def _startup() -> None:
    # your DB init function (should be quick)
    init_db()


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    # reload=True uses a lot more resources; set reload=False on low-RAM machines
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
