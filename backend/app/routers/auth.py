from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, schemas
from ..db import get_db
from ..utils import security

router = APIRouter(prefix="/auth", tags=["auth"])


def get_admin(db: Session, username: str):
    return db.query(models.Admin).filter(models.Admin.username == username).first()


@router.post("/login", response_model=schemas.Token)
def login(form: schemas.AdminLogin, db: Session = Depends(get_db)):
    admin = get_admin(db, form.username)
    if not admin or not security.verify_password(form.password, admin.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = security.create_access_token(data={"sub": admin.username})
    return {"access_token": access_token, "token_type": "bearer"}
