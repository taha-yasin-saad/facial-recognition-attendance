import asyncio
import io
import os
import csv
from datetime import datetime
from typing import Optional

import cv2
import numpy as np
from fastapi import (
    FastAPI, HTTPException, Query, Form, File, UploadFile,
    Request, Response,
)
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from config import API_HOST, API_PORT, KNOWN_FACES_DIR, DASHBOARD_AUTO_REFRESH_SECONDS, KIOSK_FRAME_WIDTH
from core.encoder import build_encodings, add_user_encodings, remove_user_encodings
from core.detector import FaceDetector
from core.attendance import AttendanceManager
from database.db import (
    init_db,
    add_user, get_user, get_all_users,
    update_user, set_user_active, delete_user,
    get_active_user_ids, get_departments,
    get_attendance_log, get_present_now, get_stats_today,
    get_hourly_checkins, get_monthly_report, get_monthly_daily_counts,
    get_dept_monthly_hours, get_user_attendance_history,
    get_user_monthly_hours, get_user_total_hours_alltime,
    get_user_total_days_alltime,
    record_checkin, record_checkout, get_checkin_record_today,
    get_unknown_logs, get_unknown_log, mark_unknown_registered, next_guest_id,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="UniAttend API", version="2.0.0")

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "dashboard", "static")),
    name="static",
)

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "dashboard", "templates"))


def _hms(decimal_hours) -> str:
    """Format decimal hours as 'Xh Ym'."""
    if decimal_hours is None:
        return "—"
    total_m = int(round(float(decimal_hours) * 60))
    h = total_m // 60
    m = total_m % 60
    return f"{h}h {m:02d}m"


templates.env.filters["hms"] = _hms

# Singleton detector shared across kiosk requests
_kiosk_detector: Optional[FaceDetector] = None
_kiosk_attendance = AttendanceManager()


def _get_kiosk_detector() -> FaceDetector:
    global _kiosk_detector
    if _kiosk_detector is None:
        _kiosk_detector = FaceDetector()
    return _kiosk_detector


@app.on_event("startup")
def startup():
    init_db()
    os.makedirs(KNOWN_FACES_DIR, exist_ok=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _current_month() -> str:
    return datetime.now().strftime("%Y-%m")


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


# ══════════════════════════════════════════════════════════════════════════════
# REST API — /api/...
# ══════════════════════════════════════════════════════════════════════════════

# ── Users ──────────────────────────────────────────────────────────────────────

@app.get("/api/users")
def api_list_users(
    dept: Optional[str] = Query(None),
    active: Optional[bool] = Query(None),
):
    return get_all_users(department=dept, active_only=active)


@app.get("/api/users/{user_id}")
def api_get_user(user_id: str):
    user = get_user(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user


@app.post("/api/users/register", status_code=201)
async def api_register_user(
    user_id: str = Form(...),
    full_name: str = Form(...),
    department: str = Form(...),
    role: str = Form(""),
    email: str = Form(""),
    photos: list[UploadFile] = File(...),
):
    if get_user(user_id):
        raise HTTPException(409, "User ID already exists")

    save_dir = os.path.join(KNOWN_FACES_DIR, user_id)
    os.makedirs(save_dir, exist_ok=True)

    saved_paths = []
    for i, photo in enumerate(photos):
        content = await photo.read()
        path = os.path.join(save_dir, f"{i+1:02d}.jpg")
        with open(path, "wb") as f:
            f.write(content)
        saved_paths.append(path)

    photo_path = saved_paths[0] if saved_paths else None
    ok = add_user(user_id, full_name, department, role, email, photo_path)
    if not ok:
        raise HTTPException(500, "Failed to insert user record")

    encoded = add_user_encodings(user_id, saved_paths)
    return {
        "user_id": user_id,
        "full_name": full_name,
        "photos_saved": len(saved_paths),
        "faces_encoded": encoded,
    }


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None


@app.patch("/api/users/{user_id}")
def api_update_user(user_id: str, body: UserUpdate):
    if not get_user(user_id):
        raise HTTPException(404, "User not found")
    update_user(user_id, **body.model_dump(exclude_none=True))
    return get_user(user_id)


class StatusBody(BaseModel):
    is_active: bool


@app.patch("/api/users/{user_id}/status")
def api_set_status(user_id: str, body: StatusBody):
    if not get_user(user_id):
        raise HTTPException(404, "User not found")
    set_user_active(user_id, body.is_active)
    if not body.is_active:
        remove_user_encodings(user_id)
    else:
        face_dir = os.path.join(KNOWN_FACES_DIR, user_id)
        if os.path.isdir(face_dir):
            paths = [
                os.path.join(face_dir, f) for f in os.listdir(face_dir)
                if f.lower().endswith((".jpg", ".jpeg", ".png"))
            ]
            add_user_encodings(user_id, paths)
    return get_user(user_id)


@app.delete("/api/users/{user_id}", status_code=204)
def api_delete_user(user_id: str):
    if not get_user(user_id):
        raise HTTPException(404, "User not found")
    remove_user_encodings(user_id)
    delete_user(user_id)


# ── Attendance ─────────────────────────────────────────────────────────────────

@app.get("/api/attendance/today")
def api_today():
    return get_attendance_log(date=_today())


@app.get("/api/attendance/present")
def api_present():
    return get_present_now()


@app.get("/api/attendance/stats/today")
def api_stats_today():
    return get_stats_today()


@app.get("/api/attendance/stats/hourly")
def api_hourly(date: Optional[str] = Query(None)):
    return get_hourly_checkins(date=date)


@app.get("/api/attendance/report/monthly")
def api_monthly_report(month: str = Query(default=None)):
    return get_monthly_report(month or _current_month())


@app.get("/api/attendance/stats/monthly")
def api_monthly_daily(month: str = Query(default=None)):
    return get_monthly_daily_counts(month or _current_month())


@app.get("/api/attendance/{user_id}")
def api_user_history(user_id: str, limit: int = Query(60)):
    if not get_user(user_id):
        raise HTTPException(404, "User not found")
    return get_user_attendance_history(user_id, limit=limit)


@app.get("/api/attendance/export")
def api_export_csv(
    date_from: str = Query(alias="from", default=None),
    date_to: str = Query(alias="to", default=None),
):
    rows = get_attendance_log(date_from=date_from, date_to=date_to, limit=10000)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=[
        "id", "user_id", "full_name", "department", "role",
        "event_type", "timestamp", "worked_hours", "door_id", "method",
    ])
    writer.writeheader()
    writer.writerows(rows)
    buf.seek(0)
    filename = f"attendance_{date_from or 'all'}_{date_to or 'all'}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ── Encodings ─────────────────────────────────────────────────────────────────

@app.post("/api/encodings/rebuild")
def api_rebuild():
    active_ids = get_active_user_ids()
    known = build_encodings(active_ids=active_ids)
    return {"users_encoded": len(known)}


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


# ── Kiosk ─────────────────────────────────────────────────────────────────────

def _run_kiosk_recognition(image_bytes: bytes) -> dict:
    arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return {"error": "invalid_image", "faces": []}

    detector = _get_kiosk_detector()
    results = detector.process_frame(img, upsample_times=1)

    faces = []
    for r in results:
        loc = list(r.location)  # [top, right, bottom, left]
        if not r.is_known:
            faces.append({"is_known": False, "confidence": round(r.confidence, 3), "location": loc})
            continue

        in_cooldown = detector.in_cooldown(r.user_id)
        user = get_user(r.user_id)
        face: dict = {
            "is_known": True,
            "user_id": r.user_id,
            "full_name": user["full_name"] if user else r.user_id,
            "department": user["department"] if user else "",
            "role": user["role"] if user else "",
            "confidence": round(r.confidence, 3),
            "in_cooldown": in_cooldown,
            "location": loc,
        }

        if not in_cooldown:
            event = _kiosk_attendance.process_recognition(r.user_id)
            if event:
                detector.set_cooldown(r.user_id)
                face.update(event)
                face["recorded"] = True
            else:
                face["recorded"] = False

        faces.append(face)

    return {"faces": faces}


@app.post("/api/kiosk/recognize")
async def api_kiosk_recognize(frame: UploadFile = File(...)):
    data = await frame.read()
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _run_kiosk_recognition, data)
    return result


@app.post("/api/kiosk/reload")
def api_kiosk_reload():
    global _kiosk_detector
    _kiosk_detector = FaceDetector()
    return {"status": "reloaded", "users": len(_kiosk_detector._user_ids)}


# ══════════════════════════════════════════════════════════════════════════════
# Dashboard HTML Routes
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/", response_class=RedirectResponse)
def root():
    return RedirectResponse("/dashboard")


@app.get("/kiosk", response_class=HTMLResponse)
def kiosk_page(request: Request):
    return templates.TemplateResponse(request, "kiosk.html", {"capture_width": KIOSK_FRAME_WIDTH})


@app.get("/dashboard", response_class=HTMLResponse)
def dash_home(request: Request):
    stats = get_stats_today()
    present = get_present_now()
    hourly = get_hourly_checkins()
    now = datetime.now()
    return templates.TemplateResponse(request, "index.html", {
        "stats": stats,
        "present": present,
        "hourly": hourly,
        "refresh": DASHBOARD_AUTO_REFRESH_SECONDS,
        "now": now,
    })


@app.get("/dashboard/users", response_class=HTMLResponse)
def dash_users(
    request: Request,
    dept: Optional[str] = Query(None),
    active: Optional[str] = Query(None),
    page: int = Query(1),
    q: Optional[str] = Query(None),
):
    active_filter = None
    if active == "1":
        active_filter = True
    elif active == "0":
        active_filter = False

    users = get_all_users(department=dept, active_only=active_filter)
    if q:
        q_lower = q.lower()
        users = [
            u for u in users
            if q_lower in u["full_name"].lower()
            or q_lower in u["user_id"].lower()
            or q_lower in u["email"].lower()
        ]

    per_page = 20
    total = len(users)
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    paged = users[(page - 1) * per_page: page * per_page]
    departments = get_departments()

    return templates.TemplateResponse(request, "users.html", {
        "users": paged,
        "total": total,
        "page": page,
        "total_pages": total_pages,
        "departments": departments,
        "dept_filter": dept or "",
        "active_filter": active or "",
        "q": q or "",
    })


@app.get("/dashboard/users/add", response_class=HTMLResponse)
def dash_add_user(request: Request):
    departments = get_departments()
    return templates.TemplateResponse(request, "user_add.html", {
        "departments": departments,
    })


@app.get("/dashboard/users/{user_id}", response_class=HTMLResponse)
def dash_user_detail(request: Request, user_id: str):
    user = get_user(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    history = get_user_attendance_history(user_id, limit=60)
    monthly_hours = list(reversed(get_user_monthly_hours(user_id, months=6)))
    departments = get_departments()

    total_days = get_user_total_days_alltime(user_id)
    total_hours = get_user_total_hours_alltime(user_id)

    return templates.TemplateResponse(request, "user_detail.html", {
        "user": user,
        "history": history,
        "monthly_hours": monthly_hours,
        "departments": departments,
        "total_days": total_days,
        "total_hours": total_hours,
    })


@app.get("/dashboard/attendance", response_class=HTMLResponse)
def dash_attendance(
    request: Request,
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    dept: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    page: int = Query(1),
):
    per_page = 50
    offset = (page - 1) * per_page
    rows = get_attendance_log(
        date_from=date_from, date_to=date_to,
        department=dept, event_type=event_type,
        limit=per_page + 1, offset=offset,
    )
    has_next = len(rows) > per_page
    rows = rows[:per_page]
    departments = get_departments()

    return templates.TemplateResponse(request, "attendance.html", {
        "rows": rows,
        "page": page,
        "has_next": has_next,
        "departments": departments,
        "date_from": date_from or "",
        "date_to": date_to or "",
        "dept_filter": dept or "",
        "event_filter": event_type or "",
    })


@app.get("/dashboard/reports", response_class=HTMLResponse)
def dash_reports(
    request: Request,
    month: Optional[str] = Query(None),
):
    target_month = month or _current_month()
    report = get_monthly_report(target_month)
    daily = get_monthly_daily_counts(target_month)
    dept_hours = get_dept_monthly_hours(target_month)

    total_hours = round(sum(r["total_hours"] or 0 for r in report), 1)
    total_active = len(report)
    avg_days = round(sum(r["days_present"] or 0 for r in report) / max(total_active, 1), 1)

    top_user = max(report, key=lambda r: r["total_hours"] or 0) if report else None

    return templates.TemplateResponse(request, "reports.html", {
        "month": target_month,
        "report": report,
        "daily": daily,
        "dept_hours": dept_hours,
        "total_hours": total_hours,
        "avg_days": avg_days,
        "top_user": top_user,
    })


# ── Dashboard form actions ────────────────────────────────────────────────────

@app.post("/dashboard/users/{user_id}/edit")
async def dash_edit_user(
    user_id: str,
    full_name: str = Form(...),
    department: str = Form(...),
    role: str = Form(""),
    email: str = Form(""),
):
    if not get_user(user_id):
        raise HTTPException(404)
    update_user(user_id, full_name=full_name, department=department,
                role=role, email=email)
    return RedirectResponse(f"/dashboard/users/{user_id}?saved=1", status_code=303)


@app.post("/dashboard/users/{user_id}/deactivate")
def dash_deactivate(user_id: str):
    if not get_user(user_id):
        raise HTTPException(404)
    set_user_active(user_id, False)
    remove_user_encodings(user_id)
    return RedirectResponse(f"/dashboard/users/{user_id}?deactivated=1", status_code=303)


@app.post("/dashboard/users/{user_id}/activate")
def dash_activate(user_id: str):
    if not get_user(user_id):
        raise HTTPException(404)
    set_user_active(user_id, True)
    face_dir = os.path.join(KNOWN_FACES_DIR, user_id)
    if os.path.isdir(face_dir):
        paths = [
            os.path.join(face_dir, f) for f in os.listdir(face_dir)
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        ]
        add_user_encodings(user_id, paths)
    return RedirectResponse(f"/dashboard/users/{user_id}?activated=1", status_code=303)


@app.post("/dashboard/users/{user_id}/delete")
def dash_delete(user_id: str):
    if not get_user(user_id):
        raise HTTPException(404)
    remove_user_encodings(user_id)
    delete_user(user_id)
    return RedirectResponse("/dashboard/users?deleted=1", status_code=303)


# ── Guest / Unknown logs ──────────────────────────────────────────────────────

@app.get("/dashboard/guests", response_class=HTMLResponse)
def dash_guests(request: Request, page: int = Query(1), show_all: bool = Query(False)):
    per_page = 24
    offset = (page - 1) * per_page
    logs = get_unknown_logs(unregistered_only=not show_all, limit=per_page + 1, offset=offset)
    has_next = len(logs) > per_page
    logs = logs[:per_page]
    return templates.TemplateResponse(request, "guests.html", {
        "logs": logs,
        "page": page,
        "has_next": has_next,
        "show_all": show_all,
    })


@app.get("/dashboard/guests/image/{filename}")
def serve_guest_image(filename: str):
    path = os.path.join(BASE_DIR, "data", "unknown_logs", os.path.basename(filename))
    if not os.path.isfile(path):
        raise HTTPException(404, "Image not found")
    return FileResponse(path, media_type="image/jpeg")


@app.post("/dashboard/guests/{log_id}/register")
async def dash_register_guest(
    log_id: int,
    full_name: str = Form(...),
    notes: str = Form(""),
):
    log = get_unknown_log(log_id)
    if not log:
        raise HTTPException(404, "Unknown log not found")

    user_id = next_guest_id()
    snapshot = log.get("snapshot_path")

    ok = add_user(user_id, full_name, department="Guest",
                  role=notes or "Visitor", email="", photo_path=snapshot)
    if not ok:
        raise HTTPException(500, "Failed to create guest record")

    if snapshot and os.path.isfile(snapshot):
        add_user_encodings(user_id, [snapshot])
        global _kiosk_detector
        _kiosk_detector = None

    mark_unknown_registered(log_id, user_id)
    return RedirectResponse(f"/dashboard/users/{user_id}?registered=1", status_code=303)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host=API_HOST, port=API_PORT, reload=True)
