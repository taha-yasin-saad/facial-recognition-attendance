from pydantic import BaseModel, Field
from typing import List, Optional
import datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AdminLogin(BaseModel):
    username: str
    password: str


class EmployeeCreate(BaseModel):
    employee_code: str
    full_name: str
    department: Optional[str] = None


class EmployeeOut(BaseModel):
    id: int
    employee_code: str
    full_name: str
    department: Optional[str]

    class Config:
        orm_mode = True


class AttendanceOut(BaseModel):
    id: int
    employee_id: int
    timestamp: datetime.datetime
    type: str
    confidence: float
    device_id: Optional[str]
    face_distance: float

    class Config:
        orm_mode = True


class LivenessRequest(BaseModel):
    challenge_id: str
    # frames will be handled as files in route


class ChallengeOut(BaseModel):
    challenge_id: str
    challenge_type: str


class RecognitionResult(BaseModel):
    employee_id: Optional[int]
    distance: Optional[float]
    confidence: Optional[float]
    success: bool

