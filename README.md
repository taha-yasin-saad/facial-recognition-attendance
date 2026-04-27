# UniAttend — Face Recognition Attendance System

University employee door access control with a full Admin Dashboard.

## Stack

Python 3.10+ · OpenCV · face_recognition (dlib) · SQLite · FastAPI · Jinja2 · TailwindCSS · Chart.js

---

## Installation

```bash
# 1. Create virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS

# 2. Install dlib (needs C++ build tools on Windows; easiest via cmake)
pip install cmake dlib

# 3. Install all dependencies
pip install -r requirements.txt
```

> **Windows tip:** If `dlib` fails to build, download a prebuilt wheel from
> https://github.com/z-mahmud22/Dlib_Windows_Python3.x and install it with `pip install <wheel>.whl`.

---

## Register an Employee

### Via CLI (terminal)

```bash
python scripts/register_employee.py \
    --id EMP001 \
    --name "Ahmed Al Mansouri" \
    --dept "IT" \
    --role "Engineer" \
    --email "ahmed@university.ae"
```

Captures 5 webcam photos and encodes them automatically.

### Via Dashboard

Open `http://localhost:8000/dashboard/employees/add`, fill in the form, and use the live webcam capture.

---

## Running the System

Run **both processes in separate terminals**:

**Terminal 1 — Web server + Dashboard:**
```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Live recognition loop:**
```bash
python main.py
```

| Key | Action |
|-----|--------|
| `Q` | Quit |
| `R` | Reload face encodings (after registering new employees) |

---

## Dashboard

| URL | Page |
|-----|------|
| `http://localhost:8000/dashboard` | Home overview |
| `http://localhost:8000/dashboard/employees` | Employee management |
| `http://localhost:8000/dashboard/employees/add` | Add new employee |
| `http://localhost:8000/dashboard/attendance` | Attendance log |
| `http://localhost:8000/dashboard/reports` | HR reports |
| `http://localhost:8000/docs` | API docs (Swagger) |

---

## REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/employees` | List employees (`?dept=&active=`) |
| GET | `/api/employees/{id}` | Single employee |
| POST | `/api/employees/register` | Register (multipart) |
| PATCH | `/api/employees/{id}` | Update details |
| PATCH | `/api/employees/{id}/status` | Activate / deactivate |
| DELETE | `/api/employees/{id}` | Hard delete |
| GET | `/api/attendance/today` | Today's log |
| GET | `/api/attendance/present` | Who is inside now |
| GET | `/api/attendance/stats/today` | Today's counts |
| GET | `/api/attendance/stats/hourly` | Check-ins per hour |
| GET | `/api/attendance/report/monthly?month=2026-04` | Monthly worked hours |
| GET | `/api/attendance/stats/monthly?month=2026-04` | Daily count for line chart |
| GET | `/api/attendance/export?from=2026-04-01&to=2026-04-30` | CSV export |
| POST | `/api/encodings/rebuild` | Rebuild face encodings cache |
| GET | `/health` | Health check |

### CSV Export Example

```bash
curl "http://localhost:8000/api/attendance/export?from=2026-04-01&to=2026-04-30" \
     -o april_attendance.csv
```

---

## Configuration (`config.py`)

| Variable | Default | Description |
|----------|---------|-------------|
| `CAMERA_INDEX` | `0` | Webcam index or RTSP URL |
| `FACE_TOLERANCE` | `0.50` | Match threshold (lower = stricter) |
| `RECOGNITION_COOLDOWN` | `300` | Seconds between events for same employee |
| `MIN_HOURS_BEFORE_CHECKOUT` | `1` | Min hours inside before checkout |
| `DOOR_ID` | `"MAIN_ENTRANCE"` | Door identifier for logging |

---

## Kiosk Upgrade (Phase 2)

Change `CAMERA_INDEX` in `config.py` to the RTSP stream URL of the entrance camera:

```python
CAMERA_INDEX = "rtsp://admin:password@192.168.1.100:554/stream"
```

---

## Project Structure

```
├── main.py                    # Live recognition loop (run separately)
├── api.py                     # FastAPI: REST API + Dashboard routes
├── config.py                  # All configuration
├── core/
│   ├── detector.py            # Face detection + recognition
│   ├── encoder.py             # Face encoding cache management
│   └── attendance.py          # Check-in / check-out logic
├── database/
│   ├── db.py                  # SQLite queries
│   └── models.py              # DDL schemas
├── dashboard/
│   ├── templates/             # Jinja2 HTML templates
│   └── static/                # CSS + JS
├── data/
│   ├── known_faces/           # {employee_id}/*.jpg
│   ├── encodings.pkl          # Cached face encodings
│   └── unknown_logs/          # Snapshots of unrecognized faces
└── scripts/
    └── register_employee.py   # CLI registration tool
```
