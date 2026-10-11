from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database.connection import get_db, engine
from app.models import User
from app.utils.security import current_user, roles
from app.services.analytics import dashboard, report, rows

router=APIRouter(prefix='/api',tags=['Analytics'])

@router.get('/dashboard/statistics')
def statistics(db:Session=Depends(get_db),user:User=Depends(current_user)): return dashboard(db,user)

@router.get('/reports/monthly-cache')
def monthly_cache(db:Session=Depends(get_db),user:User=Depends(current_user)):
    roles(user,'ADMIN'); return {'items':rows(db,'SELECT * FROM monthly_case_statistics ORDER BY stat_month',{}),'notice':'Precomputed summary; see refreshed_at. Completed means currently CLOSED in the case-date cohort.'}

@router.post('/reports/monthly-cache/refresh')
def refresh(user:User=Depends(current_user)):
    roles(user,'ADMIN')
    # The refresh procedure owns its transaction on an independent connection.
    with engine.connect().execution_options(isolation_level='AUTOCOMMIT') as conn: conn.execute(text('CALL refresh_monthly_case_statistics()'))
    return {'message':'Monthly statistics refreshed'}

@router.get('/reports/doctor-statistics')
def doctor_statistics(db:Session=Depends(get_db),user:User=Depends(current_user)):
    roles(user,'ADMIN','DOCTOR')
    from app.services.records import doctor_id
    return {'items':rows(db,'SELECT * FROM doctor_case_statistics WHERE (:did IS NULL OR doctor_id=:did)',{'did':doctor_id(db,user) if user.role=='DOCTOR' else None})}

@router.get('/reports/{name}')
def get_report(name:str,page:int=Query(1,ge=1),page_size:int=Query(20,ge=1,le=100),date_from:date|None=None,date_to:date|None=None,q:str=Query('',max_length=200),sort:str='total',direction:str='desc',doctor_id:int|None=None,db:Session=Depends(get_db),user:User=Depends(current_user)):
    return report(db,user,name,page,page_size,date_from,date_to,q,sort,direction,doctor_id)
