# CareTrack — project presentation and viva guide

CareTrack is an educational demonstration project using fictional data. It is not intended for real clinical use.

## Problem statement and objectives

Paper-style case records distribute patient demographics, case narratives, observations, encounter measurements, product documents and scheduling across repeated records. Retrieving a longitudinal history is slow, and repeated facts create update anomalies. CareTrack demonstrates how a normalized relational database, transactional API and role-aware interface connect those records.

The objectives are structured case taking, quick history retrieval, consistent relationships, concurrent appointment integrity, appropriate role access, useful reporting, attributable operations and an explainable implementation of the required SQL concepts. Fictional observations and imaginary products support the DBMS exercise without medical advice.

The main use cases are registration/search/edit, patient profile/history, eleven-step case creation, draft recovery, symptoms/history/allergies/lifestyle, encounter vitals/examination, diagnosis and fictional prescription recording, subsequent visits, follow-up planning/resolution, appointments, doctor/account management, reports/dashboard and audit inspection.

## Three-person responsibilities

| Member | Ownership | Presentation segment |
|---|---|---|
| 1 — Database & DBMS | ERD, keys, participation, normalization/FDs, schema/indexes, seed, SQL labs, views/routines/triggers | Model and Workbench demonstration |
| 2 — Backend | FastAPI, SQLAlchemy, Pydantic, JWT/Argon2, role/ownership, transactions, appointments, errors and integration tests | Request flow, atomicity, concurrency and API docs |
| 3 — Frontend | React/TypeScript, responsive workspace, case form, profile/timeline, scheduling, charts/reports and browser tests | Application walkthrough and user flows |

All members should understand the full data path and be able to explain why the database remains the source of truth.

## ERD explanation

Show `ER_DIAGRAM.md` and the imported Workbench EER model. Begin with Patient 1:N Case and Doctor 1:N Case. A case has multiple visits, while each visit records its attending doctor. Case M:N Symptom is resolved through `case_symptoms`; Prescription M:N Medicine through `prescription_medicines`. Each junction has a composite PK that prevents duplicate associations and determines the relationship attributes.

Patient owns multiple history/allergy records and at most one current lifestyle row. A visit optionally owns one vitals row, one examination, one prescription, many diagnoses and many follow-up plans. Doctor/patient each have many appointments. A Doctor profile references exactly one User and the unique user_id guarantees at most one Doctor per account. Audit actor is optional after account deletion, but actor_username retains attribution. The reporting cache is derived infrastructure rather than a new clinical entity.

Mandatory participation belongs to each FK child: a visit needs a case, a case needs a patient and doctor. Parent participation is generally optional: a newly registered patient can have no case. Submitted-case participation is stronger than a simple FK and is enforced by workflow validation/trigger rules requiring an initial encounter. Explain optional one-to-one links as unique visit_id or patient_id FKs.

## Keys, schema and specialization

Use `RELATIONAL_SCHEMA.md` for every implemented column and constraint. Integer surrogate IDs give stable references. Username/login email and doctor license/professional email are unique candidate identifiers under their nonnull constraints. Patient email is nullable UNIQUE; it is not a required candidate key. Phone is indexed and intentionally nonunique because a fictional household can share a phone. Product presentation has stable unique `medicine_code`; a referenced presentation is immutable except activation.

Users are a total, disjoint specialization using role ADMIN/DOCTOR/RECEPTIONIST. Only Doctor has extra subtype attributes, so one Doctor extension table is justified. Empty Admin and Receptionist tables add no independent facts. Constraints enforce accepted roles and Doctor-to-DOCTOR account linkage. Explain that every DOCTOR account is provisioned with its profile atomically by the API; direct SQL administrators must maintain the reverse participation rule.

## Normalization and functional dependencies

Show the detailed worked derivation in `NORMALIZATION.md`. Start with a conceptual record containing repeated symptoms/medicines and duplicated patient/doctor facts. UNF → 1NF makes each relationship occurrence atomic and removes numbered repeating columns. 1NF → 2NF separates facts depending on only one component of a composite key. 2NF → 3NF removes facts depending on a nonkey determinant.

Examples to state aloud:

- patient_id → name, DOB, gender, contact and address attributes.
- doctor_id → user_id, name, specialization, license and professional contacts.
- case_id → patient_id, assigned doctor, case date, narrative and workflow.
- visit_id → case_id, attending doctor, encounter time/type/narrative.
- (case_id, symptom_id) → severity, duration, frequency, notes, recorded_at.
- (prescription_id, medicine_id) → amount, frequency, route, duration, instructions.
- visit_id → optional one-to-one vitals/examination/prescription facts.

Do not put doctor_name in cases: case_id → doctor_id → doctor_name creates a transitive dependency. Do not repeat case_id in follow_ups: follow_up_id → visit_id → case_id. Do not permanently store age or BMI. Relationship attributes such as dosage belong to the prescription/product association, not the medicine catalog. The 19 operational relations meet the documented 3NF argument; the physical monthly cache is an intentionally denormalized read model with explicit refresh semantics.

## SQL features and advanced database objects

Use `SQL_LAB_GUIDE.md` for the exact demonstration order. There are 57 DQL queries and separate safe DDL, DML, DCL and TCL examples. Point out MySQL-specific behavior: DDL implicit commits, INTERSECT/EXCEPT version floor, no native FULL OUTER JOIN, and no native materialized views.

Live views join and aggregate current data. Stored functions calculate age, BMI, visit count and doctor workload. Procedures implement registration, case closing, follow-up planning and serialized appointment scheduling. Audit/timestamp/date/role triggers protect important writes. The monthly summary is a stored physical table populated atomically by a refresh procedure; completed_cases counts cases currently closed within each case-month cohort. It is not a closure-event report.

A case submission commits its entire graph together. A failed FK/validation rolls everything back, including triggered audit rows. A SAVEPOINT can discard an optional prescription while retaining earlier writes. Appointment prevention uses a lock on the doctor row, then overlap checking and insertion inside one transaction. This covers concurrent insertion into an initially empty schedule, unlike a check performed without a shared lock.

## Security explanation

Show hashed passwords without copying complete hashes into slides. JWTs are signed, expiring, and validated against current active users. Pydantic and database constraints validate complementary rules. Role checks block reception clinical access; doctors write only assigned cases. SQL parameters and allowlisted sorting prevent user input from becoming SQL syntax. Environment secrets stay out of frontend/source. Audit context is cleared before returning pooled connections.

This is an educational security implementation: no MFA, password reset, login throttling, full token revocation or clinical compliance claims. SQL administrator credentials are used for installation/labs only, while API requests use a restricted runtime account.

## Thirty-step live demo

1. Sign in as Reception with the documented demo account.
2. Register a new patient named clearly as a fictional demo.
3. Search the patient by name/email in Patients.
4. Schedule today's appointment with Doctor 1; use a free slot such as 14:00–14:30 IST.
5. Sign out using the account control and sign in as Doctor.
6. Open the dashboard's today's schedule; the new patient is assigned through the booking.
7. Start a new case from the patient or appointment action.
8. Enter a fictional chief complaint and narrative.
9. Select two baseline symptoms and their relationship attributes.
10. Add a fictional history episode.
11. Add a fictional allergy record.
12. Enter current lifestyle fields.
13. Record sample height/weight and show calculated BMI preview without interpretation.
14. Enter fictional physical examination text.
15. Add a clearly fictional diagnosis observation.
16. Add an imaginary product with nonactionable demo text.
17. Schedule a follow-up and provide a fictional reason.
18. Save a draft, reload/resume, then submit and show SUBMITTED state.
19. Open the patient profile and its clinical tabs.
20. Open the timeline; explain encounter vs date-only event granularity.
21. Open/print the fictional prescription and point to its disclaimer.
22. Show follow-up scheduling; mark it completed in Follow-ups if demonstrating closure.
23. Return to the doctor dashboard.
24. Show counts/charts updated from MySQL; doctor metrics are scoped.
25. Open reports, change filters/sort, and export the current page.
26. In Workbench run selected Q01/Q16/Q23/Q29/Q41/Q54 examples.
27. Execute the patient → case → visit transaction in the TCL lab.
28. Show ROLLBACK removes the new graph.
29. Show ROLLBACK TO SAVEPOINT discards the optional prescription.
30. Sign in as Admin and inspect the attributed audit trail generated by application and trigger writes.

Avoid closing a seeded case with pending follow-ups during the live demo. Explain the rejection and resolve the pending plan first. Marking an appointment completed changes scheduling status; it does not manufacture a visit or diagnosis.

## Screenshots and presentation outline

Capture login with disclaimer, Admin dashboard with charts, patient registration/search, eleven-step form, draft recovery, case details, eight-tab profile, timeline, fictional prescription, overlap error, reports, audit trail and Workbench ERD/constraints/transaction outputs. Verified local screenshots are `dashboard.png`, `tablet.png`, `case-taking.png` and `login.png` when generated by browser testing. Do not include `.env` or database passwords in captures.

Suggested slides: problem/objectives; use cases/roles; architecture; ERD; relational keys/constraints; normalization; SQL coverage; advanced objects; transaction/concurrency; UI walkthrough; test evidence; limitations/future scope/team responsibilities. Keep enough time for the live record-to-MySQL demonstration.

## Viva prompts

| Question | Defensible answer |
|---|---|
| Why a junction table? | Each M:N occurrence and its relationship-specific attributes need an independently keyed relation. |
| Why no stored age/BMI? | They depend on DOB/current date or height/weight and should be derived to avoid stale duplication. |
| Why phone is not UNIQUE? | Households can share it; email is optional and SQL nullable UNIQUE is not a universal identity. |
| Why follow-up has no case_id? | visit_id already determines case_id; storing both risks inconsistent facts. |
| Why separate draft state? | Completeness and clinical workflow are different dimensions. |
| Why not cascade clinical case deletion? | Clinical parent/history must survive accidental deletion; owned optional components can cascade. |
| Can a SELECT overlap check race? | Yes. Serialize all writers through the doctor row and retain the lock through insertion. |
| Does MySQL have materialized views? | No native syntax; our physical cache plus refresh transaction is an equivalent with explicit staleness. |
| Is an audit trigger an access-control policy? | No. The API authenticates/authorizes; triggers require trusted context and record mutations. |
| Why one runtime DB account? | Connection pooling is simple; JWT roles and row ownership remain backend responsibilities. |

## Known limitations and future scope

The project assumes one clinic and one role per account. Appointment slots are a list view with date filters, not a drag-and-drop calendar; there is no timezone selection or multi-clinic scheduling. Current lifestyle is a snapshot; history/allergies are shared patient records and do not have version history. Subsequent symptom changes use encounter narrative rather than a second versioned symptom relation. Clinical documents have limited editing/versioning, and cancelled/closed history is intentionally retained. Clinical profile tabs paginate cases and related records; a single expanded case currently includes all of its encounters. Report CSV exports only the visible page. The monthly summary needs explicit refresh. Installation is not a schema upgrade manager. Automated tests cover the documented educational flows, not performance/load, accessibility certification or production security.

Future extensions may include a mobile app; email/SMS appointment/follow-up reminders; richer analytics; document uploads and medical report attachments; carefully governed AI-assisted summarization; telemedicine; multi-clinic support; versioned clinical amendments; MFA/rate limiting; backup/restore tooling and more extensive accessibility/load testing. These are proposed extensions, not delivered features. Any real clinical use would need a separate regulated, privacy-preserving design and review.
