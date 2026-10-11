from sqlalchemy import Column, Integer, BigInteger, SmallInteger, String, Text, Date, Time, Numeric, Boolean, ForeignKey, CheckConstraint, UniqueConstraint, Index, text
from sqlalchemy.dialects.mysql import DATETIME
from app.database.base import Base

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    audit_id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
    actor_username = Column(String(50), nullable=False)
    action = Column(String(20), nullable=False)
    entity_type = Column(String(40), nullable=False)
    entity_id = Column(String(64), nullable=False)
    description = Column(String(500), nullable=False)
    created_at = Column(DATETIME(fsp=6), nullable=False, server_default=text('CURRENT_TIMESTAMP(6)'))
    __table_args__ = (
        CheckConstraint("action IN ('INSERT','UPDATE','DELETE','CLOSE','LOGIN','DEACTIVATE','REFRESH')", name='ck_audit_logs_0'),
        Index('ix_audit_logs_0', 'created_at', 'audit_id'),
        Index('ix_audit_logs_1', 'user_id', 'created_at', 'audit_id'),
        Index('ix_audit_logs_2', 'entity_type', 'entity_id', 'created_at', 'audit_id'),
        {'mysql_engine':'InnoDB', 'mysql_charset':'utf8mb4', 'mysql_collate':'utf8mb4_0900_ai_ci'},
    )
