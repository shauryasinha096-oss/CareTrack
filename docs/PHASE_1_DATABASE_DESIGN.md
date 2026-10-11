# CareTrack — Phase 1 database architecture

**Delivery status:** Phases 1–11 are implemented. The user authorized all phases without further approval. This document records the original architecture; see IMPLEMENTATION.md and TESTING.md for the delivered behavior and executed checks.  
**Prepared:** 11 October 2026.  
**Scope:** conceptual model, logical 3NF model, physical design decisions, and an implementation verification plan. No application or schema implementation has been performed.

> CareTrack is an educational demonstration project using fictional data. It is not intended for real clinical use.

## 1. Project statement and architecture

CareTrack replaces a fictional paper case file with structured, searchable patient demographics, cases, encounters, observations, prescriptions, and scheduling records. Its academic objective is to demonstrate relational modeling, keys, constraints, normalization, joins, transactions, stored objects, auditing, and access control through one coherent application.

The main workflows are patient registration/search; appointment booking; a doctor completing the eleven-step case form; subsequent visits; patient history and timeline retrieval; follow-up management; and scoped dashboards/reports. Admin manages users, doctors, vocabulary, and audit access. Reception handles demographics and scheduling. Clinical records belong to doctor/admin workflows.

The intended data path is React → authenticated FastAPI routes → service transactions → SQLAlchemy/PyMySQL → MySQL. All persisted application information, dashboards, reports, and catalog options originate from MySQL. There is no fallback hardcoded patient store or SQLite substitute.

## 2. Complete table and entity inventory

The model contains **19 operational tables**, including two associative entities, and **one derived reporting cache** explicitly required by the brief.

| # | Table | Entity / responsibility |
|---|---|---|
| 1 | users | Authentication identity and role |
| 2 | doctors | Doctor specialization of a user |
| 3 | patients | Fictional demographic identity |
| 4 | medical_cases | Longitudinal patient case |
| 5 | visits | An individual encounter within a case |
| 6 | symptoms | Reusable symptom vocabulary |
| 7 | case_symptoms | Case–symptom association and its observations |
| 8 | medical_history | Patient-level condition episodes |
| 9 | allergies | Patient-level allergen/reaction observations |
| 10 | lifestyle_history | Current patient lifestyle snapshot |
| 11 | vital_signs | Optional measurement set for a visit |
| 12 | examinations | Optional examination record for a visit |
| 13 | diagnoses | Diagnosis observations for a visit |
| 14 | medicines | Fictional catalog products |
| 15 | prescriptions | Optional prescription document for a visit |
| 16 | prescription_medicines | Prescription–medicine association and regimen |
| 17 | appointments | Independent scheduling record |
| 18 | follow_ups | Follow-up plan originating at a visit |
| 19 | audit_logs | Attributable operation metadata |
| 20 | monthly_case_statistics | Rebuildable monthly case summary |

The [relational schema](RELATIONAL_SCHEMA.md) is the complete attribute/type/constraint list for every table. The [normalization analysis](NORMALIZATION.md) lists all relation determinants and the proposed 3NF decomposition. The [ER diagram](ER_DIAGRAM.md) contains every attribute and FK.

No extra admin, receptionist, address, manufacturer, diagnosis-catalog, clinic, or billing tables are needed for the stated requirements.

## 3. Modeling assumptions and changes from the suggested fields

These are explicit proposed decisions, so the viva does not depend on undocumented assumptions.

1. **Follow-up case is derived.** `follow_ups.visit_id` is mandatory. The case is obtained through `visits.case_id`; `follow_ups.case_id` is omitted. Keeping both would introduce `follow_up_id → visit_id → case_id`, because a visit may originate several follow-up plans. The API can expose the derived case ID without duplicating it in storage.
2. **Age and BMI are derived.** No stored age column and no independently writable BMI column. Query functions calculate age at a specified/current date and BMI from that visit's height and weight. Missing measurements produce NULL BMI. This prevents contradictory stored values.
3. **Optional one-to-one means zero or one.** A newly registered patient need not have lifestyle information. A visit need not yet have vitals, an examination, or a prescription. Mandatory child FKs plus UNIQUE constrain each optional child to its actual owner; they do not force the parent to have a child.
4. **Case and visit doctors have different meanings.** Case doctor is the current assignee; visit doctor is the actual attending doctor. Assignment may change without rewriting past attendance. Prescription doctor is the actual prescriber, who may be a separately authorized doctor. No equality FD between these three attributes is assumed.
5. **Professional and login emails have different meanings.** `users.email` is a login identity; `doctors.email` is a professional contact address. They may coincide, but are not required to be equal. Doctor name/contact data is not repeated in cases.
6. **Shared patient phones are valid.** A household may share a contact number. Patient phone is required and indexed, not UNIQUE. Optional patient email is UNIQUE when known; store missing email as NULL, not an empty string. Only patient_id is an unconditional patient candidate key.
7. **Drafts need a separate completion state.** Add `medical_cases.record_state` with DRAFT/SUBMITTED, leaving the four requested case statuses unchanged. Drafts remain OPEN; submitted records cannot revert to DRAFT. Patient and assigned doctor must exist before a draft can be persisted. The full field dictionary defines which fields may be incomplete.
8. **Stable product identity matters.** Add a unique non-null `medicines.medicine_code`. Medicine name alone cannot identify different strengths/forms. One row represents one fictional catalog presentation. Once referenced, product-defining changes require a new code; deactivate older products. No medicine recommendations are generated.
9. **One product regimen per prescription.** The requested `(prescription_id, medicine_id)` key permits one line for each product. Repeated/tapered lines for the same product are outside the current scope. Supporting those later would require an explicit prescription line identity.
10. **Lifestyle is a current snapshot.** Keep the requested table name `lifestyle_history`, but implement patient 0..1 lifestyle record. This does not claim to retain every former lifestyle value. Visit notes preserve encounter-specific narrative. A versioned lifestyle ledger would be a separate future requirement.
11. **Symptoms are case-level baseline observations.** `case_symptoms` implements the requested M:N case relation. Add `recorded_at` so its first recording can appear in a timeline. Later changes associated with a particular encounter go in that visit's notes. Structured per-visit symptom revisions are outside this 19-table operational model; no fabricated longitudinal symptom history will be shown.
12. **Diagnoses are observations.** The requested diagnoses table records a diagnosis label/type on a visit, not a reusable catalog entry. Repeating the same diagnosis label across visits is meaningful. Within a visit, `(visit_id, diagnosis_name, diagnosis_type)` is UNIQUE. Multiple co-primary labels are allowed; the brief does not require a single primary label.
13. **Appointments and follow-ups are different facts.** A follow-up plan is not an appointment and does not automatically reserve a slot. Walk-in visits are possible; cancelled bookings need not have visits. No artificial mandatory appointment–visit relation is added. Completing a plan records `actual_date`; it does not imply a foreign key to a completion encounter.
14. **Audit actor labels are historical facts.** Add `actor_username`, the username at event time (or SYSTEM/SEED), so historical attribution survives renamed/deleted users. This is distinct from the user's current username. `entity_id` supports canonical composite identifiers for junction-table events.
15. **The monthly table is a cache.** It counts SUBMITTED cases by their case-date month. `completed_cases` means cases currently CLOSED in that cohort, not closures that occurred in that month. Add `refreshed_at` so reports can disclose freshness. Live dashboard totals remain live queries.

Text notes are atomic narrative attributes at the application's chosen level of interpretation. Searchable lists of symptoms and medicines are junction rows, never comma-separated values or numbered columns.

## 4. Primary keys, candidate keys, and foreign keys

A candidate key is a minimal set of attributes that identifies every tuple. Every primary key below is also a candidate key. A surrogate ID does not make genuine non-key dependencies disappear; those are analyzed separately.

| Relation | Primary key | Other unconditional candidate keys |
|---|---|---|
| users | user_id | username; email |
| doctors | doctor_id | user_id; license_number; email |
| patients | patient_id | None; nullable unique email is only a conditional identifier |
| medical_cases | case_id | None |
| visits | visit_id | None; equal timestamps are possible |
| symptoms | symptom_id | symptom_name |
| case_symptoms | (case_id, symptom_id) | None |
| medical_history | history_id | None; repeat episodes allowed |
| allergies | allergy_id | None assumed |
| lifestyle_history | lifestyle_id | patient_id |
| vital_signs | vital_id | visit_id |
| examinations | examination_id | visit_id |
| diagnoses | diagnosis_id | (visit_id, diagnosis_name, diagnosis_type) |
| medicines | medicine_id | medicine_code |
| prescriptions | prescription_id | visit_id |
| prescription_medicines | (prescription_id, medicine_id) | None |
| appointments | appointment_id | None; slot equality does not define identity |
| follow_ups | follow_up_id | None; multiple plans from a visit allowed |
| audit_logs | audit_id | None |
| monthly_case_statistics | stat_month | None |

UNIQUE comparisons follow the chosen collation. Login emails/usernames and catalog names are trimmed and consistently normalized before storage; empty unique strings are rejected. IDs are not inferred from names, phone numbers, or dates.

Every FK is individually listed with its delete behavior in section 9. All referenced targets are PRIMARY KEYs; the schema does not rely on MySQL's historical ability to reference a non-unique index.

## 5. Relationships, cardinalities, and participation

Read each row as: for one parent, how many children may exist; for one child, how many parents must exist. **Total participation** means mandatory; **partial participation** means optional. Parents with a zero minimum participate partially. Non-null child FKs imply total participation for that relationship.

| Parent → child | Children per parent | Parents per child | Participation / enforcement |
|---|---|---|---|
| users → doctors | 0..1 | 1 | User partial, doctor total; UNIQUE NOT NULL user_id |
| patients → medical_cases | 0..N | 1 | Patient partial, case total |
| doctors → medical_cases | 0..N | 1 | Doctor partial, case total |
| medical_cases → visits | 0..N while DRAFT; 1..N when SUBMITTED | 1 | Case conditionally total on submission; visit total; minimum requires transaction rule |
| doctors → visits | 0..N | 1 | Doctor partial, visit total; actual attendance |
| medical_cases → case_symptoms | 0..N | 1 | Case partial, association total |
| symptoms → case_symptoms | 0..N | 1 | Symptom partial, association total |
| patients → medical_history | 0..N | 1 | Patient partial, history total |
| patients → allergies | 0..N | 1 | Patient partial, allergy total |
| patients → lifestyle_history | 0..1 | 1 | Patient partial, lifestyle total; UNIQUE patient_id |
| visits → vital_signs | 0..1 | 1 | Visit partial, measurement set total; UNIQUE visit_id |
| visits → examinations | 0..1 | 1 | Visit partial, examination total; UNIQUE visit_id |
| visits → diagnoses | 0..N | 1 | Visit partial, diagnosis total |
| visits → prescriptions | 0..1 | 1 | Visit partial, prescription total; UNIQUE visit_id |
| doctors → prescriptions | 0..N | 1 | Doctor partial, prescription total; actual authorship |
| prescriptions → prescription_medicines | 0..N during draft editing; 1..N at submitted document completion | 1 | Minimum requires service transaction, association total |
| medicines → prescription_medicines | 0..N | 1 | Catalog product partial, association total |
| patients → appointments | 0..N | 1 | Patient partial, booking total |
| doctors → appointments | 0..N | 1 | Doctor partial, booking total |
| visits → follow_ups | 0..N | 1 | Visit partial, plan total |
| users → audit_logs | 0..N | 0..1 | Both partial; NULL actor for system/seed or deleted account |

Derived conceptual relations are Case M:N Symptom through case_symptoms; Prescription M:N Medicine through prescription_medicines; and Case 0..N FollowUp through visits. Case–FollowUp is a join path, not an extra stored FK. The reporting cache has no ownership relation to a single case.

The user/doctor specialization rule strengthens the generic ER edge: an ADMIN or RECEPTIONIST user has zero doctor profiles; every operational DOCTOR account has exactly one. An FK alone cannot enforce that role predicate or the existence of a child row.

## 6. Generalization / specialization decision

Conceptually, USER specializes into ADMIN, DOCTOR, and RECEPTIONIST. The specialization is **total and disjoint**: every account has exactly one allowed role. It is not a multi-role model.

Implement the common identity in users, with a constrained role discriminator. Only DOCTOR has additional required attributes, so doctors is its extension with UNIQUE NOT NULL user_id. Admin and receptionist subtypes have no distinct attributes and do not warrant empty tables. This combines a role discriminator with one meaningful extension table.

Provision a doctor account and its profile in one transaction. Validate/lock the user when creating the profile; reject profiles for other roles. Protect role changes with the same lock: an account with a doctor profile cannot be demoted until its profile is validly removed, which is normally prevented by existing clinical references. A doctor account is deactivated, not casually converted into another role. A failed two-step provisioning must roll back both inserts. Database role/profile guard triggers plus controlled API/procedure writes will enforce these cross-table rules; no CHECK containing a subquery will be proposed.

## 7. Constraint and validation strategy

| Rule | Enforcement layer | Reason |
|---|---|---|
| Identity, mandatory references | PRIMARY KEY, NOT NULL, FOREIGN KEY | Universal relational integrity |
| Natural identity and 0..1 ownership | UNIQUE + NOT NULL | Enforce alternate keys and maximum cardinality |
| Role/status/type domains | VARCHAR + named CHECK; Pydantic enums | Explicit, explainable domains; consistent API errors |
| Meaningful required strings | Pydantic trim/length validation; CHECK for submitted complaint | NOT NULL alone permits empty strings |
| Non-future DOB/history dates | BEFORE INSERT/UPDATE guards plus API validation | Current-date comparison is not a valid MySQL deterministic CHECK |
| Valid dates and lengths | Strict SQL modes plus typed Pydantic inputs | Reject zero/invalid dates and truncation |
| Email / phone representation | API validation and normalization | Format checks are distinct from identity/uniqueness |
| Missing values | NULL rather than invented zeros/empty clinical entries | Unknown is not a measurement or normal finding |
| Measurement representation | DECIMAL/SMALLINT plus documented positive/percentage checks | Basic integrity only, not clinical advice |
| Appointment interval | Row CHECK plus serialized overlap service | CHECK can compare same-row times, not concurrent bookings |
| Doctor user-role membership | Guard triggers + atomic provisioning/role-change services | Cross-table predicate |
| Follow-up scheduled date not before originating visit's clinic date | Trigger/service validation on plan insert/update | Comparison crosses tables |
| Follow-up completion date | Row CHECK for status/null consistency; API/trigger for non-future and chronology | Unplanned early completion may precede scheduled_date, but not originating visit |
| Submitted case has initial visit | Atomic submission service; parent locked during transition | FKs cannot assert minimum child count |
| Prescription has at least one valid product line on completion | Atomic service validation | Parent FK cannot force children |
| Initial visit/entered clinical documents complete at submission | Service validates entire case bundle | Conditional and cross-table completeness |
| Non-future recorded encounters/prescription dates, prescription not before originating encounter date | API plus cross-table/date guards | Appointments/follow-ups may be future; performed encounters differ |
| No visits added to CLOSED/DRAFT cases except initial draft editing | Locked case service | Avoid changing a completed case accidentally |
| No submitted-record ownership changes | Service rejects changing case patient or visit case | Prevent moving history between patients |

CHECK expressions allow NULL to evaluate UNKNOWN, so required values also need NOT NULL. Domain checks use named constraints, unique across the schema. No CHECK is placed on an AUTO_INCREMENT column or on FK columns with referential actions; date/status checks operate on ordinary columns. These choices follow [MySQL CHECK restrictions](https://dev.mysql.com/doc/refman/8.0/en/create-table-check-constraints.html).

Allowed workflow: OPEN → UNDER_REVIEW/FOLLOW_UP/CLOSED; UNDER_REVIEW → OPEN/FOLLOW_UP/CLOSED; FOLLOW_UP → OPEN/UNDER_REVIEW/CLOSED. CLOSED is terminal for this demo. Closing requires SUBMITTED state and no PENDING follow-up plans; the user must explicitly complete/cancel plans first. Appointment edits preserve historical COMPLETED/NO_SHOW entries; CANCELLED does not delete the booking. Follow-ups transition PENDING → COMPLETED/MISSED/CANCELLED; MISSED may be explicitly rescheduled to PENDING, with actual_date NULL. Any rescheduling rechecks the originating visit date. These are proposed application workflow rules, not automatic medical judgments.

## 8. Transactions and concurrency

### Case-taking and draft persistence

Persist an initial draft only after valid patient_id and doctor_id are selected. Save all currently valid entered child records in one transaction; incomplete optional sections have no child row until their required fields are valid. Upsert one-to-one rows using their unique owner key. The UI must keep incomplete in-progress values when navigating steps and report that incomplete sections have not yet been persisted. Never manufacture placeholder diagnoses or medicines to satisfy required fields.

For final submission: authenticate/authorize; lock the case; validate all entered sections; create or complete its initial visit; persist symptoms, history, allergies, lifestyle, vitals, examination, diagnoses, prescription lines and follow-up plans; set record_state SUBMITTED; commit once. No clinical section is mandatory merely to force a filled form: missing optional examination/prescription data is permitted. If supplied, a prescription needs valid lines. On any failure, roll back the entire submission. Use returned IDs to update the same draft on retries; a failed request must not silently create another case.

Subsequent visits are created atomically for an authorized doctor on an open submitted case. Preserve past visits when changing the current case assignee. Lock the case during close, submission, and new-visit operations; reject deletion of the sole initial visit of a submitted case. The proposed API has no general visit-delete operation.

### Appointment overlap prevention

A pre-insert SELECT without a shared locking protocol is insufficient: two requests can both observe an empty slot. Use this protocol for every create, edit, cancellation, reactivation, and booking-status mutation:

1. Begin an InnoDB transaction.
2. Lock the existing doctors row with SELECT … FOR UPDATE. This serializes scheduling even when that doctor has no appointment rows yet.
3. For a doctor reassignment, lock both old/new doctor IDs in increasing order before taking the appointment row lock. Re-read after locks and retry if the old assignment changed. All scheduling paths use this same lock order.
4. Run a current locking read of same-doctor/same-date appointments, excluding the edited appointment ID. Check `existing.start_time < proposed.end_time AND existing.end_time > proposed.start_time`. Exclude only CANCELLED entries; retained COMPLETED/NO_SHOW records still occupy their historical interval. Adjacent intervals are permitted.
5. Validate local date/time and allowed status transition, write the booking, commit; map conflict to HTTP 409.

Use READ COMMITTED service transactions or explicitly current locking reads, avoiding a stale repeatable-read snapshot for the conflict test. Deadlocks receive a bounded retry of the entire transaction. A check on equal start_time alone cannot detect partial overlaps. Keep transactions short and execute no external calls while holding locks. [MySQL locking reads](https://dev.mysql.com/doc/refman/8.0/en/innodb-locking-reads.html) provide the underlying mechanism; the doctor-row protocol is this project's design.

The guarantee assumes all appointment writers follow this service/procedure contract. Workbench examples must use the same controlled path, and ordinary demo roles must not have unrestricted appointment-table writes. This is not a native exclusion constraint; privileged arbitrary SQL can bypass the protocol.

### Savepoints, audits, and transaction ownership

The realistic TCL demo registers a patient, creates a case and initial visit, sets a savepoint before prescription creation, rolls back an invalid prescription attempt to that savepoint, and either completes the case or rolls everything back. Rolled-back inserts may leave gaps in AUTO_INCREMENT IDs; IDs are not gapless serial numbers.

The API service owns transaction boundaries. Business procedures such as register_patient, close_case, and schedule_followup are composable and do not internally COMMIT the caller's transaction. Workbench wraps them with explicit START TRANSACTION/COMMIT/ROLLBACK. Stored procedures validate input, signal errors, and let the caller decide whether to roll back the whole transaction or to a savepoint. The standalone cache-refresh procedure has its own documented transaction and is never invoked inside a case-writing transaction.

Audit triggers participate in the same InnoDB transaction: rolled-back patient/case changes also roll back their audits. Failed login/security attempts are separate application events; an audit trigger is not a durable record of rolled-back writes.

## 9. Foreign-key policies and deletion behavior

All FKs use **ON UPDATE CASCADE** for referential completeness. IDs are immutable through the API; the clause does not authorize ID editing. Use soft deactivation for users/catalogs, case closure for clinical cases, and appointment/follow-up cancellation for scheduling.

| Child FK → parent PK | ON DELETE | Justification |
|---|---|---|
| doctors.user_id → users.user_id | RESTRICT | Do not orphan a professional identity |
| medical_cases.patient_id → patients.patient_id | RESTRICT | Do not delete the owner of case history |
| medical_cases.doctor_id → doctors.doctor_id | RESTRICT | Preserve assigned-doctor reference |
| visits.case_id → medical_cases.case_id | RESTRICT | Cases with encounters cannot be removed casually |
| visits.doctor_id → doctors.doctor_id | RESTRICT | Preserve actual attendance |
| case_symptoms.case_id → medical_cases.case_id | CASCADE | Association has no meaning without its case |
| case_symptoms.symptom_id → symptoms.symptom_id | RESTRICT | Deactivate referenced vocabulary instead |
| medical_history.patient_id → patients.patient_id | CASCADE | Owned patient extension; patient with cases/bookings remains protected |
| allergies.patient_id → patients.patient_id | CASCADE | Owned patient extension |
| lifestyle_history.patient_id → patients.patient_id | CASCADE | Owned current patient snapshot |
| vital_signs.visit_id → visits.visit_id | CASCADE | Measurement set is a visit component |
| examinations.visit_id → visits.visit_id | CASCADE | Examination is a visit component |
| diagnoses.visit_id → visits.visit_id | CASCADE | Observations are visit components |
| prescriptions.visit_id → visits.visit_id | CASCADE | Prescription is a visit document |
| prescriptions.doctor_id → doctors.doctor_id | RESTRICT | Preserve prescriber attribution |
| prescription_medicines.prescription_id → prescriptions.prescription_id | CASCADE | Lines cannot exist without their document |
| prescription_medicines.medicine_id → medicines.medicine_id | RESTRICT | Referenced product must remain identifiable |
| appointments.patient_id → patients.patient_id | RESTRICT | Retain booking history; cancel instead |
| appointments.doctor_id → doctors.doctor_id | RESTRICT | Retain booking attribution |
| follow_ups.visit_id → visits.visit_id | RESTRICT | A plan's originating encounter must remain identifiable |
| audit_logs.user_id → users.user_id | SET NULL | Preserve the event if an unreferenced account is removed |

API DELETE patients succeeds only for an admin and when no restrictive case/appointment references exist, otherwise returns 409. API DELETE cases is admin-only and limited to an unused DRAFT without visits; otherwise 409. API DELETE appointments means cancellation and retains the row. No general clinical-visit purge is exposed. Cascade demonstrations use synthetic disposable records in a transaction or an isolated demonstration schema, not arbitrary seeded history.

MySQL cascaded FK actions do not invoke child-table triggers. Consequently, a parent deletion audit summarizes its component removal; the design does not promise an automatically triggered audit per cascaded child. Application audit tables are append-only to runtime roles, with the documented SET NULL referential exception. See [MySQL FK actions](https://dev.mysql.com/doc/refman/8.0/en/create-table-foreign-keys.html).

## 10. Indexing strategy

PRIMARY KEYs and UNIQUE constraints already create indexes. InnoDB requires FK-supporting indexes and may create them automatically; Phase 2 names/reuses suitable indexes rather than creating redundant duplicates. Composite indexes work from their leftmost prefix; a patient/date index does not replace a doctor/date index.

| Table | Proposed additional/supporting index | Purpose |
|---|---|---|
| patients | (last_name, first_name, patient_id) | Name-prefix filtering and stable alphabetical pagination |
| patients | (first_name, patient_id) | First-name prefix searches |
| patients | (phone) | Exact phone search, including shared numbers |
| patients | (created_at, patient_id) | Registration reports and recent patients |
| doctors | (last_name, first_name, doctor_id) | Doctor directory |
| medical_cases | (patient_id, case_date, case_id) | Patient case history |
| medical_cases | (doctor_id, record_state, case_status, case_date, case_id) | Assigned doctor workload/status filtering |
| medical_cases | (record_state, case_status, case_date, case_id) | Active/closed submitted case lists |
| medical_cases | (case_date, case_id) | Monthly cohorts and date-range reports |
| visits | (case_id, visit_date, visit_id) | Ordered encounter history |
| visits | (doctor_id, visit_date, visit_id) | Attending-doctor workload |
| visits | (visit_date, visit_id) | Global encounter date reports |
| case_symptoms | (symptom_id, case_id) | Reverse side of M:N and top-symptom aggregation |
| medical_history | (patient_id, diagnosed_date, history_id) | Condition history retrieval |
| allergies | (patient_id) | Patient allergy lookup |
| diagnoses | (diagnosis_name, visit_id) | Label search and aggregate counts |
| medicines | (medicine_name, medicine_id) | Catalog prefix search |
| prescriptions | (doctor_id, prescription_date, prescription_id) | Prescriber reports |
| prescriptions | (prescription_date, prescription_id) | Monthly prescription total |
| prescription_medicines | (medicine_id, prescription_id) | Reverse side of M:N and product frequency |
| appointments | (doctor_id, appointment_date, start_time, appointment_id) | Doctor/date overlap scan and calendar |
| appointments | (patient_id, appointment_date, appointment_id) | Patient booking history |
| appointments | (appointment_date, status, appointment_id) | Today's appointments and date/status filters |
| follow_ups | (status, scheduled_date, follow_up_id) | Pending/upcoming/missed queue |
| follow_ups | (visit_id) | Originating-visit FK and case traversal |
| audit_logs | (created_at, audit_id) | Stable chronological audit pagination |
| audit_logs | (user_id, created_at, audit_id) | Actor audit lookup |
| audit_logs | (entity_type, entity_id, created_at, audit_id) | Entity operation history |

Unique indexes already cover users.username/email; doctors.user_id/license_number/email; patients.email; symptoms.symptom_name; medicines.medicine_code; one-to-one owner keys; and the composite diagnosis label key. The two junction PKs cover their first FK, while the reverse indexes cover their second FK. Cache stat_month PK supports month-range reads.

Backend pagination uses LIMIT/OFFSET with a maximum page size and deterministic tiebreaker ID. Filter fields and sorting are allowlisted; values are bound parameters. For patient ID, phone and email prefer exact matching; use prefix LIKE for names. `%substring%` search is supported if desired but cannot be claimed to use an ordinary B-tree efficiently. No FULLTEXT index or patient-table scan avoidance is promised for arbitrary substring search. Use indexed date ranges instead of wrapping an indexed date column in a function in WHERE; grouping by month may still use date expressions. Validate final choices with EXPLAIN on seeded data rather than claiming every index is beneficial.

## 11. Advanced DBMS object plan

This is an architecture plan; definitions and demonstrations belong to later phases.

| Object | Proposed behavior and application use |
|---|---|
| patient_case_summary view | Submitted case listing with patient/current assigned-doctor names, chief complaint and status; API still applies role scope and pagination |
| upcoming_followups view | PENDING plans on/after clinic date, joined through visits/cases/patients/assigned doctor; API applies role scope and basic-field projection for reception |
| doctor_case_statistics view | Per-doctor submitted total/active/closed cases, retaining doctors with zero cases; admin reports and scoped doctor dashboard |
| calculate_age(date_of_birth) function | Completed years at current clinic date; NOT DETERMINISTIC, NO SQL; NULL for absent input, invalid dates rejected earlier |
| calculate_bmi(height_cm, weight_kg) function | Rounded decimal result; DETERMINISTIC, NO SQL; NULL for missing/non-positive inputs |
| patient_visit_count(patient_id) function | Submitted-case visit count through cases; NOT DETERMINISTIC, READS SQL DATA |
| doctor_case_count(doctor_id) function | Current assigned submitted-case count; NOT DETERMINISTIC, READS SQL DATA |
| register_patient procedure | Validates demographics, inserts a patient, returns new ID; caller transaction |
| close_case procedure | Locks case, validates SUBMITTED state and resolved plans, changes status; caller transaction; case trigger supplies audit |
| schedule_followup procedure | Validates originating visit and chronology, creates plan; caller transaction |
| refresh_monthly_case_statistics procedure | Serialized rebuild using DELETE + INSERT SELECT in one independent transaction; writes consistent refreshed_at |
| Patient AFTER INSERT / AFTER UPDATE triggers | Create concise actor-attributed audit metadata |
| Case AFTER INSERT / AFTER UPDATE triggers | Audit creation, update, submission/closure; one appropriate action per mutation |
| BEFORE UPDATE timestamp triggers | Maintain patients.updated_at, medical_cases.updated_at and lifestyle_history.updated_at |
| Date and doctor-role guard triggers | Reject cross-table/current-date violations where a row CHECK cannot express the rule |

Function calls will appear in actual profile/report queries, not only unused SQL files. Aggregate list reports should use set-based joins instead of invoking count functions once per row. Avoid multiplying counts when joining multiple one-to-many relations: preaggregate independent children, or use COUNT(DISTINCT appropriate_id) with a stated counting unit.

**MySQL does not provide native materialized views. A materialized-view equivalent is implemented using a precomputed summary table and refresh procedure/event.** This is explicitly documented by the [MySQL views FAQ](https://dev.mysql.com/doc/refman/8.0/en/faqs-views.html).

Refresh uses DELETE, not TRUNCATE, so failures can roll back and readers do not see a committed empty intermediate result. Serialize independent refreshes with a named lock released in success/error handlers; build counts from one INSERT SELECT source statement; on error roll back and preserve the last committed cache. The procedure owns its transaction and must run outside an existing one. No cache table is presented as the source of operational truth. An optional EVENT requires deliberate scheduler setup and is deferred; manual refresh suffices for the assignment. [MySQL implicit commits](https://dev.mysql.com/doc/refman/8.0/en/implicit-commit.html) explain why DDL/TRUNCATE is separated from TCL demonstrations.

## 12. Security and role scope

JWT identities represent application users, not MySQL accounts. Hash passwords with Argon2id; check active state on protected requests, not just the JWT role claim. Keep signing secret and database URL in environment variables. Configure explicit CORS origins, use Pydantic request/response schemas, parameterize SQL, and return friendly 401/403/404/409/422 errors without stack traces or raw database credentials.

| Capability | Admin | Doctor | Receptionist |
|---|---|---|---|
| Register/search basic demographics | Yes | Yes | Yes |
| Edit demographics | Yes | Assigned patients | Yes |
| Delete unused patient/draft | Yes, restrictive policy | No | No |
| View full patient clinical history | All patients | Assigned patients | No |
| Search unassigned patients | Basic demographics | Basic demographics | Basic demographics |
| Create/read/edit cases and clinical observations | All | Own assigned cases; authorized attending/prescribing work | No |
| Book/edit/cancel appointments | All | Own doctor scope | All |
| View upcoming follow-ups | All | Assigned scope | Basic scheduling details only |
| Modify follow-up clinical reasons/instructions | Yes | Assigned scope | No |
| Manage users/doctors/catalogs | Yes | Read necessary catalogs | Read doctor directory only |
| Dashboards/reports | All | Assigned scope | Scheduling/demographic aggregates only |
| Audit logs | Yes | No | No |

For this project, a doctor's assigned patient is one with a case currently assigned to that doctor or a non-cancelled appointment with that doctor. The authorization service can additionally permit a recorded attending/prescribing doctor to read their own encounter/document. A prior attendance does not grant unrestricted editing of other doctors' cases. A doctor may create a new case assigned to themselves for a registered patient; that creates the new assignment. ID guessing never substitutes for ownership checks. Reception responses exclude diagnosis, medicines, examination, clinical history, free-text case notes and follow-up instructions. Full-text instructions/reasons may contain clinical narrative, so the reception queue uses patient/doctor/date/status only.

MySQL DCL demonstrations define separate least-privilege database roles in later phases. Admin full privileges apply to the project schema, not global root or GRANT OPTION. Doctor/reception demonstration roles use scoped views and controlled routines where table writes would bypass business rules; GRANT/REVOKE does not implement patient-level JWT authorization. The app runtime account has no schema-changing privileges. A migration account installs schema/routines/triggers. Runtime can execute business procedures and authorized SQL without being root. Avoid unrestricted pooled SET ROLE switching as a substitute for API authorization.

Triggers cannot infer the JWT user from CURRENT_USER(), which identifies the database execution account. The backend sets connection-local actor ID/label from the authenticated request, or an explicit SEED/SYSTEM context, before writes; clears it on check-in and checkout; and never accepts client-supplied actor overrides. Missing actor context is rejected for audited app writes rather than silently reusing a previous pooled identity. Guards validate that a non-system actor exists and is active. This attribution trusts the backend/privileged operator; it is not cryptographically tamper-proof against database administrators. Other important mutations use service audit inserts once per operation; patient/case mutations rely on their triggers to avoid duplicate events.

## 13. Reporting, timeline, and data scope

Default active cases are SUBMITTED with OPEN/UNDER_REVIEW/FOLLOW_UP status. Drafts are a separate queue and excluded from headline clinical/report totals. Today's appointments use clinic-local date; upcoming plans are PENDING with scheduled_date on/after that date. Prescription-month counts use prescription_date, excluding documents still attached to draft cases. Every number has a defined counting unit and role scope.

The patient profile uses patient → cases → visits for chronology, with left joins or separate paginated queries for optional details. Timeline events come from visit_date, case_symptoms.recorded_at, prescription_date, follow-up scheduled/actual dates, patient/case creation timestamps and authorized audit metadata. A date-only event displays a date, not an invented time or precise event ordering. The timeline is a care-record narrative, not an immutable revision history of every edited field. Current demographics/lifestyle and case-level baseline symptoms are labeled as such.

History, allergies and lifestyle have their own patient endpoints/services or sections within the case submission transaction; the proposed eventual API list must be expanded accordingly so these are never browser-only data. Admin user management and audit-log retrieval likewise require backend endpoints. Ten required reports are generated from operational joins or the clearly labeled monthly cache, with server filters/sort/pagination. Medication and diagnosis summaries are descriptive fictional counts only.

## 14. MySQL compatibility baseline

Proposed minimum: **MySQL 8.0.31**, InnoDB, utf8mb4, consistent utf8mb4_0900_ai_ci collation for names/search. Byte-sensitive identifiers such as fictional license/product codes may explicitly use utf8mb4_0900_as_cs. Column pairs in FKs have identical types/sign; table names are lowercase snake_case. Use INT/BIGINT AUTO_INCREMENT, DATE, TIME, DATETIME(6), DECIMAL, VARCHAR and TEXT. BOOLEAN is MySQL's alias with explicit 0/1 checks.

- CHECK constraints are enforced from 8.0.16; expressions cannot use nondeterministic current-time functions, subqueries or stored functions. Use date guards for current-date comparisons. [CHECK documentation](https://dev.mysql.com/doc/refman/8.0/en/create-table-check-constraints.html)
- Native INTERSECT and EXCEPT are available from 8.0.31. Include these demonstrations and clearly labeled EXISTS/NOT EXISTS equivalents for older 8.0.16–8.0.30 lab installations if necessary. Those older versions would require an explicitly documented compatibility adjustment, not an unannounced lowering of the baseline. [Set operations](https://dev.mysql.com/doc/refman/8.0/en/set-operations.html)
- FULL OUTER JOIN has no native MySQL operator; demonstrate LEFT JOIN combined with unmatched RIGHT JOIN rows using UNION ALL (or the requested LEFT JOIN UNION RIGHT JOIN formulation when duplicate elimination is intentional). Do not accidentally discard meaningful duplicate rows. [MySQL join syntax](https://dev.mysql.com/doc/refman/8.0/en/join.html)
- No native materialized view: use the documented physical cache. [Views FAQ](https://dev.mysql.com/doc/refman/8.0/en/faqs-views.html)
- Foreign-key checks are immediate in InnoDB, not deferred. NO ACTION behaves as RESTRICT; child cascade changes do not activate child triggers. Never disable foreign_key_checks to make seeds appear valid. [FK documentation](https://dev.mysql.com/doc/refman/8.0/en/create-table-foreign-keys.html)
- Most DDL and TRUNCATE implicitly commit; SQL demonstrations use disposable tables/schema and remain separate from rollback/savepoint examples. Atomic DDL does not mean user-transactional DDL. [Implicit commits](https://dev.mysql.com/doc/refman/8.0/en/implicit-commit.html)

Store instant timestamps in UTC DATETIME(6), set SQL session timezone to +00:00, and convert to Asia/Kolkata for display. Appointment date/time pairs and case/prescription/follow-up dates use the fixed clinic calendar. The date guard and age function derive clinic date using the explicit +05:30 offset; this avoids relying on installed MySQL timezone tables for this single-zone demo. Never compare a local appointment date directly with the UTC server date near midnight. No multi-clinic or daylight-saving-zone support is claimed.

Connection initialization sets strict date handling and ONLY_FULL_GROUP_BY. Stored routines use appropriate DETERMINISTIC/NOT DETERMINISTIC and SQL-data-access declarations. Function/trigger installation and optional events may require privileges unavailable to a runtime account, especially with binary logging; setup documents those requirements rather than asking the runtime to use root. MySQL Workbench is a client, not the database server or version authority.

## 15. Phase boundaries and next implementation deliverables

Phase 1 artifacts are architecture, full dictionary, FDs/normalization, Mermaid, DBML and editable draw.io. MySQL Workbench reverse engineering is deferred until schema creation in Phase 2. No fabricated application screenshots, test results, SQL installation commands, or demo credentials are included.

Phase 2 created `database/01_create_database.sql` and `02_schema.sql`, matching this dictionary and named constraints/indexes. Review the actual local server version first, apply to a disposable development schema, inspect SHOW CREATE TABLE/information_schema, and exercise PK/FK/UNIQUE/CHECK/NULL behavior. Trigger/procedure-dependent rules are tracked explicitly until their later implementation, not claimed to exist from table DDL alone. Phase 3 seeds valid fictional parent rows before children. Later phases add backend, frontend, advanced objects, end-to-end verification and the final presentation guide.

Later SQL files 03–13 retain the brief's requested ordering/names. Integration setup must install audit/guard triggers and required routines **before** seeding, or deliberately backfill labeled seed audit events; filename numbering alone must not dictate an incorrect installation order. Seed generation must satisfy the full brief's minima: 150 patients, 20 doctors, 40 symptoms, 40 fictional medicines, 250 cases, 400 visits, 500+ case-symptom rows, 300 diagnoses, 200 prescriptions, 500 prescription-medicine rows, 300 non-overlapping appointments, 150 plans, 200 history rows, 100 allergies and 500 audit events. Referenced IDs are taken from created parents, not random unchecked numbers.

Team responsibilities remain: Member 1 database/DBMS and seeds; Member 2 APIs/authentication/transactions; Member 3 React UX/API integration. All three should be able to explain the shared design; this division does not imply spawning implementation agents or starting later phases.

## 16. Implementation acceptance checklist

This is the original design acceptance checklist. Executed database, API and browser verification is recorded in TESTING.md.

- [ ] Empty schema creates cleanly on the selected MySQL version; all 20 tables and 21 FKs match the design.
- [ ] Duplicate usernames, login emails, doctor license/user mapping, symptom names and product codes fail.
- [ ] Two NULL patient emails succeed; duplicate known emails fail; two patients sharing a phone succeed.
- [ ] Invalid FK, role/status domain, missing mandatory value, malformed email, future DOB and invalid dates fail through the appropriate layer.
- [ ] Optional one-to-one records may be absent; duplicate lifestyle/vitals/examination/prescription owner keys fail.
- [ ] Junction keys reject duplicate pairs; multiple distinct symptoms/products succeed.
- [ ] Patient/case/doctor/catalog RESTRICT behavior and owned-child CASCADE behavior are verified in disposable test data.
- [ ] Unreferenced-user deletion nulls the audit user FK and preserves event-time actor label.
- [ ] Doctor/profile atomic provisioning and invalid role changes are tested, including concurrent changes.
- [ ] Draft save/edit preserves entered data, updates the same IDs, and is distinguishable from submitted cases.
- [ ] Case submission succeeds as one transaction; a child failure rolls back all writes and trigger audits.
- [ ] SAVEPOINT before prescription, ROLLBACK TO SAVEPOINT, full ROLLBACK and COMMIT produce the expected persisted state.
- [ ] Close/new-visit races respect the case lock and allowed workflow; historical attendance survives reassignment.
- [ ] Follow-up date/status guards reject mismatched or impossible states; case IDs in API responses are derived consistently.
- [ ] Two independent connections booking overlapping slots yield exactly one success; empty schedules, adjacent intervals, edits, cancellations, reactivation and doctor reassignment are covered.
- [ ] Reception clinical reads/modifications return 403; basic scheduling responses never include clinical narrative.
- [ ] Doctor ownership checks hold across case/detail/report endpoints and do not rely on hidden UI controls.
- [ ] Trigger actor identity survives connection pooling without leaking the previous request's actor.
- [ ] Functions/procedures/views produce correct outputs and are actually used where promised.
- [ ] Cache refresh is atomic, repeatable, rollback-safe and labeled with freshness; results match the defined submitted-case cohorts.
- [ ] Forty meaningful DQL demonstrations cover requested operators/joins/aggregates, with version-specific alternatives labeled.
- [ ] Search/sort/pagination and live reports return database results; filters are bound/allowlisted and joins do not inflate counts.
- [ ] The fictional receptionist → doctor → patient timeline → reports demo completes after application implementation.

## 17. Approval decision

Review the dictionary, relationship matrix and normalization alongside the ERD. The principal decisions to approve are the derived follow-up case link, derived BMI/age, explicit optional one-to-one cardinalities, separate case/visit/prescriber semantics, shared patient phone handling, persisted draft state, and the clearly labeled monthly summary cache.

**The user subsequently authorized all remaining phases without approval gates. The completed implementation and test evidence are linked from README.md.**
