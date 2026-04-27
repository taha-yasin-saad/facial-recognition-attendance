import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Camera — change to RTSP URL string for Kiosk deployment
CAMERA_INDEX = 0
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS = 30

# Face recognition
FACE_TOLERANCE = 0.50
FRAME_RESIZE_SCALE = 0.5
KIOSK_FRAME_WIDTH  = 640   # Browser captures at this width; keeps upload small
RECOGNITION_COOLDOWN = 300       # 5-minute cooldown between events for same employee
MIN_HOURS_BEFORE_CHECKOUT = 0    # No minimum — employees can check out for a break at any time
BREAK_ALLOWED_HOURS = 1.0        # Paid break allowance per day (excluded from worked hours automatically)
DOOR_ID = "MAIN_ENTRANCE"

# Paths
DATA_DIR = os.path.join(BASE_DIR, "data")
KNOWN_FACES_DIR = os.path.join(DATA_DIR, "known_faces")
ENCODINGS_PATH = os.path.join(DATA_DIR, "encodings.pkl")
DB_PATH = os.path.join(DATA_DIR, "attendance.db")
UNKNOWN_LOGS_PATH = os.path.join(DATA_DIR, "unknown_logs")

# Registration
REGISTRATION_PHOTOS = 5
REGISTRATION_INTERVAL = 1.0

# API / Dashboard
API_HOST = "0.0.0.0"
API_PORT = 8000
DASHBOARD_SECRET_KEY = "change-this-in-production"
DASHBOARD_AUTO_REFRESH_SECONDS = 30

# Display
DISPLAY_SCALE = 1.0
FONT_SCALE = 0.65
BOX_COLOR_CHECKIN = (0, 255, 0)       # Green — checked in
BOX_COLOR_CHECKOUT = (255, 165, 0)    # Orange — checked out
BOX_COLOR_UNKNOWN = (0, 0, 255)       # Red — unknown
BOX_COLOR_COOLDOWN = (0, 200, 255)    # Cyan — in cooldown
