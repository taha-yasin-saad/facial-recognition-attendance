import os
from datetime import datetime
from typing import Optional

import cv2

from config import UNKNOWN_LOGS_PATH
from database.db import (
    get_user, determine_next_event, record_checkin,
    record_checkout, get_checkin_record_today, get_total_hours_today, log_unknown_face,
)


class AttendanceManager:
    def __init__(self):
        os.makedirs(UNKNOWN_LOGS_PATH, exist_ok=True)

    def process_recognition(self, user_id: str) -> Optional[dict]:
        """
        Determines and records the correct event for a recognized user.
        Returns event info dict or None if nothing was recorded.
        """
        user = get_user(user_id)
        if not user or not user["is_active"]:
            return None

        next_event = determine_next_event(user_id)
        if next_event is None:
            return None

        if next_event == "check_in":
            result = record_checkin(user_id)
        else:
            checkin = get_checkin_record_today(user_id)
            if not checkin:
                return None
            result = record_checkout(user_id, checkin["timestamp"])
            result["total_hours_today"] = get_total_hours_today(user_id)

        return {
            "user_id": user_id,
            "full_name": user["full_name"],
            "department": user["department"],
            "role": user["role"],
            **result,
        }

    def log_unknown(self, frame) -> str:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        path = os.path.join(UNKNOWN_LOGS_PATH, f"unknown_{ts}.jpg")
        cv2.imwrite(path, frame)
        log_unknown_face(snapshot_path=path)
        return path
