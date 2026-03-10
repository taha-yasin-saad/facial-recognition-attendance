from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Header
from sqlalchemy.orm import Session
from typing import List
from uuid import uuid4
import datetime
from .. import models, schemas
from ..db import get_db
from ..services import liveness_service, face_service

router = APIRouter(prefix="/kiosk", tags=["kiosk"])


def get_challenge(db: Session, cid: str):
    return db.query(models.KioskChallenge).filter(models.KioskChallenge.id == cid).first()


@router.get("/challenge", response_model=schemas.ChallengeOut)
def create_challenge(device_id: str = Header(None), db: Session = Depends(get_db)):
    if not device_id:
        raise HTTPException(status_code=400, detail="Missing device_id header")
    cid = str(uuid4())
    import random
    types = ["BLINK", "TURN_LEFT", "TURN_RIGHT", "SMILE"]
    challenge_type = random.choice(types)
    rec = models.KioskChallenge(id=cid, device_id=device_id, challenge_type=challenge_type)
    db.add(rec)
    db.commit()
    return {"challenge_id": cid, "challenge_type": challenge_type}


@router.post("/liveness")
async def check_liveness(challenge_id: str = Header(None), files: List[UploadFile] = File(...), device_id: str = Header(None), db: Session = Depends(get_db)):
    if not challenge_id:
        raise HTTPException(status_code=400, detail="Missing challenge_id header")
    ch = get_challenge(db, challenge_id)
    if not ch or (datetime.datetime.utcnow() - ch.created_at).total_seconds() > 60:
        raise HTTPException(status_code=400, detail="Challenge expired or invalid")
    frames = []
    for f in files:
        frames.append(await f.read())
    passed = liveness_service.analyze_frames(frames, ch.challenge_type)
    ch.passed = 1 if passed else 0
    db.commit()
    return {"passed": passed, "reason": None if passed else "CHALLENGE_NOT_MET"}


@router.post("/recognize")
async def recognize(frame: UploadFile = File(...), type: str = Header(None), device_id: str = Header(None), db: Session = Depends(get_db)):
    # verify recent passed challenge for device
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(seconds=60)
    ch = db.query(models.KioskChallenge).filter(models.KioskChallenge.device_id == device_id, models.KioskChallenge.passed == 1, models.KioskChallenge.created_at >= cutoff).order_by(models.KioskChallenge.created_at.desc()).first()
    if not ch:
        raise HTTPException(status_code=400, detail="Liveness not passed")
    content = await frame.read()
    try:
        emb = face_service.image_to_embedding(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    # gather all embeddings
    all_emb = []
    emps = db.query(models.Employee).all()
    for emp in emps:
        for e in emp.embeddings:
            all_emb.append((emp.id, e.vector))
    if not all_emb:
        raise HTTPException(status_code=400, detail="No employees enrolled")
    ids = [t[0] for t in all_emb]
    vectors = [t[1] for t in all_emb]
    match = face_service.match_embedding(vectors, emb)
    if not match:
        raise HTTPException(status_code=400, detail="No match")
    idx, dist, conf = match
    employee_id = ids[idx]
    rec = models.Attendance(
        employee_id=employee_id,
        type=type,
        confidence=conf,
        device_id=device_id,
        face_distance=dist,
    )
    db.add(rec)
    db.commit()
    return {"employee_id": employee_id, "distance": dist, "confidence": conf, "success": True}
