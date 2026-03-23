import json
from datetime import datetime
from database import SessionLocal, Doctor, Appointment, Patient

def get_available_doctors():
    db = SessionLocal()
    doctors = db.query(Doctor).all()
    result = []
    for d in doctors:
        result.append({
            "id": d.id,
            "name": d.name,
            "specialty": d.specialty,
            "slots": json.loads(d.available_slots)
        })
    db.close()
    return result

def book_appointment(patient_phone: str, doctor_id: int, slot: str, language: str):
    db = SessionLocal()

    # Check slot not already taken
    slot_dt = datetime.strptime(slot, "%Y-%m-%d %H:%M")
    existing = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.scheduled_time == slot_dt,
        Appointment.status == "confirmed"
    ).first()

    if existing:
        db.close()
        return {"success": False, "reason": "Slot already booked. Please choose another."}

    # Get or create patient
    patient = db.query(Patient).filter(Patient.phone == patient_phone).first()
    if not patient:
        patient = Patient(phone=patient_phone, name="Unknown", preferred_language=language)
        db.add(patient)
        db.commit()
        db.refresh(patient)

    # Book it
    appt = Appointment(
        patient_id=patient.id,
        doctor_id=doctor_id,
        scheduled_time=slot_dt,
        language_used=language,
        status="confirmed"
    )
    db.add(appt)

    # Remove slot from doctor's availability
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    slots = json.loads(doctor.available_slots)
    if slot in slots:
        slots.remove(slot)
        doctor.available_slots = json.dumps(slots)

    db.commit()
    db.close()
    return {"success": True, "appointment_id": appt.id, "slot": slot}

def cancel_appointment(appointment_id: int):
    db = SessionLocal()
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        db.close()
        return {"success": False, "reason": "Appointment not found"}
    appt.status = "cancelled"
    db.commit()
    db.close()
    return {"success": True}

def get_patient_appointments(patient_phone: str):
    db = SessionLocal()
    patient = db.query(Patient).filter(Patient.phone == patient_phone).first()
    if not patient:
        db.close()
        return []
    appts = db.query(Appointment).filter(
        Appointment.patient_id == patient.id,
        Appointment.status == "confirmed"
    ).all()
    result = [{"id": a.id, "doctor_id": a.doctor_id,
               "time": str(a.scheduled_time), "status": a.status} for a in appts]
    db.close()
    return result