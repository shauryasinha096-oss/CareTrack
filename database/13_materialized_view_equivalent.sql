-- MySQL does not provide native materialized views. This is a precomputed cache.
DELIMITER $$
CREATE PROCEDURE refresh_monthly_case_statistics()
BEGIN
  DECLARE acquired INT DEFAULT 0;
  DECLARE refreshed DATETIME(6);
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    IF acquired=1 THEN DO RELEASE_LOCK(CONCAT(DATABASE(),'.monthly_refresh')); END IF;
    RESIGNAL;
  END;
  SELECT GET_LOCK(CONCAT(DATABASE(),'.monthly_refresh'),5) INTO acquired;
  IF acquired<>1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Another refresh is running'; END IF;
  START TRANSACTION;
  SET refreshed=UTC_TIMESTAMP(6);
  DELETE FROM monthly_case_statistics;
  INSERT INTO monthly_case_statistics(stat_month,total_cases,unique_patients,completed_cases,refreshed_at)
  SELECT CAST(DATE_FORMAT(case_date,'%Y-%m-01') AS DATE),COUNT(*),COUNT(DISTINCT patient_id),
         SUM(case_status='CLOSED'),refreshed
  FROM medical_cases WHERE record_state='SUBMITTED' GROUP BY CAST(DATE_FORMAT(case_date,'%Y-%m-01') AS DATE);
  COMMIT;
  DO RELEASE_LOCK(CONCAT(DATABASE(),'.monthly_refresh'));
END$$
DELIMITER ;
-- Invoke outside another transaction: CALL refresh_monthly_case_statistics();
-- Optional, deliberate scheduler setup (not enabled automatically):
-- CREATE EVENT refresh_caretrack_monthly ON SCHEDULE EVERY 1 HOUR
-- DO CALL refresh_monthly_case_statistics();
