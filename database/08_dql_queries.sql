-- MySQL 8.0.31+ (verified on 8.4). Every query uses actual CareTrack tables.
USE caretrack;
-- Q01 WHERE: open submitted cases.
SELECT case_id,patient_id,chief_complaint FROM medical_cases WHERE case_status='OPEN' AND record_state='SUBMITTED';
-- Q02 COUNT: registered patients.
SELECT COUNT(*) AS patients FROM patients;
-- Q03 SUM: fictional prescription product-day associations, not recommended treatment.
SELECT SUM(duration_days) AS fictional_product_days FROM prescription_medicines;
-- Q04 AVG: age distribution.
SELECT AVG(calculate_age(date_of_birth)) AS average_age FROM patients;
-- Q05 MIN: earliest case.
SELECT MIN(case_date) AS earliest_case FROM medical_cases;
-- Q06 MAX: latest visit.
SELECT MAX(visit_date) AS latest_visit FROM visits;
-- Q07 IN: selected case states.
SELECT case_id,case_status FROM medical_cases WHERE case_status IN ('OPEN','FOLLOW_UP');
-- Q08 NOT IN: inactive or historical workflow states excluded.
SELECT appointment_id,status FROM appointments WHERE status NOT IN ('CANCELLED','NO_SHOW');
-- Q09 LIKE: patient name search.
SELECT patient_id,first_name,last_name FROM patients WHERE CONCAT(first_name,' ',last_name) LIKE '%Aarav%';
-- Q10 DISTINCT: represented cities.
SELECT DISTINCT city FROM patients WHERE city IS NOT NULL ORDER BY city;
-- Q11 ORDER BY: urgent cases first, explicit priority mapping.
SELECT case_id,priority,case_date FROM medical_cases ORDER BY FIELD(priority,'URGENT','HIGH','MEDIUM','LOW'),case_date DESC;
-- Q12 LIMIT: ten newest patients.
SELECT patient_id,first_name,created_at FROM patients ORDER BY created_at DESC,patient_id DESC LIMIT 10;
-- Q13 OFFSET: next page.
SELECT patient_id,first_name FROM patients ORDER BY patient_id LIMIT 10 OFFSET 10;
-- Q14 GROUP BY: status totals.
SELECT case_status,COUNT(*) AS cases FROM medical_cases WHERE record_state='SUBMITTED' GROUP BY case_status;
-- Q15 HAVING: doctors with more than ten active cases.
SELECT doctor_id,COUNT(*) AS active_cases FROM medical_cases WHERE record_state='SUBMITTED' AND case_status<>'CLOSED' GROUP BY doctor_id HAVING COUNT(*)>10;
-- Q16 INNER JOIN: assigned case doctor.
SELECT c.case_id,CONCAT(d.first_name,' ',d.last_name) AS doctor FROM medical_cases c INNER JOIN doctors d ON d.doctor_id=c.doctor_id;
-- Q17 LEFT JOIN: include patients without cases.
SELECT p.patient_id,COUNT(c.case_id) AS case_count FROM patients p LEFT JOIN medical_cases c ON c.patient_id=p.patient_id GROUP BY p.patient_id;
-- Q18 RIGHT JOIN: include doctors without appointments.
SELECT d.doctor_id,COUNT(a.appointment_id) AS appointments FROM appointments a RIGHT JOIN doctors d ON d.doctor_id=a.doctor_id GROUP BY d.doctor_id;
-- Q19 CROSS JOIN: sample doctor/day planning grid, not booked slots.
SELECT d.doctor_id,days.planning_day FROM doctors d CROSS JOIN (SELECT CURRENT_DATE() AS planning_day UNION ALL SELECT CURRENT_DATE()+INTERVAL 1 DAY) days;
-- Q20 SELF JOIN: pairs of fictional patients sharing a household phone.
SELECT p.patient_id,q.patient_id,p.phone FROM patients p JOIN patients q ON p.phone=q.phone AND p.patient_id<q.patient_id;
-- Q21 UNION: patients appearing in either cases or appointments, duplicate elimination.
SELECT patient_id FROM medical_cases UNION SELECT patient_id FROM appointments;
-- Q22 UNION ALL: preserve all contact events.
SELECT patient_id,'CASE' AS kind FROM medical_cases UNION ALL SELECT patient_id,'APPOINTMENT' FROM appointments;
-- Q23 INTERSECT: patients in both sets (native since MySQL 8.0.31).
SELECT patient_id FROM medical_cases INTERSECT SELECT patient_id FROM appointments;
-- Q24 EXCEPT: case patients without appointments (native since MySQL 8.0.31).
SELECT patient_id FROM medical_cases EXCEPT SELECT patient_id FROM appointments;
-- Q25 ANY: doctors whose workload exceeds at least one other doctor's workload.
SELECT * FROM doctor_case_statistics WHERE total_cases > ANY (SELECT total_cases FROM doctor_case_statistics);
-- Q26 ALL: maximum doctor workload including ties.
SELECT * FROM doctor_case_statistics WHERE total_cases >= ALL (SELECT total_cases FROM doctor_case_statistics);
-- Q27 Simple subquery: patients with active cases.
SELECT * FROM patients WHERE patient_id IN (SELECT patient_id FROM medical_cases WHERE case_status<>'CLOSED' AND record_state='SUBMITTED');
-- Q28 Nested subquery: patients with fictional product DEMO-MED-001.
SELECT patient_id FROM medical_cases WHERE case_id IN (SELECT case_id FROM visits WHERE visit_id IN (SELECT visit_id FROM prescriptions WHERE prescription_id IN (SELECT prescription_id FROM prescription_medicines WHERE medicine_id=1)));
-- Q29 Correlated subquery: latest visit date per patient.
SELECT p.patient_id,(SELECT MAX(v.visit_date) FROM visits v JOIN medical_cases c ON c.case_id=v.case_id WHERE c.patient_id=p.patient_id) AS latest_visit FROM patients p;
-- Q30 EXISTS: patients with a follow-up plan.
SELECT p.patient_id FROM patients p WHERE EXISTS (SELECT 1 FROM medical_cases c JOIN visits v ON v.case_id=c.case_id JOIN follow_ups f ON f.visit_id=v.visit_id WHERE c.patient_id=p.patient_id);
-- Q31 NOT EXISTS: patients with no follow-up plan.
SELECT p.patient_id FROM patients p WHERE NOT EXISTS (SELECT 1 FROM medical_cases c JOIN visits v ON v.case_id=c.case_id JOIN follow_ups f ON f.visit_id=v.visit_id WHERE c.patient_id=p.patient_id);
-- Q32 CASE: workflow labels.
SELECT case_id,CASE WHEN record_state='DRAFT' THEN 'Incomplete' WHEN case_status='CLOSED' THEN 'Resolved' ELSE 'Active' END AS workflow FROM medical_cases;
-- Q33 Date functions: monthly registrations.
SELECT DATE_FORMAT(created_at+INTERVAL 330 MINUTE,'%Y-%m') AS month,COUNT(*) AS registrations FROM patients GROUP BY month ORDER BY month;
-- Q34 String functions: formatted fictional contact list.
SELECT patient_id,CONCAT(first_name,' ',last_name) AS name,LOWER(email) AS demo_email FROM patients;
-- Q35 Aggregate with joins: patient visit statistics, more than three.
SELECT p.patient_id,COUNT(v.visit_id) AS visits FROM patients p JOIN medical_cases c ON c.patient_id=p.patient_id JOIN visits v ON v.case_id=c.case_id GROUP BY p.patient_id HAVING COUNT(v.visit_id)>3;
-- Q36 Multiple joins: fictional prescription traceability.
SELECT p.patient_id,c.case_id,v.visit_id,r.prescription_id,m.medicine_code FROM patients p JOIN medical_cases c ON c.patient_id=p.patient_id JOIN visits v ON v.case_id=c.case_id JOIN prescriptions r ON r.visit_id=v.visit_id JOIN prescription_medicines pm ON pm.prescription_id=r.prescription_id JOIN medicines m ON m.medicine_id=pm.medicine_id;
-- Q37 Most common diagnosis observations.
SELECT diagnosis_name,COUNT(*) AS observations FROM diagnoses GROUP BY diagnosis_name ORDER BY observations DESC,diagnosis_name LIMIT 10;
-- Q38 Most common baseline symptoms.
SELECT s.symptom_name,COUNT(*) AS cases FROM symptoms s JOIN case_symptoms cs ON cs.symptom_id=s.symptom_id GROUP BY s.symptom_id,s.symptom_name ORDER BY cases DESC,s.symptom_name LIMIT 10;
-- Q39 Doctor workload and DB function.
SELECT doctor_id,CONCAT(first_name,' ',last_name) AS doctor,doctor_case_count(doctor_id) AS cases FROM doctors ORDER BY cases DESC;
-- Q40 Patient visit count function.
SELECT patient_id,patient_visit_count(patient_id) AS visits FROM patients ORDER BY visits DESC,patient_id LIMIT 20;
-- Q41 FULL OUTER JOIN equivalent: UNION removes duplicated matched rows.
SELECT p.patient_id,c.case_id FROM patients p LEFT JOIN medical_cases c ON c.patient_id=p.patient_id
UNION SELECT p.patient_id,c.case_id FROM patients p RIGHT JOIN medical_cases c ON c.patient_id=p.patient_id;
-- Q42 Upcoming follow-up view actually used in dashboard.
SELECT * FROM upcoming_followups ORDER BY follow_up_date,follow_up_id;
-- Q43 Cancelled appointments.
SELECT * FROM appointments WHERE status='CANCELLED' ORDER BY appointment_date DESC;
-- Q44 Doctor appointment counts.
SELECT d.doctor_id,COUNT(a.appointment_id) AS bookings FROM doctors d LEFT JOIN appointments a ON a.doctor_id=d.doctor_id GROUP BY d.doctor_id ORDER BY bookings DESC;
-- Q45 Most frequently prescribed fictional products.
SELECT m.medicine_id,m.medicine_name,COUNT(*) AS documents FROM medicines m JOIN prescription_medicines pm ON pm.medicine_id=m.medicine_id GROUP BY m.medicine_id,m.medicine_name ORDER BY documents DESC;
-- Q46 Patients with multiple submitted cases.
SELECT patient_id,COUNT(*) AS cases FROM medical_cases WHERE record_state='SUBMITTED' GROUP BY patient_id HAVING COUNT(*)>1;
-- Q47 Cases with multiple diagnosis observations.
SELECT v.case_id,COUNT(d.diagnosis_id) AS observations FROM visits v JOIN diagnoses d ON d.visit_id=v.visit_id GROUP BY v.case_id HAVING COUNT(*)>1;
-- Q48 Both a baseline symptom and visit diagnosis (same case).
SELECT DISTINCT c.patient_id FROM medical_cases c JOIN case_symptoms cs ON cs.case_id=c.case_id JOIN visits v ON v.case_id=c.case_id JOIN diagnoses d ON d.visit_id=v.visit_id WHERE cs.symptom_id=1 AND d.diagnosis_name='Fictional observation 1';
-- Q49 Latest case per patient, deterministic tie breaker.
SELECT case_id,patient_id,case_date FROM (SELECT c.*,ROW_NUMBER() OVER(PARTITION BY patient_id ORDER BY case_date DESC,case_id DESC) AS rn FROM medical_cases c) ranked WHERE rn=1;
-- Q50 Doctors with above-average workload.
SELECT * FROM doctor_case_statistics WHERE total_cases>(SELECT AVG(total_cases) FROM doctor_case_statistics);
-- Q51 Patients without prescriptions, anti-correlated subquery.
SELECT p.patient_id FROM patients p WHERE NOT EXISTS(SELECT 1 FROM medical_cases c JOIN visits v ON v.case_id=c.case_id JOIN prescriptions r ON r.visit_id=v.visit_id WHERE c.patient_id=p.patient_id);
-- Q52 Cases without any follow-up.
SELECT c.case_id FROM medical_cases c WHERE NOT EXISTS(SELECT 1 FROM visits v JOIN follow_ups f ON f.visit_id=v.visit_id WHERE v.case_id=c.case_id);
-- Q53 Materialized-view equivalent (explicitly refreshed cache).
SELECT * FROM monthly_case_statistics ORDER BY stat_month;
-- Q54 BMI function; never permanently store a derived value.
SELECT vital_id,visit_id,calculate_bmi(height_cm,weight_kg) AS bmi FROM vital_signs;
-- Q55 Portable pre-8.0.31 intersection equivalent.
SELECT DISTINCT c.patient_id FROM medical_cases c WHERE EXISTS(SELECT 1 FROM appointments a WHERE a.patient_id=c.patient_id);
-- Q56 Portable pre-8.0.31 EXCEPT equivalent.
SELECT DISTINCT c.patient_id FROM medical_cases c WHERE NOT EXISTS(SELECT 1 FROM appointments a WHERE a.patient_id=c.patient_id);
-- Q57 Case assignments for doctor 1.
SELECT * FROM patient_case_summary WHERE doctor_id=1 ORDER BY case_date DESC;
