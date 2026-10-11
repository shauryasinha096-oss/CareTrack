"""Run against seeded MySQL; per-test data is isolated by an outer transaction."""
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4
import os
from pathlib import Path
from dotenv import load_dotenv
import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from sqlalchemy import text, select, func, delete, create_engine
from sqlalchemy.orm import Session
from app.main import app
from app.database.connection import engine, get_db, SessionLocal
from app.models import *
from app.schemas import AppointmentInput, clinic_today
from app.services.records import save_appointment

@pytest.fixture
def client():
    with engine.connect() as connection:
        outer=connection.begin()
        def transaction_session():
            with Session(bind=connection,join_transaction_mode='create_savepoint',expire_on_commit=False) as db:
                try:
                    db.execute(text('SET @caretrack_user_id=NULL,@caretrack_system=NULL'))
                    yield db
                    db.commit()
                except Exception:
                    db.rollback(); raise
                finally:
                    db.execute(text('SET @caretrack_user_id=NULL,@caretrack_system=NULL')); db.commit()
        app.dependency_overrides[get_db]=transaction_session
        with TestClient(app) as c: yield c
        app.dependency_overrides.clear(); outer.rollback()

def auth(client,role='admin'):
    email={'admin':'admin','doctor':'doctor1','reception':'reception'}[role]+'@caretrack.example.com'
    response=client.post('/api/auth/login',json={'email':email,'password':'CareTrackDemo2026!'})
    assert response.status_code==200,response.text
    return {'Authorization':'Bearer '+response.json()['access_token']}

def patient_data():
    return {'first_name':'Viva','last_name':'Fictional','date_of_birth':'2000-01-01','gender':'UNDISCLOSED','phone':'0000099999','email':f'viva.{uuid4().hex}@example.com','city':'Pune'}

def test_auth_and_role_isolation(client):
    assert client.get('/api/patients').status_code==401
    assert client.post('/api/auth/login',json={'email':'admin@caretrack.example.com','password':'wrong'}).status_code==401
    reception=auth(client,'reception')
    for endpoint in ('cases','diagnoses','prescriptions','audit-logs','patients/1/history','patients/1/timeline'):
        assert client.get('/api/'+endpoint,headers=reception).status_code==403,endpoint
    for endpoint,payload in [('diagnoses',{'visit_id':1,'diagnosis_name':'Fake'}),('cases',{'patient_id':1,'doctor_id':1,'chief_complaint':'Demo'})]:
        assert client.post('/api/'+endpoint,headers=reception,json=payload).status_code==403
    assert 'notes' not in client.get('/api/appointments',headers=reception).json()['items'][0]
    follow=client.get('/api/followups',headers=reception).json()['items'][0]
    assert 'reason' not in follow and 'instructions' not in follow
    stats=client.get('/api/dashboard/statistics',headers=reception)
    assert stats.status_code==200,stats.text
    assert 'active_cases' not in stats.json()['statistics']

def test_patient_crud_validation_and_pagination(client):
    headers=auth(client)
    payload=patient_data(); response=client.post('/api/patients',headers=headers,json=payload)
    assert response.status_code==201,response.text
    pid=response.json()['patient_id']
    assert client.post('/api/patients',headers=headers,json=payload).status_code==409
    for field,value in [('email','bad-email'),('date_of_birth',(clinic_today()+timedelta(days=1)).isoformat()),('first_name','')]:
        assert client.post('/api/patients',headers=headers,json={**payload,field:value}).status_code==422
    assert client.post('/api/patients',headers=headers,json={**payload,'email':None}).status_code==201
    payload['city']='Mumbai'; assert client.put(f'/api/patients/{pid}',headers=headers,json=payload).status_code==200
    found=client.get('/api/patients',headers=headers,params={'q':payload['email']}).json()
    assert found['total']==1 and found['items'][0]['patient_id']==pid
    a=client.get('/api/patients',headers=headers,params={'page_size':5,'page':1,'sort':'first_name','direction':'asc'}).json()
    b=client.get('/api/patients',headers=headers,params={'page_size':5,'page':2,'sort':'first_name','direction':'asc'}).json()
    assert len(a['items'])==5 and not ({p['patient_id'] for p in a['items']}&{p['patient_id'] for p in b['items']})
    assert client.delete(f'/api/patients/{pid}',headers=headers).status_code==200
    assert client.get(f'/api/patients/{pid}',headers=headers).status_code==404
    assert client.delete('/api/patients/1',headers=headers).status_code==409

def test_complete_case_flow_draft_and_rollback(client):
    admin=auth(client); doctor=auth(client,'doctor'); reception=auth(client,'reception')
    pid=client.post('/api/patients',headers=reception,json=patient_data()).json()['patient_id']
    data={'patient_id':pid,'doctor_id':1,'chief_complaint':'Fictional demonstration complaint','record_state':'DRAFT','symptoms':[{'symptom_id':1,'severity':'MILD'},{'symptom_id':2,'severity':'MODERATE'}],
      'history':[{'condition_name':'Fictional earlier event'}],'allergies':[{'allergen':'Fictional material'}],
      'lifestyle':{'sleep_hours':7,'smoking_status':'UNDISCLOSED'},'vitals':{'height_cm':170,'weight_kg':65},
      'examination':{'general_appearance':'Fictional narrative'},'diagnoses':[{'diagnosis_name':'Fictional label'}],
      'prescription':{'doctor_id':1,'medicines':[{'medicine_id':1,'dosage':'Demo amount','frequency':'Demo interval','route':'Demo route','duration_days':3}]},
      'followup':{'scheduled_date':(clinic_today()+timedelta(days=7)).isoformat(),'reason':'Fictional follow-up'}}
    r=client.post('/api/cases',headers=doctor,json=data); assert r.status_code==201,r.text
    identity=r.json()['case_id']; visit_id=r.json()['visit_id']
    data['history'][0]['history_id']=r.json()['saved_ids']['history'][0]
    data['allergies'][0]['allergy_id']=r.json()['saved_ids']['allergies'][0]
    saved=client.put(f'/api/cases/{identity}/bundle',headers=doctor,json=data); assert saved.status_code==200,saved.text
    data['record_state']='SUBMITTED'
    r=client.put(f'/api/cases/{identity}/bundle',headers=doctor,json=data); assert r.status_code==200,r.text
    detail=client.get(f'/api/cases/{identity}',headers=doctor).json()
    assert detail['record_state']=='SUBMITTED' and len(detail['symptoms'])==2
    assert len(detail['visits'])==1 and detail['visits'][0]['vitals']['bmi']==22.49
    rx=detail['visits'][0]['prescription']; assert len(rx['medicines'])==1
    assert client.get(f"/api/prescriptions/{rx['prescription_id']}",headers=doctor).status_code==200
    history=client.get(f'/api/patients/{pid}/history',headers=doctor).json()
    assert len(history['medical_history'])==1 and len(history['allergies'])==1
    assert client.get(f'/api/patients/{pid}/timeline',headers=doctor).json()['total']>=5
    assert client.put(f'/api/cases/{identity}',headers=doctor,json={'case_status':'CLOSED'}).status_code==409
    fid=detail['visits'][0]['followups'][0]['follow_up_id']
    assert client.put(f'/api/followups/{fid}',headers=doctor,json={'status':'COMPLETED'}).status_code==200
    assert client.post('/api/visits',headers=doctor,json={'case_id':identity,'doctor_id':1,'chief_complaint':'Fictional subsequent encounter'}).status_code==201
    assert client.put(f'/api/cases/{identity}',headers=doctor,json={'case_status':'CLOSED'}).status_code==200
    before=client.get('/api/cases',headers=admin).json()['total']
    invalid={**data,'record_state':'SUBMITTED','symptoms':[{'symptom_id':999999,'severity':'MILD'}]}
    assert client.post('/api/cases',headers=doctor,json=invalid).status_code==404
    assert client.get('/api/cases',headers=admin).json()['total']==before

def test_reports_stored_objects_constraints_and_actor_context(client):
    headers=auth(client)
    for name in ('patients','cases','diagnoses','symptoms','medicines','appointments','followups','active-cases','closed-cases','multiple-cases','monthly-cache','doctor-statistics'):
        r=client.get('/api/reports/'+name,headers=headers); assert r.status_code==200,(name,r.text)
        assert len(r.json()['items'])>0
    assert client.get('/api/dashboard/statistics',headers=headers).status_code==200
    assert client.get('/api/cases',headers=headers,params={'q':'Fictional observation A'}).status_code==200
    with engine.connect() as conn:
        assert conn.scalar(text("SELECT calculate_age('2000-01-01')"))>=26
        assert float(conn.scalar(text('SELECT calculate_bmi(170,65)')))==22.49
        assert conn.scalar(text('SELECT patient_visit_count(1)'))>0
        assert conn.scalar(text('SELECT doctor_case_count(1)'))>0
        assert conn.scalar(text("SELECT COUNT(*) FROM information_schema.referential_constraints WHERE constraint_schema='caretrack'"))==21
    load_dotenv(Path(__file__).resolve().parents[2]/'.env')
    migration_engine=create_engine(os.environ['MYSQL_ADMIN_URL'])
    with migration_engine.connect() as conn:
        assert conn.scalar(text("SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema='caretrack'"))>=3
    migration_engine.dispose()
    user=auth(client,'doctor')
    p=client.post('/api/patients',headers=user,json=patient_data()).json()
    logs=client.get('/api/audit-logs',headers=headers,params={'q':'PATIENT'}).json()['items']
    assert any(x['entity_id']==str(p['patient_id']) and x['actor_username']=='doctor1' for x in logs)

def test_appointment_overlap_and_adjacent_slot(client):
    headers=auth(client,'reception')
    data={'patient_id':1,'doctor_id':1,'appointment_date':'2040-01-01','start_time':'09:00','end_time':'09:30'}
    first=client.post('/api/appointments',headers=headers,json=data); assert first.status_code==201,first.text
    assert client.post('/api/appointments',headers=headers,json={**data,'start_time':'09:15','end_time':'09:45'}).status_code==409
    assert client.post('/api/appointments',headers=headers,json={**data,'start_time':'09:30','end_time':'10:00'}).status_code==201
    aid=first.json()['appointment_id']
    assert client.delete(f'/api/appointments/{aid}',headers=headers).status_code==200
    assert client.post('/api/appointments',headers=headers,json=data).status_code==201

def test_concurrent_empty_schedule_is_serialized():
    barrier=Barrier(2); unique_date=date(2041,1,1)+timedelta(days=int(uuid4().hex[:4],16))
    payload=AppointmentInput(patient_id=1,doctor_id=2,appointment_date=unique_date,start_time='08:00',end_time='08:30')
    def attempt():
        with SessionLocal() as db:
            user=db.get(User,1); db.execute(text('SET @caretrack_user_id=1,@caretrack_system=NULL'))
            barrier.wait()
            try:
                row=save_appointment(db,user,payload); db.commit(); return ('ok',row['appointment_id'])
            except HTTPException as e: db.rollback(); return ('conflict',e.status_code)
    with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(lambda _:attempt(),range(2)))
    assert sorted(r[0] for r in results)==['conflict','ok'],results
    created=[r[1] for r in results if r[0]=='ok']
    with SessionLocal() as db: db.execute(delete(Appointment).where(Appointment.appointment_id.in_(created))); db.commit()

def test_encounter_sections_and_database_guards(client):
    from sqlalchemy.exc import DBAPIError
    headers=auth(client); reception=auth(client,'reception')
    pid=client.post('/api/patients',headers=headers,json=patient_data()).json()['patient_id']
    result=client.post('/api/cases',headers=headers,json={'patient_id':pid,'doctor_id':1,'chief_complaint':'Fictional measurements test','record_state':'SUBMITTED'})
    assert result.status_code==201,result.text
    vid=result.json()['visit_id']
    assert client.put(f'/api/visits/{vid}/vitals',headers=reception,json={'height_cm':170}).status_code==403
    assert client.put(f'/api/visits/{vid}/vitals',headers=headers,json={'height_cm':170,'weight_kg':65}).status_code==200
    assert client.put(f'/api/visits/{vid}/vitals',headers=headers,json={'height_cm':170,'weight_kg':68}).status_code==200
    assert client.put(f'/api/visits/{vid}/examination',headers=headers,json={'general_appearance':'Fictional test narrative'}).status_code==200
    assert client.get(f'/api/visits/{vid}',headers=headers).json()['vitals']['bmi']==23.53
    assert client.put(f'/api/visits/{vid}/vitals',headers=headers,json={'oxygen_saturation':101}).status_code==422
    # Bypass Pydantic to prove MySQL itself enforces the constraints.
    with engine.connect() as conn:
        tx=conn.begin();conn.execute(text('SET @caretrack_user_id=1,@caretrack_system=NULL'))
        invalid=[
            "INSERT INTO patients(first_name,last_name,date_of_birth,gender,phone) VALUES('Demo','Future','2999-01-01','UNDISCLOSED','0000000000')",
            "UPDATE doctors SET license_number=(SELECT license_number FROM (SELECT license_number FROM doctors WHERE doctor_id=1) x) WHERE doctor_id=2",
            "UPDATE vital_signs SET height_cm=-1 WHERE vital_id=1",
            "INSERT INTO users(username,email,password_hash,role) VALUES('bad_role_demo','bad.role@example.com','not-a-real-password','UNKNOWN')",
            "INSERT INTO case_symptoms(case_id,symptom_id,severity) VALUES(999999,1,'MILD')",
        ]
        for sql in invalid:
            with pytest.raises(DBAPIError) as caught:
                with conn.begin_nested(): conn.execute(text(sql))
            assert caught.value.orig.args[0] in (1062,1452,1644,3819),caught.value
        tx.rollback()

def test_admin_account_provisioning_is_atomic_and_disable_is_immediate(client):
    headers=auth(client); reception=auth(client,'reception'); suffix=uuid4().hex[:12]
    data={'username':'demo_'+suffix,'login_email':f'login.{suffix}@example.com','password':'FictionalPassword2026!',
        'first_name':'Demo','last_name':'Doctor','specialization':'Educational practice','license_number':'DEMO-'+suffix,
        'phone':'0000000011','email':f'professional.{suffix}@example.com'}
    assert client.post('/api/doctors',headers=reception,json=data).status_code==403
    result=client.post('/api/doctors',headers=headers,json=data);assert result.status_code==201,result.text
    doctor=result.json(); uid=doctor['user_id']
    assert 'password_hash' not in doctor
    duplicate={**data,'username':'second_'+suffix,'login_email':f'second.{suffix}@example.com'}
    before=client.get('/api/users',headers=headers).json()['total']
    assert client.post('/api/doctors',headers=headers,json=duplicate).status_code==409
    assert client.get('/api/users',headers=headers).json()['total']==before
    result=client.post('/api/auth/login',json={'email':data['login_email'],'password':data['password']})
    assert result.status_code==200
    token={'Authorization':'Bearer '+result.json()['access_token']}
    assert client.get('/api/auth/me',headers=token).status_code==200
    assert client.put(f'/api/users/{uid}',headers=headers,json={'is_active':False}).status_code==200
    assert client.get('/api/auth/me',headers=token).status_code==401
    assert client.post('/api/auth/login',json={'email':data['login_email'],'password':data['password']}).status_code==401
