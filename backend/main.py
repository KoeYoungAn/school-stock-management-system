import os
from datetime import datetime
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database import Base, engine, get_db
import models  # noqa: ensure tables registered
from auth import router as auth_router
from crud import ALL_ROUTERS
from seed import seed

os.makedirs("uploads", exist_ok=True)
Base.metadata.create_all(bind=engine)
seed()

app = FastAPI(title="School Stock Management System")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Handle Pydantic validation errors"""
    errors = []
    for error in exc.errors():
        field = '.'.join(str(loc) for loc in error['loc'] if loc != 'body')
        errors.append({
            'field': field,
            'message': error['msg']
        })
    return JSONResponse(
        status_code=422,
        content={
            'detail': 'Validation failed',
            'errors': errors
        }
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", "http://127.0.0.1:5173",
        "http://localhost:5174", "http://127.0.0.1:5174",
        "http://localhost:3000", "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(auth_router)
for r in ALL_ROUTERS:
    app.include_router(r)


@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    db_ok = True
    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
    except Exception:
        db_ok = False
    return {
        "status": "ok",
        "database": "connected" if db_ok else "error",
        "app": "School Stock Management System",
        "timestamp": datetime.utcnow().isoformat(),
    }
