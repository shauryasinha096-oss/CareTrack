# Verification record

Executed locally on 11 October 2026 against Oracle MySQL **8.4.11**, Python 3.12.14, FastAPI 0.115.12, SQLAlchemy 2.0.40, Vite 6.4.4, React 18, and headless installed Google Chrome through Playwright. Only fictional records were used.

## Results

| Check | Actual result |
|---|---|
| Backend integration suite | **8 passed** in the final complete run; one upstream Starlette/AnyIO deprecation warning |
| Browser screen/case workflow tests | **3 passed** together in the final run after correcting a test search fixture |
| TypeScript strict build | Passed |
| Vite production build | Passed; separate app, React and chart bundles, no bundle-size warning |
| SQL labs 04–08 | 119 statements executed successfully, including USE/context and transaction statements; 57 application DQL queries |
| Clean-schema SQL seed restore | Passed; all required minima and 12 monthly cache rows verified, temporary verification database removed |
| Single-command launcher | API and frontend started successfully; MySQL-backed health check returned 200 |
| Installer rerun | Passed without dropping operational tables or clearing records |
| HTTP/database readiness | `/api/health` returned 200 after querying MySQL; Vite root returned 200 |
| Visual QA | Desktop dashboard with actual charts, login, case form and tablet layout captured and inspected |

The SQL lab statement total is 9 + 17 + 16 + 19 + 58 = 119; Q01–Q57 are the 57 SELECT queries in the DQL file. A test fixture initially used the wrong seeded email, and duplicate text required a more precise UI assertion; both were corrected. Early SQL lab errors exposed required audit-context/action/actor fields and were corrected before the successful full run. The final constraint test rejects specific integrity errors and does not accept a lock timeout as proof of a constraint.

## Reproduce

```bash
# From caretrack/backend, with seeded MySQL and the root .env configured:
.venv/bin/python -m pytest -q

# From caretrack:
backend/.venv/bin/python scripts/verify_sql.py --seed-import

# From caretrack/frontend:
npm run build

# With API and Vite running:
npm run test:e2e
```

Set CHROME_PATH to your local Chrome/Chromium executable if it differs from the macOS default. The SQL lab verifier uses the administrator URL because it must create routines, lab tables, SQL roles and a disposable seed-verification database. Application traffic uses the restricted runtime URL. Under desktop sandboxing, starting loopback servers/Chrome or connecting to MySQL may require native host permissions.

## Executed checklist

- [x] Login success/failure, missing JWT rejection, role access and reception clinical rejection.
- [x] Reception appointment/follow-up responses omit clinical notes/reasons/instructions.
- [x] Patient create/read/update/delete, invalid email, empty required name, future DOB and duplicate email.
- [x] Shared household phone accepted; scoped search, sorting and page separation.
- [x] Draft save, returned history/allergy IDs, repeated save without duplication, reload recovery and atomic submission.
- [x] Symptoms, lifestyle, history, allergies, vitals/BMI, examination, fictional diagnosis and product association persistence.
- [x] Prescription retrieval, patient history and database timeline.
- [x] Subsequent encounter creation; vital/examination editing and reception denial.
- [x] Pending follow-up blocks closure; completion enables closing the case.
- [x] Invalid symptom FK rolls back the complete case request.
- [x] Appointment overlap rejected; adjacent intervals accepted; cancellation releases a slot.
- [x] Concurrent initially empty schedule: exactly one of two competing bookings commits.
- [x] Browser appointment creation, overlap error, edit to Confirmed and cancellation retention.
- [x] All ten report families plus live views/cache endpoints return database results.
- [x] Four stored functions, business procedures, audit attribution, trigger metadata and 21 FK definitions.
- [x] Direct SQL future DOB, invalid FK/role/measurement and duplicate license constraints.
- [x] DDL lab isolation, DML cascading/RESTRICT, DCL GRANT/REVOKE, TCL rollback/savepoint/commit.
- [x] Atomic doctor/profile provisioning: duplicate license rolls back the new login account.
- [x] Account disabling rejects an already-issued JWT and future login immediately.
- [x] Admin page navigation with no browser JavaScript errors, record pagination and tablet rendering.

## Isolation and persisted test records

Most API tests use an outer MySQL transaction and SAVEPOINT-based request sessions, then roll back. The concurrency test commits one booking to test real locks and removes that booking afterward; its audit event remains. Browser tests intentionally commit clearly named `BrowserDemo` patients and associated fictional cases, so those records remain inspectable. The seed baseline is 150 patients/250 cases/400 visits; live totals can therefore be higher after browser tests. SQL lab verification commits a labelled audit event, while patient/case/visit lab records roll back.

The clean seed restore creates `caretrack_seed_verification` only if absent, installs the real schema/routines/triggers, imports `03_seed_data.sql`, checks row minima, and removes that test database on success. If an import fails, the test database is retained for inspection and a subsequent attempt refuses to overwrite it.

## Verification limits

These checks cover educational functional behavior and a concrete concurrency race. They do not establish load capacity, regulatory suitability, exhaustive security, cross-browser compatibility or accessibility certification. No hosted deployment, external messaging, real patient data or medical advice is involved. No pytest failures remain; the single deprecation warning originates in Starlette's TestClient, not CareTrack logic.


## Deployment update — 12 October 2026

- **20 backend tests passed**: the original 8 API integration tests and 12 deployment tests covering TLS verification, a server refusing TLS before authentication, invalid CA files, remote plaintext rejection, special-character passwords, CORS, schema-independent SQL, and advisory-lock cleanup. One existing Starlette/AnyIO deprecation warning remains.
- **2 additional MySQL initialization tests passed** independently against new disposable schemas on an isolated MySQL 8.4.11 instance with verified TLS and schema-only service users. One starts empty and proves full fixture initialization plus an unchanged repeat run; the other starts with an existing user at ID 901 and proves missing accounts are added without importing fixed IDs or replacing existing data. Changed passwords and disabled accounts survive reruns. No SUPER/global privileges were granted to these initializer users. The isolated server used `--skip-log-bin`; the initial test against a server with binary logging and its default creator policy correctly failed with the documented provider-policy message. No operational server global settings were changed.
- **4 browser tests passed**: the 3 existing local workflows and a separate production preview test proving configured cross-origin API routing, browser deep-link fallback, and no production password autofill. The production browser test stubs the configured backend response; it does not claim to test a live Render service.
- Strict TypeScript and Vite production build passed, including a build with a configured backend URL.
- All **119 local SQL lab statements** passed again, and the schema-independent SQL schema/seed restored successfully into a fresh verification database; that temporary database was removed.
- Aiven and Render were not contacted: service hostname, credentials, and CA certificate were not supplied. End-to-end hosted TLS, service permissions, and platform deployment remain to be checked after private dashboard configuration.

The two initialization tests are intentionally skipped in the ordinary suite. They require `CARETRACK_INIT_TEST=1`, a newly provisioned empty schema whose name starts with `caretrack_deploy_test_`, and a user with the documented schema-only privileges. Run each test in a separately provisioned schema. Never point them at Aiven's operational `defaultdb` or your existing local data.

For the production browser test, build the frontend with `VITE_API_URL=https://caretrack-test-api.example.com/api`, start a Vite production preview, then run:

```bash
CARETRACK_PRODUCTION_PREVIEW=http://127.0.0.1:5174 npm run test:e2e -- tests/deployment.spec.ts
```

Without `CARETRACK_PRODUCTION_PREVIEW`, the production-only browser check is skipped. Restore a normal build with your real configured API URL before publishing artifacts; Vercel always builds from source.
