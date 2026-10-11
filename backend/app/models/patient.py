from sqlalchemy import Column, Integer, BigInteger, SmallInteger, String, Text, Date, Time, Numeric, Boolean, ForeignKey, CheckConstraint, UniqueConstraint, Index, text
from sqlalchemy.dialects.mysql import DATETIME
from app.database.base import Base

class Patient(Base):
    __tablename__ = 'patients'
    patient_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(20), nullable=False)
    blood_group = Column(String(3), nullable=True)
    phone = Column(String(20), nullable=False)
    email = Column(String(254), nullable=True, unique=True)
    address = Column(String(255), nullable=True)
    city = Column(String(80), nullable=True)
    occupation = Column(String(100), nullable=True)
    marital_status = Column(String(20), nullable=True)
    emergency_contact_name = Column(String(100), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    created_at = Column(DATETIME(fsp=6), nullable=False, server_default=text('CURRENT_TIMESTAMP(6)'))
    updated_at = Column(DATETIME(fsp=6), nullable=False, server_default=text('CURRENT_TIMESTAMP(6)'))
    __table_args__ = (
        CheckConstraint("gender IN ('FEMALE','MALE','NON_BINARY','OTHER','UNDISCLOSED')", name='ck_patients_0'),
        CheckConstraint("blood_group IS NULL OR blood_group IN ('A+','A-','B+','B-','AB+','AB-','O+','O-')", name='ck_patients_1'),
        CheckConstraint("marital_status IS NULL OR marital_status IN ('SINGLE','MARRIED','DIVORCED','WIDOWED','UNDISCLOSED')", name='ck_patients_2'),
        Index('ix_patients_0', 'last_name', 'first_name', 'patient_id'),
        Index('ix_patients_1', 'first_name', 'patient_id'),
        Index('ix_patients_2', 'phone'),
        Index('ix_patients_3', 'created_at', 'patient_id'),
        {'mysql_engine':'InnoDB', 'mysql_charset':'utf8mb4', 'mysql_collate':'utf8mb4_0900_ai_ci'},
    )

class MedicalHistory(Base):
    __tablename__ = 'medical_history'
    history_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    patient_id = Column(Integer, ForeignKey('patients.patient_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    condition_name = Column(String(150), nullable=False)
    diagnosed_date = Column(Date, nullable=True)
    treatment = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    __table_args__ = (
        Index('ix_medical_history_0', 'patient_id', 'diagnosed_date', 'history_id'),
        {'mysql_engine':'InnoDB', 'mysql_charset':'utf8mb4', 'mysql_collate':'utf8mb4_0900_ai_ci'},
    )

class Allergy(Base):
    __tablename__ = 'allergies'
    allergy_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    patient_id = Column(Integer, ForeignKey('patients.patient_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    allergen = Column(String(150), nullable=False)
    allergy_type = Column(String(20), nullable=False)
    reaction = Column(String(255), nullable=True)
    severity = Column(String(10), nullable=False)
    notes = Column(Text, nullable=True)
    __table_args__ = (
        CheckConstraint("allergy_type IN ('MEDICATION','FOOD','ENVIRONMENTAL','OTHER')", name='ck_allergies_0'),
        CheckConstraint("severity IN ('MILD','MODERATE','SEVERE')", name='ck_allergies_1'),
        Index('ix_allergies_0', 'patient_id'),
        {'mysql_engine':'InnoDB', 'mysql_charset':'utf8mb4', 'mysql_collate':'utf8mb4_0900_ai_ci'},
    )

class LifestyleHistory(Base):
    __tablename__ = 'lifestyle_history'
    lifestyle_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    patient_id = Column(Integer, ForeignKey('patients.patient_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, unique=True)
    smoking_status = Column(String(15), nullable=True)
    alcohol_status = Column(String(15), nullable=True)
    exercise_frequency = Column(String(30), nullable=True)
    sleep_hours = Column(Numeric(4, 2), nullable=True)
    diet_type = Column(String(30), nullable=True)
    occupation_notes = Column(Text, nullable=True)
    updated_at = Column(DATETIME(fsp=6), nullable=False, server_default=text('CURRENT_TIMESTAMP(6)'))
    __table_args__ = (
        CheckConstraint("smoking_status IS NULL OR smoking_status IN ('NEVER','FORMER','CURRENT','UNDISCLOSED')", name='ck_lifestyle_history_0'),
        CheckConstraint("alcohol_status IS NULL OR alcohol_status IN ('NEVER','FORMER','CURRENT','UNDISCLOSED')", name='ck_lifestyle_history_1'),
        CheckConstraint('sleep_hours IS NULL OR sleep_hours BETWEEN 0 AND 24', name='ck_lifestyle_history_2'),
        {'mysql_engine':'InnoDB', 'mysql_charset':'utf8mb4', 'mysql_collate':'utf8mb4_0900_ai_ci'},
    )
