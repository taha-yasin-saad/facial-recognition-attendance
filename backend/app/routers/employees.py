from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from .. import schemas, models
from ..db import get_db
from ..services import face_service
from ..utils import deps

router = APIRouter(prefix="/employees", tags=["employees"])


def get_employee(db: Session, emp_id: int):
    return db.query(models.Employee).filter(models.Employee.id == emp_id).first()


@router.post("", response_model=schemas.EmployeeOut)
def create_employee(emp: schemas.EmployeeCreate, db: Session = Depends(get_db), admin: str = Depends(deps.admin_required)):
    db_emp = models.Employee(
        employee_code=emp.employee_code,
        full_name=emp.full_name,
        department=emp.department,
    )
    db.add(db_emp)
    db.commit()
    db.refresh(db_emp)
    return db_emp


@router.get("", response_model=List[schemas.EmployeeOut])
def list_employees(db: Session = Depends(get_db), admin: str = Depends(deps.admin_required)):
    return db.query(models.Employee).all()


@router.post("/{id}/enroll")
async def enroll_images(id: int, files: List[UploadFile] = File(...), db: Session = Depends(get_db), admin: str = Depends(deps.admin_required)):
    emp = get_employee(db, id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    if not 3 <= len(files) <= 10:
        raise HTTPException(status_code=400, detail="Must upload between 3 and 10 images")
    for f in files:
        content = await f.read()
        try:
            emb = face_service.image_to_embedding(content)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
        db_emb = models.Embedding(employee_id=emp.id, vector=emb)
        db.add(db_emb)
    db.commit()
    return {"ok": True}
