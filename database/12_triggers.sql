USE caretrack;

DELIMITER $$

CREATE PROCEDURE assert_audit_actor()
BEGIN
  IF @caretrack_user_id IS NULL THEN
    IF COALESCE(@caretrack_system,'') NOT IN ('SEED','SYSTEM') THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Authenticated audit context is required';
    END IF;
  ELSEIF NOT EXISTS(SELECT 1 FROM users WHERE user_id=@caretrack_user_id AND is_active=1) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Invalid audit actor';
  END IF;
END$$

CREATE TRIGGER patients_before_insert BEFORE INSERT ON patients FOR EACH ROW
BEGIN
  CALL assert_audit_actor();
  IF NEW.date_of_birth>DATE(UTC_TIMESTAMP()+INTERVAL 330 MINUTE) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Date of birth cannot be in the future'; END IF;
END$$

CREATE TRIGGER patients_audit_insert AFTER INSERT ON patients FOR EACH ROW
BEGIN
  INSERT INTO audit_logs(user_id,actor_username,action,entity_type,entity_id,description)
  VALUES(@caretrack_user_id,COALESCE((SELECT username FROM users WHERE user_id=@caretrack_user_id),@caretrack_system),
    'INSERT','PATIENT',CAST(NEW.patient_id AS CHAR),'Patient record insert');
END$$

CREATE TRIGGER patients_before_update BEFORE UPDATE ON patients FOR EACH ROW
BEGIN
  CALL assert_audit_actor();
  SET NEW.updated_at=UTC_TIMESTAMP(6);
  IF NEW.date_of_birth>DATE(UTC_TIMESTAMP()+INTERVAL 330 MINUTE) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Date of birth cannot be in the future'; END IF;
END$$

CREATE TRIGGER patients_audit_update AFTER UPDATE ON patients FOR EACH ROW
BEGIN
  INSERT INTO audit_logs(user_id,actor_username,action,entity_type,entity_id,description)
  VALUES(@caretrack_user_id,COALESCE((SELECT username FROM users WHERE user_id=@caretrack_user_id),@caretrack_system),
    'UPDATE','PATIENT',CAST(NEW.patient_id AS CHAR),'Patient record update');
END$$

CREATE TRIGGER medical_cases_before_insert BEFORE INSERT ON medical_cases FOR EACH ROW
BEGIN
  CALL assert_audit_actor();
  IF NEW.case_date>DATE(UTC_TIMESTAMP()+INTERVAL 330 MINUTE) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Case date cannot be in the future'; END IF;
  IF NEW.record_state='SUBMITTED' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Create a draft and initial visit before submission'; END IF;
END$$

CREATE TRIGGER medical_cases_audit_insert AFTER INSERT ON medical_cases FOR EACH ROW
BEGIN
  INSERT INTO audit_logs(user_id,actor_username,action,entity_type,entity_id,description)
  VALUES(@caretrack_user_id,COALESCE((SELECT username FROM users WHERE user_id=@caretrack_user_id),@caretrack_system),
    'INSERT','CASE',CAST(NEW.case_id AS CHAR),'Case record insert');
END$$

CREATE TRIGGER medical_cases_before_update BEFORE UPDATE ON medical_cases FOR EACH ROW
BEGIN
  CALL assert_audit_actor();
  SET NEW.updated_at=UTC_TIMESTAMP(6);
  IF NEW.case_date>DATE(UTC_TIMESTAMP()+INTERVAL 330 MINUTE) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Case date cannot be in the future'; END IF;
  IF OLD.record_state='SUBMITTED' AND NEW.record_state='DRAFT' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Submitted cases cannot revert to drafts'; END IF;
  IF OLD.record_state='SUBMITTED' AND NEW.patient_id<>OLD.patient_id THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Case patient cannot be reassigned'; END IF;
  IF OLD.case_status='CLOSED' AND NEW.case_status<>'CLOSED' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Closed cases cannot be reopened'; END IF;
  IF NEW.record_state='SUBMITTED' AND NOT EXISTS(SELECT 1 FROM visits WHERE case_id=NEW.case_id AND visit_type='INITIAL_CONSULTATION') THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Submitted cases require an initial visit'; END IF;
  IF NEW.case_status='CLOSED' AND EXISTS(SELECT 1 FROM follow_ups f JOIN visits v ON v.visit_id=f.visit_id WHERE v.case_id=NEW.case_id AND f.status='PENDING') THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Resolve pending follow-ups first'; END IF;
END$$

CREATE TRIGGER medical_cases_audit_update AFTER UPDATE ON medical_cases FOR EACH ROW
BEGIN
  INSERT INTO audit_logs(user_id,actor_username,action,entity_type,entity_id,description)
  VALUES(@caretrack_user_id,COALESCE((SELECT username FROM users WHERE user_id=@caretrack_user_id),@caretrack_system),
    IF(NEW.case_status='CLOSED' AND OLD.case_status<>'CLOSED','CLOSE','UPDATE'),'CASE',CAST(NEW.case_id AS CHAR),'Case record update');
END$$

CREATE TRIGGER lifestyle_timestamp BEFORE UPDATE ON lifestyle_history FOR EACH ROW
SET NEW.updated_at=UTC_TIMESTAMP(6)$$

CREATE TRIGGER doctors_role_insert BEFORE INSERT ON doctors FOR EACH ROW
BEGIN
  IF NOT EXISTS(SELECT 1 FROM users WHERE user_id=NEW.user_id AND role='DOCTOR') THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Doctor profile requires a DOCTOR user';
  END IF;
END$$

CREATE TRIGGER followups_guard_insert BEFORE INSERT ON follow_ups FOR EACH ROW
BEGIN
  DECLARE origin DATE;
  SELECT DATE(visit_date+INTERVAL 330 MINUTE) INTO origin FROM visits WHERE visit_id=NEW.visit_id;
  IF NEW.scheduled_date<origin OR (NEW.actual_date IS NOT NULL AND
     (NEW.actual_date<origin OR NEW.actual_date>DATE(UTC_TIMESTAMP()+INTERVAL 330 MINUTE))) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Invalid follow-up chronology';
  END IF;
END$$

CREATE TRIGGER history_date_insert BEFORE INSERT ON medical_history FOR EACH ROW
BEGIN
  IF NEW.diagnosed_date>DATE(UTC_TIMESTAMP()+INTERVAL 330 MINUTE) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='History date cannot be in the future';
  END IF;
END$$

CREATE TRIGGER doctors_role_update BEFORE UPDATE ON doctors FOR EACH ROW
BEGIN
  IF NOT EXISTS(SELECT 1 FROM users WHERE user_id=NEW.user_id AND role='DOCTOR') THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Doctor profile requires a DOCTOR user';
  END IF;
END$$

CREATE TRIGGER followups_guard_update BEFORE UPDATE ON follow_ups FOR EACH ROW
BEGIN
  DECLARE origin DATE;
  SELECT DATE(visit_date+INTERVAL 330 MINUTE) INTO origin FROM visits WHERE visit_id=NEW.visit_id;
  IF NEW.scheduled_date<origin OR (NEW.actual_date IS NOT NULL AND
     (NEW.actual_date<origin OR NEW.actual_date>DATE(UTC_TIMESTAMP()+INTERVAL 330 MINUTE))) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Invalid follow-up chronology';
  END IF;
END$$

CREATE TRIGGER history_date_update BEFORE UPDATE ON medical_history FOR EACH ROW
BEGIN
  IF NEW.diagnosed_date>DATE(UTC_TIMESTAMP()+INTERVAL 330 MINUTE) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='History date cannot be in the future';
  END IF;
END$$

CREATE TRIGGER users_role_guard BEFORE UPDATE ON users FOR EACH ROW
BEGIN
  IF NEW.role<>'DOCTOR' AND EXISTS(SELECT 1 FROM doctors WHERE user_id=OLD.user_id) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Deactivate a referenced doctor rather than changing role';
  END IF;
END$$

DELIMITER ;
