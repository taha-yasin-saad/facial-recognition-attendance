from typing import List
import io
import numpy as np
import face_recognition


# heuristic functions for blink, head turn, smile

def eye_aspect_ratio(eye_landmarks):
    # eye_landmarks: list of (x,y)
    # compute EAR
    a = np.linalg.norm(np.array(eye_landmarks[1]) - np.array(eye_landmarks[5]))
    b = np.linalg.norm(np.array(eye_landmarks[2]) - np.array(eye_landmarks[4]))
    c = np.linalg.norm(np.array(eye_landmarks[0]) - np.array(eye_landmarks[3]))
    if c == 0:
        return 0
    return (a + b) / (2.0 * c)


def mouth_aspect_ratio(mouth_landmarks):
    a = np.linalg.norm(np.array(mouth_landmarks[14]) - np.array(mouth_landmarks[18]))
    b = np.linalg.norm(np.array(mouth_landmarks[12]) - np.array(mouth_landmarks[16]))
    if b == 0:
        return 0
    return a / b


def analyze_frames(frames: List[bytes], challenge_type: str) -> bool:
    # frames: raw image bytes list
    landmarks_seq = []
    for b in frames:
        image = face_recognition.load_image_file(io.BytesIO(b))
        locs = face_recognition.face_locations(image)
        if len(locs) != 1:
            continue
        lm = face_recognition.face_landmarks(image, locs)[0]
        landmarks_seq.append(lm)
    if not landmarks_seq:
        return False
    if challenge_type == "BLINK":
        # detect a dip then rise in EAR for either eye
        ears = []
        for lm in landmarks_seq:
            le = eye_aspect_ratio(lm.get("left_eye", []))
            re = eye_aspect_ratio(lm.get("right_eye", []))
            ears.append((le + re) / 2)
        # require minimum dip below threshold
        if min(ears) < 0.2 and max(ears) - min(ears) > 0.08:
            return True
        return False
    elif challenge_type in ("TURN_LEFT", "TURN_RIGHT"):
        # simple nose relative x movement
        xs = []
        for lm in landmarks_seq:
            nose = lm.get("nose_tip", [])
            if nose:
                xs.append(nose[0][0])
        if len(xs) < 2:
            return False
        if challenge_type == "TURN_LEFT" and xs[-1] < xs[0] - 5:
            return True
        if challenge_type == "TURN_RIGHT" and xs[-1] > xs[0] + 5:
            return True
        return False
    elif challenge_type == "SMILE":
        mrs = []
        for lm in landmarks_seq:
            mar = mouth_aspect_ratio(lm.get("top_lip", []) + lm.get("bottom_lip", []))
            mrs.append(mar)
        if max(mrs) > 0.5:
            return True
        return False
    return False
