# UniAttend — Face Recognition Attendance System

A door-access and attendance system for a university/workplace, powered by real-time face recognition in the browser, backed by a FastAPI REST API, an admin dashboard, and a SQLite time-tracking engine.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python) ![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-green?logo=fastapi) ![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey?logo=sqlite) ![License](https://img.shields.io/badge/License-MIT-yellow)

---

## Problem

Manual attendance (badge taps, sign-in sheets, spreadsheets) is slow, easy to game with buddy-punching, and produces messy data for HR. UniAttend replaces the sign-in step with a face at the door:

- A browser-based **kiosk** runs on any device with a webcam — no dedicated capture process or native client to install on the terminal.
- Recognizing a registered face automatically records the correct event — **check-in** on arrival, **check-out** on exit — and computes worked hours per session, so an employee who steps out for a break and returns is tracked correctly across multiple sessions in a day.
- A **cooldown** window prevents the same person being logged repeatedly while lingering in front of the camera.
- **Unknown faces** are captured and surfaced in the dashboard, where an admin can register them as guests in one click.
- HR gets a live dashboard, filterable attendance logs, monthly reports, and **CSV export** for payroll — no manual data entry.

---

## Tech Stack

Only libraries actually declared in `requirements.txt` and/or imported in the source are listed.

| Layer | Technology | Where |
|-------|-----------|-------|
| Face recognition | `face_recognition` (dlib) | `core/encoder.py`, `core/detector.py` |
| Image / array ops | `opencv-python` (`cv2`), `numpy` | `core/*`, `api.py`, `scripts/*` |
| Web framework | `fastapi` + `uvicorn[standard]` | `api.py` |
| Multipart uploads | `python-multipart` | photo/frame upload endpoints |
| Templating | `jinja2` | `dashboard/templates/*` |
| Data validation | `pydantic` (v2) | request models in `api.py` |
| Database | `sqlite3` (Python stdlib) + WAL mode | `database/db.py`, `database/models.py` |
| CSV export | `csv` (Python stdlib) | `/api/attendance/export` in `api.py` |
| Frontend styling | TailwindCSS (CDN) | `dashboard/templates/base.html` |
| Charts | Chart.js 4.4.0 (CDN) | `dashboard/templates/reports.html` |
| Webcam capture | Browser `getUserMedia` API | `dashboard/static/js/webcam.js` |

Also declared in `requirements.txt`: `aiofiles`, `Pillow` (transitive/runtime support for FastAPI file serving and `face_recognition` image loading). `pandas` is listed as a dependency but is **not** imported anywhere in the current code — CSV export is done with the stdlib `csv` module.

---

## Results / Behavior

This is an application, not a benchmark project — there are no published accuracy figures, and none are claimed here. The following are the actual, code-verified behaviors and configuration defaults.

**Recognition pipeline** (`core/detector.py`)
- Face **detection** uses dlib's HOG model (`face_recognition.face_locations(..., model="hog")`).
- Incoming frames are downscaled by `FRAME_RESIZE_SCALE = 0.5` before detection for speed, then coordinates are rescaled back to full resolution.
- A face is matched by nearest **Euclidean distance** across all stored encodings; it is accepted only if the best distance is `<= FACE_TOLERANCE (0.50)`. Reported confidence is `1 - distance`.
- Kiosk recognition runs off the event loop via `run_in_executor`, so frame processing does not block the API.

**Attendance logic** (`core/attendance.py`, `database/db.py`)
- Per-person **cooldown** of `RECOGNITION_COOLDOWN = 300s` (5 min) prevents duplicate events, enforced both in-memory (kiosk) and via a DB timestamp check.
- Event direction is decided automatically: no event today → `check_in`; last event `check_out` → `check_in`; last event `check_in` → `check_out`.
- **Worked hours** are computed per session at check-out as `(checkout - checkin)` in hours (2-decimal precision) and summed across sessions for daily and all-time totals. Multiple check-in/check-out cycles per day (e.g. lunch breaks) are handled by matching the current open session.
- `MIN_HOURS_BEFORE_CHECKOUT = 0` by default (checkout allowed any time); `DOOR_ID = "MAIN_ENTRANCE"` is stamped on every record.

**Registration**
- Captures `REGISTRATION_PHOTOS = 5` photos per person (CLI or dashboard webcam) and rebuilds/extends the encodings cache automatically.

**Included test** (`test_user_story.py`)
- A scripted end-to-end scenario over a simulated workday (08:00 in → 12:00 out → 13:00 in → 17:30 out) asserting session hours of 4h + 4h30m and a **daily total of 8h 30m** with the 1h break excluded. (Note: this script currently references a stale `employee_id` column and predates the `user_id` schema — see cleanup notes below.)

---

## Running Locally

**Prerequisites:** Python 3.10+, a webcam, and a C++ toolchain for building `dlib`.

```bash
# 1. Clone
git clone git@github.com:taha-yasin-saad/facial-recognition-attendance.git
cd facial-recognition-attendance

# 2. Virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux / macOS

# 3. Install dlib first (needs C++ build tools on Windows)
pip install cmake dlib

# 4. Install the rest
pip install -r requirements.txt
```

> **Windows tip:** if `dlib` fails to build, grab a prebuilt wheel from
> [z-mahmud22/Dlib_Windows_Python3.x](https://github.com/z-mahmud22/Dlib_Windows_Python3.x)
> and `pip install <wheel>.whl`.

**Start the server** (API + dashboard + kiosk, single process):

```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
# or: python api.py
```

The database and data directories are created automatically on first startup (`init_db()` on the FastAPI `startup` event). Then:

- Dashboard: `http://localhost:8000/dashboard`
- Kiosk (door terminal): `http://localhost:8000/kiosk`
- API docs (Swagger): `http://localhost:8000/docs`

**Register a user — via dashboard:** open `http://localhost:8000/dashboard/users/add`, fill the form, capture photos with the live webcam.

**Register a user — via CLI** (opens a local OpenCV webcam window and captures 5 photos):

```bash
python scripts/register_employee.py \
    --id USR001 \
    --name "Ahmed Al Mansouri" \
    --dept "IT" \
    --role "Engineer" \
    --email "ahmed@university.ae"
    # --photos 5   (optional; defaults to REGISTRATION_PHOTOS)
```

---

## Screenshot

![screenshot placeholder](docs/screenshot.png) <!-- TODO: Taha to add real screenshot/GIF -->

---

## Dashboard & Pages

| URL | Page |
|-----|------|
| `/` | Redirects to `/dashboard` |
| `/dashboard` | Live overview & today's stats |
| `/dashboard/users` | User list, search, filters, pagination |
| `/dashboard/users/add` | Register a new user (webcam) |
| `/dashboard/users/{id}` | User detail: history, monthly hours, all-time totals |
| `/dashboard/attendance` | Full attendance log with date/dept/event filters |
| `/dashboard/reports` | Monthly HR report + charts |
| `/dashboard/guests` | Unknown-face alerts / guest registration |
| `/kiosk` | Face-recognition kiosk (door terminal) |
| `/docs` | Swagger API docs |

---

## REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/users` | List users (`?dept=&active=`) |
| `GET` | `/api/users/{id}` | Single user detail |
| `POST` | `/api/users/register` | Register user (multipart photos) |
| `PATCH` | `/api/users/{id}` | Update user fields |
| `PATCH` | `/api/users/{id}/status` | Activate / deactivate (rebuilds encodings) |
| `DELETE` | `/api/users/{id}` | Delete user |
| `GET` | `/api/attendance/today` | Today's attendance log |
| `GET` | `/api/attendance/present` | Who is currently inside |
| `GET` | `/api/attendance/stats/today` | Today's summary counts |
| `GET` | `/api/attendance/stats/hourly` | Check-ins per hour (`?date=`) |
| `GET` | `/api/attendance/stats/monthly` | Daily check-in counts for a month (`?month=YYYY-MM`) |
| `GET` | `/api/attendance/report/monthly` | Per-user worked hours (`?month=YYYY-MM`) |
| `GET` | `/api/attendance/{id}` | Per-user attendance history (`?limit=`) |
| `GET` | `/api/attendance/export` | CSV export (`?from=YYYY-MM-DD&to=YYYY-MM-DD`) |
| `POST` | `/api/encodings/rebuild` | Rebuild face-encodings cache for active users |
| `POST` | `/api/kiosk/recognize` | Submit a webcam frame for recognition |
| `POST` | `/api/kiosk/reload` | Reload encodings into the kiosk detector |
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
| `CAMERA_INDEX` | `0` | Local camera index used by the CLI registration tool |
| `FACE_TOLERANCE` | `0.50` | Max match distance — lower is stricter |
| `FRAME_RESIZE_SCALE` | `0.5` | Downscale factor applied before detection |
| `KIOSK_FRAME_WIDTH` | `640` | Capture width sent from browser to server |
| `RECOGNITION_COOLDOWN` | `300` | Seconds between events for the same person |
| `MIN_HOURS_BEFORE_CHECKOUT` | `0` | Min hours inside before checkout is allowed |
| `BREAK_ALLOWED_HOURS` | `1.0` | Paid break allowance per day (config value) |
| `DOOR_ID` | `"MAIN_ENTRANCE"` | Door label recorded on every attendance row |
| `REGISTRATION_PHOTOS` | `5` | Photos captured per user during registration |
| `DASHBOARD_AUTO_REFRESH_SECONDS` | `30` | Dashboard auto-refresh interval |

---

## Project Structure

```
├── api.py                     # FastAPI app: REST API + Dashboard + Kiosk routes
├── config.py                  # Global configuration & paths
├── requirements.txt
├── core/
│   ├── detector.py            # Face detection, matching, cooldown
│   ├── encoder.py             # Encoding build / load / add / remove (pickle cache)
│   └── attendance.py          # Check-in/out orchestration, unknown-face logging
├── database/
│   ├── db.py                  # All SQLite queries (users, attendance, reports)
│   └── models.py              # DDL: users, attendance, unknown_logs + indexes
├── dashboard/
│   ├── templates/             # Jinja2 HTML (base, kiosk, users, reports, ...)
│   └── static/                # dashboard.css, webcam.js
├── scripts/
│   └── register_employee.py   # CLI webcam registration tool
├── test_user_story.py         # End-to-end workday scenario script
└── data/                      # Runtime data (git-ignored, created on startup)
    ├── known_faces/{user_id}/*.jpg
    ├── encodings.pkl          # Cached face encodings
    ├── attendance.db          # SQLite database (WAL)
    └── unknown_logs/          # Snapshots of unrecognized faces
```

---

## License

MIT
