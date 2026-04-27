import time
from dataclasses import dataclass
from typing import Optional

import cv2
import face_recognition
import numpy as np

from config import FACE_TOLERANCE, FRAME_RESIZE_SCALE, RECOGNITION_COOLDOWN
from core.encoder import load_encodings


@dataclass
class RecognitionResult:
    employee_id: Optional[str]
    confidence: float
    location: tuple          # (top, right, bottom, left) — full-scale
    is_known: bool
    event_type: Optional[str] = None   # 'check_in' | 'check_out' | None


class FaceDetector:
    def __init__(self):
        self._known: dict = {}
        self._emp_ids: list[str] = []
        self._all_encodings: list = []
        self._cooldown_map: dict[str, float] = {}
        self.reload()

    def reload(self):
        self._known = load_encodings()
        self._emp_ids = []
        self._all_encodings = []
        for eid, encs in self._known.items():
            for enc in encs:
                self._emp_ids.append(eid)
                self._all_encodings.append(enc)

    def in_cooldown(self, employee_id: str) -> bool:
        last = self._cooldown_map.get(employee_id, 0)
        return (time.time() - last) < RECOGNITION_COOLDOWN

    def set_cooldown(self, employee_id: str):
        self._cooldown_map[employee_id] = time.time()

    def process_frame(self, frame: np.ndarray, upsample_times: int = 1) -> list[RecognitionResult]:
        scale = FRAME_RESIZE_SCALE
        small = cv2.resize(frame, (0, 0), fx=scale, fy=scale)
        rgb_small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

        locations = face_recognition.face_locations(rgb_small, model="hog", number_of_times_to_upsample=upsample_times)
        if not locations:
            return []

        encodings = face_recognition.face_encodings(rgb_small, locations, num_jitters=1)
        results = []
        inv = 1.0 / scale

        for enc, loc in zip(encodings, locations):
            top, right, bottom, left = [int(v * inv) for v in loc]
            full_loc = (top, right, bottom, left)

            if not self._all_encodings:
                results.append(RecognitionResult(None, 0.0, full_loc, False))
                continue

            distances = face_recognition.face_distance(self._all_encodings, enc)
            best_idx = int(np.argmin(distances))
            best_dist = float(distances[best_idx])
            confidence = max(0.0, 1.0 - best_dist)

            if best_dist <= FACE_TOLERANCE:
                results.append(RecognitionResult(
                    self._emp_ids[best_idx], confidence, full_loc, True
                ))
            else:
                results.append(RecognitionResult(None, confidence, full_loc, False))

        return results

    def draw_results(self, frame: np.ndarray, results: list[RecognitionResult],
                     info_map: dict[str, dict]) -> np.ndarray:
        from config import (
            BOX_COLOR_CHECKIN, BOX_COLOR_CHECKOUT,
            BOX_COLOR_UNKNOWN, BOX_COLOR_COOLDOWN, FONT_SCALE,
        )
        out = frame.copy()
        for r in results:
            top, right, bottom, left = r.location

            if not r.is_known:
                color = BOX_COLOR_UNKNOWN
                label = "Unknown"
            elif self.in_cooldown(r.employee_id):
                color = BOX_COLOR_COOLDOWN
                emp = info_map.get(r.employee_id, {})
                label = emp.get("full_name", r.employee_id)
            elif r.event_type == "check_out":
                color = BOX_COLOR_CHECKOUT
                emp = info_map.get(r.employee_id, {})
                label = f"OUT: {emp.get('full_name', r.employee_id)}"
            else:
                color = BOX_COLOR_CHECKIN
                emp = info_map.get(r.employee_id, {})
                label = f"IN: {emp.get('full_name', r.employee_id)}"

            cv2.rectangle(out, (left, top), (right, bottom), color, 2)
            cv2.rectangle(out, (left, bottom - 30), (right, bottom), color, cv2.FILLED)
            cv2.putText(
                out, f"{label} ({r.confidence:.0%})",
                (left + 4, bottom - 8),
                cv2.FONT_HERSHEY_DUPLEX, FONT_SCALE, (255, 255, 255), 1,
            )
        return out
