from fastapi import HTTPException, Header
from .security import decode_access_token


def admin_required(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    if not payload.get("sub"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return payload.get("sub")
