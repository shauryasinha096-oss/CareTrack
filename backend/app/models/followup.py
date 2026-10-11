from sqlalchemy import Column, Integer, BigInteger, SmallInteger, String, Text, Date, Time, Numeric, Boolean, ForeignKey, CheckConstraint, UniqueConstraint, Index, text
from sqlalchemy.dialects.mysql import DATETIME
from app.database.base import Base

class FollowUp(Base):
    __tablename__ = 'follow_ups'
    follow_up_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    visit_id = Column(Integer, ForeignKey('visits.visit_id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    scheduled_date = Column(Date, nullable=False)
    actual_date = Column(Date, nullable=True)
    status = Column(String(15), nullable=False, server_default=text("'PENDING'"))
    reason = Column(String(255), nullable=False)
    instructions = Column(Text, nullable=True)
    __table_args__ = (
        CheckConstraint("status IN ('PENDING','COMPLETED','MISSED','CANCELLED')", name='ck_follow_ups_0'),
        CheckConstraint("(status = 'COMPLETED' AND actual_date IS NOT NULL) OR (status <> 'COMPLETED' AND actual_date IS NULL)", name='ck_follow_ups_1'),
        Index('ix_follow_ups_0', 'status', 'scheduled_date', 'follow_up_id'),
        Index('ix_follow_ups_1', 'visit_id'),
        {'mysql_engine':'InnoDB', 'mysql_charset':'utf8mb4', 'mysql_collate':'utf8mb4_0900_ai_ci'},
    )
