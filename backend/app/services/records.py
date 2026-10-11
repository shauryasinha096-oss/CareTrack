"""Database-backed record queries, ownership checks and atomic clinical writes."""
from datetime import datetime, time, timezone, timedelta
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import select, func, or_, exists, delete, text
from sqlalchemy.orm import Session
from app.models import *
from app.schemas import CaseBundle, ClinicalSections, clinic_today
from app.utils.security import roles

def record_dict(obj):
    return {c.name:getattr(obj,c.name) for c in obj.__table__.columns if c.name!='password_hash'}

def must_get(db, model, key, lock=False):
    primary=list(model.__table__.primary_key)[0]
    obj=db.scalar(select(model).where(primary==key).with_for_update()) if lock else db.get(model,key)
    if obj is None: raise HTTPException(404,'Record not found')
    return obj

def doctor_id(db,user):
    did=db.scalar(select(Doctor.doctor_id).where(Doctor.user_id==user.user_id))
    if user.role=='DOCTOR' and not did: raise HTTPException(403,'Doctor profile is not configured')
    return did

def require_case(db,user,case_id,write=False):
    roles(user,'ADMIN','DOCTOR')
    case=must_get(db,MedicalCase,case_id,lock=write)
    if user.role=='DOCTOR' and case.doctor_id!=doctor_id(db,user):
        if write: raise HTTPException(403,'This case is assigned to another doctor')
        require_patient(db,user,case.patient_id)
    if write and case.case_status=='CLOSED': raise HTTPException(409,'This case is closed')
    return case

def require_patient(db,user,patient_id):
    must_get(db,Patient,patient_id)
    roles(user,'ADMIN','DOCTOR')
    if user.role=='DOCTOR':
        did=doctor_id(db,user)
        has_case=db.scalar(select(exists().where(MedicalCase.patient_id==patient_id,MedicalCase.doctor_id==did)))
        has_booking=db.scalar(select(exists().where(Appointment.patient_id==patient_id,Appointment.doctor_id==did,Appointment.status!='CANCELLED')))
        if not has_case and not has_booking: raise HTTPException(403,'Clinical history is limited to assigned patients')

def audit(db,user,action,entity,identity,description):
    db.add(AuditLog(user_id=user.user_id,actor_username=user.username,action=action,entity_type=entity,entity_id=str(identity),description=description))

def page_query(db,query,page=1,page_size=20,sort_column=None,direction='desc'):
    total=db.scalar(select(func.count()).select_from(query.order_by(None).subquery()))
    if sort_column is not None: query=query.order_by(None).order_by(sort_column.asc() if direction=='asc' else sort_column.desc(),list(query.selected_columns)[0].desc())
    rows=db.execute(query.limit(page_size).offset((page-1)*page_size)).mappings().all()
    return {'items':[dict(r) for r in rows],'total':total,'page':page,'page_size':page_size}

def list_records(db,user,resource,page,page_size,q='',status=None,doctor=None,patient=None,date_from=None,date_to=None,sort=None,direction='desc',case_id=None,visit_id=None):
    model=MODELS[resource]; table=model.__table__
    query=select(*table.c)
    p=Patient.__table__; d=Doctor.__table__; c=MedicalCase.__table__; v=Visit.__table__
    if resource in ('users','audit_logs'): roles(user,'ADMIN')
    if resource in ('symptoms','medicines','diagnoses','prescriptions','visits','medical_cases'): roles(user,'ADMIN','DOCTOR')
    joined_case=False
    if resource=='medical_cases':
        query=select(*table.c,func.concat(p.c.first_name,' ',p.c.last_name).label('patient_name'),func.concat(d.c.first_name,' ',d.c.last_name).label('doctor_name')).select_from(table.join(p).join(d))
        if user.role=='DOCTOR': query=query.where(table.c.doctor_id==doctor_id(db,user))
        if doctor: query=query.where(table.c.doctor_id==doctor)
        if patient: query=query.where(table.c.patient_id==patient)
        if case_id: query=query.where(table.c.case_id==case_id)
    elif resource=='appointments':
        cols=[x for x in table.c if user.role!='RECEPTIONIST' or x.name!='notes']
        query=select(*cols,func.concat(p.c.first_name,' ',p.c.last_name).label('patient_name'),func.concat(d.c.first_name,' ',d.c.last_name).label('doctor_name')).select_from(table.join(p).join(d))
        if user.role=='DOCTOR': query=query.where(table.c.doctor_id==doctor_id(db,user))
        if doctor: query=query.where(table.c.doctor_id==doctor)
        if patient: query=query.where(table.c.patient_id==patient)
    elif resource in ('visits','diagnoses','prescriptions','follow_ups'):
        path=table.join(c,table.c.case_id==c.c.case_id) if resource=='visits' else table.join(v,table.c.visit_id==v.c.visit_id).join(c,v.c.case_id==c.c.case_id)
        cols=[x for x in table.c if user.role!='RECEPTIONIST' or x.name in ('follow_up_id','visit_id','scheduled_date','actual_date','status')]
        extra=[c.c.patient_id,func.concat(p.c.first_name,' ',p.c.last_name).label('patient_name'),func.concat(d.c.first_name,' ',d.c.last_name).label('doctor_name')]
        if resource!='visits': extra.append(c.c.case_id)
        query=select(*cols,*extra).select_from(path.join(p,c.c.patient_id==p.c.patient_id).join(d,c.c.doctor_id==d.c.doctor_id))
        joined_case=True
        if user.role=='DOCTOR': query=query.where(c.c.doctor_id==doctor_id(db,user))
        if doctor: query=query.where(c.c.doctor_id==doctor)
        if patient: query=query.where(c.c.patient_id==patient)
        if case_id: query=query.where(c.c.case_id==case_id)
        if visit_id and 'visit_id' in table.c: query=query.where(table.c.visit_id==visit_id)
    if 'password_hash' in table.c: query=select(*[x for x in table.c if x.name!='password_hash'])
    if q:
        if resource=='patients':
            query=query.where(or_(table.c.first_name.like(q+'%'),table.c.last_name.like(q+'%'),func.concat(table.c.first_name,' ',table.c.last_name).like(q+'%'),table.c.phone==q,table.c.email==q,table.c.patient_id==int(q) if q.isdigit() else False))
        elif resource=='medical_cases':
            diagnosis_match=exists(select(1).select_from(Diagnosis.__table__.join(v)).where(v.c.case_id==table.c.case_id,Diagnosis.diagnosis_name.like('%'+q+'%')))
            query=query.where(or_(table.c.chief_complaint.like('%'+q+'%'),p.c.first_name.like(q+'%'),p.c.last_name.like(q+'%'),d.c.first_name.like(q+'%'),table.c.case_id==int(q) if q.isdigit() else False,diagnosis_match))
        else:
            searchable=[x for x in table.c if x.name in ('symptom_name','medicine_name','diagnosis_name','first_name','last_name','username','entity_type','action','reason','notes')]
            # Reception cannot search clinical notes/reasons.
            if user.role=='RECEPTIONIST': searchable=[x for x in searchable if x.name not in ('notes','reason')]
            predicates=[x.like('%'+q+'%') for x in searchable]
            if resource in ('appointments','visits','follow_ups','prescriptions'): predicates.extend([p.c.first_name.like(q+'%'),p.c.last_name.like(q+'%')])
            if predicates: query=query.where(or_(*predicates))
    status_col=table.c.get('case_status') if resource=='medical_cases' else table.c.get('status')
    if status and status_col is not None: query=query.where(status_col==status)
    date_name=next((n for n in ('case_date','appointment_date','scheduled_date','visit_date','prescription_date','created_at') if n in table.c),None)
    if date_name:
        dc=table.c[date_name]
        if date_from: query=query.where(dc>=date_from)
        if date_to: query=query.where(dc<date_to+timedelta(days=1))
    allowed={x.name:x for x in table.c if x.name!='password_hash'}
    chosen=allowed.get(sort or '')
    if sort and chosen is None: raise HTTPException(400,'Unsupported sort field')
    primary=list(table.primary_key)[0]
    query=query.order_by(primary.desc())
    return page_query(db,query,page,page_size,chosen,direction)

def ensure_active_doctor(db,identity):
    doc=must_get(db,Doctor,identity)
    if not must_get(db,User,doc.user_id).is_active: raise HTTPException(409,'Doctor is inactive')
    return doc

def upsert_child(db,model,key,value,data):
    row=db.scalar(select(model).where(getattr(model,key)==value))
    if row is None: row=model(**{key:value}); db.add(row)
    for field,val in data.items(): setattr(row,field,val)
    db.flush()
    return row

def save_sections(db,user,visit,sections: ClinicalSections):
    if sections.vitals: upsert_child(db,VitalSign,'visit_id',visit.visit_id,sections.vitals.model_dump())
    if sections.examination: upsert_child(db,Examination,'visit_id',visit.visit_id,sections.examination.model_dump())
    db.execute(delete(Diagnosis).where(Diagnosis.visit_id==visit.visit_id))
    for diag in sections.diagnoses: db.add(Diagnosis(visit_id=visit.visit_id,**diag.model_dump()))
    existing=db.scalar(select(Prescription).where(Prescription.visit_id==visit.visit_id))
    if sections.prescription:
        data=sections.prescription
        ensure_active_doctor(db,data.doctor_id)
        if user.role=='DOCTOR' and data.doctor_id!=doctor_id(db,user): raise HTTPException(403,'A doctor must author their own prescription')
        if data.prescription_date<(visit.visit_date+timedelta(minutes=330)).date(): raise HTTPException(422,'Prescription cannot precede its visit')
        row=upsert_child(db,Prescription,'visit_id',visit.visit_id,data.model_dump(exclude={'medicines'}))
        db.execute(delete(PrescriptionMedicine).where(PrescriptionMedicine.prescription_id==row.prescription_id))
        for item in data.medicines:
            med=must_get(db,Medicine,item.medicine_id)
            if not med.is_active: raise HTTPException(409,'This fictional medicine is inactive')
            db.add(PrescriptionMedicine(prescription_id=row.prescription_id,**item.model_dump()))
    elif existing:
        db.delete(existing)
    # Draft initial-visit bundle owns its single editable follow-up plan.
    existing_follow=db.scalar(select(FollowUp).where(FollowUp.visit_id==visit.visit_id).order_by(FollowUp.follow_up_id))
    if sections.followup:
        data=sections.followup.model_dump()
        if existing_follow:
            for k,val in data.items(): setattr(existing_follow,k,val)
        else: db.add(FollowUp(visit_id=visit.visit_id,**data))
    elif existing_follow:
        db.delete(existing_follow)
    db.flush()

def save_case(db,user,bundle: CaseBundle,identity=None):
    roles(user,'ADMIN','DOCTOR')
    must_get(db,Patient,bundle.patient_id); ensure_active_doctor(db,bundle.doctor_id)
    if user.role=='DOCTOR' and bundle.doctor_id!=doctor_id(db,user): raise HTTPException(403,'Create cases assigned to yourself')
    if identity:
        case=require_case(db,user,identity,write=True)
        if case.record_state!='DRAFT': raise HTTPException(409,'Submitted cases use the case editing and subsequent-visit workflows')
        if case.patient_id!=bundle.patient_id: raise HTTPException(409,'A saved draft cannot be moved to another patient')
    else:
        case=MedicalCase(patient_id=bundle.patient_id,doctor_id=bundle.doctor_id,case_date=bundle.case_date,chief_complaint='',record_state='DRAFT')
        db.add(case); db.flush()
    for key in ('doctor_id','case_date','chief_complaint','present_illness','priority','notes'): setattr(case,key,getattr(bundle,key))
    db.flush()
    existing_symptoms={s.symptom_id:s for s in db.scalars(select(CaseSymptom).where(CaseSymptom.case_id==case.case_id))}
    selected_ids={s.symptom_id for s in bundle.symptoms}
    if len(selected_ids)!=len(bundle.symptoms): raise HTTPException(422,'Select each symptom once')
    for sid,row in existing_symptoms.items():
        if sid not in selected_ids: db.delete(row)
    for symptom in bundle.symptoms:
        catalog=must_get(db,Symptom,symptom.symptom_id)
        if not catalog.is_active: raise HTTPException(409,'Symptom is inactive')
        row=existing_symptoms.get(symptom.symptom_id)
        if row:
            for k,val in symptom.model_dump().items(): setattr(row,k,val)
        else: db.add(CaseSymptom(case_id=case.case_id,**symptom.model_dump()))
    visit=db.scalar(select(Visit).where(Visit.case_id==case.case_id,Visit.visit_type=='INITIAL_CONSULTATION'))
    if visit is None:
        visit=Visit(case_id=case.case_id,doctor_id=bundle.doctor_id,visit_date=datetime.now(timezone.utc).replace(tzinfo=None),visit_type='INITIAL_CONSULTATION',chief_complaint=bundle.chief_complaint)
        db.add(visit); db.flush()
    visit.chief_complaint=bundle.chief_complaint; visit.doctor_id=bundle.doctor_id
    save_sections(db,user,visit,bundle)
    saved_ids={}
    for name,model,key in [('history',MedicalHistory,'history_id'),('allergies',Allergy,'allergy_id')]:
        saved_ids[name]=[]
        for item in getattr(bundle,name):
            data=item.model_dump(); prior_id=data.pop(key,None)
            row=must_get(db,model,prior_id) if prior_id else model(patient_id=case.patient_id)
            if row.patient_id!=case.patient_id: raise HTTPException(403,'Patient history ownership does not match')
            for field,val in data.items(): setattr(row,field,val)
            if not prior_id: db.add(row)
            db.flush(); saved_ids[name].append(getattr(row,key))
    if bundle.lifestyle: upsert_child(db,LifestyleHistory,'patient_id',case.patient_id,bundle.lifestyle.model_dump())
    db.flush()
    case.record_state=bundle.record_state; case.case_status=bundle.case_status
    db.flush()
    return {'case_id':case.case_id,'visit_id':visit.visit_id,'record_state':case.record_state,'saved_ids':saved_ids}

def case_detail(db,user,identity):
    case=require_case(db,user,identity)
    result=record_dict(case)
    result['patient']=record_dict(must_get(db,Patient,case.patient_id))
    result['doctor']=record_dict(must_get(db,Doctor,case.doctor_id))
    result['symptoms']=[dict(r) for r in db.execute(select(*CaseSymptom.__table__.c,Symptom.symptom_name).join(Symptom).where(CaseSymptom.case_id==identity)).mappings()]
    result['visits']=[visit_detail(db,user,v.visit_id) for v in db.scalars(select(Visit).where(Visit.case_id==identity).order_by(Visit.visit_date.desc()))]
    return result

def visit_detail(db,user,identity):
    visit=must_get(db,Visit,identity); require_case(db,user,visit.case_id)
    result=record_dict(visit)
    vitals=db.scalar(select(VitalSign).where(VitalSign.visit_id==identity))
    exam=db.scalar(select(Examination).where(Examination.visit_id==identity))
    result['vitals']=record_dict(vitals) if vitals else None
    if vitals: result['vitals']['bmi']=db.scalar(select(func.calculate_bmi(vitals.height_cm,vitals.weight_kg)))
    result['examination']=record_dict(exam) if exam else None
    result['diagnoses']=[record_dict(r) for r in db.scalars(select(Diagnosis).where(Diagnosis.visit_id==identity))]
    rx=db.scalar(select(Prescription).where(Prescription.visit_id==identity))
    result['prescription']=prescription_detail(db,user,rx.prescription_id) if rx else None
    result['followups']=[record_dict(r) for r in db.scalars(select(FollowUp).where(FollowUp.visit_id==identity))]
    return result

def prescription_detail(db,user,identity):
    rx=must_get(db,Prescription,identity); visit=must_get(db,Visit,rx.visit_id); require_case(db,user,visit.case_id)
    data=record_dict(rx)
    data['medicines']=[dict(r) for r in db.execute(select(*PrescriptionMedicine.__table__.c,Medicine.medicine_name,Medicine.medicine_code).join(Medicine).where(PrescriptionMedicine.prescription_id==identity)).mappings()]
    return data

def save_appointment(db,user,payload,identity=None):
    previous=must_get(db,Appointment,identity) if identity else None
    # Existing appointment is read without a row lock; take shared doctor lock order first.
    doctor_ids=sorted(set([payload.doctor_id]+([previous.doctor_id] if previous else [])))
    for did in doctor_ids: must_get(db,Doctor,did,lock=True)
    if previous:
        db.refresh(previous,with_for_update=True)
        if previous.doctor_id not in doctor_ids: raise HTTPException(409,'Appointment changed. Please reload and retry')
        if previous.status in ('COMPLETED','NO_SHOW'): raise HTTPException(409,'Historical appointments cannot be edited')
    if user.role=='DOCTOR':
        did=doctor_id(db,user)
        if payload.doctor_id!=did or (previous and previous.doctor_id!=did): raise HTTPException(403,'Manage only your own appointments')
    must_get(db,Patient,payload.patient_id); ensure_active_doctor(db,payload.doctor_id)
    if payload.status!='CANCELLED':
        query=select(Appointment.appointment_id).where(Appointment.doctor_id==payload.doctor_id,Appointment.appointment_date==payload.appointment_date,Appointment.status!='CANCELLED',Appointment.start_time<payload.end_time,Appointment.end_time>payload.start_time)
        if identity: query=query.where(Appointment.appointment_id!=identity)
        if db.scalar(query.limit(1).with_for_update()): raise HTTPException(409,'This time overlaps another appointment for this doctor')
    row=previous or Appointment()
    for key,val in payload.model_dump().items():
        if previous and user.role=='RECEPTIONIST' and key=='notes': continue
        setattr(row,key,val)
    if not previous: db.add(row)
    db.flush(); audit(db,user,'UPDATE' if previous else 'INSERT','APPOINTMENT',row.appointment_id,'Appointment scheduling record saved')
    result=record_dict(row)
    if user.role=='RECEPTIONIST': result.pop('notes',None)
    return result
