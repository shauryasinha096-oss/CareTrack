from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, text, delete
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models import *
from app.schemas import *
from app.services.records import *
from app.utils.security import current_user, roles, verify_password, create_token, hash_password

router=APIRouter(prefix='/api')

@router.post('/auth/login',tags=['Authentication'])
def login(payload: Login,db: Session=Depends(get_db)):
    user=db.scalar(select(User).where(User.email==payload.email.lower()))
    if not user or not user.is_active or not verify_password(payload.password,user.password_hash): raise HTTPException(401,'Email or password is incorrect')
    audit(db,user,'LOGIN','USER',user.user_id,'Application sign-in')
    return {'access_token':create_token(user),'token_type':'bearer','user':record_dict(user)}

@router.get('/auth/me',tags=['Authentication'])
def me(user: User=Depends(current_user)): return record_dict(user)

def register_listing(path,resource):
    def endpoint(page: int=Query(1,ge=1),page_size: int=Query(20,ge=1,le=100),q: str=Query('',max_length=200),status: str|None=None,doctor_id: int|None=None,patient_id: int|None=None,date_from: date|None=None,date_to: date|None=None,sort: str|None=None,direction: Literal['asc','desc']='desc',case_id: int|None=None,visit_id: int|None=None,db: Session=Depends(get_db),user: User=Depends(current_user)):
        return list_records(db,user,resource,page,page_size,q,status,doctor_id,patient_id,date_from,date_to,sort,direction,case_id,visit_id)
    endpoint.__name__='list_'+resource
    router.add_api_route('/'+path,endpoint,methods=['GET'],tags=[path.title()])

for path,resource in [('patients','patients'),('cases','medical_cases'),('visits','visits'),('appointments','appointments'),('symptoms','symptoms'),('diagnoses','diagnoses'),('medicines','medicines'),('prescriptions','prescriptions'),('followups','follow_ups'),('doctors','doctors'),('audit-logs','audit_logs'),('users','users')]: register_listing(path,resource)

@router.get('/patients/{identity}')
def patient_detail(identity:int,db:Session=Depends(get_db),user:User=Depends(current_user)):
    result=record_dict(must_get(db,Patient,identity))
    result['age']=db.scalar(select(func.calculate_age(Patient.date_of_birth)).where(Patient.patient_id==identity))
    return result

@router.post('/patients',status_code=201)
def create_patient(payload:PatientInput,db:Session=Depends(get_db),user:User=Depends(current_user)):
    row=Patient(**payload.model_dump()); db.add(row); db.flush(); return record_dict(row)

@router.put('/patients/{identity}')
def update_patient(identity:int,payload:PatientInput,db:Session=Depends(get_db),user:User=Depends(current_user)):
    if user.role=='DOCTOR': require_patient(db,user,identity)
    row=must_get(db,Patient,identity,lock=True)
    for k,v in payload.model_dump().items(): setattr(row,k,v)
    db.flush(); return record_dict(row)

@router.delete('/patients/{identity}')
def delete_patient(identity:int,db:Session=Depends(get_db),user:User=Depends(current_user)):
    roles(user,'ADMIN'); row=must_get(db,Patient,identity,lock=True)
    audit(db,user,'DELETE','PATIENT',identity,'Unused fictional patient deleted; owned extensions cascade')
    db.delete(row); db.flush(); return {'message':'Patient deleted'}

@router.get('/patients/{identity}/history')
def patient_history(identity:int,page:int=Query(1,ge=1),page_size:int=Query(20,ge=1,le=100),db:Session=Depends(get_db),user:User=Depends(current_user)):
    require_patient(db,user,identity)
    cases=db.scalars(select(MedicalCase).where(MedicalCase.patient_id==identity).order_by(MedicalCase.case_date.desc(),MedicalCase.case_id.desc()).offset((page-1)*page_size).limit(page_size)).all()
    data={'cases':[case_detail(db,user,c.case_id) for c in cases], 'page':page,'page_size':page_size,
          'case_total':db.scalar(select(func.count()).select_from(MedicalCase).where(MedicalCase.patient_id==identity)),
          'visit_count':db.scalar(select(func.patient_visit_count(identity)))}
    for name,model in [('medical_history',MedicalHistory),('allergies',Allergy)]:
        data[name]=[record_dict(r) for r in db.scalars(select(model).where(model.patient_id==identity).order_by(list(model.__table__.primary_key)[0]).limit(page_size).offset((page-1)*page_size))]
        data[name+'_total']=db.scalar(select(func.count()).select_from(model).where(model.patient_id==identity))
    lifestyle=db.scalar(select(LifestyleHistory).where(LifestyleHistory.patient_id==identity)); data['lifestyle']=record_dict(lifestyle) if lifestyle else None
    return data

@router.get('/patients/{identity}/timeline')
def patient_timeline(identity:int,page:int=Query(1,ge=1),page_size:int=Query(30,ge=1,le=100),db:Session=Depends(get_db),user:User=Depends(current_user)):
    require_patient(db,user,identity)
    sql='''SELECT event_date,event_type,entity_id,description FROM (
    SELECT c.created_at event_date,'Case created' event_type,c.case_id entity_id,c.chief_complaint description FROM medical_cases c WHERE c.patient_id=:pid
    UNION ALL SELECT v.visit_date,'Visit',v.visit_id,v.chief_complaint FROM visits v JOIN medical_cases c ON c.case_id=v.case_id WHERE c.patient_id=:pid
    UNION ALL SELECT cs.recorded_at,'Symptoms recorded',cs.symptom_id,s.symptom_name FROM case_symptoms cs JOIN symptoms s ON s.symptom_id=cs.symptom_id JOIN medical_cases c ON c.case_id=cs.case_id WHERE c.patient_id=:pid
    UNION ALL SELECT v.visit_date,'Diagnosis recorded',d.diagnosis_id,d.diagnosis_name FROM diagnoses d JOIN visits v ON v.visit_id=d.visit_id JOIN medical_cases c ON c.case_id=v.case_id WHERE c.patient_id=:pid
    UNION ALL SELECT CAST(r.prescription_date AS DATETIME),'Prescription',r.prescription_id,'Fictional prescription document' FROM prescriptions r JOIN visits v ON v.visit_id=r.visit_id JOIN medical_cases c ON c.case_id=v.case_id WHERE c.patient_id=:pid
    UNION ALL SELECT CAST(f.scheduled_date AS DATETIME),'Follow-up scheduled',f.follow_up_id,f.reason FROM follow_ups f JOIN visits v ON v.visit_id=f.visit_id JOIN medical_cases c ON c.case_id=v.case_id WHERE c.patient_id=:pid
    UNION ALL SELECT CAST(f.actual_date AS DATETIME),'Follow-up completed',f.follow_up_id,f.reason FROM follow_ups f JOIN visits v ON v.visit_id=f.visit_id JOIN medical_cases c ON c.case_id=v.case_id WHERE c.patient_id=:pid AND f.actual_date IS NOT NULL
    ) timeline'''
    total=db.scalar(text('SELECT COUNT(*) FROM ('+sql+') counted'),{'pid':identity})
    rows=db.execute(text(sql+' ORDER BY event_date DESC,event_type,entity_id DESC LIMIT :lim OFFSET :off'),{'pid':identity,'lim':page_size,'off':(page-1)*page_size}).mappings()
    return {'items':[dict(r) for r in rows],'total':total,'page':page,'page_size':page_size}

@router.post('/cases',status_code=201)
def create_case(payload:CaseBundle,db:Session=Depends(get_db),user:User=Depends(current_user)): return save_case(db,user,payload)

@router.put('/cases/{identity}/bundle')
def update_draft(identity:int,payload:CaseBundle,db:Session=Depends(get_db),user:User=Depends(current_user)): return save_case(db,user,payload,identity)

@router.get('/cases/{identity}')
def get_case(identity:int,db:Session=Depends(get_db),user:User=Depends(current_user)): return case_detail(db,user,identity)

@router.put('/cases/{identity}')
def edit_case(identity:int,payload:CaseUpdate,db:Session=Depends(get_db),user:User=Depends(current_user)):
    row=require_case(db,user,identity,write=True)
    data=payload.model_dump(exclude_unset=True)
    if data.get('doctor_id'):
        roles(user,'ADMIN'); ensure_active_doctor(db,data['doctor_id'])
    target=data.pop('case_status',None)
    for k,v in data.items():
        if k in ('doctor_id','chief_complaint','priority') and v is None: raise HTTPException(422,'Required values cannot be null')
        setattr(row,k,v)
    db.flush()
    if target=='CLOSED': db.execute(text('CALL close_case(:id)'),{'id':identity}); db.refresh(row)
    elif target:
        if row.record_state=='DRAFT' and target!='OPEN': raise HTTPException(409,'Submit this draft before changing its workflow')
        row.case_status=target; db.flush()
    return record_dict(row)

@router.delete('/cases/{identity}')
def delete_case(identity:int,db:Session=Depends(get_db),user:User=Depends(current_user)):
    roles(user,'ADMIN'); row=require_case(db,user,identity,write=True)
    if row.record_state!='DRAFT': raise HTTPException(409,'Only unused drafts can be deleted')
    db.delete(row); db.flush(); audit(db,user,'DELETE','CASE',identity,'Unused draft case deleted'); return {'message':'Case deleted'}

@router.get('/visits/{identity}')
def get_visit(identity:int,db:Session=Depends(get_db),user:User=Depends(current_user)): return visit_detail(db,user,identity)

@router.post('/visits',status_code=201)
def create_visit(payload:VisitInput,db:Session=Depends(get_db),user:User=Depends(current_user)):
    case=require_case(db,user,payload.case_id,write=True)
    if case.record_state!='SUBMITTED': raise HTTPException(409,'Submit the initial case before adding a visit')
    ensure_active_doctor(db,payload.doctor_id)
    if user.role=='DOCTOR' and payload.doctor_id!=doctor_id(db,user): raise HTTPException(403,'Record your own attending identity')
    row=Visit(**payload.model_dump(exclude={'vitals','examination','diagnoses','prescription','followup'})); db.add(row); db.flush()
    save_sections(db,user,row,payload); audit(db,user,'INSERT','VISIT',row.visit_id,'Subsequent fictional encounter created')
    return {'visit_id':row.visit_id}

def save_visit_section(identity, payload, model, db, user):
    visit=must_get(db,Visit,identity)
    case=require_case(db,user,visit.case_id,write=True)
    if case.case_status=='CLOSED': raise HTTPException(409,'Closed case encounters cannot be changed')
    row=db.scalar(select(model).where(model.visit_id==identity).with_for_update())
    if row is None:
        row=model(visit_id=identity); db.add(row)
    for key,value in payload.model_dump().items(): setattr(row,key,value)
    db.flush(); audit(db,user,'UPDATE',model.__tablename__.upper(),identity,'Encounter section saved')
    return record_dict(row)

@router.put('/visits/{identity}/vitals')
def save_vitals(identity:int,payload:VitalInput,db:Session=Depends(get_db),user:User=Depends(current_user)):
    return save_visit_section(identity,payload,VitalSign,db,user)

@router.put('/visits/{identity}/examination')
def save_examination(identity:int,payload:ExaminationInput,db:Session=Depends(get_db),user:User=Depends(current_user)):
    return save_visit_section(identity,payload,Examination,db,user)

@router.post('/appointments',status_code=201)
def create_appointment(payload:AppointmentInput,db:Session=Depends(get_db),user:User=Depends(current_user)): return save_appointment(db,user,payload)

@router.put('/appointments/{identity}')
def edit_appointment(identity:int,payload:AppointmentInput,db:Session=Depends(get_db),user:User=Depends(current_user)): return save_appointment(db,user,payload,identity)

@router.delete('/appointments/{identity}')
def cancel_appointment(identity:int,db:Session=Depends(get_db),user:User=Depends(current_user)):
    row=must_get(db,Appointment,identity)
    values=record_dict(row); values.pop('appointment_id'); values.pop('created_at'); values['status']='CANCELLED'
    return save_appointment(db,user,AppointmentInput.model_validate(values),identity)

def register_catalog(path,model,schema):
    def create(payload:schema,db:Session=Depends(get_db),user:User=Depends(current_user)):
        roles(user,'ADMIN'); row=model(**payload.model_dump()); db.add(row); db.flush()
        audit(db,user,'INSERT',path.upper(),getattr(row,list(model.__table__.primary_key)[0].name),'Catalog entry created'); return record_dict(row)
    def update(identity:int,payload:schema,db:Session=Depends(get_db),user:User=Depends(current_user)):
        roles(user,'ADMIN'); row=must_get(db,model,identity,lock=True)
        if model is Medicine and db.scalar(select(func.count()).select_from(PrescriptionMedicine).where(PrescriptionMedicine.medicine_id==identity)):
            if any(getattr(row,k)!=v for k,v in payload.model_dump().items() if k!='is_active'): raise HTTPException(409,'Referenced medicine presentation is immutable; create a new demo code')
        for k,v in payload.model_dump().items(): setattr(row,k,v)
        db.flush(); audit(db,user,'UPDATE',path.upper(),identity,'Catalog entry updated'); return record_dict(row)
    create.__name__='create_'+path; update.__name__='update_'+path
    router.add_api_route('/'+path,create,methods=['POST'],status_code=201)
    router.add_api_route('/'+path+'/{identity}',update,methods=['PUT'])
register_catalog('symptoms',Symptom,SymptomInput)
register_catalog('medicines',Medicine,MedicineInput)

@router.post('/diagnoses',status_code=201)
def create_diagnosis(payload:DiagnosisInput,db:Session=Depends(get_db),user:User=Depends(current_user)):
    visit=must_get(db,Visit,payload.visit_id); require_case(db,user,visit.case_id,write=True)
    row=Diagnosis(**payload.model_dump()); db.add(row); db.flush(); audit(db,user,'INSERT','DIAGNOSIS',row.diagnosis_id,'Fictional diagnosis observation recorded'); return record_dict(row)

@router.get('/prescriptions/{identity}')
def get_prescription(identity:int,db:Session=Depends(get_db),user:User=Depends(current_user)): return prescription_detail(db,user,identity)

@router.post('/prescriptions',status_code=201)
def create_prescription(payload:PrescriptionInput,db:Session=Depends(get_db),user:User=Depends(current_user)):
    visit=must_get(db,Visit,payload.visit_id); require_case(db,user,visit.case_id,write=True)
    if user.role=='DOCTOR' and payload.doctor_id!=doctor_id(db,user): raise HTTPException(403,'Author your own prescription')
    ensure_active_doctor(db,payload.doctor_id)
    if payload.prescription_date<(visit.visit_date+timedelta(minutes=330)).date(): raise HTTPException(422,'Prescription cannot precede its visit')
    row=Prescription(**payload.model_dump(exclude={'medicines'})); db.add(row); db.flush()
    for item in payload.medicines:
        med=must_get(db,Medicine,item.medicine_id)
        if not med.is_active: raise HTTPException(409,'Fictional product is inactive')
        db.add(PrescriptionMedicine(prescription_id=row.prescription_id,**item.model_dump()))
    db.flush(); audit(db,user,'INSERT','PRESCRIPTION',row.prescription_id,'Fictional prescription created'); return prescription_detail(db,user,row.prescription_id)

@router.post('/followups',status_code=201)
def create_followup(payload:FollowupInput,db:Session=Depends(get_db),user:User=Depends(current_user)):
    visit=must_get(db,Visit,payload.visit_id); require_case(db,user,visit.case_id,write=True)
    db.execute(text('CALL schedule_followup(:v,:d,:r,:i,@new_followup_id)'),{'v':payload.visit_id,'d':payload.scheduled_date,'r':payload.reason,'i':payload.instructions})
    identity=db.scalar(text('SELECT @new_followup_id')); audit(db,user,'INSERT','FOLLOW_UP',identity,'Follow-up plan created'); return record_dict(must_get(db,FollowUp,identity))

@router.put('/followups/{identity}')
def edit_followup(identity:int,payload:FollowupUpdate,db:Session=Depends(get_db),user:User=Depends(current_user)):
    row=must_get(db,FollowUp,identity); visit=must_get(db,Visit,row.visit_id); require_case(db,user,visit.case_id,write=True)
    if row.status in ('COMPLETED','CANCELLED'): raise HTTPException(409,'This follow-up is already resolved')
    data=payload.model_dump(exclude_unset=True)
    for k,v in data.items():
        if k in ('scheduled_date','status','reason') and v is None: raise HTTPException(422,'Required values cannot be null')
        setattr(row,k,v)
    if row.status=='COMPLETED' and row.actual_date is None: row.actual_date=clinic_today()
    if row.status!='COMPLETED': row.actual_date=None
    db.flush(); audit(db,user,'UPDATE','FOLLOW_UP',identity,'Follow-up scheduling state updated'); return record_dict(row)

@router.post('/doctors',status_code=201)
def create_doctor(payload:DoctorInput,db:Session=Depends(get_db),user:User=Depends(current_user)):
    roles(user,'ADMIN')
    account=User(username=payload.username,email=str(payload.login_email).lower(),password_hash=hash_password(payload.password),role='DOCTOR'); db.add(account); db.flush()
    data=payload.model_dump(exclude={'username','login_email','password'}); data['email']=str(data['email']).lower()
    doc=Doctor(user_id=account.user_id,**data); db.add(doc); db.flush(); audit(db,user,'INSERT','DOCTOR',doc.doctor_id,'Doctor account and profile provisioned atomically'); return record_dict(doc)

@router.put('/doctors/{identity}')
def edit_doctor(identity:int,payload:DoctorUpdate,db:Session=Depends(get_db),user:User=Depends(current_user)):
    roles(user,'ADMIN'); row=must_get(db,Doctor,identity,lock=True)
    data=payload.model_dump(exclude_unset=True)
    active=data.pop('is_active',None)
    if active is not None: must_get(db,User,row.user_id).is_active=active
    for k,v in data.items():
        if v is None: raise HTTPException(422,'Doctor details cannot be null')
        setattr(row,k,v)
    db.flush(); audit(db,user,'UPDATE','DOCTOR',identity,'Doctor profile updated'); return record_dict(row)

@router.post('/users',status_code=201)
def create_user(payload:UserInput,db:Session=Depends(get_db),user:User=Depends(current_user)):
    roles(user,'ADMIN'); data=payload.model_dump(exclude={'password'}); data['email']=str(data['email']).lower()
    row=User(**data,password_hash=hash_password(payload.password)); db.add(row); db.flush(); audit(db,user,'INSERT','USER',row.user_id,'Application account created'); return record_dict(row)

@router.put('/users/{identity}')
def edit_user(identity:int,payload:UserUpdate,db:Session=Depends(get_db),user:User=Depends(current_user)):
    roles(user,'ADMIN')
    if identity==user.user_id and not payload.is_active: raise HTTPException(409,'You cannot disable your own account')
    row=must_get(db,User,identity,lock=True); row.is_active=payload.is_active; db.flush(); audit(db,user,'UPDATE','USER',identity,'Account active state changed'); return record_dict(row)

def register_patient_section(path,model,schema,primary):
    def create(identity:int,payload:schema,db:Session=Depends(get_db),user:User=Depends(current_user)):
        require_patient(db,user,identity)
        data=payload.model_dump(); data.pop(primary,None)
        row=upsert_child(db,model,'patient_id',identity,data) if model is LifestyleHistory else model(patient_id=identity,**data)
        if model is not LifestyleHistory: db.add(row); db.flush()
        audit(db,user,'INSERT',path.upper(),getattr(row,primary),'Patient-level fictional record saved'); return record_dict(row)
    create.__name__='save_'+path
    router.add_api_route('/patients/{identity}/'+path,create,methods=['POST'],status_code=201)
register_patient_section('medical-history',MedicalHistory,HistoryInput,'history_id')
register_patient_section('allergies',Allergy,AllergyInput,'allergy_id')
register_patient_section('lifestyle',LifestyleHistory,LifestyleInput,'lifestyle_id')
