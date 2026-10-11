USE caretrack;
-- Seeded admin attribution for this laboratory session.
SET @caretrack_user_id=1,@caretrack_system=NULL;
DROP PROCEDURE IF EXISTS dml_restrict_lab;
DELIMITER $$
CREATE PROCEDURE dml_restrict_lab()
BEGIN
  DECLARE blocked BOOLEAN DEFAULT FALSE;
  BEGIN
    DECLARE CONTINUE HANDLER FOR 1451 SET blocked=TRUE;
    DELETE FROM patients WHERE patient_id=1;
  END;
  SELECT blocked AS clinical_parent_delete_was_restricted;
END$$
DELIMITER ;
START TRANSACTION;
-- INSERT: temporary fictional patient; audit trigger participates in this transaction.
INSERT INTO patients(first_name,last_name,date_of_birth,gender,phone)
VALUES('DemoDML','Learner','2000-01-01','UNDISCLOSED','0000000000');
SET @lab_patient=LAST_INSERT_ID();
INSERT INTO medical_history(patient_id,condition_name,notes)
VALUES(@lab_patient,'Fictional training history','Will cascade when parent is deleted');
-- Normal UPDATE.
UPDATE patients SET city='Pune' WHERE patient_id=@lab_patient;
-- Multiple-row UPDATE (rolled back).
UPDATE medical_cases SET priority='LOW' WHERE case_status='OPEN' AND record_state='SUBMITTED';
-- Relationship UPDATE using a join (rolled back).
UPDATE medical_cases c JOIN doctors d ON d.doctor_id=c.doctor_id
SET c.notes='Fictional relationship UPDATE demonstration' WHERE d.doctor_id=1 AND c.case_status='OPEN';
-- DELETE with CASCADE: history is owned by this otherwise unused patient.
DELETE FROM patients WHERE patient_id=@lab_patient;
SELECT COUNT(*) AS remaining_owned_history FROM medical_history WHERE patient_id=@lab_patient;
-- Non-cascading RESTRICT: catch the expected FK failure without aborting this script.
-- The lab routine was created before START TRANSACTION to avoid implicit commit.
CALL dml_restrict_lab();
ROLLBACK;
DROP PROCEDURE dml_restrict_lab;
SET @caretrack_user_id=NULL,@caretrack_system=NULL;
