## GitHub Copilot Prompt (Browser Kiosk + Liveness)

**Build a full-stack facial recognition attendance system with a browser kiosk and liveness (anti-spoof) challenge-response.**

### Tech Stack (use these)

- Backend: **Python FastAPI**
- Face recognition + landmarks: **face_recognition** (dlib embeddings + landmarks) and **OpenCV**
- DB: **SQLite** via **SQLAlchemy**
- Frontend: **React (Vite) + TypeScript**
- Auth: **Admin JWT** + **Kiosk device token**
- Local run: **Docker Compose**

---

## Functional Requirements

### 1) Admin Authentication

- `POST /auth/login` returns JWT
- Store hashed password (bcrypt)
- Seed script/command to create initial admin based on `.env`

### 2) Employee Enrollment

- Admin can create employee: `employee_code`, `full_name`, optional `department`
- Admin uploads **3–10** images per employee
- Backend validates: **exactly 1 face** per image
- Generate embedding per image and store in DB as JSON float array
- Do NOT store raw photos by default (privacy)
- Endpoints:
  - `POST /employees`
  - `GET /employees`
  - `POST /employees/{id}/enroll` (multipart images[])

### 3) Browser Kiosk (Webcam)

- React `/kiosk` page uses **getUserMedia**
- Show live video preview
- Two modes: button “Check In/Out” and auto mode (capture every N seconds)
- Capture frame from `<video>` into `<canvas>` and upload as **image/jpeg**
- Send to backend:
  - `POST /kiosk/recognize` with multipart form-data: `frame`, `type=IN|OUT`, `device_id`
  - Include kiosk token header: `X-KIOSK-TOKEN`

### 4) Liveness / Anti-Spoof (Challenge-Response)

Implement a lightweight liveness step before logging attendance:

**Kiosk UI flow:**

1. User opens `/kiosk`
2. System shows a random challenge:
   - **Blink** (preferred)
   - OR **Turn head left**, **turn head right**
   - OR **Smile**

3. Kiosk captures a short burst of frames (e.g., 2–4 seconds at 5 FPS)
4. Sends burst frames to backend `/kiosk/liveness` OR sends frames sequentially and backend evaluates liveness state
5. Only if liveness passes → allow `/kiosk/recognize` and log attendance

**Backend liveness detection rules (simple heuristics):**

- Use `face_recognition.face_landmarks` to extract key points:
  - Eyes: compute **Eye Aspect Ratio (EAR)** and detect blink as EAR dips below threshold then rises
  - Head turn: compare relative position of nose tip to left/right eye or face box ratio across frames to infer yaw direction
  - Smile: compare mouth width/height ratio increase across frames

- Must detect exactly 1 face in each usable frame; allow some dropped frames
- If liveness fails, return reason: `NO_FACE`, `MULTIPLE_FACES`, `CHALLENGE_NOT_MET`, `LOW_QUALITY`

**Endpoints (add these):**

- `GET /kiosk/challenge` → returns `{challenge_id, challenge_type}` (random)
- `POST /kiosk/liveness` → accepts burst frames + challenge_id, returns `{passed, reason}`
- `POST /kiosk/recognize` → only logs attendance if `passed_liveness=true` for recent challenge (store short-lived challenge result in memory cache or DB with expiry)

**Security:**

- Challenge must expire (e.g., 30–60 seconds)
- Associate challenge with `device_id` (and optionally a session id)
- Rate-limit `/kiosk/liveness` and `/kiosk/recognize`

### 5) Recognition + Attendance

- Matching compares unknown embedding to all stored embeddings
- Choose smallest distance
- Threshold from env: `FACE_DISTANCE_THRESHOLD` default 0.50
- Log attendance: `employee_id`, `ts UTC ISO`, `type`, `confidence`, `device_id`
- Return response: matched employee + distance + confidence

### 6) Attendance Logs + CSV Export

- Admin can view logs with filters: date range, employee_code, device_id, type
- Export:
  - `GET /attendance/export.csv`

---

## Non-Functional Requirements

- CORS for frontend origin
- Rate limiting on kiosk endpoints
- Clear validation errors for no-face/multi-face
- `.env.example` for backend + frontend
- Tests for key backend endpoints:
  - auth login
  - enroll validation
  - challenge creation + expiry
  - liveness detection basic cases (mock landmarks)
  - recognize logs attendance only after valid liveness

---

## Required Project Structure

- `backend/`
  - `app/main.py`
  - `app/db.py`
  - `app/models.py`
  - `app/schemas.py`
  - `app/services/face_service.py` (embeddings + match)
  - `app/services/liveness_service.py` (EAR blink + head turn + smile)
  - `app/routers/auth.py`
  - `app/routers/employees.py`
  - `app/routers/kiosk.py`
  - `app/routers/attendance.py`
  - `app/utils/security.py` (JWT + bcrypt)
  - `tests/`

- `frontend/`
  - Pages: Login, Employees, Enroll, Attendance, **Kiosk**
  - Components:
    - `WebcamCapture.tsx` (video + canvas frame extraction)
    - `LivenessChallenge.tsx` (shows challenge + progress + status)
    - `ProtectedRoute.tsx`

- `docker-compose.yml`

---

## API Contract (must implement exactly)

- `POST /auth/login`
- `POST /employees`
- `GET /employees`
- `POST /employees/{id}/enroll`
- `GET /kiosk/challenge`
- `POST /kiosk/liveness`
- `POST /kiosk/recognize`
- `GET /attendance`
- `GET /attendance/export.csv`

---

## Deliverables

- Full working codebase backend + frontend
- Docker compose run
- README with setup + usage + curl examples
- Notes on liveness limitations and tuning thresholds (EAR threshold, smile ratio)

**Now generate the complete codebase accordingly.**


## GitHub Copilot Prompt (Beautiful Niche UI + Animations)

You are upgrading the existing facial-recognition attendance system frontend (React + Vite + TypeScript) into a premium, niche, modern product UI.

### UI/UX Goals

* Make the UI look like a **high-end SaaS product** (clean, modern, minimal, premium)
* Strong typography hierarchy, consistent spacing, soft shadows, rounded corners
* Smooth micro-interactions, subtle gradients, glass/blur effects where appropriate
* Design should feel **fast**, **calm**, **professional**, **trustworthy**

### Tech Requirements

* Use:

  * **TailwindCSS**
  * **shadcn/ui** components
  * **Framer Motion** for animations
  * **lucide-react** icons
* Use **React Router** for routing
* Use a clean layout with:

  * Sidebar + topbar for admin pages
  * Fullscreen kiosk mode

### Pages to implement/redesign

1. `/login`
2. `/admin/employees` (list + create modal)
3. `/admin/enroll/:id` (upload images with progress UI)
4. `/admin/attendance` (filters, table, export button)
5. `/kiosk` (camera view, challenge UI, recognition result UI)

### Layout Rules

* Admin Layout:

  * Left sidebar (collapsible)
  * Topbar (search input optional)
  * Main content in card containers
* Kiosk Layout:

  * Fullscreen center content
  * Large video preview card
  * Large CTA buttons (Check In / Check Out)
  * Animated status feedback (success/fail)
  * Prominent liveness challenge UI

### Visual Design Requirements

* Use a consistent theme:

  * Neutral background (light + dark mode support)
  * Accent color for success/focus states
  * Success and error states must feel premium (not loud)
* Use modern UI patterns:

  * Skeleton loaders
  * Toast notifications
  * Animated progress indicators
  * Empty states with illustrations/icons
* Make forms visually pleasing:

  * floating labels or clean label spacing
  * input focus rings
  * proper validation messages

### Animation Requirements (Framer Motion)

Implement subtle, premium animations:

* Page transitions (fade + slight translate)
* Cards appear with stagger animations
* Buttons have hover/tap scaling micro-interactions
* Success recognition:

  * animated check icon
  * glow pulse behind card
* Failure recognition:

  * subtle shake or bounce + warning icon
* Liveness challenge:

  * animated stepper progress (e.g., “Blink → Verified”)
  * countdown timer animation
* Sidebar open/close animation
* Modal open/close animations

### Components to Build (must be reusable)

* `AppLayout` (sidebar + topbar)
* `KioskLayout` (fullscreen)
* `MotionCard`, `MotionButton`
* `StatCards` (e.g., today attendance, late count, total hours)
* `DataTable` with sorting and filter chips
* `UploadDropzone` with preview + progress
* `StatusToast` (success/error/info)
* `LivenessChallengeCard` (stepper + timer + status)

### Data Display

* Employee list:

  * Avatar placeholder generated from initials
  * Status badges (Enrolled / Not Enrolled)
  * Quick actions (Enroll, View logs)
* Attendance logs:

  * Filter chips (Today, This week, Employee)
  * Table with sticky header, zebra rows
  * Export CSV button styled as premium
* Add a dashboard home page `/admin`:

  * Summary cards + animated mini charts (optional using recharts)
  * “Recent activity” list

### Implementation Rules

* Keep code production-ready:

  * strong folder structure: `components/`, `pages/`, `layouts/`, `lib/`
  * TypeScript types everywhere
  * avoid inline messy Tailwind strings; create components for repeated patterns
* Ensure accessibility:

  * proper aria labels
  * keyboard focus states
* Responsive:

  * Works on laptop kiosk screen and tablets

### Deliverable

Generate the full updated frontend code:

* Tailwind setup + shadcn/ui installed usage
* Framer Motion integrated
* All pages redesigned as described
* Ensure the UI is coherent and consistent across pages

Now implement these UI upgrades across the React frontend.

---

## Extra “Style Direction” (optional, add at the bottom)

Use a “**premium security + HR tech**” vibe:

* calm background
* subtle glass cards
* clean icons
* smooth transitions
* minimal but expressive

