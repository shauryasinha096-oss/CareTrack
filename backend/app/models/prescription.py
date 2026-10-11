from sqlalchemy import Column, Integer, BigInteger, SmallInteger, String, Text, Date, Time, Numeric, Boolean, ForeignKey, CheckConstraint, UniqueConstraint, Index, text
from sqlalchemy.dialects.mysql import DATETIME
from app.database.base import Base

class Prescription(Base):
    __tablename__ = 'prescriptions'
    prescription_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    visit_id = Column(Integer, ForeignKey('visits.visit_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, unique=True)
    doctor_id = Column(Integer, ForeignKey('doctors.doctor_id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    prescription_date = Column(Date, nullable=False)
    notes = Column(Text, nullable=True)
    __table_args__ = (
        Index('ix_prescriptions_0', 'doctor_id', 'prescription_date', 'prescription_id'),
        Index('ix_prescriptions_1', 'prescription_date', 'prescription_id'),
        {'mysql_engine':'InnoDB', 'mysql_charset':'utf8mb4', 'mysql_collate':'utf8mb4_0900_ai_ci'},
    )

class PrescriptionMedicine(Base):
    __tablename__ = 'prescription_medicines'
    prescription_id = Column(Integer, ForeignKey('prescriptions.prescription_id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, autoincrement=False, nullable=False)
    medicine_id = Column(Integer, ForeignKey('medicines.medicine_id', ondelete='RESTRICT', onupdate='CASCADE'), primary_key=True, autoincrement=False, nullable=False)
    dosage = Column(String(100), nullable=False)
    frequency = Column(String(100), nullable=False)
    route = Column(String(50), nullable=False)
    duration_days = Column(SmallInteger, nullable=False)
    instructions = Column(Text, nullable=True)
    __table_args__ = (
        CheckConstraint('duration_days > 0', name='ck_prescription_medicines_0'),
        Index('ix_prescription_medicines_0', 'medicine_id', 'prescription_id'),
        {'mysql_engine':'InnoDB', 'mysql_charset':'utf8mb4', 'mysql_collate':'utf8mb4_0900_ai_ci'},
    )
