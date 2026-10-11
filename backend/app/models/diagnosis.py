from sqlalchemy import Column, Integer, BigInteger, SmallInteger, String, Text, Date, Time, Numeric, Boolean, ForeignKey, CheckConstraint, UniqueConstraint, Index, text
from sqlalchemy.dialects.mysql import DATETIME
from app.database.base import Base

class Diagnosis(Base):
    __tablename__ = 'diagnoses'
    diagnosis_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    visit_id = Column(Integer, ForeignKey('visits.visit_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    diagnosis_name = Column(String(150), nullable=False)
    diagnosis_type = Column(String(15), nullable=False, server_default=text("'PRIMARY'"))
    notes = Column(Text, nullable=True)
    __table_args__ = (
        UniqueConstraint('visit_id', 'diagnosis_name', 'diagnosis_type', name='uq_diagnoses_group_0'),
        CheckConstraint("diagnosis_type IN ('PRIMARY','SECONDARY','DIFFERENTIAL')", name='ck_diagnoses_0'),
        Index('ix_diagnoses_0', 'diagnosis_name', 'visit_id'),
        {'mysql_engine':'InnoDB', 'mysql_charset':'utf8mb4', 'mysql_collate':'utf8mb4_0900_ai_ci'},
    )
