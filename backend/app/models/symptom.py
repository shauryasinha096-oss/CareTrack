from sqlalchemy import Column, Integer, BigInteger, SmallInteger, String, Text, Date, Time, Numeric, Boolean, ForeignKey, CheckConstraint, UniqueConstraint, Index, text
from sqlalchemy.dialects.mysql import DATETIME
from app.database.base import Base

class Symptom(Base):
    __tablename__ = 'symptoms'
    symptom_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    symptom_name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, server_default=text('TRUE'))
    __table_args__ = (
        CheckConstraint('is_active IN (0,1)', name='ck_symptoms_0'),
        {'mysql_engine':'InnoDB', 'mysql_charset':'utf8mb4', 'mysql_collate':'utf8mb4_0900_ai_ci'},
    )
