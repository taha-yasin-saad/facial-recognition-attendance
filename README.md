# Facial Recognition Attendance System

This repository implements a full-stack facial recognition attendance system with a browser kiosk and liveness challenge-response. The backend is built with **Python/FastAPI** and the frontend uses React (Vite + TypeScript).

## Backend Overview

- **Tech stack:** FastAPI, SQLAlchemy (SQLite), face_recognition, OpenCV
- **JWT admin auth** with bcrypt-hashed password
- Liveness detection via EAR/blink, head-turn, smile heuristics
- Facial recognition via dlib embeddings
- Attendance logs stored in SQLite

### API Endpoints

| Method | Path                     | Description                      |
| ------ | ------------------------ | -------------------------------- |
| POST   | `/auth/login`            | Returns admin JWT                |
| POST   | `/employees`             | Create employee (admin)          |
| GET    | `/employees`             | List employees (admin)           |
| POST   | `/employees/{id}/enroll` | Upload 3–10 images for employee  |
| GET    | `/kiosk/challenge`       | Get random liveness challenge    |
| POST   | `/kiosk/liveness`        | Submit burst frames for liveness |
| POST   | `/kiosk/recognize`       | Recognize face & log attendance  |
| GET    | `/attendance`            | Query attendance logs (admin)    |
| GET    | `/attendance/export.csv` | Download CSV export (admin)      |

## Quick Start (Local)

1. **Clone repo** and copy `.env.example` to `.env` adjusting values.
2. Install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
3. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```
   App listens on `http://localhost:8000`.

Or using Docker Compose (includes frontend & backend):

```bash
docker-compose up --build
```

- `backend` service runs at `http://localhost:8000` with live reload.
- `frontend` service runs at `http://localhost:3000` and proxies `/api` to backend.

Both services mount local code so changes appear immediately.

## Usage Examples (curl)

```bash
# login to get token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin"}' | jq -r .access_token)

# create employee
curl -X POST http://localhost:8000/employees \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"employee_code":"E1","full_name":"Alice"}'

# enroll images (example files)
curl -X POST http://localhost:8000/employees/1/enroll \
  -H "Authorization: Bearer $TOKEN" \
  -F "files=@/path/to/photo1.jpg" -F "files=@/path/to/photo2.jpg" \
  -F "files=@/path/to/photo3.jpg"

# kiosk flow
curl -X GET http://localhost:8000/kiosk/challenge -H "device_id: kiosk1"
# (capture frames per challenge type)
# submit liveness frames
curl -X POST http://localhost:8000/kiosk/liveness \
  -H "challenge_id: <id>" -H "device_id: kiosk1" \
  -F "files=@frame1.jpg" -F "files=@frame2.jpg"
# recognition
curl -X POST http://localhost:8000/kiosk/recognize \
  -H "device_id: kiosk1" -H "type: IN" \
  -F "frame=@capture.jpg"

# query attendance
curl -X GET http://localhost:8000/attendance \
  -H "Authorization: Bearer $TOKEN"

# download CSV
curl -X GET http://localhost:8000/attendance/export.csv \
  -H "Authorization: Bearer $TOKEN" -o log.csv
```

## Notes

- Liveness detections use simplistic heuristics; thresholds may need tuning.
- Embeddings are stored as JSON arrays; raw images are discarded for privacy.
- Challenges expire after 60 seconds and are tied to `device_id`.

## Testing

Run backend tests via:

```bash
cd backend
pytest
```

## Frontend

The frontend app lives in `frontend/`. It uses Vite + React + TypeScript.

### Local development

To start the development server manually:

```bash
cd frontend
npm install
npm run dev
```

The dev server runs on `http://localhost:3000` and proxies `/api` to `http://localhost:8000` (configured in `vite.config.ts`).

Environment variables are defined in `.env` or `.env.local`; an example is provided in `.env.example`:

```text
VITE_API_URL=http://localhost:8000
```

### Using Docker Compose

Run both backend and frontend with one command:

```bash
docker-compose up --build
```

- `backend` service exposes port 8000.
- `frontend` service exposes port 3000 and will install dependencies and serve via Vite.
- The compose setup mounts source code into containers so edits are reflected live.

You can also build a production frontend image by running `npm run build` inside the `frontend` container or locally.

---

Feel free to extend the frontend or adjust Docker configuration for production deployment.
"# facial-recognition-attendance" 
