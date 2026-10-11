USE caretrack;
DELIMITER $$
-- Caller owns transaction for these composable business procedures.
CREATE PROCEDURE register_patient(IN p_first VARCHAR(50),IN p_last VARCHAR(50),IN p_dob DATE,
 IN p_gender VARCHAR(20),IN p_phone VARCHAR(20),IN p_email VARCHAR(254),OUT p_id INT)
BEGIN
  IF CHAR_LENGTH(TRIM(p_first))=0 OR CHAR_LENGTH(TRIM(p_last))=0
     OR p_dob>DATE(UTC_TIMESTAMP()+INTERVAL 330 MINUTE) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Invalid fictional patient details';
  END IF;
  INSERT INTO patients(first_name,last_name,date_of_birth,gender,phone,email)
  VALUES(TRIM(p_first),TRIM(p_last),p_dob,p_gender,p_phone,NULLIF(LOWER(TRIM(p_email)),''));
  SET p_id=LAST_INSERT_ID();
END$$
CREATE PROCEDURE close_case(IN p_case INT)
BEGIN
  DECLARE state VARCHAR(10) DEFAULT NULL;
  SELECT record_state INTO state FROM medical_cases WHERE case_id=p_case FOR UPDATE;
  IF state IS NULL OR state<>'SUBMITTED' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='A submitted case is required'; END IF;
  IF EXISTS(SELECT 1 FROM follow_ups f JOIN visits v ON v.visit_id=f.visit_id
            WHERE v.case_id=p_case AND f.status='PENDING') THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Resolve pending follow-ups before closing';
  END IF;
  UPDATE medical_cases SET case_status='CLOSED' WHERE case_id=p_case;
END$$
CREATE PROCEDURE schedule_followup(IN p_visit INT,IN p_date DATE,IN p_reason VARCHAR(255),IN p_instructions TEXT,OUT p_id INT)
BEGIN
  DECLARE origin DATE DEFAULT NULL;
  SELECT DATE(visit_date+INTERVAL 330 MINUTE) INTO origin FROM visits WHERE visit_id=p_visit;
  IF origin IS NULL OR p_date<origin OR CHAR_LENGTH(TRIM(p_reason))=0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Invalid follow-up origin, date or reason';
  END IF;
  INSERT INTO follow_ups(visit_id,scheduled_date,reason,instructions) VALUES(p_visit,p_date,p_reason,p_instructions);
  SET p_id=LAST_INSERT_ID();
END$$
CREATE PROCEDURE schedule_appointment(IN p_patient INT,IN p_doctor INT,IN p_date DATE,
 IN p_start TIME,IN p_end TIME,IN p_type VARCHAR(20),IN p_notes TEXT,OUT p_id INT)
BEGIN
  DECLARE locked_doctor INT DEFAULT NULL;
  DECLARE collisions INT DEFAULT 0;
  SELECT doctor_id INTO locked_doctor FROM doctors WHERE doctor_id=p_doctor FOR UPDATE;
  IF locked_doctor IS NULL THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Doctor not found'; END IF;
  SELECT COUNT(*) INTO collisions FROM appointments
  WHERE doctor_id=p_doctor AND appointment_date=p_date AND status<>'CANCELLED'
    AND start_time<p_end AND end_time>p_start FOR UPDATE;
  IF collisions>0 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Appointment overlaps an existing booking'; END IF;
  INSERT INTO appointments(patient_id,doctor_id,appointment_date,start_time,end_time,appointment_type,notes)
  VALUES(p_patient,p_doctor,p_date,p_start,p_end,p_type,p_notes);
  SET p_id=LAST_INSERT_ID();
END$$
DELIMITER ;
