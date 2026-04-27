import os
import pickle
from typing import Optional

import face_recognition

from config import KNOWN_FACES_DIR, ENCODINGS_PATH


def encode_image(image_path: str) -> Optional[list]:
    img = face_recognition.load_image_file(image_path)
    encodings = face_recognition.face_encodings(img)
    return encodings[0] if encodings else None


def build_encodings(active_ids: set[str] = None) -> dict:
    """Build {user_id: [encodings]} from disk. If active_ids given, skip inactive."""
    known = {}
    if not os.path.isdir(KNOWN_FACES_DIR):
        return known

    for user_id in os.listdir(KNOWN_FACES_DIR):
        if active_ids is not None and user_id not in active_ids:
            continue
        folder = os.path.join(KNOWN_FACES_DIR, user_id)
        if not os.path.isdir(folder):
            continue
        encodings = []
        for fname in os.listdir(folder):
            if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            enc = encode_image(os.path.join(folder, fname))
            if enc is not None:
                encodings.append(enc)
        if encodings:
            known[user_id] = encodings

    save_encodings(known)
    return known


def save_encodings(data: dict):
    os.makedirs(os.path.dirname(ENCODINGS_PATH), exist_ok=True)
    with open(ENCODINGS_PATH, "wb") as f:
        pickle.dump(data, f)


def load_encodings() -> dict:
    if not os.path.exists(ENCODINGS_PATH):
        return build_encodings()
    with open(ENCODINGS_PATH, "rb") as f:
        return pickle.load(f)


def add_user_encodings(user_id: str, image_paths: list[str]) -> int:
    known = load_encodings()
    new_encodings = []
    for path in image_paths:
        enc = encode_image(path)
        if enc is not None:
            new_encodings.append(enc)
    if new_encodings:
        existing = known.get(user_id, [])
        known[user_id] = existing + new_encodings
        save_encodings(known)
    return len(new_encodings)


def remove_user_encodings(user_id: str):
    known = load_encodings()
    if user_id in known:
        del known[user_id]
        save_encodings(known)
