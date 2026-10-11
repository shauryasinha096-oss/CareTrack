from sqlalchemy import Column, Integer, BigInteger, SmallInteger, String, Text, Date, Time, Numeric, Boolean, ForeignKey, CheckConstraint, UniqueConstraint, Index, text
from sqlalchemy.dialects.mysql import DATETIME
from app.database.base import Base

class Medicine(Base):
    __tablename__ = 'medicines'
    medicine_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    medicine_code = Column(String(40), nullable=False, unique=True)
    medicine_name = Column(String(150), nullable=False)
    generic_name = Column(String(150), nullable=False)
    manufacturer = Column(String(150), nullable=False)
    medicine_type = Column(String(15), nullable=False)
    strength = Column(String(50), nullable=False)
    form = Column(String(50), nullable=False)
    is_active = Column(Boolean, nullable=False, server_default=text('TRUE'))
    __table_args__ = (
        CheckConstraint("medicine_type IN ('TABLET','CAPSULE','SYRUP','INJECTION','CREAM','DROPS')", name='ck_medicines_0'),
        CheckConstraint('is_active IN (0,1)', name='ck_medicines_1'),
        Index('ix_medicines_0', 'medicine_name', 'medicine_id'),
        {'mysql_engine':'InnoDB', 'mysql_charset':'utf8mb4', 'mysql_collate':'utf8mb4_0900_ai_ci'},
    )
