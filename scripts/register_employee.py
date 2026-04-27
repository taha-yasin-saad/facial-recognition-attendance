"""
Register a new employee by capturing photos from the webcam.

Usage:
    python scripts/register_employee.py \
        --id EMP001 --name "Ahmed Al Mansouri" \
        --dept "IT" --role "Engineer" --email "ahmed@university.ae"
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import cv2

from config import CAMERA_INDEX, KNOWN_FACES_DIR, REGISTRATION_PHOTOS, REGISTRATION_INTERVAL
from core.encoder import add_employee_encodings
from database.db import init_db, add_employee, get_employee


def capture_photos(employee_id: str, count: int, interval: float) -> list[str]:
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("[ERROR] Cannot open camera.")
        sys.exit(1)

    save_dir = os.path.join(KNOWN_FACES_DIR, employee_id)
    os.makedirs(save_dir, exist_ok=True)

    paths = []
    print(f"[INFO] Capturing {count} photos — look at the camera...")

    for i in range(count):
        for _ in range(10):
            cap.read()

        ret, frame = cap.read()
        if not ret:
            print(f"[WARN] Skipped photo {i+1}")
            continue

        path = os.path.join(save_dir, f"{i+1:02d}.jpg")
        cv2.imwrite(path, frame)
        paths.append(path)
        print(f"  [{i+1}/{count}] Saved → {path}")

        cv2.imshow("Registration — press Q to cancel", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            print("[INFO] Cancelled by user.")
            break

        if i < count - 1:
            time.sleep(interval)

    cap.release()
    cv2.destroyAllWindows()
    return paths


def main():
    parser = argparse.ArgumentParser(description="Register an employee face")
    parser.add_argument("--id", required=True, dest="employee_id", help="Unique employee ID")
    parser.add_argument("--name", required=True, help="Full name")
    parser.add_argument("--dept", required=True, help="Department")
    parser.add_argument("--role", default="", help="Job role/title")
    parser.add_argument("--email", default="", help="Email address")
    parser.add_argument("--photos", type=int, default=REGISTRATION_PHOTOS,
                        help=f"Number of photos to capture (default: {REGISTRATION_PHOTOS})")
    args = parser.parse_args()

    init_db()

    if get_employee(args.employee_id):
        print(f"[ERROR] Employee {args.employee_id} already exists.")
        sys.exit(1)

    photos = capture_photos(args.employee_id, args.photos, REGISTRATION_INTERVAL)
    if not photos:
        print("[ERROR] No photos captured. Aborting.")
        sys.exit(1)

    photo_path = photos[0]
    ok = add_employee(args.employee_id, args.name, args.dept, args.role, args.email, photo_path)
    if not ok:
        print("[ERROR] Failed to insert employee record.")
        sys.exit(1)

    encoded = add_employee_encodings(args.employee_id, photos)
    print(f"\n[OK] Registered {args.name} ({args.employee_id})")
    print(f"     Photos: {len(photos)}  |  Faces encoded: {encoded}")
    if encoded == 0:
        print("[WARN] No faces detected — re-run in better lighting.")


if __name__ == "__main__":
    main()
