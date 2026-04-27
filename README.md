# UniAttend — Face Recognition Attendance System

A university employee door access and attendance system powered by real-time face recognition, with a full admin dashboard and REST API.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python) ![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-green?logo=fastapi) ![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey?logo=sqlite) ![License](https://img.shields.io/badge/License-MIT-yellow)

---

## Features

- **Real-time face recognition** via webcam or RTSP camera stream
- **Automatic check-in / check-out** with cooldown enforcement
- **Guest registration** directly from unknown-face alerts
- **Admin dashboard** — live overview, employee management, attendance log, HR reports
- **REST API** with Swagger docs
- **CSV export** for payroll/HR integrations
- **Kiosk mode** — browser-based webcam capture endpoint for door terminals

---

## Stack

| Layer | Technology |
|-------|-----------|
| Face recognition | `face_recognition` (dlib) + OpenCV |
| Backend | FastAPI + Uvicorn |
| Templates | Jinja2 + TailwindCSS |
| Charts | Chart.js |
| Database | SQLite (via `sqlite3`) |
| Data | Pandas (CSV export) |

---

## Installation

```bash
# 1. Clone the repo
git clone git@github.com:taha-yasin-saad/facial-recognition-attendance.git
cd facial-recognition-attendance

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux / macOS

# 3. Install dlib (requires C++ build tools on Windows)
pip install cmake dlib

# 4. Install all dependencies
pip install -r requirements.txt
```

> **Windows tip:** If `dlib` fails to build, download a prebuilt wheel from
> [z-mahmud22/Dlib_Windows_Python3.x](https://github.com/z-mahmud22/Dlib_Windows_Python3.x)
> and install it with `pip install <wheel>.whl`.

---

## Running the System

Run **both processes in separate terminals**:

**Terminal 1 — API server + Dashboard:**
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
| `R` | Reload face encodings (after adding new employees) |

---

## Register an Employee

### Via Dashboard

Navigate to `http://localhost:8000/dashboard/employees/add`, fill in the form, and capture photos using the live webcam.

### Via CLI

```bash
python scripts/register_employee.py \
    --id EMP001 \
    --name "Ahmed Al Mansouri" \
    --dept "IT" \
    --role "Engineer" \
    --email "ahmed@university.ae"
```

Captures 5 webcam photos and rebuilds the face encodings cache automatically.

---

## Dashboard

| URL | Page |
|-----|------|
| `/dashboard` | Live overview & today's stats |
| `/dashboard/employees` | Employee list & management |
| `/dashboard/employees/add` | Register new employee |
| `/dashboard/attendance` | Full attendance log with filters |
| `/dashboard/reports` | Monthly HR reports & charts |
| `/docs` | Swagger API docs |

---

## REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/employees` | List employees (`?dept=&active=`) |
| `GET` | `/api/employees/{id}` | Single employee detail |
| `POST` | `/api/employees/register` | Register employee (multipart) |
| `PATCH` | `/api/employees/{id}` | Update employee fields |
| `PATCH` | `/api/employees/{id}/status` | Activate / deactivate |
| `DELETE` | `/api/employees/{id}` | Delete employee |
| `GET` | `/api/attendance/today` | Today's attendance log |
| `GET` | `/api/attendance/present` | Who is currently inside |
| `GET` | `/api/attendance/stats/today` | Today's summary counts |
| `GET` | `/api/attendance/stats/hourly` | Check-ins per hour |
| `GET` | `/api/attendance/report/monthly?month=YYYY-MM` | Monthly worked hours per employee |
| `GET` | `/api/attendance/export?from=YYYY-MM-DD&to=YYYY-MM-DD` | CSV export |
| `POST` | `/api/encodings/rebuild` | Rebuild face encodings cache |
| `GET` | `/health` | Health check |

**CSV export example:**
```bash
curl "http://localhost:8000/api/attendance/export?from=2026-04-01&to=2026-04-30" \
     -o april_attendance.csv
```

---

## Configuration

All settings live in `config.py`:

| Variable | Default | Description |
|----------|---------|-------------|
| `CAMERA_INDEX` | `0` | Webcam index or RTSP URL string |
| `FACE_TOLERANCE` | `0.50` | Match threshold — lower is stricter |
| `RECOGNITION_COOLDOWN` | `300` | Seconds between events for the same person |
| `MIN_HOURS_BEFORE_CHECKOUT` | `0` | Min hours inside before checkout is allowed |
| `DOOR_ID` | `"MAIN_ENTRANCE"` | Door label recorded in attendance logs |
| `REGISTRATION_PHOTOS` | `5` | Photos captured per employee during registration |

### RTSP / Kiosk upgrade

To use an IP camera instead of a USB webcam, set `CAMERA_INDEX` in `config.py`:

```python
CAMERA_INDEX = "rtsp://admin:password@192.168.1.100:554/stream"
```

---

## Project Structure

```
├── main.py                    # Live recognition loop
├── api.py                     # FastAPI routes (REST API + Dashboard)
├── config.py                  # Global configuration
├── core/
│   ├── detector.py            # Face detection & recognition
│   ├── encoder.py             # Encoding cache management
│   └── attendance.py          # Check-in / check-out logic
├── database/
│   ├── db.py                  # All SQLite queries
│   └── models.py              # DDL table schemas
├── dashboard/
│   ├── templates/             # Jinja2 HTML templates
│   └── static/                # CSS & JS assets
├── data/                      # Runtime data (git-ignored)
│   ├── known_faces/           # {employee_id}/*.jpg
│   ├── encodings.pkl          # Cached face encodings
│   ├── attendance.db          # SQLite database
│   └── unknown_logs/          # Snapshots of unrecognized faces
└── scripts/
    └── register_employee.py   # CLI registration tool
```

---

## License

MIT
