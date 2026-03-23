from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///./voice_agent.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True)
    phone = Column(String, unique=True)
    name = Column(String)
    preferred_language = Column(String, default="en")
    created_at = Column(DateTime, default=datetime.utcnow)

class Doctor(Base):
    __tablename__ = "doctors"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    specialty = Column(String)
    available_slots = Column(String)  # JSON string of available times

class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer)
    doctor_id = Column(Integer)
    scheduled_time = Column(DateTime)
    status = Column(String, default="confirmed")  # confirmed/cancelled/rescheduled
    language_used = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)
    seed_data()

def seed_data():
    db = SessionLocal()
    # Only seed if empty
    if db.query(Doctor).count() == 0:
        doctors = [
            Doctor(name="Dr. Priya Sharma", specialty="General Physician",
                   available_slots='["2024-12-20 09:00", "2024-12-20 10:00", "2024-12-20 14:00", "2024-12-21 11:00"]'),
            Doctor(name="Dr. Rajan Kumar", specialty="Cardiologist",
                   available_slots='["2024-12-20 11:00", "2024-12-20 15:00", "2024-12-21 09:00"]'),
            Doctor(name="Dr. Meena Iyer", specialty="Dermatologist",
                   available_slots='["2024-12-20 12:00", "2024-12-21 10:00", "2024-12-21 15:00"]'),
        ]
        db.add_all(doctors)
        db.commit()
    db.close()