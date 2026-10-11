from datetime import date, timedelta
from fastapi import HTTPException
from sqlalchemy import text
from app.schemas import clinic_today
from app.services.records import doctor_id
from app.utils.security import roles

def rows(db,sql,params): return [dict(r) for r in db.execute(text(sql),params).mappings()]
def scalar(db,sql,params): return db.scalar(text(sql),params)

def dashboard(db,user):
    did=doctor_id(db,user) if user.role=='DOCTOR' else None
    params={'did':did,'today':clinic_today(),'month':clinic_today().replace(day=1)}
    patient_scope="(:did IS NULL OR EXISTS(SELECT 1 FROM medical_cases pc WHERE pc.patient_id=p.patient_id AND pc.doctor_id=:did) OR EXISTS(SELECT 1 FROM appointments pa WHERE pa.patient_id=p.patient_id AND pa.doctor_id=:did AND pa.status<>'CANCELLED'))"
    cs="c.record_state='SUBMITTED' AND (:did IS NULL OR c.doctor_id=:did)"
    stats={
      'total_patients':scalar(db,'SELECT COUNT(*) FROM patients p WHERE '+patient_scope,params),
      'todays_appointments':scalar(db,"SELECT COUNT(*) FROM appointments WHERE appointment_date=:today AND status<>'CANCELLED' AND (:did IS NULL OR doctor_id=:did)",params),
      'upcoming_followups':scalar(db,'SELECT COUNT(*) FROM upcoming_followups WHERE (:did IS NULL OR doctor_id=:did)',params),
      'total_doctors':scalar(db,"SELECT COUNT(*) FROM doctors d JOIN users u ON u.user_id=d.user_id WHERE u.is_active=1",params),
    }
    charts={
      'patients_per_month':rows(db,"SELECT DATE_FORMAT(p.created_at,'%Y-%m') label,COUNT(*) total FROM patients p WHERE "+patient_scope+" GROUP BY label ORDER BY label",params),
      'appointment_status':rows(db,'SELECT status label,COUNT(*) total FROM appointments WHERE (:did IS NULL OR doctor_id=:did) GROUP BY status ORDER BY total DESC',params),
    }
    recent={
      'patients':rows(db,'SELECT p.patient_id,p.first_name,p.last_name,p.city,p.created_at FROM patients p WHERE '+patient_scope+' ORDER BY p.created_at DESC,p.patient_id DESC LIMIT 5',params),
      'appointments':rows(db,"SELECT a.appointment_id,a.patient_id,a.doctor_id,a.appointment_date,TIME_FORMAT(a.start_time,'%H:%i:%s') start_time,TIME_FORMAT(a.end_time,'%H:%i:%s') end_time,a.status,CONCAT(p.first_name,' ',p.last_name) patient_name,CONCAT(d.first_name,' ',d.last_name) doctor_name FROM appointments a JOIN patients p ON p.patient_id=a.patient_id JOIN doctors d ON d.doctor_id=a.doctor_id WHERE a.appointment_date=:today AND (:did IS NULL OR a.doctor_id=:did) ORDER BY a.start_time,a.appointment_id LIMIT 6",params),
      'followups':rows(db,'SELECT * FROM upcoming_followups WHERE (:did IS NULL OR doctor_id=:did) ORDER BY follow_up_date,follow_up_id LIMIT 5',params),
    }
    if user.role!='RECEPTIONIST':
        stats['active_cases']=scalar(db,"SELECT COUNT(*) FROM medical_cases c WHERE "+cs+" AND c.case_status<>'CLOSED'",params)
        stats['prescriptions_this_month']=scalar(db,'SELECT COUNT(*) FROM prescriptions r JOIN visits v ON v.visit_id=r.visit_id JOIN medical_cases c ON c.case_id=v.case_id WHERE '+cs+' AND r.prescription_date>=:month AND r.prescription_date<=:today',params)
        charts.update({
          'cases_per_month':rows(db,"SELECT DATE_FORMAT(c.case_date,'%Y-%m') label,COUNT(*) total FROM medical_cases c WHERE "+cs+' GROUP BY label ORDER BY label',params),
          'top_symptoms':rows(db,'SELECT s.symptom_name label,COUNT(*) total FROM case_symptoms x JOIN symptoms s ON s.symptom_id=x.symptom_id JOIN medical_cases c ON c.case_id=x.case_id WHERE '+cs+' GROUP BY s.symptom_id,s.symptom_name ORDER BY total DESC,label LIMIT 6',params),
          'top_diagnoses':rows(db,'SELECT x.diagnosis_name label,COUNT(*) total FROM diagnoses x JOIN visits v ON v.visit_id=x.visit_id JOIN medical_cases c ON c.case_id=v.case_id WHERE '+cs+' GROUP BY x.diagnosis_name ORDER BY total DESC,label LIMIT 6',params),
          'case_status':rows(db,'SELECT c.case_status label,COUNT(*) total FROM medical_cases c WHERE '+cs+' GROUP BY c.case_status',params),
        })
        recent['cases']=rows(db,'SELECT * FROM patient_case_summary WHERE (:did IS NULL OR doctor_id=:did) ORDER BY case_date DESC,case_id DESC LIMIT 5',params)
    return {'statistics':stats,'charts':charts,'recent':recent,'clinic_date':clinic_today()}

def report(db,user,name,page,page_size,date_from,date_to,q,sort,direction,doctor_filter=None):
    if user.role=='RECEPTIONIST' and name not in ('patients','appointments','followups'): roles(user,'ADMIN','DOCTOR')
    did=doctor_id(db,user) if user.role=='DOCTOR' else doctor_filter
    params={'did':did,'start':date_from or date(1000,1,1),'end':(date_to or clinic_today())+timedelta(days=1),'q':'%'+q+'%','lim':page_size,'off':(page-1)*page_size}
    cs="c.record_state='SUBMITTED' AND (:did IS NULL OR c.doctor_id=:did) AND c.case_date>=:start AND c.case_date<:end"
    queries={
      'patients':"SELECT DATE_FORMAT(p.created_at,'%Y-%m') label,COUNT(*) total FROM patients p WHERE p.created_at>=:start AND p.created_at<:end AND (:did IS NULL OR EXISTS(SELECT 1 FROM medical_cases c WHERE c.patient_id=p.patient_id AND c.doctor_id=:did) OR EXISTS(SELECT 1 FROM appointments a WHERE a.patient_id=p.patient_id AND a.doctor_id=:did AND a.status<>'CANCELLED')) GROUP BY label",
      'cases':"SELECT CONCAT(d.first_name,' ',d.last_name) label,COUNT(c.case_id) total FROM doctors d LEFT JOIN medical_cases c ON c.doctor_id=d.doctor_id AND "+cs+" WHERE (:did IS NULL OR d.doctor_id=:did) GROUP BY d.doctor_id,d.first_name,d.last_name",
      'symptoms':'SELECT s.symptom_name label,COUNT(*) total FROM symptoms s JOIN case_symptoms x ON x.symptom_id=s.symptom_id JOIN medical_cases c ON c.case_id=x.case_id WHERE '+cs+' GROUP BY s.symptom_id,s.symptom_name',
      'diagnoses':'SELECT x.diagnosis_name label,COUNT(*) total FROM diagnoses x JOIN visits v ON v.visit_id=x.visit_id JOIN medical_cases c ON c.case_id=v.case_id WHERE '+cs+' GROUP BY x.diagnosis_name',
      'medicines':'SELECT m.medicine_name label,COUNT(*) total FROM medicines m JOIN prescription_medicines x ON x.medicine_id=m.medicine_id JOIN prescriptions r ON r.prescription_id=x.prescription_id JOIN visits v ON v.visit_id=r.visit_id JOIN medical_cases c ON c.case_id=v.case_id WHERE '+cs+' GROUP BY m.medicine_id,m.medicine_name',
      'appointments':'SELECT status label,COUNT(*) total FROM appointments WHERE appointment_date>=:start AND appointment_date<:end AND (:did IS NULL OR doctor_id=:did) GROUP BY status',
      'followups':'SELECT f.status label,COUNT(*) total FROM follow_ups f JOIN visits v ON v.visit_id=f.visit_id JOIN medical_cases c ON c.case_id=v.case_id WHERE f.scheduled_date>=:start AND f.scheduled_date<:end AND (:did IS NULL OR c.doctor_id=:did) GROUP BY f.status',
      'active-cases':"SELECT c.case_status label,COUNT(*) total FROM medical_cases c WHERE "+cs+" AND c.case_status<>'CLOSED' GROUP BY c.case_status",
      'closed-cases':"SELECT DATE_FORMAT(c.case_date,'%Y-%m') label,COUNT(*) total FROM medical_cases c WHERE "+cs+" AND c.case_status='CLOSED' GROUP BY label",
      'multiple-cases':"SELECT CONCAT(p.first_name,' ',p.last_name,' · #',p.patient_id) label,COUNT(*) total FROM patients p JOIN medical_cases c ON c.patient_id=p.patient_id WHERE "+cs+' GROUP BY p.patient_id,p.first_name,p.last_name HAVING COUNT(*)>1',
    }
    if date_from is None and date_to is None:
        queries['cases']='SELECT doctor_name label,total_cases total FROM doctor_case_statistics WHERE (:did IS NULL OR doctor_id=:did)'
    if name not in queries: raise HTTPException(404,'Report not found')
    if sort not in ('label','total') or direction not in ('asc','desc'): raise HTTPException(400,'Invalid report sorting')
    base='SELECT * FROM ('+queries[name]+') report WHERE label LIKE :q'
    total=scalar(db,'SELECT COUNT(*) FROM ('+base+') counted',params)
    data=rows(db,base+f' ORDER BY {sort} {direction},label ASC LIMIT :lim OFFSET :off',params)
    return {'items':data,'total':total,'page':page,'page_size':page_size,'report':name}
