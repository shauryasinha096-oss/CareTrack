from sqlalchemy import Column, Integer, BigInteger, SmallInteger, String, Text, Date, Time, Numeric, Boolean, ForeignKey, CheckConstraint, UniqueConstraint, Index, text
from sqlalchemy.dialects.mysql import DATETIME
from app.database.base import Base

class MedicalCase(Base):
    __tablename__ = 'medical_cases'
    case_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    patient_id = Column(Integer, ForeignKey('patients.patient_id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    doctor_id = Column(Integer, ForeignKey('doctors.doctor_id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    case_date = Column(Date, nullable=False)
    chief_complaint = Column(Text, nullable=False)
    present_illness = Column(Text, nullable=True)
    case_status = Column(String(20), nullable=False, server_default=text("'OPEN'"))
    priority = Column(String(10), nullable=False, server_default=text("'MEDIUM'"))
    record_state = Column(String(10), nullable=False, server_default=text("'DRAFT'"))
    notes = Column(Text, nullable=True)
    created_at = Column(DATETIME(fsp=6), nullable=False, server_default=text('CURRENT_TIMESTAMP(6)'))
    updated_at = Column(DATETIME(fsp=6), nullable=False, server_default=text('CURRENT_TIMESTAMP(6)'))
    __table_args__ = (
        CheckConstraint("case_status IN ('OPEN','UNDER_REVIEW','FOLLOW_UP','CLOSED')", name='ck_medical_cases_0'),
        CheckConstraint("priority IN ('LOW','MEDIUM','HIGH','URGENT')", name='ck_medical_cases_1'),
        CheckConstraint("record_state IN ('DRAFT','SUBMITTED')", name='ck_medical_cases_2'),
        CheckConstraint("record_state = 'DRAFT' OR CHAR_LENGTH(TRIM(chief_complaint)) > 0", name='ck_medical_cases_3'),
        CheckConstraint("record_state <> 'DRAFT' OR case_status = 'OPEN'", name='ck_medical_cases_4'),
        Index('ix_medical_cases_0', 'patient_id', 'case_date', 'case_id'),
        Index('ix_medical_cases_1', 'doctor_id', 'record_state', 'case_status', 'case_date', 'case_id'),
        Index('ix_medical_cases_2', 'record_state', 'case_status', 'case_date', 'case_id'),
        Index('ix_medical_cases_3', 'case_date', 'case_id'),
        {'mysql_engine':'InnoDB', 'mysql_charset':'utf8mb4', 'mysql_collate':'utf8mb4_0900_ai_ci'},
    )

class CaseSymptom(Base):
    __tablename__ = 'case_symptoms'
    case_id = Column(Integer, ForeignKey('medical_cases.case_id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, autoincrement=False, nullable=False)
    symptom_id = Column(Integer, ForeignKey('symptoms.symptom_id', ondelete='RESTRICT', onupdate='CASCADE'), primary_key=True, autoincrement=False, nullable=False)
    severity = Column(String(10), nullable=False)
    duration = Column(String(80), nullable=True)
    frequency = Column(String(80), nullable=True)
    notes = Column(Text, nullable=True)
    recorded_at = Column(DATETIME(fsp=6), nullable=False, server_default=text('CURRENT_TIMESTAMP(6)'))
    __table_args__ = (
        CheckConstraint("severity IN ('MILD','MODERATE','SEVERE')", name='ck_case_symptoms_0'),
        Index('ix_case_symptoms_0', 'symptom_id', 'case_id'),
        {'mysql_engine':'InnoDB', 'mysql_charset':'utf8mb4', 'mysql_collate':'utf8mb4_0900_ai_ci'},
    )
