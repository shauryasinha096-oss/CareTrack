CREATE VIEW patient_case_summary AS
SELECT p.patient_id, CONCAT(p.first_name,' ',p.last_name) AS patient_name,
       c.case_id,c.case_date,c.doctor_id,CONCAT(d.first_name,' ',d.last_name) AS doctor_name,
       c.chief_complaint,c.case_status,c.priority
FROM patients p JOIN medical_cases c ON c.patient_id=p.patient_id
JOIN doctors d ON d.doctor_id=c.doctor_id WHERE c.record_state='SUBMITTED';

CREATE VIEW upcoming_followups AS
SELECT f.follow_up_id,p.patient_id,CONCAT(p.first_name,' ',p.last_name) AS patient_name,
       c.doctor_id,CONCAT(d.first_name,' ',d.last_name) AS doctor_name,
       c.case_id,f.visit_id,f.scheduled_date AS follow_up_date,f.status
FROM follow_ups f JOIN visits v ON v.visit_id=f.visit_id
JOIN medical_cases c ON c.case_id=v.case_id JOIN patients p ON p.patient_id=c.patient_id
JOIN doctors d ON d.doctor_id=c.doctor_id
WHERE f.status='PENDING' AND c.record_state='SUBMITTED'
AND f.scheduled_date>=DATE(UTC_TIMESTAMP()+INTERVAL 330 MINUTE);

CREATE VIEW doctor_case_statistics AS
SELECT d.doctor_id,CONCAT(d.first_name,' ',d.last_name) AS doctor_name,
       COUNT(c.case_id) AS total_cases,
       COALESCE(SUM(c.case_status<>'CLOSED'),0) AS active_cases,
       COALESCE(SUM(c.case_status='CLOSED'),0) AS closed_cases
FROM doctors d LEFT JOIN medical_cases c ON c.doctor_id=d.doctor_id AND c.record_state='SUBMITTED'
GROUP BY d.doctor_id,d.first_name,d.last_name;

CREATE VIEW receptionist_patients AS
SELECT patient_id,first_name,last_name,date_of_birth,gender,phone,email,city FROM patients;
