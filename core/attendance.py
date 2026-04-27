import os
from datetime import datetime
from typing import Optional

import cv2

from config import UNKNOWN_LOGS_PATH
from database.db import (
    get_employee, determine_next_event, record_checkin,
    record_checkout, get_checkin_record_today, get_total_hours_today, log_unknown_face,
)


class AttendanceManager:
    def __init__(self):
        os.makedirs(UNKNOWN_LOGS_PATH, exist_ok=True)

    def process_recognition(self, employee_id: str) -> Optional[dict]:
        """
        Determines and records the correct event for a recognized employee.
        Returns event info dict or None if nothing was recorded.
        """
        emp = get_employee(employee_id)
        if not emp or not emp["is_active"]:
            return None

        next_event = determine_next_event(employee_id)
        if next_event is None:
            return None

        if next_event == "check_in":
            result = record_checkin(employee_id)
        else:
            checkin = get_checkin_record_today(employee_id)
            if not checkin:
                return None
            result = record_checkout(employee_id, checkin["timestamp"])
            result["total_hours_today"] = get_total_hours_today(employee_id)

        return {
            "employee_id": employee_id,
            "full_name": emp["full_name"],
            "department": emp["department"],
            "role": emp["role"],
            **result,
        }

    def log_unknown(self, frame) -> str:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        path = os.path.join(UNKNOWN_LOGS_PATH, f"unknown_{ts}.jpg")
        cv2.imwrite(path, frame)
        log_unknown_face(snapshot_path=path)
        return path
