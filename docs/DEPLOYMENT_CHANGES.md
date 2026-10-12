# Deployment update: changed files

All paths below are relative to the CareTrack repository root. Replace existing files at these paths and add the new files. The deployment update ZIP contains exactly these files, without an enclosing directory. Extract it first and upload its contents while preserving folder structure. Do not upload the ZIP itself as application source.

The active project is the outer `caretrack` directory. An older nested `caretrack/caretrack` archive copy was left unchanged; do not deploy that copy.

Changes: shared verified TLS connections; configured schema initialization with no managed-user provisioning; serialized, non-destructive tables/routines/triggers/views installation and transactional fictional demo seeding; Vercel CORS and API URL; production login password entry; Vercel SPA routing; Render Free Blueprint and detailed setup.

Validation on 12 October 2026: 20 backend tests, 2 separately run TLS MySQL initialization tests with schema-only users, 4 browser checks, strict TypeScript/Vite builds, 119 SQL lab statements, and a clean SQL schema/seed restore passed. Two database initialization tests are skipped in the default suite because each requires its own disposable empty schema. The production browser check stubs the configured API response. Actual Aiven/Render deployment was not tested because no hostname, service credentials or CA certificate was supplied. See TESTING.md for details and the managed binary-log policy prerequisite.

## Files

- `.env.example`
- `.gitignore`
- `README.md`
- `render.yaml`
- `backend/app/config.py`
- `backend/app/database/connection.py`
- `backend/app/database/settings.py`
- `backend/seed.py`
- `backend/tests/test_integration.py`
- `backend/tests/test_deployment.py`
- `backend/tests/test_initialization_mysql.py`
- `database/02_schema.sql`
- `database/03_seed_data.sql`
- `database/09_views.sql`
- `database/10_functions.sql`
- `database/11_procedures.sql`
- `database/12_triggers.sql`
- `database/13_materialized_view_equivalent.sql`
- `database/schema.sql`
- `frontend/.env.example`
- `frontend/vercel.json`
- `frontend/src/vite-env.d.ts`
- `frontend/src/services/api.ts`
- `frontend/src/pages/Login.tsx`
- `frontend/tests/deployment.spec.ts`
- `scripts/database.py`
- `scripts/provision_database.py`
- `scripts/generate_schema.py`
- `scripts/generate_triggers.py`
- `scripts/verify_sql.py`
- `docs/DEPLOYMENT.md`
- `docs/TESTING.md`
- `docs/DEPLOYMENT_CHANGES.md`
