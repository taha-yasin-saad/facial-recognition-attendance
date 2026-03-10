import io
import face_recognition
import numpy as np
from typing import List, Optional

FACE_DISTANCE_THRESHOLD = float(
    __import__("os").getenv("FACE_DISTANCE_THRESHOLD", "0.5")
)


def image_to_embedding(image_bytes: bytes) -> List[float]:
    image = face_recognition.load_image_file(io.BytesIO(image_bytes))
    enc = face_recognition.face_encodings(image)
    if not enc:
        raise ValueError("No face found")
    return enc[0].tolist()


def match_embedding(known_embeddings: List[List[float]], unknown: List[float]) -> Optional[tuple]:
    if not known_embeddings:
        return None
    distances = face_recognition.face_distance(known_embeddings, unknown)
    best_idx = int(np.argmin(distances))
    best_distance = float(distances[best_idx])
    confidence = max(0.0, 1.0 - best_distance / FACE_DISTANCE_THRESHOLD)
    return best_idx, best_distance, confidence
