from sqlalchemy import Column, Integer, BigInteger, SmallInteger, String, Text, Date, Time, Numeric, Boolean, ForeignKey, CheckConstraint, UniqueConstraint, Index, text
from sqlalchemy.dialects.mysql import DATETIME
from app.database.base import Base

class Appointment(Base):
    __tablename__ = 'appointments'
    appointment_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    patient_id = Column(Integer, ForeignKey('patients.patient_id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    doctor_id = Column(Integer, ForeignKey('doctors.doctor_id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    appointment_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    appointment_type = Column(String(20), nullable=False)
    status = Column(String(15), nullable=False, server_default=text("'SCHEDULED'"))
    notes = Column(Text, nullable=True)
    created_at = Column(DATETIME(fsp=6), nullable=False, server_default=text('CURRENT_TIMESTAMP(6)'))
    __table_args__ = (
        CheckConstraint("appointment_type IN ('CONSULTATION','FOLLOW_UP','ROUTINE_CHECKUP','EMERGENCY')", name='ck_appointments_0'),
        CheckConstraint("status IN ('SCHEDULED','CONFIRMED','COMPLETED','CANCELLED','NO_SHOW')", name='ck_appointments_1'),
        CheckConstraint("start_time >= '00:00:00' AND start_time < '24:00:00'", name='ck_appointments_2'),
        CheckConstraint("end_time > start_time AND end_time <= '24:00:00'", name='ck_appointments_3'),
        Index('ix_appointments_0', 'doctor_id', 'appointment_date', 'start_time', 'appointment_id'),
        Index('ix_appointments_1', 'patient_id', 'appointment_date', 'appointment_id'),
        Index('ix_appointments_2', 'appointment_date', 'status', 'appointment_id'),
        {'mysql_engine':'InnoDB', 'mysql_charset':'utf8mb4', 'mysql_collate':'utf8mb4_0900_ai_ci'},
    )
