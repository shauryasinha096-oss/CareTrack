# CareTrack — functional dependencies and normalization

> Phase 1 proposed model. Educational demonstration using fictional data; not intended for real clinical use.

## 1. What is being proved

Normalization depends on the meaning of attributes and the functional dependencies (FDs) that hold for every valid database state. An artificial ID alone does not prove 3NF.

The operational design uses the business assumptions in [the architecture](PHASE_1_DATABASE_DESIGN.md). The [dictionary](RELATIONAL_SCHEMA.md) contains the complete final relation signatures. For every nontrivial FD `X → A`, 3NF requires X to be a superkey or A to be prime (part of a candidate key). BCNF has the stronger requirement that every determinant X be a superkey.

The proposed operational relations satisfy 3NF under the dependencies below; the listed nontrivial determinants are candidate keys, so they also satisfy BCNF under those assumptions. This is an assumption-based design argument, not a claim that any possible future business rule will preserve BCNF. Nullable optional values require SQL-specific handling: a nullable UNIQUE email is not treated as a relational candidate key.

## 2. Conceptual unnormalized record (UNF)

Consider a paper file represented as one nested record:

```text
PATIENT_CASE_FILE(
  patient_id, first_name, last_name, date_of_birth, phone, email, ...,
  histories = { (history_id, condition_name, diagnosed_date, treatment, ...) },
  allergies = { (allergy_id, allergen, allergy_type, reaction, ...) },
  lifestyle = (smoking_status, alcohol_status, sleep_hours, ...),
  cases = {
    (case_id, case_date, assigned_doctor_id, assigned_doctor_name, ...,
     chief_complaint, case_status, ...,
     symptoms = { (symptom_id, symptom_name, severity, duration, frequency, ...) },
     visits = {
       (visit_id, attending_doctor_id, attending_doctor_name, visit_date, ...,
        measurements = (height_cm, weight_kg, temperature, ...),
        examination = (...),
        diagnoses = { (diagnosis_id, diagnosis_name, diagnosis_type, ...) },
        prescription =
          (prescription_id, prescriber_doctor_id, prescription_date, ...,
           medicines = { (medicine_id, medicine_name, manufacturer,
                           dosage, frequency, route, duration_days, ...) }),
        followups = { (follow_up_id, scheduled_date, status, ...) })
     })
  },
  appointments = { (appointment_id, doctor_id, appointment_date, ...) }
)
```

Repeated groups/nested sets and symptom1/symptom2 or medicine1/medicine2 versions are not first normal form. They make inserts, updates and joins difficult and impose artificial limits on how many child items can be recorded.

## 3. UNF → 1NF: atomic values and independent repeating groups

Assign identities to real entities and extract each repeating group into flat rows. Keep one symptom association per row, one prescription product per row, one diagnosis per row, etc. Do not turn independent symptom and medicine groups into a Cartesian product; they have different owners.

For illustrating subsequent decomposition, two deliberately wide but atomic staging relations are sufficient:

```text
CASE_SYMPTOM_1NF(
  case_id, symptom_id,
  case_date, chief_complaint,
  patient_id, patient_first_name, patient_last_name, patient_phone,
  assigned_doctor_id, assigned_doctor_name, assigned_doctor_specialization,
  symptom_name, symptom_description,
  severity, duration, frequency, symptom_notes, recorded_at
)
key = (case_id, symptom_id)

PRESCRIPTION_LINE_1NF(
  prescription_id, medicine_id,
  visit_id, prescription_date, prescription_notes,
  prescriber_doctor_id, prescriber_doctor_name,
  case_id, visit_date, attending_doctor_id, attending_doctor_name,
  patient_id, patient_name,
  medicine_code, medicine_name, generic_name, manufacturer,
  medicine_type, strength, form,
  dosage, frequency, route, duration_days, instructions
)
key = (prescription_id, medicine_id)
```

Separate header rows are retained for cases/prescriptions with no children; their existence must not depend on a staging join producing a row. Patient histories, allergies, visits, diagnoses, follow-up plans and bookings are separately flattened at their own grain. A name is split into first_name/last_name because those parts have separate application meaning. Free-text notes remain one narrative value; searchable multi-valued catalog associations are never hidden there.

These wide relations are in 1NF, but contain partial and transitive dependencies.

## 4. 1NF → 2NF: remove partial dependencies

2NF requires 1NF and that every non-prime attribute depend on the whole candidate key, not a proper subset of a composite key.

In CASE_SYMPTOM_1NF:

```text
case_id → case_date, chief_complaint, patient_id, assigned_doctor_id,
          patient details, assigned doctor details
symptom_id → symptom_name, symptom_description
(case_id, symptom_id) → severity, duration, frequency, symptom_notes, recorded_at
```

Patient/doctor details in the first line follow by transitivity through their respective IDs. Decompose to:

```text
CASE_HEADER_2NF(case_id, case_date, chief_complaint,
                patient_id, patient details,
                assigned_doctor_id, assigned doctor details)
SYMPTOMS(symptom_id, symptom_name, description, is_active)
CASE_SYMPTOMS(case_id, symptom_id, severity, duration, frequency, notes, recorded_at)
```

Now association attributes depend on the entire pair. Case attributes are no longer repeated once per symptom; symptom vocabulary is no longer repeated once per case.

In PRESCRIPTION_LINE_1NF:

```text
prescription_id → visit_id, prescription_date, prescription_notes,
                  prescriber_doctor_id, prescriber details,
                  visit/case/patient details
medicine_id → medicine_code, medicine_name, generic_name, manufacturer,
              medicine_type, strength, form
(prescription_id, medicine_id) → dosage, frequency, route, duration_days, instructions
```

Decompose to:

```text
PRESCRIPTION_HEADER_2NF(prescription_id, visit_id, prescription_date,
                       prescription_notes, prescriber_doctor_id,
                       prescriber details, visit/case/patient details)
MEDICINES(medicine_id, medicine_code, medicine_name, generic_name,
          manufacturer, medicine_type, strength, form, is_active)
PRESCRIPTION_MEDICINES(prescription_id, medicine_id,
                      dosage, frequency, route, duration_days, instructions)
```

Regimen is a fact about the document/product pair, not a permanent property of a catalog medicine. Other entity/header relations have simple primary keys; nevertheless their alternate candidate keys must also be considered. Singleton candidate keys cannot have nonempty proper-subset partial dependencies. The composite diagnosis alternate key is an event identity; no subset is assumed to determine its diagnosis_id or notes.

## 5. 2NF → 3NF: remove transitive dependencies

### Cases, patients and doctors

CASE_HEADER_2NF contains:

```text
case_id → patient_id → patient details
case_id → assigned_doctor_id → assigned doctor details
```

Neither patient_id nor assigned_doctor_id identifies one case: both may have many cases. Move demographics to patients and professional attributes to doctors. Keep only patient_id and doctor_id references plus case-specific attributes in medical_cases.

### Prescription headers, encounters and authors

PRESCRIPTION_HEADER_2NF contains visit-specific, case-specific, demographic and professional attributes:

```text
visit_id → case_id, attending_doctor_id, visit_date, encounter details
case_id → patient_id, current assigned_doctor_id, case details
patient_id → patient details
attending_doctor_id → attending doctor details
prescriber_doctor_id → prescriber professional details
```

Extract visits, medical_cases, patients and doctors; retain only prescription-specific attributes, its visit_id and the actual prescriber's doctor_id. Because visit_id is UNIQUE NOT NULL in prescriptions, it is an alternate candidate key: copying visit_date into prescriptions would not automatically be a 3NF violation there, but it would still duplicate an encounter fact unnecessarily. The design has one owning relation for each fact and avoids that duplication. Likewise, prescriber and attending doctor are distinct roles, so there is no assumed `visit.doctor_id → prescription.doctor_id` dependency across author choices.

### Follow-up origin

The suggested follow_ups with both visit_id and case_id has:

```text
follow_up_id → visit_id → case_id
```

A visit may have several plans, so visit_id is not a follow_ups superkey. case_id is non-prime in follow_ups. Remove case_id from that relation and join to visits when it is needed. This is a real 3NF correction, not merely a performance preference. It also removes the possibility of a plan claiming one case while its visit belongs to another.

### Derived attributes

Storing independent height, weight and BMI values introduces the non-key determinant `(height_cm, weight_kg) → bmi`, and permits contradictory data. Omit writable BMI and calculate it in a view/query/function. Age depends on date of birth and the reference date; it changes without a patient edit. Do not store it as permanent demographic data.

### Other independent facts

- User authentication attributes belong in users; professional attributes belong in doctors. doctors.user_id is UNIQUE, so doctor specialization is a 1:1 extension, not repeated credentials.
- Patient medical-history episodes and allergies have their own identities and patient FK, avoiding repeating groups. Condition/allergen labels alone do not determine episode-specific dates, reactions or notes.
- The current lifestyle snapshot has both lifestyle_id and patient_id as candidate keys.
- A measurement/examination row has both its own ID and unique visit_id as candidate keys.
- Diagnosis_id identifies an observation; diagnosis_name alone does not determine its type, notes or visit. A separate global diagnosis catalog is not implied.
- Appointments identify booking events independently of clinical cases. Booking date/time do not determine a patient or a doctor globally.
- Audit actor_username is the event-time label, so current user_id does not determine every historical actor label after a rename. entity references do not imply current target rows must exist.

## 6. Functional dependencies for every final relation

Notation: `N(R)` means **all attributes of R except the attributes in the listed primary key**, exactly as enumerated in the dictionary. `K → R` means K determines every attribute of R; trivial dependencies are included implicitly. Each listed alternate key also determines the entire relation. There are no additional assumed non-key FDs.

| Relation R | Primary-key dependency | Alternate-key dependencies / qualification |
|---|---|---|
| users | user_id → N(users) | username → users; email → users |
| doctors | doctor_id → N(doctors) | user_id → doctors; license_number → doctors; email → doctors |
| patients | patient_id → N(patients) | Known unique email identifies at most one row, but nullable email is not an unconditional candidate key |
| medical_cases | case_id → N(medical_cases) | patient_id/doctor_id do not determine a case |
| visits | visit_id → N(visits) | case_id/doctor_id/date are not unique encounter identities |
| symptoms | symptom_id → N(symptoms) | symptom_name → symptoms |
| case_symptoms | (case_id, symptom_id) → severity, duration, frequency, notes, recorded_at | Neither component alone determines an observation |
| medical_history | history_id → N(medical_history) | No patient/condition/date natural key is asserted |
| allergies | allergy_id → N(allergies) | Reactions/notes are record-specific, not determined by allergen alone |
| lifestyle_history | lifestyle_id → N(lifestyle_history) | patient_id → lifestyle_history |
| vital_signs | vital_id → N(vital_signs) | visit_id → vital_signs; derived BMI excluded |
| examinations | examination_id → N(examinations) | visit_id → examinations |
| diagnoses | diagnosis_id → N(diagnoses) | (visit_id, diagnosis_name, diagnosis_type) → diagnoses |
| medicines | medicine_id → N(medicines) | medicine_code → medicines |
| prescriptions | prescription_id → N(prescriptions) | visit_id → prescriptions; prescriber is an independent author role |
| prescription_medicines | (prescription_id, medicine_id) → dosage, frequency, route, duration_days, instructions | Neither component alone determines regimen |
| appointments | appointment_id → N(appointments) | Overlap rule is an interval constraint, not an FD |
| follow_ups | follow_up_id → N(follow_ups) | visit_id is not unique; case_id excluded |
| audit_logs | audit_id → N(audit_logs) | Event timestamp and actor ID are not keys |
| monthly_case_statistics | stat_month → total_cases, unique_patients, completed_cases, refreshed_at | Derived projection; statistics are not independently authoritative facts |

For example, the full patient FD is:

```text
patient_id → first_name, last_name, date_of_birth, gender, blood_group,
             phone, email, address, city, occupation, marital_status,
             emergency_contact_name, emergency_contact_phone,
             created_at, updated_at
```

The full case FD is:

```text
case_id → patient_id, doctor_id, case_date, chief_complaint,
          present_illness, case_status, priority, record_state,
          notes, created_at, updated_at
```

Identical values do not establish a semantic FD: manufacturer does not determine all medicines; generic_name does not determine a single manufacturer; name does not determine a person; doctor specialization does not determine a unique doctor. Medicine category and fine presentation are independently defined catalog attributes, not two labels for the same code. If later requirements introduce a true code → label mapping, that code/label pair must move to a lookup relation.

## 7. Lossless joins and dependency preservation

For a binary decomposition R into R1 and R2, a sufficient lossless-join condition is that their intersection functionally determines one side. Extracting symptoms shares symptom_id, which determines SYMPTOMS; extracting patients shares patient_id, which determines PATIENTS. Extracting medicines shares medicine_id, which determines MEDICINES. Each header/detail split uses the corresponding header or catalog key, so recombination does not invent contradictory entity values.

The UNF-to-flat step models independent repeating groups; it is not presented as a dependency-preserving decomposition of an already-existing single flat universal relation. Optional parents with no children remain header rows and need LEFT JOIN for a full listing. Inner joins of every child table will not recover parents without observations, and an unrestricted multi-child join will multiply rows. These query issues are separate from the lossless decomposition argument.

The listed FDs are preserved locally by PRIMARY KEY/UNIQUE constraints after the decomposition. FKs preserve valid references. Cross-table workflow rules (role membership, submitted-case child minimums, chronology and appointment overlap) are not FDs and are not solved by 3NF; they need the explicitly documented triggers/services/transactions. Removing follow_ups.case_id preserves its derivability through the existing `visit_id → case_id` FD in visits.

## 8. Final relation set and scope of the cache

```text
3NF operational relations = {
  users, doctors, patients, medical_cases, visits, symptoms, case_symptoms,
  medical_history, allergies, lifestyle_history, vital_signs, examinations,
  diagnoses, medicines, prescriptions, prescription_medicines,
  appointments, follow_ups, audit_logs
}

Derived reporting relation = {
  monthly_case_statistics(stat_month, total_cases, unique_patients,
                          completed_cases, refreshed_at)
}
```

The reporting relation has a key-based internal schema, but stores intentionally redundant aggregates relative to operational relations. Its presence does not mean operational data was denormalized. It is isolated, rebuildable and labeled with refresh time. It cannot be freely edited as another source of case truth.

## 9. Viva examples of anomalies removed

| Anomaly in a wide record | Result of the decomposition |
|---|---|
| Change a phone in every symptom/visit row | Update one patients row |
| Spell a symptom differently in each case | Reference a single symptoms row |
| A doctor cannot be inserted without a case | Create user/doctor independently |
| Deleting the last case removes patient demographics | Patient has an independent identity; reference policy is explicit |
| A medicine catalog update overwrites dosage for every patient | Catalog presentation and per-prescription regimen are separate |
| A follow-up stores mismatched case and visit IDs | Case is derived from its single visit FK |
| Height/weight changes leave an old BMI | BMI is recomputed |
| Second vital row is accidentally created for one visit | UNIQUE visit_id rejects it |
| Two bookings overlap despite distinct start times | Serialized interval check handles this non-FD constraint |

For the viva, explain both what normalization guarantees and what it does not: access control, temporal completeness, concurrency, safe deletion and workflow transitions still need their own enforcement mechanisms.
