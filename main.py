import sys
import time

import cv2


def _hms(decimal_hours) -> str:
    if not decimal_hours:
        return ""
    total_m = int(round(float(decimal_hours) * 60))
    h, m = divmod(total_m, 60)
    return f"{h}h {m:02d}m"

from config import CAMERA_INDEX, CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS, DISPLAY_SCALE
from core.detector import FaceDetector
from core.attendance import AttendanceManager
from database.db import init_db, get_all_users


def build_info_map(users: list[dict]) -> dict[str, dict]:
    return {u["user_id"]: u for u in users}


def open_camera(source) -> cv2.VideoCapture:
    if isinstance(source, str) and source.startswith("rtsp"):
        cap = cv2.VideoCapture(source)
    else:
        cap = cv2.VideoCapture(int(source), cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
        cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open camera: {source}")
        sys.exit(1)
    return cap


def run():
    init_db()
    detector = FaceDetector()
    manager = AttendanceManager()
    users = get_all_users(active_only=True)
    info_map = build_info_map(users)

    cap = open_camera(CAMERA_INDEX)
    print("[INFO] Face Recognition Attendance — Q: quit  R: reload encodings")

    frame_count = 0
    fps_start = time.time()
    display_fps = 0.0
    last_results = []
    unknown_throttle: dict[str, float] = {}   # loc_key → last_logged

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[WARN] Dropped frame")
            continue

        frame_count += 1

        if frame_count % 2 == 0:
            t0 = time.time()
            last_results = detector.process_frame(frame)
            elapsed_ms = (time.time() - t0) * 1000

            for r in last_results:
                if r.is_known:
                    if not detector.in_cooldown(r.user_id):
                        info = manager.process_recognition(r.user_id)
                        if info:
                            detector.set_cooldown(r.user_id)
                            r.event_type = info.get("event_type")
                            hours_str = f" — {_hms(info.get('worked_hours'))}" if info.get("worked_hours") else ""
                            print(
                                f"[{info['event_type'].upper()}] {info['full_name']} "
                                f"({info['user_id']}) {info['timestamp']}{hours_str}"
                            )
                else:
                    top, right, bottom, left = r.location
                    region_key = f"{left//100}_{top//100}"
                    last_logged = unknown_throttle.get(region_key, 0)
                    if time.time() - last_logged > 30:
                        manager.log_unknown(frame)
                        unknown_throttle[region_key] = time.time()
                        print("[UNKNOWN] Face logged")

            cv2.putText(frame, f"Rec: {elapsed_ms:.0f}ms", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (180, 180, 180), 1)

        frame = detector.draw_results(frame, last_results, info_map)

        now = time.time()
        if now - fps_start >= 1.0:
            display_fps = frame_count / (now - fps_start)
            frame_count = 0
            fps_start = now
        cv2.putText(frame, f"FPS: {display_fps:.1f}", (10, 55),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (180, 180, 180), 1)

        if DISPLAY_SCALE != 1.0:
            frame = cv2.resize(frame, (0, 0), fx=DISPLAY_SCALE, fy=DISPLAY_SCALE)

        cv2.imshow("UniAttend — Face Recognition", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("r"):
            print("[INFO] Reloading encodings...")
            detector.reload()
            users = get_all_users(active_only=True)
            info_map = build_info_map(users)
            print(f"[INFO] {len(info_map)} active users loaded")

    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] Session ended.")


if __name__ == "__main__":
    run()
