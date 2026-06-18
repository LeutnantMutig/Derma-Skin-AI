from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, Float
from sqlalchemy.orm import relationship

from .database import Base
from datetime import datetime

# -----------------------------
# AUTH USER MODEL (NEW)
# -----------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    
    name = Column(String, nullable=False)
    age = Column(Integer)
    gender = Column(String)
    email = Column(String)
    contact = Column(String)

    allergies = Column(String)
    medical_history = Column(String)
    current_treatments = Column(String)
    family_history = Column(String)

    emergency_name = Column(String)
    emergency_contact = Column(String)
    emergency_relation = Column(String)

    symptoms = Column(String)

    # relationships
    checkups = relationship("Checkup", back_populates="patient")
    treatments = relationship("Treatment", back_populates="patient")
    records = relationship("Record", back_populates="patient")
    treatment_plans = relationship("TreatmentPlan", back_populates="patient")


class Disease(Base):
    __tablename__ = "diseases"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, default="")

    remedies = relationship("Remedy", back_populates="disease")
    disease_images = relationship("DiseaseImage", back_populates="disease", cascade="all, delete-orphan")


class DiseaseImage(Base):
    __tablename__ = "disease_images"

    id = Column(Integer, primary_key=True)
    disease_id = Column(Integer, ForeignKey("diseases.id"), nullable=False)
    image_path = Column(String, nullable=False)
    image_name = Column(String, nullable=True)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    disease = relationship("Disease", back_populates="disease_images")


class Remedy(Base):
    __tablename__ = "remedies"

    id = Column(Integer, primary_key=True)
    disease_id = Column(Integer, ForeignKey("diseases.id"))
    name = Column(String, nullable=False)
    ingredients = Column(Text, nullable=True, default="")
    preparation = Column(Text, nullable=True, default="")
    steps = Column(Text, nullable=True, default="")
    duration_days = Column(Integer, default=14)
    allergy_warnings = Column(Text, nullable=True, default="")

    disease = relationship("Disease", back_populates="remedies")



class Checkup(Base):
    __tablename__ = "checkups"

    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    image_path = Column(String, nullable=True)
    symptoms = Column(Text, default="")
    notes = Column(Text, default="")
    predicted_condition = Column(String, nullable=True)
    confidence = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    allergies = Column(Text, default="")
    
    patient = relationship("Patient", back_populates="checkups")


class Treatment(Base):
    __tablename__ = "treatments"

    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    disease_name = Column(String, nullable=False)
    remedy_name = Column(String, nullable=False)
    duration_days = Column(Integer, default=14)
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=True)
    cured = Column(Boolean, default=False)
    notes = Column(Text, default="")

    patient = relationship("Patient", back_populates="treatments")


class Record(Base):
    __tablename__ = "records"

    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    contact = Column(String, nullable=True)
    before_image_path = Column(String, nullable=True)
    predicted_disease = Column(String, nullable=True)
    confidence_score = Column(Float, default=0.0)
    allergies = Column(Text, default="")
    suggested_remedies = Column(Text, default="")
    start_date = Column(DateTime, default=datetime.utcnow)
    after_image_path = Column(String, nullable=True)
    cure_status = Column(String, default="In Progress")
    end_date = Column(DateTime, nullable=True)
    notes = Column(String, nullable="")

    patient = relationship("Patient", back_populates="records")


# -------------------- TreatmentPlan Model --------------------

class TreatmentPlan(Base):
    __tablename__ = "treatment_plans"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    checkup_id = Column(Integer, ForeignKey("checkups.id"))

    disease_name = Column(String)
    remedy_name = Column(String)
    medicines = Column(Text, default="")
    dosage = Column(String)
    notes = Column(Text, default="")

    start_date = Column(DateTime, default=datetime.utcnow)
    next_checkup_date = Column(DateTime)
    progress_percent = Column(Integer, default=0)
    auto_progress = Column(Boolean, default=True)
    cured = Column(Boolean, default=False)

    before_image_path = Column(String)
    after_image_path = Column(String)

    # Relationships
    patient = relationship("Patient", back_populates="treatment_plans")
    checkup = relationship("Checkup", backref="treatment")


