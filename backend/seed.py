"""Deterministic, fictional-only data, with valid references and non-overlapping slots."""
from datetime import datetime, timedelta, time, timezone
import os
from sqlalchemy import select, func, text, or_
from app.database.connection import SessionLocal
from app.database.settings import DatabaseSettings
from app.models import *
from app.schemas import clinic_today
from app.utils.security import hash_password

FIRST=['Aarav','Riya','Kabir','Ananya','Vivaan','Meera','Arjun','Ishita','Dev','Kiara','Reyansh','Avni','Dhruv','Tara','Aditya','Nisha','Ishan','Kavya','Neil','Sana','Ayaan','Diya','Krish','Maya','Rohan','Leela','Ved','Sia','Yash','Ruhi']
LAST=['Mehta','Shah','Patel','Desai','Joshi','Trivedi','Kapoor','Rao','Verma','Iyer','Sethi','Bhat','Soni','Malhotra','Kulkarni','Nair','Bansal','Jain','Reddy','Sen']
CITIES=['Ahmedabad','Mumbai','Pune','Surat','Vadodara','Delhi','Bengaluru','Jaipur','Indore','Nashik']
SYMPTOMS=['Headache','Fever','Cough','Fatigue','Nausea','Vomiting','Dizziness','Chest discomfort','Shortness of breath','Abdominal pain','Back pain','Joint pain','Sore throat','Runny nose','Skin rash','Weakness','Body ache','Loss of appetite','Sneezing','Congestion','Dry mouth','Itching','Muscle stiffness','Watery eyes','Restlessness','Chills','Night sweats','Hoarseness','Ear discomfort','Bloating','Indigestion','Palpitations','Sleep disturbance','Dry skin','Tingling','Eye discomfort','Neck discomfort','Swelling','Dry cough','Reduced energy']

def demo_password():
    value = os.getenv('DEMO_PASSWORD')
    if not value and DatabaseSettings().url().host in ('localhost', '127.0.0.1', '::1'):
        value = 'CareTrackDemo2026!'
    if not value or len(value) < 12:
        raise RuntimeError('Set DEMO_PASSWORD to at least 12 characters before creating hosted demo accounts')
    return value


def ensure_demo_accounts(db):
    """Add missing natural-key accounts; never reset a password or change a role."""
    encoded = None
    created = 0
    accounts = [('admin', 'ADMIN'), ('reception', 'RECEPTIONIST')]
    accounts += [(f'doctor{i+1}', 'DOCTOR') for i in range(20)]
    for username, role in accounts:
        email = username + '@caretrack.example.com'
        matches = db.scalars(select(User).where(or_(User.email == email, User.username == username))).all()
        if matches:
            if len(matches) != 1 or matches[0].email != email or matches[0].username != username or matches[0].role != role:
                raise RuntimeError(f'Demo identity collision for {username}; existing identity preserved. Resolve manually before retrying.')
            user = matches[0]
        else:
            if encoded is None:
                encoded = hash_password(demo_password())
            user = User(username=username, email=email, password_hash=encoded, role=role)
            db.add(user)
            db.flush()
            created += 1
        if role == 'DOCTOR' and not db.scalar(select(Doctor).where(Doctor.user_id == user.user_id)):
            i = int(username[6:]) - 1
            license_number = f'DEMO-LIC-{i+1:03}'
            professional_email = f'professional.doctor{i+1}@example.com'
            if db.scalar(select(Doctor).where(or_(Doctor.license_number == license_number, Doctor.email == professional_email))):
                raise RuntimeError(f'Demo doctor identity collision for {username}; existing doctor preserved')
            db.add(Doctor(user_id=user.user_id, first_name=FIRST[i], last_name=LAST[i],
                          specialization='Educational cases', license_number=license_number,
                          phone=f'000000{i+1:04}', email=professional_email))
            db.flush()
    return created


def seed():
    today=clinic_today(); now=datetime.now(timezone.utc).replace(tzinfo=None)
    with SessionLocal() as db:
        # Fixed IDs in the full teaching graph are safe only when EVERY source table is empty.
        populated = any(db.scalar(select(func.count()).select_from(model))
                        for name, model in MODELS.items()
                        if name != 'monthly_case_statistics')
        if populated:
            created = ensure_demo_accounts(db)
            db.commit()
            print(f'Existing dataset preserved; {created} missing fictional login accounts added. Existing passwords unchanged.')
            return
        db.execute(text("SET @caretrack_user_id=NULL, @caretrack_system='SEED'"))
        encoded=hash_password(demo_password())
        db.add_all([User(user_id=1,username='admin',email='admin@caretrack.example.com',password_hash=encoded,role='ADMIN'),User(user_id=2,username='reception',email='reception@caretrack.example.com',password_hash=encoded,role='RECEPTIONIST')]); db.flush()
        for i in range(20):
            uid=i+3
            db.add(User(user_id=uid,username=f'doctor{i+1}',email=f'doctor{i+1}@caretrack.example.com',password_hash=encoded,role='DOCTOR'))
        db.flush()
        for i in range(20):
            db.add(Doctor(doctor_id=i+1,user_id=i+3,first_name=FIRST[i],last_name=LAST[i],specialization=['General practice','Family practice','Internal medicine','Educational cases'][i%4],license_number=f'DEMO-LIC-{i+1:03}',phone=f'000000{i+1:04}',email=f'professional.doctor{i+1}@example.com'))
        for i in range(150):
            db.add(Patient(patient_id=i+1,first_name=FIRST[i%30],last_name=LAST[(i//30+i)%20],date_of_birth=today.replace(year=today.year-20-i%49,month=1+i%12,day=1+i%27),gender=['MALE','FEMALE','UNDISCLOSED'][i%3],blood_group=['A+','B+','O+','AB+'][i%4],phone=f'000001{i+1:04}',email=f'fictional.patient{i+1}@example.com',address=f'{i+1} Fictional Demo Lane',city=CITIES[i%10],occupation=['Student','Designer','Teacher','Engineer','Researcher'][i%5],marital_status='UNDISCLOSED',created_at=now-timedelta(days=(i*11)%330)))
        for i,name in enumerate(SYMPTOMS): db.add(Symptom(symptom_id=i+1,symptom_name=name,description='Fictional educational vocabulary entry'))
        for i in range(40): db.add(Medicine(medicine_id=i+1,medicine_code=f'DEMO-MED-{i+1:03}',medicine_name=f'DemoCare {i+1:02}',generic_name=f'Fictional compound {chr(65+i%26)}{i//26}',manufacturer='Imaginary Learning Labs',medicine_type=['TABLET','CAPSULE','SYRUP','CREAM','DROPS'][i%5],strength='Demo strength only',form=['Coated tablet','Gel capsule','Liquid','Topical cream','Drop solution'][i%5]))
        db.flush()
        cases=[]
        for i in range(250):
            day=today-timedelta(days=(i*7)%350)
            case=MedicalCase(case_id=i+1,patient_id=i%150+1,doctor_id=i%20+1,case_date=day,chief_complaint=f'Fictional case study: {SYMPTOMS[i%40].lower()}',present_illness='Synthetic narrative for the DBMS demonstration. No real patient information.',case_status='OPEN',priority=['LOW','MEDIUM','MEDIUM','HIGH','URGENT'][i%5],record_state='DRAFT',created_at=datetime.combine(day,time(3,30)))
            db.add(case); cases.append(case)
        db.flush()
        for i in range(400):
            ci=i if i<250 else i-250
            case=cases[ci]
            vd=case.case_date+timedelta(days=0 if i<250 else min(7,(today-case.case_date).days))
            db.add(Visit(visit_id=i+1,case_id=ci+1,doctor_id=case.doctor_id,visit_date=datetime.combine(vd,time(3,30)),visit_type='INITIAL_CONSULTATION' if i<250 else 'FOLLOW_UP',chief_complaint=case.chief_complaint,doctor_notes='Fictional encounter notes for educational demonstration.',created_at=datetime.combine(vd,time(3,30))))
        db.flush()
        for i,case in enumerate(cases):
            for j in range(3): db.add(CaseSymptom(case_id=case.case_id,symptom_id=(i+j*7)%40+1,severity=['MILD','MODERATE','SEVERE'][(i+j)%3],duration=f'{1+(i+j)%14} demo days',frequency='Reported in fictional case',recorded_at=datetime.combine(case.case_date,time(3,30))))
        for i in range(300):
            vid=i+1 if i<250 else i-249
            db.add(Diagnosis(visit_id=vid,diagnosis_name=f'Fictional observation {chr(65+i%12)}',diagnosis_type='PRIMARY' if i<250 else 'SECONDARY',notes='Synthetic label, not a medical conclusion.'))
        for i in range(250):
            db.add(VitalSign(visit_id=i+1,temperature=36.5+(i%7)/10,systolic_bp=110+i%20,diastolic_bp=70+i%10,heart_rate=65+i%20,respiratory_rate=14+i%5,oxygen_saturation=96+i%4,height_cm=155+i%30,weight_kg=50+i%35))
            db.add(Examination(visit_id=i+1,general_appearance='Fictional structured examination entry.',other_findings='Educational record; no diagnostic assessment.'))
        for i in range(200): db.add(Prescription(prescription_id=i+1,visit_id=i+1,doctor_id=cases[i].doctor_id,prescription_date=cases[i].case_date,notes='DEMO ONLY — fictional products and regimen text. Not treatment advice.'))
        db.flush()
        for i in range(200):
            for j in range(3): db.add(PrescriptionMedicine(prescription_id=i+1,medicine_id=(i+j*9)%40+1,dosage='Fictional demo amount',frequency='Demo frequency',route='Demo route',duration_days=3+i%7,instructions='Non-actionable educational example only.'))
        for i in range(300):
            day=today+timedelta(days=i//20-7)
            db.add(Appointment(patient_id=i%150+1,doctor_id=i%20+1,appointment_date=day,start_time=time(10,0),end_time=time(10,30),appointment_type=['CONSULTATION','FOLLOW_UP','ROUTINE_CHECKUP'][i%3],status=['COMPLETED','NO_SHOW','CANCELLED'][i%3] if day<today else ['SCHEDULED','CONFIRMED'][i%2],notes='Synthetic scheduling record'))
        for i in range(150):
            closed=i%5==4
            db.add(FollowUp(visit_id=i+1,scheduled_date=today+timedelta(days=i%21),actual_date=today if closed else None,status='COMPLETED' if closed else 'PENDING',reason='Fictional educational follow-up plan',instructions='Demo only; no medical advice.'))
        for i in range(200): db.add(MedicalHistory(patient_id=i%150+1,condition_name=f'Mock historical condition {i%15+1}',diagnosed_date=today-timedelta(days=400+i),treatment='Fictional prior record',notes='Synthetic history episode'))
        for i in range(100): db.add(Allergy(patient_id=i+1,allergen=f'Fictional allergen {i%8+1}',allergy_type=['FOOD','ENVIRONMENTAL','MEDICATION','OTHER'][i%4],reaction='Demo reaction description',severity=['MILD','MODERATE'][i%2]))
        for i in range(150): db.add(LifestyleHistory(patient_id=i+1,smoking_status='UNDISCLOSED',alcohol_status='UNDISCLOSED',exercise_frequency='Demo entry',sleep_hours=7+i%2,diet_type='Demo preference'))
        db.flush()
        for i,case in enumerate(cases): case.record_state='SUBMITTED'; case.case_status=['OPEN','UNDER_REVIEW','FOLLOW_UP','OPEN','CLOSED'][i%5]
        db.flush(); db.commit()
        db.execute(text('CALL refresh_monthly_case_statistics()')); db.commit()
        counts={name:db.scalar(select(func.count()).select_from(model)) for name,model in MODELS.items()}
        db.execute(text('SET @caretrack_user_id=NULL, @caretrack_system=NULL')); db.commit()
    print('Seed complete (fictional only): '+', '.join(f'{k}={v}' for k,v in counts.items()))

if __name__ == '__main__':
    # Use the same cross-process initialization lock as the documented CLI.
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
    from database import initialize
    initialize(seed_only=True)
