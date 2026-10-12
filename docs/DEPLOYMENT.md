# Deploy CareTrack: Vercel + Render Free + Aiven MySQL

The repository root must contain `backend/`, `frontend/`, `scripts/`, `database/`, and `render.yaml`. Deploy this directory, not a surrounding directory or a nested archive copy. No deployment or database credentials belong in Git.

## 1. Aiven connection and certificate

Use the existing Aiven database **defaultdb**, port **11641**, username **avnadmin**, and the exact service hostname from Aiven. Download the service's CA certificate. Store it locally outside Git or as a Render secret file. Do not use the service's IP address: TLS verifies the hostname as well as the certificate chain.

Set these variables in Render's Environment settings:

| Variable | Value |
| --- | --- |
| `DB_HOST` | Exact hostname from Aiven, without a protocol or port |
| `DB_PORT` | `11641` |
| `DB_NAME` | `defaultdb` |
| `DB_USER` | `avnadmin` |
| `DB_PASSWORD` | Your Aiven password; paste privately into Render |
| `DATABASE_SSL` | `true` |
| `DATABASE_SSL_CA` | `/etc/secrets/aiven-ca.pem` |
| `JWT_SECRET` | A unique random secret of at least 32 characters |
| `JWT_EXPIRE_MINUTES` | `480` |
| `DEMO_PASSWORD` | Your chosen fictional demo account password, at least 12 characters |
| `CORS_ORIGINS` | `["https://care-track-jet.vercel.app","http://localhost:5173","http://127.0.0.1:5173"]` |
| `PYTHON_VERSION` | `3.12.12` |

In Render, add a **secret file** named `aiven-ca.pem`, containing the downloaded PEM certificate. It is mounted at `/etc/secrets/aiven-ca.pem`. The PEM is not a database password, but keep deployment files out of the repository. Generate a JWT secret locally with `python3 -c 'import secrets; print(secrets.token_urlsafe(48))'`; paste the result into Render, never Git.

The `DB_*` variables take precedence over `DATABASE_URL`, so passwords with `@`, `:`, `/`, `%`, or spaces work without URL encoding. Alternatively set only `DATABASE_URL=mysql+pymysql://avnadmin:URL_ENCODED_PASSWORD@YOUR_AIVEN_HOST:11641/defaultdb`, along with TLS settings. Do not add SSL options in the URL query. Do not set `MYSQL_ADMIN_URL` on Render.

Both SQLAlchemy and direct PyMySQL scripts share the same verified SSL context. TLS 1.2 or newer, certificate validation and hostname validation are enabled. Remote plaintext is rejected, and a connection that does not negotiate TLS is refused. Missing/invalid CA files fail rather than disabling verification. The API uses a small recycled connection pool for a demo database.

## 2. Safe initialization

From the repository root, with the above environment variables set:

```bash
python -m pip install -r backend/requirements.txt
python scripts/database.py init
```

For an existing local virtual environment use `backend/.venv/bin/python scripts/database.py init` instead. To initialize Aiven from your Mac, set the Aiven values in an ignored root `.env` (or environment) and set `DATABASE_SSL_CA` to the absolute path of the downloaded CA file. Preserve your local configuration separately; never upload either file. Structured `DB_*` values override a local `DATABASE_URL`. Schema-only migration needs no JWT secret; full initialization and the web service require one.

`init` selects the database from the connection settings. It creates missing tables, functions, procedures, triggers and views in dependency order, then adds fictional demo data. A database-scoped advisory lock serializes concurrent initialization, including the seed transaction. It never creates a database or MySQL login, reads `mysql.user`, issues GRANT/REVOKE, sets global server variables, assigns another account as DEFINER, drops objects, replaces an existing view, or resets existing passwords.

On a completely empty source dataset, it creates the full fictional teaching graph: 150 patients, 20 doctors, 250 cases, 400 visits, and associated clinical and scheduling records. On a populated or partially populated database, it leaves the dataset alone and adds only missing demo login accounts and their doctor profiles using natural keys and generated IDs. Existing accounts, roles, passwords and disabled state are preserved. An identity collision fails safely and rolls back that seed transaction; it never claims an unrelated account. All account/graph inserts are transactional. MySQL DDL commits individually, so a failed migration can leave some newly created objects; resolve the reported issue and rerun safely.

Existing object definitions are preserved, not automatically upgraded. This command is an initial installer, not an ALTER migration system. Versioned schema changes need deliberate migrations. The summary cache is populated after a fresh full seed; reruns preserve existing data/cache. If a fresh seed committed but its cache refresh was interrupted, run `CALL refresh_monthly_case_statistics();` outside a transaction to rebuild this derived cache.

Accounts are `admin@caretrack.example.com`, `reception@caretrack.example.com`, and `doctor1@caretrack.example.com` through `doctor20@caretrack.example.com`. Newly created accounts use `DEMO_PASSWORD`; all stored passwords are Argon2id hashes. Changing that environment variable later does **not** reset existing account passwords.

Schema permissions needed: SELECT, INSERT, UPDATE, DELETE, CREATE, INDEX, REFERENCES, CREATE VIEW, SHOW VIEW, CREATE ROUTINE, EXECUTE and TRIGGER on the target database. No SUPER, CREATE USER, role administration, global grants or access to the mysql system schema is needed. Aiven's default `avnadmin` is the intended service user. If MySQL reports error 1419/1227 for stored objects, the provider must permit routine/trigger creation under its binary-log policy (`log_bin_trust_function_creators`); the installer reports this explicitly and never tries `SET GLOBAL` or silently omits triggers. Do not mislabel nondeterministic functions as deterministic to bypass policy.

Do not run `scripts/provision_database.py`, `scripts/setup_local_env.py`, `scripts/verify_sql.py`, or SQL labs 01/04–08 on Aiven. Those are deliberately local administrator exercises. Do not import `03_seed_data.sql` into a populated database: it is an optional fixed-ID snapshot for an empty selected schema. Use `database.py init` for deployment.

## 3. Render Free backend

Create a **Web Service**, connect the GitHub repository, choose **Python 3** and **Free**, and leave **Root Directory empty**. The repository root must be the CareTrack directory containing `backend/` and `scripts/`.

**Build command:**

```bash
pip install -r backend/requirements.txt
```

**Start command (safe initialization at each start):**

```bash
python scripts/database.py init && python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT
```

**Health check path:** `/api/health`

Alternatively initialize Aiven once from your Mac, then use this shorter start command:

```bash
python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT
```

`render.yaml` supplies the same settings as a Blueprint, with password/hostname prompts and a generated JWT secret. Add the CA secret file yourself. The service may initially fail until the environment and certificate are configured; redeploy after configuring them. Do not set Root Directory to `backend`: initialization needs sibling `scripts/` and `database/`.

Render Free has no shell or one-off jobs and no pre-deploy initialization is needed. Startup initialization is repeatable, or you can run it locally against Aiven. Free instances sleep after inactivity; the first request may take about a minute. No keep-alive workaround is required. Persistent data lives in Aiven, not Render's ephemeral disk.

Verify `https://YOUR-RENDER-SERVICE.onrender.com/api/health` returns `status: ok`, and `/docs` opens. No database URL, secret or password is returned by health/error endpoints.

## 4. Vercel React frontend

Import the same GitHub repository. Set:

| Setting | Value |
| --- | --- |
| Root Directory | `frontend` |
| Framework | Vite |
| Build command | `npm run build` |
| Output directory | `dist` |
| Environment variable | `VITE_API_URL=https://YOUR-RENDER-SERVICE.onrender.com/api` |

Use your actual Render URL, **including `/api`**. Set the variable for Production (and Preview only if deliberately used), then redeploy: Vite embeds the public API URL at build time. `frontend/vercel.json` rewrites browser routes such as `/patients/1` to the React entry point so refresh/deep links work. Requests go directly to the configured Render API URL. Production role buttons fill the email only; type the configured demo password yourself. Local development retains the original demo password autofill.

Only `VITE_API_URL` goes into Vercel. All `VITE_` variables are public browser code: never put Aiven credentials, JWT secrets or `DEMO_PASSWORD` there. The backend CORS allowlist includes exactly `https://care-track-jet.vercel.app` and the two local origins. Preview/custom domains require explicitly adding their exact origin to Render's `CORS_ORIGINS`; do not use a blanket wildcard.

## 5. Local development remains available

Keep the existing local root `.env`. With no `VITE_API_URL` set, frontend calls use `/api`, proxied by Vite to `http://127.0.0.1:8000`. Do not copy the hosted example URL into an active frontend `.env` for local development. Local loopback MySQL can use `DATABASE_SSL=false`; remote databases require TLS.

Existing seeded local databases need no changes. For a new local installation, provisioning is an explicit local-only step; use `scripts/provision_database.py` followed by `python scripts/database.py init --local-admin`. Only that opt-in flag uses the local administrator URL for DDL; the seed uses the runtime connection. The API can continue using its existing restricted local login.

## 6. Publish and verify

Upload the changed source files, `render.yaml`, `frontend/vercel.json`, environment **examples**, and deployment documentation to GitHub while preserving their paths. Do not upload `.env`, `.runtime`, `.venv`, `node_modules`, certificates, private keys, or local bundles. Vercel/Render receive credentials through their dashboards only.

After deployment, open `https://care-track-jet.vercel.app`, log in with the configured demo password, check patients/reports, create a clearly fictional test patient, and refresh a nested page. Check browser Network requests target the Render `/api` URL and CORS preflights succeed. Refresh Render `/api/health` after any initial cold start.

CareTrack uses fictional data and is not intended for real clinical use.

References: [Render FastAPI deployment](https://render.com/docs/deploy-fastapi), [Render Free limitations](https://render.com/docs/free), [Vercel Vite configuration](https://vercel.com/docs/frameworks/frontend/vite), [Aiven TLS certificates](https://aiven.io/docs/platform/concepts/tls-ssl-certificates), [Aiven MySQL service users](https://aiven.io/docs/products/mysql/howto/manage-service-users), [PyMySQL TLS options](https://pymysql.readthedocs.io/en/latest/modules/connections.html), [MySQL stored-program binary logging](https://dev.mysql.com/doc/refman/8.4/en/stored-programs-logging.html).
