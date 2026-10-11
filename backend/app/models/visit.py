from sqlalchemy import Column, Integer, BigInteger, SmallInteger, String, Text, Date, Time, Numeric, Boolean, ForeignKey, CheckConstraint, UniqueConstraint, Index, text
from sqlalchemy.dialects.mysql import DATETIME
from app.database.base import Base

class Visit(Base):
    __tablename__ = 'visits'
    visit_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    case_id = Column(Integer, ForeignKey('medical_cases.case_id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    doctor_id = Column(Integer, ForeignKey('doctors.doctor_id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    visit_date = Column(DATETIME(fsp=6), nullable=False)
    visit_type = Column(String(25), nullable=False)
    chief_complaint = Column(Text, nullable=False)
    doctor_notes = Column(Text, nullable=True)
    created_at = Column(DATETIME(fsp=6), nullable=False, server_default=text('CURRENT_TIMESTAMP(6)'))
    __table_args__ = (
        CheckConstraint("visit_type IN ('INITIAL_CONSULTATION','FOLLOW_UP','EMERGENCY','ROUTINE_CHECKUP')", name='ck_visits_0'),
        Index('ix_visits_0', 'case_id', 'visit_date', 'visit_id'),
        Index('ix_visits_1', 'doctor_id', 'visit_date', 'visit_id'),
        Index('ix_visits_2', 'visit_date', 'visit_id'),
        {'mysql_engine':'InnoDB', 'mysql_charset':'utf8mb4', 'mysql_collate':'utf8mb4_0900_ai_ci'},
    )

class VitalSign(Base):
    __tablename__ = 'vital_signs'
    vital_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    visit_id = Column(Integer, ForeignKey('visits.visit_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, unique=True)
    temperature = Column(Numeric(5, 2), nullable=True)
    systolic_bp = Column(SmallInteger, nullable=True)
    diastolic_bp = Column(SmallInteger, nullable=True)
    heart_rate = Column(SmallInteger, nullable=True)
    respiratory_rate = Column(SmallInteger, nullable=True)
    oxygen_saturation = Column(Numeric(5, 2), nullable=True)
    height_cm = Column(Numeric(6, 2), nullable=True)
    weight_kg = Column(Numeric(6, 2), nullable=True)
    __table_args__ = (
        CheckConstraint('temperature IS NULL OR temperature > 0', name='ck_vital_signs_0'),
        CheckConstraint('systolic_bp IS NULL OR systolic_bp > 0', name='ck_vital_signs_1'),
        CheckConstraint('diastolic_bp IS NULL OR diastolic_bp > 0', name='ck_vital_signs_2'),
        CheckConstraint('heart_rate IS NULL OR heart_rate > 0', name='ck_vital_signs_3'),
        CheckConstraint('respiratory_rate IS NULL OR respiratory_rate > 0', name='ck_vital_signs_4'),
        CheckConstraint('oxygen_saturation IS NULL OR oxygen_saturation BETWEEN 0 AND 100', name='ck_vital_signs_5'),
        CheckConstraint('height_cm IS NULL OR height_cm > 0', name='ck_vital_signs_6'),
        CheckConstraint('weight_kg IS NULL OR weight_kg > 0', name='ck_vital_signs_7'),
        {'mysql_engine':'InnoDB', 'mysql_charset':'utf8mb4', 'mysql_collate':'utf8mb4_0900_ai_ci'},
    )

class Examination(Base):
    __tablename__ = 'examinations'
    examination_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    visit_id = Column(Integer, ForeignKey('visits.visit_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, unique=True)
    general_appearance = Column(Text, nullable=True)
    cardiovascular_findings = Column(Text, nullable=True)
    respiratory_findings = Column(Text, nullable=True)
    neurological_findings = Column(Text, nullable=True)
    abdominal_findings = Column(Text, nullable=True)
    skin_findings = Column(Text, nullable=True)
    other_findings = Column(Text, nullable=True)
    __table_args__ = (
        {'mysql_engine':'InnoDB', 'mysql_charset':'utf8mb4', 'mysql_collate':'utf8mb4_0900_ai_ci'},
    )
