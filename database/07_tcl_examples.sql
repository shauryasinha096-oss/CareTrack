USE caretrack;
-- Seeded admin attribution for this laboratory session.
SET @caretrack_user_id=1,@caretrack_system=NULL;
-- Atomic patient -> case -> visit. Entire transaction rolled back on demonstration.
START TRANSACTION;
CALL register_patient('DemoTCL','Learner','2001-01-01','UNDISCLOSED','0000000000',NULL,@lab_patient);
INSERT INTO medical_cases(patient_id,doctor_id,case_date,chief_complaint)
VALUES(@lab_patient,1,CURRENT_DATE(),'Fictional transaction exercise');
SET @lab_case=LAST_INSERT_ID();
INSERT INTO visits(case_id,doctor_id,visit_date,visit_type,chief_complaint)
VALUES(@lab_case,1,UTC_TIMESTAMP(),'INITIAL_CONSULTATION','Fictional encounter');
SET @lab_visit=LAST_INSERT_ID();
-- Retain earlier work while abandoning an optional prescription.
SAVEPOINT before_prescription;
INSERT INTO prescriptions(visit_id,doctor_id,prescription_date,notes)
VALUES(@lab_visit,1,CURRENT_DATE(),'Fictional optional document');
ROLLBACK TO SAVEPOINT before_prescription;
SELECT COUNT(*) AS prescription_should_be_zero FROM prescriptions WHERE visit_id=@lab_visit;
RELEASE SAVEPOINT before_prescription;
ROLLBACK;
SELECT COUNT(*) AS patient_should_be_zero FROM patients WHERE patient_id=@lab_patient;
-- COMMIT: persist a labelled lab audit event; no patient records are changed.
START TRANSACTION;
INSERT INTO audit_logs(user_id,actor_username,action,entity_type,entity_id,description)
VALUES(NULL,'SQL_LAB','INSERT','SQL_LAB',0,'Fictional TCL COMMIT demonstration');
COMMIT;
SET @caretrack_user_id=NULL,@caretrack_system=NULL;
