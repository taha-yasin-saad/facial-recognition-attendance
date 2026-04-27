# UniAttend — Face Recognition Attendance System

A university user door access and attendance system powered by real-time face recognition, with a full admin dashboard and REST API.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python) ![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-green?logo=fastapi) ![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey?logo=sqlite) ![License](https://img.shields.io/badge/License-MIT-yellow)

---

## Features

- **Real-time face recognition** via browser-based kiosk (no extra process needed)
- **Automatic check-in / check-out** with cooldown enforcement
- **Guest registration** directly from unknown-face alerts
- **Admin dashboard** — live overview, user management, attendance log, HR reports
- **REST API** with Swagger docs
- **CSV export** for payroll/HR integrations
- **Kiosk mode** — browser-based webcam capture for door terminals, built into the dashboard

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

A single command starts everything — the API, dashboard, and kiosk:

```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

Then open `http://localhost:8000/kiosk` on the door terminal to start face recognition.

---

## Register a User

### Via Dashboard

Navigate to `http://localhost:8000/dashboard/users/add`, fill in the form, and capture photos using the live webcam.

### Via CLI

```bash
python scripts/register_employee.py \
    --id USR001 \
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
| `/dashboard/users` | User list & management |
| `/dashboard/users/add` | Register new user |
| `/dashboard/attendance` | Full attendance log with filters |
| `/dashboard/reports` | Monthly HR reports & charts |
| `/kiosk` | Face recognition kiosk (door terminal) |
| `/docs` | Swagger API docs |

---

## REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/users` | List users (`?dept=&active=`) |
| `GET` | `/api/users/{id}` | Single user detail |
| `POST` | `/api/users/register` | Register user (multipart) |
| `PATCH` | `/api/users/{id}` | Update user fields |
| `PATCH` | `/api/users/{id}/status` | Activate / deactivate |
| `DELETE` | `/api/users/{id}` | Delete user |
| `GET` | `/api/attendance/today` | Today's attendance log |
| `GET` | `/api/attendance/present` | Who is currently inside |
| `GET` | `/api/attendance/stats/today` | Today's summary counts |
| `GET` | `/api/attendance/stats/hourly` | Check-ins per hour |
| `GET` | `/api/attendance/report/monthly?month=YYYY-MM` | Monthly worked hours per user |
| `GET` | `/api/attendance/export?from=YYYY-MM-DD&to=YYYY-MM-DD` | CSV export |
| `POST` | `/api/encodings/rebuild` | Rebuild face encodings cache |
| `POST` | `/api/kiosk/recognize` | Submit a frame for recognition |
| `POST` | `/api/kiosk/reload` | Reload face encodings in the kiosk |
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
| `KIOSK_FRAME_WIDTH` | `640` | Capture width sent from browser to server |
| `FACE_TOLERANCE` | `0.50` | Match threshold — lower is stricter |
| `RECOGNITION_COOLDOWN` | `300` | Seconds between events for the same person |
| `MIN_HOURS_BEFORE_CHECKOUT` | `0` | Min hours inside before checkout is allowed |
| `DOOR_ID` | `"MAIN_ENTRANCE"` | Door label recorded in attendance logs |
| `REGISTRATION_PHOTOS` | `5` | Photos captured per user during registration |

---

## Project Structure

```
├── api.py                     # FastAPI routes (REST API + Dashboard + Kiosk)
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
│   ├── known_faces/           # {user_id}/*.jpg
│   ├── encodings.pkl          # Cached face encodings
│   ├── attendance.db          # SQLite database
│   └── unknown_logs/          # Snapshots of unrecognized faces
└── scripts/
    └── register_employee.py   # CLI registration tool
```

---

## License

MIT
