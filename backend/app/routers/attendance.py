from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from typing import Optional
import csv
import io
from .. import models, schemas
from ..db import get_db
from ..utils import deps

router = APIRouter(prefix="/attendance", tags=["attendance"])


@router.get("", response_model=list[schemas.AttendanceOut])
def list_attendance(
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    employee_code: Optional[str] = Query(None),
    device_id: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    admin: str = Depends(deps.admin_required),
):
    q = db.query(models.Attendance)
    if start:
        q = q.filter(models.Attendance.timestamp >= start)
    if end:
        q = q.filter(models.Attendance.timestamp <= end)
    if employee_code:
        q = q.join(models.Employee).filter(models.Employee.employee_code == employee_code)
    if device_id:
        q = q.filter(models.Attendance.device_id == device_id)
    if type:
        q = q.filter(models.Attendance.type == type)
    return q.all()


@router.get("/export.csv")
def export_csv(
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    admin: str = Depends(deps.admin_required),
):
    records = db.query(models.Attendance).all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "employee_id", "timestamp", "type", "confidence", "device_id", "face_distance"])
    for r in records:
        writer.writerow([r.id, r.employee_id, r.timestamp.isoformat(), r.type, r.confidence, r.device_id, r.face_distance])
    return Response(content=buf.getvalue(), media_type="text/csv")
