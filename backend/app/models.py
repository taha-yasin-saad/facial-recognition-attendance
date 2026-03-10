from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .db import Base
import datetime


class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)


class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    employee_code = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    department = Column(String, nullable=True)
    embeddings = relationship("Embedding", back_populates="employee", cascade="all, delete")
    attendances = relationship("Attendance", back_populates="employee", cascade="all, delete")


class Embedding(Base):
    __tablename__ = "embeddings"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    vector = Column(JSON, nullable=False)
    employee = relationship("Employee", back_populates="embeddings")


class Attendance(Base):
    __tablename__ = "attendances"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    type = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    device_id = Column(String, nullable=True)
    face_distance = Column(Float, nullable=False)
    employee = relationship("Employee", back_populates="attendances")


class KioskChallenge(Base):
    __tablename__ = "kiosk_challenges"
    id = Column(String, primary_key=True, index=True)
    device_id = Column(String, index=True)
    challenge_type = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    passed = Column(Integer, default=0)  # boolean as int

