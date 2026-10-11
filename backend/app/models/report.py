from sqlalchemy import Column, Integer, BigInteger, SmallInteger, String, Text, Date, Time, Numeric, Boolean, ForeignKey, CheckConstraint, UniqueConstraint, Index, text
from sqlalchemy.dialects.mysql import DATETIME
from app.database.base import Base

class MonthlyCaseStatistic(Base):
    __tablename__ = 'monthly_case_statistics'
    stat_month = Column(Date, primary_key=True, autoincrement=False, nullable=False)
    total_cases = Column(Integer, nullable=False, server_default=text('0'))
    unique_patients = Column(Integer, nullable=False, server_default=text('0'))
    completed_cases = Column(Integer, nullable=False, server_default=text('0'))
    refreshed_at = Column(DATETIME(fsp=6), nullable=False)
    __table_args__ = (
        CheckConstraint('DAYOFMONTH(stat_month) = 1', name='ck_monthly_case_statistics_0'),
        CheckConstraint('total_cases >= 0', name='ck_monthly_case_statistics_1'),
        CheckConstraint('unique_patients BETWEEN 0 AND total_cases', name='ck_monthly_case_statistics_2'),
        CheckConstraint('completed_cases BETWEEN 0 AND total_cases', name='ck_monthly_case_statistics_3'),
        {'mysql_engine':'InnoDB', 'mysql_charset':'utf8mb4', 'mysql_collate':'utf8mb4_0900_ai_ci'},
    )
