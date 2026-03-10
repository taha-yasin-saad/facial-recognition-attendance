from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .db import engine, Base, get_db
from .routers import auth, employees, kiosk, attendance
from .models import Admin
from .utils.security import get_password_hash
from sqlalchemy.orm import Session
import os

app = FastAPI()

# CORS
origins = [os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(employees.router)
app.include_router(kiosk.router)
app.include_router(attendance.router)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    # seed admin from env
    db: Session = next(get_db())
    username = os.getenv("ADMIN_USER", "admin")
    password = os.getenv("ADMIN_PASSWORD", "admin")
    if not db.query(Admin).filter(Admin.username == username).first():
        admin = Admin(username=username, hashed_password=get_password_hash(password))
        db.add(admin)
        db.commit()


# dependency to verify JWT for admin endpoints can be added later

