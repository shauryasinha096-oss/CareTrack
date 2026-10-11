# CareTrack — complete entity–relationship diagram

> Fictional data only. Phase 1 proposed design.

`||` exactly one; `o|` zero or one; `o{` zero or many. PK = primary key; FK = foreign key; UK = unique constraint (Mermaid key annotation). Optional parents have partial participation; non-null child FKs imply total participation on that child side. Composite PK attributes appear on both junction-table columns.

Mermaid uses `UK`, so the source below uses that spelling for UNIQUE. See the relationship matrix for the additional role/submission constraints that cannot be expressed by crow's-foot lines. The standalone monthly cache is deliberately unconnected.

```mermaid
erDiagram
    users {
        int user_id PK
        varchar_50 username UK
        varchar_254 email UK
        varchar_255 password_hash
        varchar_20 role
        boolean is_active
        datetime_6 created_at
    }
    doctors {
        int doctor_id PK
        int user_id FK, UK
        varchar_50 first_name
        varchar_50 last_name
        varchar_100 specialization
        varchar_50 license_number UK
        varchar_20 phone
        varchar_254 email UK
        datetime_6 created_at
    }
    patients {
        int patient_id PK
        varchar_50 first_name
        varchar_50 last_name
        date date_of_birth
        varchar_20 gender
        varchar_3 blood_group
        varchar_20 phone
        varchar_254 email UK
        varchar_255 address
        varchar_80 city
        varchar_100 occupation
        varchar_20 marital_status
        varchar_100 emergency_contact_name
        varchar_20 emergency_contact_phone
        datetime_6 created_at
        datetime_6 updated_at
    }
    medical_cases {
        int case_id PK
        int patient_id FK
        int doctor_id FK
        date case_date
        text chief_complaint
        text present_illness
        varchar_20 case_status
        varchar_10 priority
        varchar_10 record_state
        text notes
        datetime_6 created_at
        datetime_6 updated_at
    }
    visits {
        int visit_id PK
        int case_id FK
        int doctor_id FK
        datetime_6 visit_date
        varchar_25 visit_type
        text chief_complaint
        text doctor_notes
        datetime_6 created_at
    }
    symptoms {
        int symptom_id PK
        varchar_100 symptom_name UK
        text description
        boolean is_active
    }
    case_symptoms {
        int case_id PK, FK
        int symptom_id PK, FK
        varchar_10 severity
        varchar_80 duration
        varchar_80 frequency
        text notes
        datetime_6 recorded_at
    }
    medical_history {
        int history_id PK
        int patient_id FK
        varchar_150 condition_name
        date diagnosed_date
        text treatment
        text notes
    }
    allergies {
        int allergy_id PK
        int patient_id FK
        varchar_150 allergen
        varchar_20 allergy_type
        varchar_255 reaction
        varchar_10 severity
        text notes
    }
    lifestyle_history {
        int lifestyle_id PK
        int patient_id FK, UK
        varchar_15 smoking_status
        varchar_15 alcohol_status
        varchar_30 exercise_frequency
        decimal_4_2 sleep_hours
        varchar_30 diet_type
        text occupation_notes
        datetime_6 updated_at
    }
    vital_signs {
        int vital_id PK
        int visit_id FK, UK
        decimal_5_2 temperature
        smallint systolic_bp
        smallint diastolic_bp
        smallint heart_rate
        smallint respiratory_rate
        decimal_5_2 oxygen_saturation
        decimal_6_2 height_cm
        decimal_6_2 weight_kg
    }
    examinations {
        int examination_id PK
        int visit_id FK, UK
        text general_appearance
        text cardiovascular_findings
        text respiratory_findings
        text neurological_findings
        text abdominal_findings
        text skin_findings
        text other_findings
    }
    diagnoses {
        int diagnosis_id PK
        int visit_id FK
        varchar_150 diagnosis_name
        varchar_15 diagnosis_type
        text notes
    }
    medicines {
        int medicine_id PK
        varchar_40 medicine_code UK
        varchar_150 medicine_name
        varchar_150 generic_name
        varchar_150 manufacturer
        varchar_15 medicine_type
        varchar_50 strength
        varchar_50 form
        boolean is_active
    }
    prescriptions {
        int prescription_id PK
        int visit_id FK, UK
        int doctor_id FK
        date prescription_date
        text notes
    }
    prescription_medicines {
        int prescription_id PK, FK
        int medicine_id PK, FK
        varchar_100 dosage
        varchar_100 frequency
        varchar_50 route
        smallint duration_days
        text instructions
    }
    appointments {
        int appointment_id PK
        int patient_id FK
        int doctor_id FK
        date appointment_date
        time start_time
        time end_time
        varchar_20 appointment_type
        varchar_15 status
        text notes
        datetime_6 created_at
    }
    follow_ups {
        int follow_up_id PK
        int visit_id FK
        date scheduled_date
        date actual_date
        varchar_15 status
        varchar_255 reason
        text instructions
    }
    audit_logs {
        bigint audit_id PK
        int user_id FK
        varchar_50 actor_username
        varchar_20 action
        varchar_40 entity_type
        varchar_64 entity_id
        varchar_500 description
        datetime_6 created_at
    }
    monthly_case_statistics {
        date stat_month PK
        int total_cases
        int unique_patients
        int completed_cases
        datetime_6 refreshed_at
    }
    users ||--o| doctors : "user_id"
    patients ||--o{ medical_cases : "patient_id"
    doctors ||--o{ medical_cases : "doctor_id"
    medical_cases ||--o{ visits : "case_id"
    doctors ||--o{ visits : "doctor_id"
    medical_cases ||--o{ case_symptoms : "case_id"
    symptoms ||--o{ case_symptoms : "symptom_id"
    patients ||--o{ medical_history : "patient_id"
    patients ||--o{ allergies : "patient_id"
    patients ||--o| lifestyle_history : "patient_id"
    visits ||--o| vital_signs : "visit_id"
    visits ||--o| examinations : "visit_id"
    visits ||--o{ diagnoses : "visit_id"
    visits ||--o| prescriptions : "visit_id"
    doctors ||--o{ prescriptions : "doctor_id"
    prescriptions ||--o{ prescription_medicines : "prescription_id"
    medicines ||--o{ prescription_medicines : "medicine_id"
    patients ||--o{ appointments : "patient_id"
    doctors ||--o{ appointments : "doctor_id"
    visits ||--o{ follow_ups : "visit_id"
    users |o--o{ audit_logs : "user_id"
```

## Other formats

- Open `diagrams/caretrack.drawio` directly in diagrams.net/draw.io.
- Import `diagrams/caretrack.dbml` into dbdiagram.io; Markdown remains authoritative for CHECK constraints and procedural rules.
- MySQL Workbench: after Phase 2 is approved, use Database → Reverse Engineer on the implemented schema, or File → Import → Reverse Engineer MySQL Create Script. Workbench does not directly import Mermaid or DBML; no `.mwb` or executable DDL is claimed at this stage.

The draw.io drawing uses text cardinality labels (`parent 1 / child 0..N`, etc.); Mermaid and the matrix give the formal participation constraints.
