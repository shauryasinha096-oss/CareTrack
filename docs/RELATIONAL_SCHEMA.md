# CareTrack — proposed relational schema and data dictionary

> Phase 1 design for review. No DDL has been executed. Fictional data only; not intended for real clinical use.

Every table uses InnoDB, utf8mb4 and matching signed key types. Domain checks and cross-table rules are supplemented by the [architecture](PHASE_1_DATABASE_DESIGN.md). Every listed PRIMARY KEY is a candidate key. AI means AUTO_INCREMENT. Single-column UNIQUE + NOT NULL attributes are alternate candidate keys; nullable UNIQUE email is not a classical candidate key.

The tables below are the complete proposed 3NF relation signatures: each attribute appears once in its owning relation. `monthly_case_statistics` is a separate, rebuildable reporting projection.

## users

Application authentication and one disjoint role per account.

| Attribute | MySQL type | Constraints / default | Meaning |
|---|---|---|---|
| `user_id` | `INT` | PRIMARY KEY; NOT NULL; AUTO_INCREMENT |  |
| `username` | `VARCHAR(50)` | NOT NULL; UNIQUE |  |
| `email` | `VARCHAR(254)` | NOT NULL; UNIQUE | Login address, normalized to lowercase |
| `password_hash` | `VARCHAR(255)` | NOT NULL | Encoded Argon2id hash; never plaintext |
| `role` | `VARCHAR(20)` | NOT NULL |  |
| `is_active` | `BOOLEAN` | NOT NULL; DEFAULT TRUE |  |
| `created_at` | `DATETIME(6)` | NOT NULL; DEFAULT CURRENT_TIMESTAMP(6) | UTC timestamp |

username and email are separate alternate candidate keys. Disable accounts instead of deleting referenced staff.

Proposed row-level CHECK constraints:

- `role IN ('ADMIN','DOCTOR','RECEPTIONIST')`
- `is_active IN (0,1)`

## doctors

Professional profile of a doctor-role user.

| Attribute | MySQL type | Constraints / default | Meaning |
|---|---|---|---|
| `doctor_id` | `INT` | PRIMARY KEY; NOT NULL; AUTO_INCREMENT |  |
| `user_id` | `INT` | FOREIGN KEY; NOT NULL; UNIQUE; → `users.user_id` |  |
| `first_name` | `VARCHAR(50)` | NOT NULL |  |
| `last_name` | `VARCHAR(50)` | NOT NULL |  |
| `specialization` | `VARCHAR(100)` | NOT NULL |  |
| `license_number` | `VARCHAR(50)` | NOT NULL; UNIQUE | Fictional demo identifier |
| `phone` | `VARCHAR(20)` | NOT NULL |  |
| `email` | `VARCHAR(254)` | NOT NULL; UNIQUE | Professional contact address; distinct meaning from login email |
| `created_at` | `DATETIME(6)` | NOT NULL; DEFAULT CURRENT_TIMESTAMP(6) | UTC timestamp |

user_id, license_number, and professional email are alternate candidate keys. Role predicate is enforced through controlled provisioning and role-change guards, not a CHECK subquery.

## patients

Fictional demographic identity, independent of cases.

| Attribute | MySQL type | Constraints / default | Meaning |
|---|---|---|---|
| `patient_id` | `INT` | PRIMARY KEY; NOT NULL; AUTO_INCREMENT |  |
| `first_name` | `VARCHAR(50)` | NOT NULL |  |
| `last_name` | `VARCHAR(50)` | NOT NULL |  |
| `date_of_birth` | `DATE` | NOT NULL |  |
| `gender` | `VARCHAR(20)` | NOT NULL |  |
| `blood_group` | `VARCHAR(3)` | NULL allowed |  |
| `phone` | `VARCHAR(20)` | NOT NULL | Indexed; may be shared by a household |
| `email` | `VARCHAR(254)` | UNIQUE; NULL allowed | Optional unique known address; NULL for absent email |
| `address` | `VARCHAR(255)` | NULL allowed |  |
| `city` | `VARCHAR(80)` | NULL allowed |  |
| `occupation` | `VARCHAR(100)` | NULL allowed |  |
| `marital_status` | `VARCHAR(20)` | NULL allowed |  |
| `emergency_contact_name` | `VARCHAR(100)` | NULL allowed |  |
| `emergency_contact_phone` | `VARCHAR(20)` | NULL allowed |  |
| `created_at` | `DATETIME(6)` | NOT NULL; DEFAULT CURRENT_TIMESTAMP(6) | UTC timestamp |
| `updated_at` | `DATETIME(6)` | NOT NULL; DEFAULT CURRENT_TIMESTAMP(6) | Maintained by BEFORE UPDATE trigger; UTC |

DOB no later than the clinic date is a trigger/API rule. Nullable email is not a classical candidate key. Phone and name are not identifiers; age is derived.

Proposed row-level CHECK constraints:

- `gender IN ('FEMALE','MALE','NON_BINARY','OTHER','UNDISCLOSED')`
- `blood_group IS NULL OR blood_group IN ('A+','A-','B+','B-','AB+','AB-','O+','O-')`
- `marital_status IS NULL OR marital_status IN ('SINGLE','MARRIED','DIVORCED','WIDOWED','UNDISCLOSED')`

## medical_cases

A longitudinal case owned by one patient and assigned to one doctor.

| Attribute | MySQL type | Constraints / default | Meaning |
|---|---|---|---|
| `case_id` | `INT` | PRIMARY KEY; NOT NULL; AUTO_INCREMENT |  |
| `patient_id` | `INT` | FOREIGN KEY; NOT NULL; → `patients.patient_id` |  |
| `doctor_id` | `INT` | FOREIGN KEY; NOT NULL; → `doctors.doctor_id` |  |
| `case_date` | `DATE` | NOT NULL |  |
| `chief_complaint` | `TEXT` | NOT NULL | API explicitly supplies empty string only while draft; no server default |
| `present_illness` | `TEXT` | NULL allowed |  |
| `case_status` | `VARCHAR(20)` | NOT NULL; DEFAULT 'OPEN' |  |
| `priority` | `VARCHAR(10)` | NOT NULL; DEFAULT 'MEDIUM' |  |
| `record_state` | `VARCHAR(10)` | NOT NULL; DEFAULT 'DRAFT' | Form completion state, separate from case workflow |
| `notes` | `TEXT` | NULL allowed |  |
| `created_at` | `DATETIME(6)` | NOT NULL; DEFAULT CURRENT_TIMESTAMP(6) | UTC timestamp |
| `updated_at` | `DATETIME(6)` | NOT NULL; DEFAULT CURRENT_TIMESTAMP(6) | Maintained by BEFORE UPDATE trigger; UTC |

A DRAFT may have zero visits. Submitting requires at least one initial visit in the same transaction. Case doctor is current assignee; visit doctor is the actual attending doctor.

Proposed row-level CHECK constraints:

- `case_status IN ('OPEN','UNDER_REVIEW','FOLLOW_UP','CLOSED')`
- `priority IN ('LOW','MEDIUM','HIGH','URGENT')`
- `record_state IN ('DRAFT','SUBMITTED')`
- `record_state = 'DRAFT' OR CHAR_LENGTH(TRIM(chief_complaint)) > 0`
- `record_state <> 'DRAFT' OR case_status = 'OPEN'`

## visits

An individual encounter belonging to exactly one case.

| Attribute | MySQL type | Constraints / default | Meaning |
|---|---|---|---|
| `visit_id` | `INT` | PRIMARY KEY; NOT NULL; AUTO_INCREMENT |  |
| `case_id` | `INT` | FOREIGN KEY; NOT NULL; → `medical_cases.case_id` |  |
| `doctor_id` | `INT` | FOREIGN KEY; NOT NULL; → `doctors.doctor_id` |  |
| `visit_date` | `DATETIME(6)` | NOT NULL |  |
| `visit_type` | `VARCHAR(25)` | NOT NULL |  |
| `chief_complaint` | `TEXT` | NOT NULL | API explicitly supplies empty string only inside a draft case; no server default |
| `doctor_notes` | `TEXT` | NULL allowed |  |
| `created_at` | `DATETIME(6)` | NOT NULL; DEFAULT CURRENT_TIMESTAMP(6) | UTC timestamp |

No patient_id is duplicated: obtain it through medical_cases. Different visits may have different attending doctors. Subsequent visits are committed atomically; incomplete initial visits remain under a DRAFT case.

Proposed row-level CHECK constraints:

- `visit_type IN ('INITIAL_CONSULTATION','FOLLOW_UP','EMERGENCY','ROUTINE_CHECKUP')`

## symptoms

Reusable symptom vocabulary for fictional case observations.

| Attribute | MySQL type | Constraints / default | Meaning |
|---|---|---|---|
| `symptom_id` | `INT` | PRIMARY KEY; NOT NULL; AUTO_INCREMENT |  |
| `symptom_name` | `VARCHAR(100)` | NOT NULL; UNIQUE |  |
| `description` | `TEXT` | NULL allowed |  |
| `is_active` | `BOOLEAN` | NOT NULL; DEFAULT TRUE |  |



Proposed row-level CHECK constraints:

- `is_active IN (0,1)`

## case_symptoms

One case-level symptom observation per case/symptom pair.

| Attribute | MySQL type | Constraints / default | Meaning |
|---|---|---|---|
| `case_id` | `INT` | PRIMARY KEY; FOREIGN KEY; NOT NULL; → `medical_cases.case_id` |  |
| `symptom_id` | `INT` | PRIMARY KEY; FOREIGN KEY; NOT NULL; → `symptoms.symptom_id` |  |
| `severity` | `VARCHAR(10)` | NOT NULL |  |
| `duration` | `VARCHAR(80)` | NULL allowed |  |
| `frequency` | `VARCHAR(80)` | NULL allowed |  |
| `notes` | `TEXT` | NULL allowed |  |
| `recorded_at` | `DATETIME(6)` | NOT NULL; DEFAULT CURRENT_TIMESTAMP(6) | Initial association timestamp; not a revision log |

Composite PK (case_id, symptom_id). Describes the case-level baseline; later visit-specific changes are documented in visit notes. It is not a structured per-visit symptom history.

Proposed row-level CHECK constraints:

- `severity IN ('MILD','MODERATE','SEVERE')`

## medical_history

Patient-level condition history, with repeat episodes allowed.

| Attribute | MySQL type | Constraints / default | Meaning |
|---|---|---|---|
| `history_id` | `INT` | PRIMARY KEY; NOT NULL; AUTO_INCREMENT |  |
| `patient_id` | `INT` | FOREIGN KEY; NOT NULL; → `patients.patient_id` |  |
| `condition_name` | `VARCHAR(150)` | NOT NULL |  |
| `diagnosed_date` | `DATE` | NULL allowed |  |
| `treatment` | `TEXT` | NULL allowed |  |
| `notes` | `TEXT` | NULL allowed |  |

A condition name is not globally unique, and the same patient may have more than one episode.

## allergies

Patient-level fictional allergen/reaction records.

| Attribute | MySQL type | Constraints / default | Meaning |
|---|---|---|---|
| `allergy_id` | `INT` | PRIMARY KEY; NOT NULL; AUTO_INCREMENT |  |
| `patient_id` | `INT` | FOREIGN KEY; NOT NULL; → `patients.patient_id` |  |
| `allergen` | `VARCHAR(150)` | NOT NULL |  |
| `allergy_type` | `VARCHAR(20)` | NOT NULL |  |
| `reaction` | `VARCHAR(255)` | NULL allowed |  |
| `severity` | `VARCHAR(10)` | NOT NULL |  |
| `notes` | `TEXT` | NULL allowed |  |



Proposed row-level CHECK constraints:

- `allergy_type IN ('MEDICATION','FOOD','ENVIRONMENTAL','OTHER')`
- `severity IN ('MILD','MODERATE','SEVERE')`

## lifestyle_history

At most one current lifestyle snapshot per patient.

| Attribute | MySQL type | Constraints / default | Meaning |
|---|---|---|---|
| `lifestyle_id` | `INT` | PRIMARY KEY; NOT NULL; AUTO_INCREMENT |  |
| `patient_id` | `INT` | FOREIGN KEY; NOT NULL; UNIQUE; → `patients.patient_id` |  |
| `smoking_status` | `VARCHAR(15)` | NULL allowed |  |
| `alcohol_status` | `VARCHAR(15)` | NULL allowed |  |
| `exercise_frequency` | `VARCHAR(30)` | NULL allowed |  |
| `sleep_hours` | `DECIMAL(4,2)` | NULL allowed |  |
| `diet_type` | `VARCHAR(30)` | NULL allowed |  |
| `occupation_notes` | `TEXT` | NULL allowed |  |
| `updated_at` | `DATETIME(6)` | NOT NULL; DEFAULT CURRENT_TIMESTAMP(6) | Maintained by BEFORE UPDATE trigger; UTC |

Despite the requested table name, this is the selected 0..1 current-snapshot design, not a versioned lifestyle ledger. patient_id is an alternate candidate key.

Proposed row-level CHECK constraints:

- `smoking_status IS NULL OR smoking_status IN ('NEVER','FORMER','CURRENT','UNDISCLOSED')`
- `alcohol_status IS NULL OR alcohol_status IN ('NEVER','FORMER','CURRENT','UNDISCLOSED')`
- `sleep_hours IS NULL OR sleep_hours BETWEEN 0 AND 24`

## vital_signs

At most one measurement set for an individual visit.

| Attribute | MySQL type | Constraints / default | Meaning |
|---|---|---|---|
| `vital_id` | `INT` | PRIMARY KEY; NOT NULL; AUTO_INCREMENT |  |
| `visit_id` | `INT` | FOREIGN KEY; NOT NULL; UNIQUE; → `visits.visit_id` |  |
| `temperature` | `DECIMAL(5,2)` | NULL allowed | Degrees Celsius |
| `systolic_bp` | `SMALLINT` | NULL allowed | mmHg |
| `diastolic_bp` | `SMALLINT` | NULL allowed | mmHg |
| `heart_rate` | `SMALLINT` | NULL allowed | Per minute |
| `respiratory_rate` | `SMALLINT` | NULL allowed | Per minute |
| `oxygen_saturation` | `DECIMAL(5,2)` | NULL allowed | Percentage |
| `height_cm` | `DECIMAL(6,2)` | NULL allowed |  |
| `weight_kg` | `DECIMAL(6,2)` | NULL allowed |  |

Only basic representation checks, not diagnostic thresholds. Unmeasured values are NULL. BMI is calculated from height and weight and exposed by a query/function, not stored independently. visit_id is an alternate candidate key.

Proposed row-level CHECK constraints:

- `temperature IS NULL OR temperature > 0`
- `systolic_bp IS NULL OR systolic_bp > 0`
- `diastolic_bp IS NULL OR diastolic_bp > 0`
- `heart_rate IS NULL OR heart_rate > 0`
- `respiratory_rate IS NULL OR respiratory_rate > 0`
- `oxygen_saturation IS NULL OR oxygen_saturation BETWEEN 0 AND 100`
- `height_cm IS NULL OR height_cm > 0`
- `weight_kg IS NULL OR weight_kg > 0`

## examinations

At most one structured examination document per visit.

| Attribute | MySQL type | Constraints / default | Meaning |
|---|---|---|---|
| `examination_id` | `INT` | PRIMARY KEY; NOT NULL; AUTO_INCREMENT |  |
| `visit_id` | `INT` | FOREIGN KEY; NOT NULL; UNIQUE; → `visits.visit_id` |  |
| `general_appearance` | `TEXT` | NULL allowed |  |
| `cardiovascular_findings` | `TEXT` | NULL allowed |  |
| `respiratory_findings` | `TEXT` | NULL allowed |  |
| `neurological_findings` | `TEXT` | NULL allowed |  |
| `abdominal_findings` | `TEXT` | NULL allowed |  |
| `skin_findings` | `TEXT` | NULL allowed |  |
| `other_findings` | `TEXT` | NULL allowed |  |

visit_id is an alternate candidate key. No row or NULL findings mean not recorded, not normal.

## diagnoses

A diagnosis observation attached to a visit, not a global diagnosis catalog.

| Attribute | MySQL type | Constraints / default | Meaning |
|---|---|---|---|
| `diagnosis_id` | `INT` | PRIMARY KEY; NOT NULL; AUTO_INCREMENT |  |
| `visit_id` | `INT` | FOREIGN KEY; NOT NULL; → `visits.visit_id` |  |
| `diagnosis_name` | `VARCHAR(150)` | NOT NULL |  |
| `diagnosis_type` | `VARCHAR(15)` | NOT NULL; DEFAULT 'PRIMARY' |  |
| `notes` | `TEXT` | NULL allowed |  |

Additional UNIQUE (visit_id, diagnosis_name, diagnosis_type) prevents exact duplicate labels/types within one visit and forms an alternate candidate key. Multiple co-primary labels are permitted; no unsupported one-primary-only rule is assumed.

Additional table constraint: UNIQUE (visit_id, diagnosis_name, diagnosis_type).

Proposed row-level CHECK constraints:

- `diagnosis_type IN ('PRIMARY','SECONDARY','DIFFERENTIAL')`

## medicines

Fictional catalog, one identifiable product/strength/form per row.

| Attribute | MySQL type | Constraints / default | Meaning |
|---|---|---|---|
| `medicine_id` | `INT` | PRIMARY KEY; NOT NULL; AUTO_INCREMENT |  |
| `medicine_code` | `VARCHAR(40)` | NOT NULL; UNIQUE | Stable fictional catalog code, e.g. DEMO-MED-001 |
| `medicine_name` | `VARCHAR(150)` | NOT NULL |  |
| `generic_name` | `VARCHAR(150)` | NOT NULL |  |
| `manufacturer` | `VARCHAR(150)` | NOT NULL |  |
| `medicine_type` | `VARCHAR(15)` | NOT NULL |  |
| `strength` | `VARCHAR(50)` | NOT NULL |  |
| `form` | `VARCHAR(50)` | NOT NULL |  |
| `is_active` | `BOOLEAN` | NOT NULL; DEFAULT TRUE |  |

medicine_code is an alternate candidate key; brand/name alone is not. medicine_type is a broad catalog category and form is a finer presentation such as coated tablet, so neither is assumed to determine the other. No automatic medicine or dosage recommendations.

Proposed row-level CHECK constraints:

- `medicine_type IN ('TABLET','CAPSULE','SYRUP','INJECTION','CREAM','DROPS')`
- `is_active IN (0,1)`

## prescriptions

At most one fictional prescription document per visit.

| Attribute | MySQL type | Constraints / default | Meaning |
|---|---|---|---|
| `prescription_id` | `INT` | PRIMARY KEY; NOT NULL; AUTO_INCREMENT |  |
| `visit_id` | `INT` | FOREIGN KEY; NOT NULL; UNIQUE; → `visits.visit_id` |  |
| `doctor_id` | `INT` | FOREIGN KEY; NOT NULL; → `doctors.doctor_id` |  |
| `prescription_date` | `DATE` | NOT NULL |  |
| `notes` | `TEXT` | NULL allowed |  |

visit_id is an alternate candidate key. doctor_id means actual author/prescriber, who can differ from attending doctor. Author must be authorized; it is not a copied visit.doctor_id.

## prescription_medicines

One prescription line per prescription/catalog-product pair.

| Attribute | MySQL type | Constraints / default | Meaning |
|---|---|---|---|
| `prescription_id` | `INT` | PRIMARY KEY; FOREIGN KEY; NOT NULL; → `prescriptions.prescription_id` |  |
| `medicine_id` | `INT` | PRIMARY KEY; FOREIGN KEY; NOT NULL; → `medicines.medicine_id` |  |
| `dosage` | `VARCHAR(100)` | NOT NULL |  |
| `frequency` | `VARCHAR(100)` | NOT NULL |  |
| `route` | `VARCHAR(50)` | NOT NULL |  |
| `duration_days` | `SMALLINT` | NOT NULL |  |
| `instructions` | `TEXT` | NULL allowed |  |

Composite PK (prescription_id, medicine_id). One regimen per product in a prescription; variable/tapered repeated lines for the same product are outside this project scope.

Proposed row-level CHECK constraints:

- `duration_days > 0`

## appointments

Independent scheduling record for a patient and doctor.

| Attribute | MySQL type | Constraints / default | Meaning |
|---|---|---|---|
| `appointment_id` | `INT` | PRIMARY KEY; NOT NULL; AUTO_INCREMENT |  |
| `patient_id` | `INT` | FOREIGN KEY; NOT NULL; → `patients.patient_id` |  |
| `doctor_id` | `INT` | FOREIGN KEY; NOT NULL; → `doctors.doctor_id` |  |
| `appointment_date` | `DATE` | NOT NULL |  |
| `start_time` | `TIME` | NOT NULL |  |
| `end_time` | `TIME` | NOT NULL |  |
| `appointment_type` | `VARCHAR(20)` | NOT NULL |  |
| `status` | `VARCHAR(15)` | NOT NULL; DEFAULT 'SCHEDULED' |  |
| `notes` | `TEXT` | NULL allowed |  |
| `created_at` | `DATETIME(6)` | NOT NULL; DEFAULT CURRENT_TIMESTAMP(6) | UTC timestamp |

Single fixed clinic timezone Asia/Kolkata. Half-open intervals [start_time,end_time); no overnight appointments. Overlap is a serialized transaction rule, not a row CHECK or an equality UNIQUE constraint.

Proposed row-level CHECK constraints:

- `appointment_type IN ('CONSULTATION','FOLLOW_UP','ROUTINE_CHECKUP','EMERGENCY')`
- `status IN ('SCHEDULED','CONFIRMED','COMPLETED','CANCELLED','NO_SHOW')`
- `start_time >= '00:00:00' AND start_time < '24:00:00'`
- `end_time > start_time AND end_time <= '24:00:00'`

## follow_ups

One follow-up plan originating at a particular visit.

| Attribute | MySQL type | Constraints / default | Meaning |
|---|---|---|---|
| `follow_up_id` | `INT` | PRIMARY KEY; NOT NULL; AUTO_INCREMENT |  |
| `visit_id` | `INT` | FOREIGN KEY; NOT NULL; → `visits.visit_id` |  |
| `scheduled_date` | `DATE` | NOT NULL |  |
| `actual_date` | `DATE` | NULL allowed |  |
| `status` | `VARCHAR(15)` | NOT NULL; DEFAULT 'PENDING' |  |
| `reason` | `VARCHAR(255)` | NOT NULL |  |
| `instructions` | `TEXT` | NULL allowed |  |

case_id is intentionally derived through visits, avoiding follow_up_id -> visit_id -> case_id. Several plans may originate at one visit. actual_date records completion date, not a link to the completion visit. A plan does not automatically create an appointment.

Proposed row-level CHECK constraints:

- `status IN ('PENDING','COMPLETED','MISSED','CANCELLED')`
- `(status = 'COMPLETED' AND actual_date IS NOT NULL) OR (status <> 'COMPLETED' AND actual_date IS NULL)`

## audit_logs

Append-only application operation metadata with attributable actors.

| Attribute | MySQL type | Constraints / default | Meaning |
|---|---|---|---|
| `audit_id` | `BIGINT` | PRIMARY KEY; NOT NULL; AUTO_INCREMENT |  |
| `user_id` | `INT` | FOREIGN KEY; → `users.user_id`; NULL allowed |  |
| `actor_username` | `VARCHAR(50)` | NOT NULL | Historical username snapshot, or SYSTEM/SEED |
| `action` | `VARCHAR(20)` | NOT NULL |  |
| `entity_type` | `VARCHAR(40)` | NOT NULL |  |
| `entity_id` | `VARCHAR(64)` | NOT NULL | Canonical scalar or composite identifier |
| `description` | `VARCHAR(500)` | NOT NULL |  |
| `created_at` | `DATETIME(6)` | NOT NULL; DEFAULT CURRENT_TIMESTAMP(6) | UTC timestamp |

entity_type/entity_id is a validated audit reference, deliberately not a polymorphic FK: a target may have been deleted. Do not put passwords, tokens or clinical narrative in descriptions. actor_username is event-time data, not a duplicate of the current users.username.

Proposed row-level CHECK constraints:

- `action IN ('INSERT','UPDATE','DELETE','CLOSE','LOGIN','DEACTIVATE','REFRESH')`

## monthly_case_statistics

Explicit derived reporting cache; not a twentieth operational entity.

| Attribute | MySQL type | Constraints / default | Meaning |
|---|---|---|---|
| `stat_month` | `DATE` | PRIMARY KEY; NOT NULL | First day of the clinic calendar month |
| `total_cases` | `INT` | NOT NULL; DEFAULT 0 |  |
| `unique_patients` | `INT` | NOT NULL; DEFAULT 0 |  |
| `completed_cases` | `INT` | NOT NULL; DEFAULT 0 |  |
| `refreshed_at` | `DATETIME(6)` | NOT NULL | One UTC timestamp for the entire refresh batch |

Required materialized-view equivalent. Count SUBMITTED cases grouped by case_date month; completed_cases means current CLOSED status within that case-date cohort, not cases closed during that month. No FK to cases; rebuildable and potentially stale.

Proposed row-level CHECK constraints:

- `DAYOFMONTH(stat_month) = 1`
- `total_cases >= 0`
- `unique_patients BETWEEN 0 AND total_cases`
- `completed_cases BETWEEN 0 AND total_cases`

