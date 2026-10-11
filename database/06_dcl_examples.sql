-- Run with role-management privileges. Roles have no passwords and cannot log in.
-- API JWT roles are separate from MySQL roles; a pooled API connection cannot
-- safely impersonate individual doctors. API enforces row ownership separately.
CREATE ROLE IF NOT EXISTS 'caretrack_admin_role','caretrack_doctor_role','caretrack_reception_role';
GRANT ALL PRIVILEGES ON caretrack.* TO 'caretrack_admin_role';
GRANT SELECT ON caretrack.doctors TO 'caretrack_doctor_role';
GRANT SELECT,INSERT,UPDATE ON caretrack.patients TO 'caretrack_doctor_role';
GRANT SELECT,INSERT,UPDATE ON caretrack.medical_cases TO 'caretrack_doctor_role';
GRANT SELECT,INSERT,UPDATE ON caretrack.visits TO 'caretrack_doctor_role';
GRANT SELECT,INSERT,UPDATE ON caretrack.diagnoses TO 'caretrack_doctor_role';
GRANT SELECT,INSERT,UPDATE ON caretrack.prescriptions TO 'caretrack_doctor_role';
GRANT SELECT,INSERT,UPDATE ON caretrack.prescription_medicines TO 'caretrack_doctor_role';
GRANT SELECT ON caretrack.medicines TO 'caretrack_doctor_role';
GRANT SELECT ON caretrack.receptionist_patients TO 'caretrack_reception_role';
GRANT SELECT,INSERT,UPDATE ON caretrack.appointments TO 'caretrack_reception_role';
GRANT SELECT ON caretrack.upcoming_followups TO 'caretrack_reception_role';
-- Give a permission, demonstrate its removal. Final role cannot delete appointments.
GRANT DELETE ON caretrack.appointments TO 'caretrack_reception_role';
REVOKE DELETE ON caretrack.appointments FROM 'caretrack_reception_role';
SHOW GRANTS FOR 'caretrack_reception_role';
-- For a dedicated laboratory login provision a password interactively, then:
-- GRANT 'caretrack_reception_role' TO 'your_lab_login'@'localhost';
-- SET DEFAULT ROLE 'caretrack_reception_role' TO 'your_lab_login'@'localhost';
-- Never grant these schema-wide doctor permissions to untrusted clinical users.
