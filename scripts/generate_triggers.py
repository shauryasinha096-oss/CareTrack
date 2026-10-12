from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
parts=['-- Select the target database in your connection.','DELIMITER $$', '''CREATE PROCEDURE assert_audit_actor()
BEGIN
  IF @caretrack_user_id IS NULL THEN
    IF COALESCE(@caretrack_system,'') NOT IN ('SEED','SYSTEM') THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Authenticated audit context is required';
    END IF;
  ELSEIF NOT EXISTS(SELECT 1 FROM users WHERE user_id=@caretrack_user_id AND is_active=1) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Invalid audit actor';
  END IF;
END$$''']
for table,key,entity in [('patients','patient_id','PATIENT'),('medical_cases','case_id','CASE')]:
    for event in ['INSERT','UPDATE']:
        checks=['CALL assert_audit_actor();']
        if event=='UPDATE': checks.append('SET NEW.updated_at=UTC_TIMESTAMP(6);')
        if table=='patients':
            checks.append("IF NEW.date_of_birth>DATE(UTC_TIMESTAMP()+INTERVAL 330 MINUTE) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Date of birth cannot be in the future'; END IF;")
        else:
            checks.append("IF NEW.case_date>DATE(UTC_TIMESTAMP()+INTERVAL 330 MINUTE) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Case date cannot be in the future'; END IF;")
            if event=='INSERT': checks.append("IF NEW.record_state='SUBMITTED' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Create a draft and initial visit before submission'; END IF;")
            else:
                checks.extend([
                    "IF OLD.record_state='SUBMITTED' AND NEW.record_state='DRAFT' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Submitted cases cannot revert to drafts'; END IF;",
                    "IF OLD.record_state='SUBMITTED' AND NEW.patient_id<>OLD.patient_id THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Case patient cannot be reassigned'; END IF;",
                    "IF OLD.case_status='CLOSED' AND NEW.case_status<>'CLOSED' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Closed cases cannot be reopened'; END IF;",
                    "IF NEW.record_state='SUBMITTED' AND NOT EXISTS(SELECT 1 FROM visits WHERE case_id=NEW.case_id AND visit_type='INITIAL_CONSULTATION') THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Submitted cases require an initial visit'; END IF;",
                    "IF NEW.case_status='CLOSED' AND EXISTS(SELECT 1 FROM follow_ups f JOIN visits v ON v.visit_id=f.visit_id WHERE v.case_id=NEW.case_id AND f.status='PENDING') THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Resolve pending follow-ups first'; END IF;",
                ])
        parts.append(f'CREATE TRIGGER {table}_before_{event.lower()} BEFORE {event} ON {table} FOR EACH ROW\nBEGIN\n  '+'\n  '.join(checks)+'\nEND$$')
        action="'INSERT'" if event=='INSERT' else ("IF(NEW.case_status='CLOSED' AND OLD.case_status<>'CLOSED','CLOSE','UPDATE')" if table=='medical_cases' else "'UPDATE'")
        parts.append(f'''CREATE TRIGGER {table}_audit_{event.lower()} AFTER {event} ON {table} FOR EACH ROW
BEGIN
  INSERT INTO audit_logs(user_id,actor_username,action,entity_type,entity_id,description)
  VALUES(@caretrack_user_id,COALESCE((SELECT username FROM users WHERE user_id=@caretrack_user_id),@caretrack_system),
    {action},'{entity}',CAST(NEW.{key} AS CHAR),'{entity.title()} record {event.lower()}');
END$$''')
parts.append('''CREATE TRIGGER lifestyle_timestamp BEFORE UPDATE ON lifestyle_history FOR EACH ROW
SET NEW.updated_at=UTC_TIMESTAMP(6)$$''')
for event in ['INSERT','UPDATE']:
    parts.append(f'''CREATE TRIGGER doctors_role_{event.lower()} BEFORE {event} ON doctors FOR EACH ROW
BEGIN
  IF NOT EXISTS(SELECT 1 FROM users WHERE user_id=NEW.user_id AND role='DOCTOR') THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Doctor profile requires a DOCTOR user';
  END IF;
END$$''')
    parts.append(f'''CREATE TRIGGER followups_guard_{event.lower()} BEFORE {event} ON follow_ups FOR EACH ROW
BEGIN
  DECLARE origin DATE;
  SELECT DATE(visit_date+INTERVAL 330 MINUTE) INTO origin FROM visits WHERE visit_id=NEW.visit_id;
  IF NEW.scheduled_date<origin OR (NEW.actual_date IS NOT NULL AND
     (NEW.actual_date<origin OR NEW.actual_date>DATE(UTC_TIMESTAMP()+INTERVAL 330 MINUTE))) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Invalid follow-up chronology';
  END IF;
END$$''')
    parts.append(f'''CREATE TRIGGER history_date_{event.lower()} BEFORE {event} ON medical_history FOR EACH ROW
BEGIN
  IF NEW.diagnosed_date>DATE(UTC_TIMESTAMP()+INTERVAL 330 MINUTE) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='History date cannot be in the future';
  END IF;
END$$''')
parts.extend(['''CREATE TRIGGER users_role_guard BEFORE UPDATE ON users FOR EACH ROW
BEGIN
  IF NEW.role<>'DOCTOR' AND EXISTS(SELECT 1 FROM doctors WHERE user_id=OLD.user_id) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Deactivate a referenced doctor rather than changing role';
  END IF;
END$$''','DELIMITER ;'])
(ROOT/'database/12_triggers.sql').write_text('\n\n'.join(parts)+'\n')
print('Generated meaningful audit, timestamp, role and date guards.')
