-- CareTrack: fictional data only. MySQL 8.0.31+ / InnoDB.

CREATE TABLE `users` (
  `user_id` INT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(50) NOT NULL,
  `email` VARCHAR(254) NOT NULL,
  `password_hash` VARCHAR(255) NOT NULL,
  `role` VARCHAR(20) NOT NULL,
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`user_id`),
  CONSTRAINT uq_users_username UNIQUE (`username`),
  CONSTRAINT uq_users_email UNIQUE (`email`),
  CONSTRAINT ck_users_0 CHECK (role IN ('ADMIN','DOCTOR','RECEPTIONIST')),
  CONSTRAINT ck_users_1 CHECK (is_active IN (0,1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `doctors` (
  `doctor_id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `first_name` VARCHAR(50) NOT NULL,
  `last_name` VARCHAR(50) NOT NULL,
  `specialization` VARCHAR(100) NOT NULL,
  `license_number` VARCHAR(50) NOT NULL,
  `phone` VARCHAR(20) NOT NULL,
  `email` VARCHAR(254) NOT NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`doctor_id`),
  CONSTRAINT uq_doctors_user_id UNIQUE (`user_id`),
  CONSTRAINT fk_doctors_user_id FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT uq_doctors_license_number UNIQUE (`license_number`),
  CONSTRAINT uq_doctors_email UNIQUE (`email`),
  INDEX ix_doctors_0 (last_name, first_name, doctor_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `patients` (
  `patient_id` INT NOT NULL AUTO_INCREMENT,
  `first_name` VARCHAR(50) NOT NULL,
  `last_name` VARCHAR(50) NOT NULL,
  `date_of_birth` DATE NOT NULL,
  `gender` VARCHAR(20) NOT NULL,
  `blood_group` VARCHAR(3) NULL,
  `phone` VARCHAR(20) NOT NULL,
  `email` VARCHAR(254) NULL,
  `address` VARCHAR(255) NULL,
  `city` VARCHAR(80) NULL,
  `occupation` VARCHAR(100) NULL,
  `marital_status` VARCHAR(20) NULL,
  `emergency_contact_name` VARCHAR(100) NULL,
  `emergency_contact_phone` VARCHAR(20) NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`patient_id`),
  CONSTRAINT uq_patients_email UNIQUE (`email`),
  CONSTRAINT ck_patients_0 CHECK (gender IN ('FEMALE','MALE','NON_BINARY','OTHER','UNDISCLOSED')),
  CONSTRAINT ck_patients_1 CHECK (blood_group IS NULL OR blood_group IN ('A+','A-','B+','B-','AB+','AB-','O+','O-')),
  CONSTRAINT ck_patients_2 CHECK (marital_status IS NULL OR marital_status IN ('SINGLE','MARRIED','DIVORCED','WIDOWED','UNDISCLOSED')),
  INDEX ix_patients_0 (last_name, first_name, patient_id),
  INDEX ix_patients_1 (first_name, patient_id),
  INDEX ix_patients_2 (phone),
  INDEX ix_patients_3 (created_at, patient_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `medical_cases` (
  `case_id` INT NOT NULL AUTO_INCREMENT,
  `patient_id` INT NOT NULL,
  `doctor_id` INT NOT NULL,
  `case_date` DATE NOT NULL,
  `chief_complaint` TEXT NOT NULL,
  `present_illness` TEXT NULL,
  `case_status` VARCHAR(20) NOT NULL DEFAULT 'OPEN',
  `priority` VARCHAR(10) NOT NULL DEFAULT 'MEDIUM',
  `record_state` VARCHAR(10) NOT NULL DEFAULT 'DRAFT',
  `notes` TEXT NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`case_id`),
  CONSTRAINT fk_medical_cases_patient_id FOREIGN KEY (`patient_id`) REFERENCES `patients` (`patient_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_medical_cases_doctor_id FOREIGN KEY (`doctor_id`) REFERENCES `doctors` (`doctor_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT ck_medical_cases_0 CHECK (case_status IN ('OPEN','UNDER_REVIEW','FOLLOW_UP','CLOSED')),
  CONSTRAINT ck_medical_cases_1 CHECK (priority IN ('LOW','MEDIUM','HIGH','URGENT')),
  CONSTRAINT ck_medical_cases_2 CHECK (record_state IN ('DRAFT','SUBMITTED')),
  CONSTRAINT ck_medical_cases_3 CHECK (record_state = 'DRAFT' OR CHAR_LENGTH(TRIM(chief_complaint)) > 0),
  CONSTRAINT ck_medical_cases_4 CHECK (record_state <> 'DRAFT' OR case_status = 'OPEN'),
  INDEX ix_medical_cases_0 (patient_id, case_date, case_id),
  INDEX ix_medical_cases_1 (doctor_id, record_state, case_status, case_date, case_id),
  INDEX ix_medical_cases_2 (record_state, case_status, case_date, case_id),
  INDEX ix_medical_cases_3 (case_date, case_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `visits` (
  `visit_id` INT NOT NULL AUTO_INCREMENT,
  `case_id` INT NOT NULL,
  `doctor_id` INT NOT NULL,
  `visit_date` DATETIME(6) NOT NULL,
  `visit_type` VARCHAR(25) NOT NULL,
  `chief_complaint` TEXT NOT NULL,
  `doctor_notes` TEXT NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`visit_id`),
  CONSTRAINT fk_visits_case_id FOREIGN KEY (`case_id`) REFERENCES `medical_cases` (`case_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_visits_doctor_id FOREIGN KEY (`doctor_id`) REFERENCES `doctors` (`doctor_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT ck_visits_0 CHECK (visit_type IN ('INITIAL_CONSULTATION','FOLLOW_UP','EMERGENCY','ROUTINE_CHECKUP')),
  INDEX ix_visits_0 (case_id, visit_date, visit_id),
  INDEX ix_visits_1 (doctor_id, visit_date, visit_id),
  INDEX ix_visits_2 (visit_date, visit_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `symptoms` (
  `symptom_id` INT NOT NULL AUTO_INCREMENT,
  `symptom_name` VARCHAR(100) NOT NULL,
  `description` TEXT NULL,
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
  PRIMARY KEY (`symptom_id`),
  CONSTRAINT uq_symptoms_symptom_name UNIQUE (`symptom_name`),
  CONSTRAINT ck_symptoms_0 CHECK (is_active IN (0,1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `case_symptoms` (
  `case_id` INT NOT NULL,
  `symptom_id` INT NOT NULL,
  `severity` VARCHAR(10) NOT NULL,
  `duration` VARCHAR(80) NULL,
  `frequency` VARCHAR(80) NULL,
  `notes` TEXT NULL,
  `recorded_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`case_id`, `symptom_id`),
  CONSTRAINT fk_case_symptoms_case_id FOREIGN KEY (`case_id`) REFERENCES `medical_cases` (`case_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_case_symptoms_symptom_id FOREIGN KEY (`symptom_id`) REFERENCES `symptoms` (`symptom_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT ck_case_symptoms_0 CHECK (severity IN ('MILD','MODERATE','SEVERE')),
  INDEX ix_case_symptoms_0 (symptom_id, case_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `medical_history` (
  `history_id` INT NOT NULL AUTO_INCREMENT,
  `patient_id` INT NOT NULL,
  `condition_name` VARCHAR(150) NOT NULL,
  `diagnosed_date` DATE NULL,
  `treatment` TEXT NULL,
  `notes` TEXT NULL,
  PRIMARY KEY (`history_id`),
  CONSTRAINT fk_medical_history_patient_id FOREIGN KEY (`patient_id`) REFERENCES `patients` (`patient_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  INDEX ix_medical_history_0 (patient_id, diagnosed_date, history_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `allergies` (
  `allergy_id` INT NOT NULL AUTO_INCREMENT,
  `patient_id` INT NOT NULL,
  `allergen` VARCHAR(150) NOT NULL,
  `allergy_type` VARCHAR(20) NOT NULL,
  `reaction` VARCHAR(255) NULL,
  `severity` VARCHAR(10) NOT NULL,
  `notes` TEXT NULL,
  PRIMARY KEY (`allergy_id`),
  CONSTRAINT fk_allergies_patient_id FOREIGN KEY (`patient_id`) REFERENCES `patients` (`patient_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT ck_allergies_0 CHECK (allergy_type IN ('MEDICATION','FOOD','ENVIRONMENTAL','OTHER')),
  CONSTRAINT ck_allergies_1 CHECK (severity IN ('MILD','MODERATE','SEVERE')),
  INDEX ix_allergies_0 (patient_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `lifestyle_history` (
  `lifestyle_id` INT NOT NULL AUTO_INCREMENT,
  `patient_id` INT NOT NULL,
  `smoking_status` VARCHAR(15) NULL,
  `alcohol_status` VARCHAR(15) NULL,
  `exercise_frequency` VARCHAR(30) NULL,
  `sleep_hours` DECIMAL(4,2) NULL,
  `diet_type` VARCHAR(30) NULL,
  `occupation_notes` TEXT NULL,
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`lifestyle_id`),
  CONSTRAINT uq_lifestyle_history_patient_id UNIQUE (`patient_id`),
  CONSTRAINT fk_lifestyle_history_patient_id FOREIGN KEY (`patient_id`) REFERENCES `patients` (`patient_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT ck_lifestyle_history_0 CHECK (smoking_status IS NULL OR smoking_status IN ('NEVER','FORMER','CURRENT','UNDISCLOSED')),
  CONSTRAINT ck_lifestyle_history_1 CHECK (alcohol_status IS NULL OR alcohol_status IN ('NEVER','FORMER','CURRENT','UNDISCLOSED')),
  CONSTRAINT ck_lifestyle_history_2 CHECK (sleep_hours IS NULL OR sleep_hours BETWEEN 0 AND 24)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `vital_signs` (
  `vital_id` INT NOT NULL AUTO_INCREMENT,
  `visit_id` INT NOT NULL,
  `temperature` DECIMAL(5,2) NULL,
  `systolic_bp` SMALLINT NULL,
  `diastolic_bp` SMALLINT NULL,
  `heart_rate` SMALLINT NULL,
  `respiratory_rate` SMALLINT NULL,
  `oxygen_saturation` DECIMAL(5,2) NULL,
  `height_cm` DECIMAL(6,2) NULL,
  `weight_kg` DECIMAL(6,2) NULL,
  PRIMARY KEY (`vital_id`),
  CONSTRAINT uq_vital_signs_visit_id UNIQUE (`visit_id`),
  CONSTRAINT fk_vital_signs_visit_id FOREIGN KEY (`visit_id`) REFERENCES `visits` (`visit_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT ck_vital_signs_0 CHECK (temperature IS NULL OR temperature > 0),
  CONSTRAINT ck_vital_signs_1 CHECK (systolic_bp IS NULL OR systolic_bp > 0),
  CONSTRAINT ck_vital_signs_2 CHECK (diastolic_bp IS NULL OR diastolic_bp > 0),
  CONSTRAINT ck_vital_signs_3 CHECK (heart_rate IS NULL OR heart_rate > 0),
  CONSTRAINT ck_vital_signs_4 CHECK (respiratory_rate IS NULL OR respiratory_rate > 0),
  CONSTRAINT ck_vital_signs_5 CHECK (oxygen_saturation IS NULL OR oxygen_saturation BETWEEN 0 AND 100),
  CONSTRAINT ck_vital_signs_6 CHECK (height_cm IS NULL OR height_cm > 0),
  CONSTRAINT ck_vital_signs_7 CHECK (weight_kg IS NULL OR weight_kg > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `examinations` (
  `examination_id` INT NOT NULL AUTO_INCREMENT,
  `visit_id` INT NOT NULL,
  `general_appearance` TEXT NULL,
  `cardiovascular_findings` TEXT NULL,
  `respiratory_findings` TEXT NULL,
  `neurological_findings` TEXT NULL,
  `abdominal_findings` TEXT NULL,
  `skin_findings` TEXT NULL,
  `other_findings` TEXT NULL,
  PRIMARY KEY (`examination_id`),
  CONSTRAINT uq_examinations_visit_id UNIQUE (`visit_id`),
  CONSTRAINT fk_examinations_visit_id FOREIGN KEY (`visit_id`) REFERENCES `visits` (`visit_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `diagnoses` (
  `diagnosis_id` INT NOT NULL AUTO_INCREMENT,
  `visit_id` INT NOT NULL,
  `diagnosis_name` VARCHAR(150) NOT NULL,
  `diagnosis_type` VARCHAR(15) NOT NULL DEFAULT 'PRIMARY',
  `notes` TEXT NULL,
  PRIMARY KEY (`diagnosis_id`),
  CONSTRAINT fk_diagnoses_visit_id FOREIGN KEY (`visit_id`) REFERENCES `visits` (`visit_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT uq_diagnoses_group_0 UNIQUE (visit_id, diagnosis_name, diagnosis_type),
  CONSTRAINT ck_diagnoses_0 CHECK (diagnosis_type IN ('PRIMARY','SECONDARY','DIFFERENTIAL')),
  INDEX ix_diagnoses_0 (diagnosis_name, visit_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `medicines` (
  `medicine_id` INT NOT NULL AUTO_INCREMENT,
  `medicine_code` VARCHAR(40) NOT NULL,
  `medicine_name` VARCHAR(150) NOT NULL,
  `generic_name` VARCHAR(150) NOT NULL,
  `manufacturer` VARCHAR(150) NOT NULL,
  `medicine_type` VARCHAR(15) NOT NULL,
  `strength` VARCHAR(50) NOT NULL,
  `form` VARCHAR(50) NOT NULL,
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
  PRIMARY KEY (`medicine_id`),
  CONSTRAINT uq_medicines_medicine_code UNIQUE (`medicine_code`),
  CONSTRAINT ck_medicines_0 CHECK (medicine_type IN ('TABLET','CAPSULE','SYRUP','INJECTION','CREAM','DROPS')),
  CONSTRAINT ck_medicines_1 CHECK (is_active IN (0,1)),
  INDEX ix_medicines_0 (medicine_name, medicine_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `prescriptions` (
  `prescription_id` INT NOT NULL AUTO_INCREMENT,
  `visit_id` INT NOT NULL,
  `doctor_id` INT NOT NULL,
  `prescription_date` DATE NOT NULL,
  `notes` TEXT NULL,
  PRIMARY KEY (`prescription_id`),
  CONSTRAINT uq_prescriptions_visit_id UNIQUE (`visit_id`),
  CONSTRAINT fk_prescriptions_visit_id FOREIGN KEY (`visit_id`) REFERENCES `visits` (`visit_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_prescriptions_doctor_id FOREIGN KEY (`doctor_id`) REFERENCES `doctors` (`doctor_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  INDEX ix_prescriptions_0 (doctor_id, prescription_date, prescription_id),
  INDEX ix_prescriptions_1 (prescription_date, prescription_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `prescription_medicines` (
  `prescription_id` INT NOT NULL,
  `medicine_id` INT NOT NULL,
  `dosage` VARCHAR(100) NOT NULL,
  `frequency` VARCHAR(100) NOT NULL,
  `route` VARCHAR(50) NOT NULL,
  `duration_days` SMALLINT NOT NULL,
  `instructions` TEXT NULL,
  PRIMARY KEY (`prescription_id`, `medicine_id`),
  CONSTRAINT fk_prescription_medicines_prescription_id FOREIGN KEY (`prescription_id`) REFERENCES `prescriptions` (`prescription_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_prescription_medicines_medicine_id FOREIGN KEY (`medicine_id`) REFERENCES `medicines` (`medicine_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT ck_prescription_medicines_0 CHECK (duration_days > 0),
  INDEX ix_prescription_medicines_0 (medicine_id, prescription_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `appointments` (
  `appointment_id` INT NOT NULL AUTO_INCREMENT,
  `patient_id` INT NOT NULL,
  `doctor_id` INT NOT NULL,
  `appointment_date` DATE NOT NULL,
  `start_time` TIME NOT NULL,
  `end_time` TIME NOT NULL,
  `appointment_type` VARCHAR(20) NOT NULL,
  `status` VARCHAR(15) NOT NULL DEFAULT 'SCHEDULED',
  `notes` TEXT NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`appointment_id`),
  CONSTRAINT fk_appointments_patient_id FOREIGN KEY (`patient_id`) REFERENCES `patients` (`patient_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_appointments_doctor_id FOREIGN KEY (`doctor_id`) REFERENCES `doctors` (`doctor_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT ck_appointments_0 CHECK (appointment_type IN ('CONSULTATION','FOLLOW_UP','ROUTINE_CHECKUP','EMERGENCY')),
  CONSTRAINT ck_appointments_1 CHECK (status IN ('SCHEDULED','CONFIRMED','COMPLETED','CANCELLED','NO_SHOW')),
  CONSTRAINT ck_appointments_2 CHECK (start_time >= '00:00:00' AND start_time < '24:00:00'),
  CONSTRAINT ck_appointments_3 CHECK (end_time > start_time AND end_time <= '24:00:00'),
  INDEX ix_appointments_0 (doctor_id, appointment_date, start_time, appointment_id),
  INDEX ix_appointments_1 (patient_id, appointment_date, appointment_id),
  INDEX ix_appointments_2 (appointment_date, status, appointment_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `follow_ups` (
  `follow_up_id` INT NOT NULL AUTO_INCREMENT,
  `visit_id` INT NOT NULL,
  `scheduled_date` DATE NOT NULL,
  `actual_date` DATE NULL,
  `status` VARCHAR(15) NOT NULL DEFAULT 'PENDING',
  `reason` VARCHAR(255) NOT NULL,
  `instructions` TEXT NULL,
  PRIMARY KEY (`follow_up_id`),
  CONSTRAINT fk_follow_ups_visit_id FOREIGN KEY (`visit_id`) REFERENCES `visits` (`visit_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT ck_follow_ups_0 CHECK (status IN ('PENDING','COMPLETED','MISSED','CANCELLED')),
  CONSTRAINT ck_follow_ups_1 CHECK ((status = 'COMPLETED' AND actual_date IS NOT NULL) OR (status <> 'COMPLETED' AND actual_date IS NULL)),
  INDEX ix_follow_ups_0 (status, scheduled_date, follow_up_id),
  INDEX ix_follow_ups_1 (visit_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `audit_logs` (
  `audit_id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` INT NULL,
  `actor_username` VARCHAR(50) NOT NULL,
  `action` VARCHAR(20) NOT NULL,
  `entity_type` VARCHAR(40) NOT NULL,
  `entity_id` VARCHAR(64) NOT NULL,
  `description` VARCHAR(500) NOT NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`audit_id`),
  CONSTRAINT fk_audit_logs_user_id FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT ck_audit_logs_0 CHECK (action IN ('INSERT','UPDATE','DELETE','CLOSE','LOGIN','DEACTIVATE','REFRESH')),
  INDEX ix_audit_logs_0 (created_at, audit_id),
  INDEX ix_audit_logs_1 (user_id, created_at, audit_id),
  INDEX ix_audit_logs_2 (entity_type, entity_id, created_at, audit_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `monthly_case_statistics` (
  `stat_month` DATE NOT NULL,
  `total_cases` INT NOT NULL DEFAULT 0,
  `unique_patients` INT NOT NULL DEFAULT 0,
  `completed_cases` INT NOT NULL DEFAULT 0,
  `refreshed_at` DATETIME(6) NOT NULL,
  PRIMARY KEY (`stat_month`),
  CONSTRAINT ck_monthly_case_statistics_0 CHECK (DAYOFMONTH(stat_month) = 1),
  CONSTRAINT ck_monthly_case_statistics_1 CHECK (total_cases >= 0),
  CONSTRAINT ck_monthly_case_statistics_2 CHECK (unique_patients BETWEEN 0 AND total_cases),
  CONSTRAINT ck_monthly_case_statistics_3 CHECK (completed_cases BETWEEN 0 AND total_cases)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
