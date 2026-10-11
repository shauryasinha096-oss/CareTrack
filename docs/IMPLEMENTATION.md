# Implementation and API guide

CareTrack is an educational demonstration project using fictional data. It is not intended for real clinical use.

## Structure and request flow

The frontend lives in `frontend/src`: `pages` implement screens, `components` share forms/dialogs/tables, `services/api.ts` sends authenticated HTTP requests, `services/auth.tsx` restores the session, `hooks/useApi.ts` handles cancellation/loading/retry, `types` defines shared domain interfaces, and `layouts/Workspace.tsx` implements navigation. Tailwind and a custom responsive CSS theme style the app; Lucide icons and Recharts provide the requested interface elements.

The backend lives in `backend/app`: explicit SQLAlchemy `models` match the SQL schema; Pydantic `schemas` validate boundary data; `routes` expose HTTP resources; `services/records.py` enforces ownership and atomic writes; `services/analytics.py` executes bound reporting queries; `utils/security.py` hashes passwords and validates JWTs; `database/connection.py` owns request transactions and resets pooled audit context.

React fetches `/api/...` through Vite's local proxy. FastAPI authenticates the bearer token, reloads the active user and role from MySQL, sets connection audit context, validates input, executes SQLAlchemy or parameterized SQL, and commits once after successful request completion. Exceptions roll back. The backend has no alternative database provider. `/api/health` executes `SELECT 1`, so a running HTTP process alone cannot fake database health.

## Routes

The interactive OpenAPI reference at `http://127.0.0.1:8000/docs` is the precise schema reference. These are the core route families:

| Route | Operations and authorization |
|---|---|
| `/api/auth/login`, `/api/auth/me` | Login, current active account |
| `/api/patients` | All roles: scoped listing, registration; PUT updates with doctor ownership checks; admin DELETE unused records |
| `/api/patients/{id}/history`, `/timeline` | Admin or doctor assigned to patient; paged clinical history/timeline |
| `/api/cases` | Admin/doctor; atomic initial case bundle creation |
| `/api/cases/{id}/bundle` | Edit DRAFT bundle, or submit it atomically |
| `/api/cases/{id}` | Read patient history; assigned doctor/admin workflow edits; admin delete unused draft |
| `/api/visits`, `/api/visits/{id}` | Create subsequent encounter / inspect nested sections |
| `/api/visits/{id}/vitals`, `/examination` | Assigned doctor/admin PUT section, calculate BMI when reading |
| `/api/appointments` | All roles create/update/cancel with doctor scope and overlap locking |
| `/api/diagnoses`, `/api/prescriptions` | Clinical creation and retrieval; reception forbidden |
| `/api/followups` | Reception listing omits clinical reasons/instructions; clinical create/update |
| `/api/symptoms`, `/api/medicines` | Clinical reads; admin catalog creation/editing/deactivation |
| `/api/doctors`, `/api/users` | Admin provisions doctor account/profile atomically; admin manages account activation |
| `/api/audit-logs` | Admin listing/search |
| `/api/dashboard/statistics` | Role-scoped MySQL metrics/charts and three live SQL views |
| `/api/reports/{name}` | Ten parameterized reports with label/date/doctor filters, sorting, pagination |
| `/api/reports/monthly-cache/refresh` | Admin explicitly refreshes precomputed cohort statistics |

Listings accept `q`, `page`, `page_size` (maximum 100), `sort` and `direction`; relevant resources accept patient/doctor/status/date filters. Sorting identifiers are allowlisted; values are bound parameters. Exact methods, DTO defaults and response fields are visible in OpenAPI.

## Transactions and ownership

Case submission writes the case, initial visit, baseline symptom associations, history/allergies, current lifestyle snapshot, vitals, examination, diagnoses, prescription lines and follow-up in one request transaction. Validation/FK failure rolls back the complete request, including audit triggers. Drafts use the same storage model and return IDs for idempotent history/allergy edits. Incomplete repeating rows are omitted on draft save; the interface asks the learner to finish them before submission. Unsaved incomplete text is not recoverable after reload. Removing an existing patient history/allergy row from a case form does not delete that shared patient record; dedicated API routes add patient-level records. Historical deletion/edit versioning is future scope.

`record_state` DRAFT/SUBMITTED is separate from case workflow OPEN/UNDER_REVIEW/FOLLOW_UP/CLOSED. A submitted case requires a complaint and initial encounter. Closed cases cannot receive clinical writes; pending follow-ups must be resolved before closing. The case's current assignee, each visit's attending doctor and a prescription's author represent separate facts.

Appointment writes first lock the doctor row(s), in sorted order when changing doctors, then lock/re-read the appointment and run a current overlap query in READ COMMITTED isolation. Noncancelled intervals overlap exactly when `existing.start < new.end AND existing.end > new.start`. Adjacent intervals are permitted. This protects even an empty day's schedule. Direct SQL writers must use `schedule_appointment()` within an explicit transaction or follow the same locking protocol; the schema alone cannot enforce interval exclusion.

Clinical child rows are retained with RESTRICT parent references. Component records cascade only when their owning unused object is legitimately deleted. Audit rows retain an actor-name snapshot even if an account FK becomes NULL. MySQL cascaded child deletes do not fire child delete triggers; parent operation auditing supplies context.

## Authentication and data handling

Argon2id hashes passwords. JWTs are signed with a generated secret and include issuer, subject, issue and expiry times. Role/active state is re-read on every request so disabling an account takes effect immediately. Tokens are held in tab sessionStorage and cleared on sign-out/expiry. This simple educational implementation has no refresh tokens, password recovery, MFA, revocation list, or login rate limiter.

Reception cannot access clinical routes. Its appointment and follow-up responses redact clinical notes, reasons and instructions. Doctors list assigned patients and their own case workload; they can read prior cases for an assigned patient, but writes remain tied to current case assignment. Catalog/account mutation and audit listing require Admin. A single pooled MySQL runtime account is used; MySQL role examples demonstrate SQL privilege control separately from application row authorization.

The API validates formats, lengths, enums, dates and positive measurements, while MySQL adds uniqueness, checks, FK integrity and cross-table/date triggers. Measurement checks are educational data integrity limits, not medical interpretation. SQL injection is prevented with parameter binding and sort allowlists. Database error responses hide connection credentials and raw SQL. CORS is restricted to configured local origins.

Timestamps are stored in UTC. Dates and appointment wall-clock times use Asia/Kolkata. Case date is the administrative case date; initial encounter time is the actual submission/draft creation time. Timeline items derived from date-only fields cannot claim exact event timestamps; diagnoses use their encounter's timestamp because the table has no separate created_at.

## Advanced objects used in the app

The dashboard reads `patient_case_summary` and `upcoming_followups`; reporting also exposes `doctor_case_statistics`. The fourth view, `receptionist_patients`, is a restricted SQL lab view. Patient age, visit count, doctor case count and BMI use stored functions. Closing a case and creating a follow-up use stored procedures. Patient/case triggers create audit entries and enforce actor/date/state rules. Other API mutations write service audit events in the same transaction.

`monthly_case_statistics` is a reporting cache, intentionally excluded from the operational 3NF claim. Refresh obtains a MySQL advisory lock, replaces rows inside a transaction, and commits only the completed snapshot. It runs on a separate connection because the refresh procedure owns its transaction. It stores totals and unique patients by submitted case month; completed_cases means **currently closed cases in that cohort**, not closure events in that month. Refresh is explicit rather than scheduled, so values may be stale until refreshed.
