# CareTrack

**CareTrack — Digital Patient Case Taking & Clinical Record Management System**

CareTrack is an educational demonstration project using fictional data. It is not intended for real clinical use.

The complete local application uses React, TypeScript, Vite, Tailwind CSS, Lucide and Recharts → FastAPI, Pydantic and SQLAlchemy → PyMySQL → **MySQL**. MySQL is the source of truth. There is no SQLite or hardcoded frontend record fallback.

## Open this installation

The database and dependencies have been installed in this checkout. Its ignored `.env` contains generated local credentials; do not share it. The isolated MySQL 8.4 instance uses port **3307**, leaving any existing MySQL service untouched.

Start all installed local services with one command:

```bash
cd '/Users/shauryasinha/Documents/New project/caretrack'
python3 scripts/run_local.py
```

The launcher reuses listening services and stops only its own processes on Ctrl+C. Alternatively, start MySQL, API and frontend in separate terminals:

```bash
cd '/Users/shauryasinha/Documents/New project/caretrack'
bash scripts/start_local_mysql.sh
```

```bash
cd '/Users/shauryasinha/Documents/New project/caretrack'
bash scripts/start_backend.sh
```

```bash
cd '/Users/shauryasinha/Documents/New project/caretrack'
bash scripts/start_frontend.sh
```

Open [CareTrack](http://127.0.0.1:5173) and [API documentation](http://127.0.0.1:8000/docs). Stop foreground servers with Ctrl+C. If a port is occupied, check whether the corresponding server is already running before starting another instance.

A portable source copy is included in `CareTrack-source.zip`. It excludes `.env`, the local MySQL data/runtime, installed dependencies and build output; follow the fresh installation steps after extracting it.

## Demo logins

All use password **`CareTrackDemo2026!`**. Passwords in MySQL and the SQL seed are Argon2id hashes.

| Role | Email | Main scope |
|---|---|---|
| Admin | admin@caretrack.example.com | All records, users, doctors, catalogs, audits, reports |
| Doctor | doctor1@caretrack.example.com | Assigned patient history; own case writes and encounters |
| Receptionist | reception@caretrack.example.com | Demographics, appointments, basic follow-up scheduling information |

There are 20 doctor accounts (`doctor1` through `doctor20`). Registration creates patients, not public login accounts. Admins provision login accounts. Demo passwords are public solely for this fictional local project.

## Install on another computer

Prerequisites: Python 3.11+, Node.js 22+, MySQL **8.0.31+** (8.4 LTS recommended), and optionally MySQL Workbench. Use an empty `caretrack` database for initial installation.

```bash
cd caretrack
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
cp .env.example .env
```

Edit `.env`: set the MySQL administrator URL, a random runtime password in `DATABASE_URL`, and a random JWT secret of at least 32 characters. URL-encode special characters in passwords. Match your MySQL port; a normal installation usually uses 3306. The administrator connection targets the existing system database `mysql` so it can create `caretrack`.

```bash
backend/.venv/bin/python scripts/provision_database.py
backend/.venv/bin/python scripts/database.py init --local-admin
cd frontend
npm install
npm run build
npm run dev
```

Start the backend in another terminal with `bash scripts/start_backend.sh` from the project root. On Windows, use `backend\.venv\Scripts\python.exe` and run `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000` from `backend`.

Provisioning creates the `caretrack_app` loopback login without embedding passwords in SQL. Local provisioning grants per-table runtime privileges with no DDL and no audit modification/deletion. Hosted initialization never provisions users or changes grants. An existing login is preserved; if you change its password, also change it in MySQL. Migration preserves existing table/routine/trigger definitions: it is an **initial installer**, not a versioned upgrade engine. Later schema changes need explicit ALTER migrations.

Seeding preserves any existing source dataset and adds only missing fictional login accounts. The full fixture is inserted only when every source table is empty. It creates 150 patients, 20 doctors, 250 cases, 400 visits, 750 symptom associations, 300 diagnosis observations, 200 prescriptions, 600 product lines, 300 appointments, 150 follow-ups, 200 histories, 100 allergies, and at least 650 audit events. Dates are distributed across months, with appointments relative to the day of Python seeding. Browser tests add clearly labelled fictional demonstration records.

Alternatively, after migration execute `database/03_seed_data.sql` in Workbench on an **empty** schema. Choose either Python seeding or SQL seeding, never both. The exported SQL snapshot uses fixed dates and precomputed Argon2id demo hashes.

## Cloud deployment

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for Vercel, Render Free, and Aiven MySQL (`defaultdb`, verified TLS), exact commands, environment variables and safe repeatable initialization. Deploy from the CareTrack repository root.

## Features

- Role-aware dashboards with six clinical metrics, six charts, recent activity, and scheduling information. Reception receives a reduced operational dashboard.
- Patient registration, editing, server search, filtering, sorting, pagination, and protected deletion of unused patients.
- Eleven-step case taking with database drafts, reload recovery, optional structured sections, validation, and atomic submission.
- Patient profiles with eight tabs, case and visit history, prescriptions, follow-ups and a database-derived timeline.
- Subsequent visits, encounter vital signs and examination editing, diagnosis observations, fictional prescription documents and follow-up resolution.
- Appointment creation/editing/cancellation/completion/no-show status; serialized overlap prevention under concurrent requests.
- Doctor/account management, symptom and fictional medicine catalogs, attributed audit trail, ten reports, current-page CSV exports, and explicit monthly summary refresh.
- Parameterized queries, strict input schemas, JWT authentication, active-account checks, Argon2id hashing, role and ownership authorization, friendly database errors, loading and empty states.

## Database coursework

`database/` contains thirteen numbered SQL files: schema, fictional seed, DDL/DML/DCL/TCL labs, **57 DQL queries**, four views, four stored functions, business procedures, meaningful audit/validation/timestamp triggers, and a physical summary-table refresh procedure.

MySQL has no native materialized view or FULL OUTER JOIN. This project uses a physical `monthly_case_statistics` cache and serialized refresh procedure, and a LEFT/RIGHT JOIN UNION equivalent. Native INTERSECT and EXCEPT require MySQL 8.0.31+; portable EXISTS alternatives are included.

The operational model has 19 normalized tables with 21 foreign keys, plus one reporting cache. Age and BMI are calculated rather than stored. Follow-ups derive their case through the visit. `case_symptoms` and `prescription_medicines` demonstrate composite keys and M:N relationships. See the design documents for FDs, participation, subtype decisions, indexes, and deletion policies.

| Resource | Purpose |
|---|---|
| [Architecture](docs/PHASE_1_DATABASE_DESIGN.md) | Project statement, entities, relationships, assumptions |
| [Relational schema](docs/RELATIONAL_SCHEMA.md) | All attributes, types, keys and constraints |
| [Normalization](docs/NORMALIZATION.md) | UNF → 1NF → 2NF → 3NF and functional dependencies |
| [ER diagram](docs/ER_DIAGRAM.md) | Mermaid rendering and import instructions |
| [Implementation](docs/IMPLEMENTATION.md) | Backend/frontend structure, APIs, transactions, security |
| [SQL lab](docs/SQL_LAB_GUIDE.md) | Workbench order and SQL concept mapping |
| [Testing](docs/TESTING.md) | Reproducible checks and actual results |
| [Presentation guide](docs/PROJECT_PRESENTATION_GUIDE.md) | Three-person team demo, viva, limitations and future scope |

## Tests

With MySQL seeded and configured:

```bash
cd backend
.venv/bin/python -m pytest -q
cd ..
backend/.venv/bin/python scripts/verify_sql.py
cd frontend
npm run build
```

With both HTTP servers running, `npm run test:e2e` launches browser workflow tests. Set `CHROME_PATH` to your Chrome/Chromium executable (the default is macOS Chrome). SQL verification requires administrator credentials and creates only labelled lab objects/roles; it commits one labelled audit event to demonstrate COMMIT. Most API tests roll back their records. Browser tests deliberately persist fictional cases so the submission can be inspected in MySQL.

This is a local college project. Production clinical deployment, real patient data, regulatory compliance, external notifications and medical recommendations are outside its scope. Detailed practical limitations and future improvements are documented in the presentation guide.
