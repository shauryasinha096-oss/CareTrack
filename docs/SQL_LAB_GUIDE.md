# MySQL Workbench laboratory guide

CareTrack is an educational demonstration project using fictional data. It is not intended for real clinical use.

## Connect and inspect

Create a Workbench **Standard TCP/IP** connection to `127.0.0.1`, port `3307` for this isolated installation (or your configured port). Use the administrator username/password from your local `.env`, entered privately in Workbench. Never paste credentials into a submitted screenshot. The application runtime account intentionally cannot create tables/routines or modify audit rows.

Refresh Schemas, select `caretrack`, and inspect Tables, Views, Stored Procedures and Functions. Reverse Engineer the live schema to generate the MySQL Workbench EER model. Alternatively use File → Import → Reverse Engineer MySQL Create Script with `02_schema.sql`. Mermaid, draw.io and DBML exports are under `docs/diagrams`. The living SQL schema is authoritative for implemented constraints; the Phase 1 documents explain the design.

## Installation order

`scripts/database.py migrate` uses this dependency order:

1. `01_create_database.sql` — database and character set.
2. `02_schema.sql` — 20 InnoDB tables, indexes, keys, enum checks, referential actions.
3. `10_functions.sql` — four functions used by queries and API reads.
4. `11_procedures.sql` — composable patient, case, follow-up and appointment procedures.
5. `12_triggers.sql` — audit context, patient/case audits, timestamp/date/role guards.
6. `09_views.sql` — live summaries and restricted demographic projection.
7. `13_materialized_view_equivalent.sql` — serialized physical summary refresh.
8. Either Python seed or `03_seed_data.sql` on an empty schema, with triggers installed.

`database/schema.sql` is a consolidated fresh-schema installer containing the same objects in dependency order, without seed data or login provisioning.

Do not blindly execute files 01–13 in numeric order: the seed depends on installed advanced objects. Direct reruns of plain CREATE statements are not upgrade migrations. The Python installer checks object existence first.

## Safe demonstration order

Run 04–08 individually. `scripts/verify_sql.py` runs them all, consumes every result set, asserts rollback/cascade/restrict outcomes, and checks seed minima.

| File | What to explain | Persistence |
|---|---|---|
| 04 DDL | CREATE DATABASE/TABLE, ALTER column, RENAME, TRUNCATE, DROP | Only `caretrack_lab` and its temporary demonstration table; MySQL DDL implicitly commits |
| 05 DML | INSERT, scalar/multiple-row/join UPDATE, DELETE, child cascade, protected clinical parent | Operational changes rolled back; routine created before transaction and removed after it |
| 06 DCL | CREATE ROLE, GRANT and REVOKE | Three clearly named educational roles remain; no password or login is created |
| 07 TCL | START TRANSACTION, procedure, case/visit, SAVEPOINT, ROLLBACK TO, RELEASE, ROLLBACK, COMMIT | Patient/case/visit rolled back; one labelled audit event commits |
| 08 DQL | 57 read-only application queries | No writes |

The DML lab catches MySQL error 1451 in a scoped procedure to prove RESTRICT without aborting the rest of the demonstration. Use the default seed so patient 1 has clinical dependencies. The lab attributes trigger operations to seeded Admin user 1, then clears session context. This is a trusted administrator exercise, not a substitute for API authentication.

## DQL concept index

| Query | Concepts |
|---|---|
| Q01–Q13 | WHERE, COUNT, SUM, AVG, MIN, MAX, IN, NOT IN, LIKE, DISTINCT, ORDER BY, LIMIT/OFFSET |
| Q14–Q15 | GROUP BY, HAVING |
| Q16–Q20 | INNER, LEFT, RIGHT, CROSS, meaningful SELF JOIN (shared household phone) |
| Q21–Q26 | UNION, UNION ALL, INTERSECT, EXCEPT, ANY, ALL |
| Q27–Q31 | Simple, nested and correlated subqueries, EXISTS, NOT EXISTS |
| Q32–Q36 | CASE, date/string functions, aggregate joins, multi-table traceability |
| Q37–Q40 | Top diagnosis/symptom frequencies, workload, visit statistics, stored functions |
| Q41 | FULL OUTER JOIN equivalent using LEFT JOIN UNION RIGHT JOIN |
| Q42–Q52 | Follow-ups, cancellations, bookings, fictional products, multiple cases/diagnoses, latest record, workload above average, anti-joins |
| Q53–Q57 | Summary cache, BMI, portable set equivalents, assigned doctor view |

INTERSECT and EXCEPT are native on MySQL 8.0.31+. See the [official set-operation reference](https://dev.mysql.com/doc/refman/8.0/en/set-operations.html). This installation is verified on **8.4.11**. Older MySQL 8.0 versions need the EXISTS/NOT EXISTS equivalents in Q55/Q56. MySQL's SQL syntax and functionality differ from MariaDB; this project targets Oracle MySQL. `ONLY_FULL_GROUP_BY` is enabled in the API sessions and the supplied queries meet it.

## Stored objects to demonstrate

```sql
USE caretrack;
SELECT calculate_age('2000-01-01');
SELECT calculate_bmi(170,65);
SELECT patient_visit_count(1),doctor_case_count(1);
SELECT * FROM patient_case_summary LIMIT 5;
SELECT * FROM upcoming_followups LIMIT 5;
SELECT * FROM doctor_case_statistics LIMIT 5;
CALL refresh_monthly_case_statistics();
SELECT * FROM monthly_case_statistics ORDER BY stat_month;
SELECT audit_id,actor_username,action,entity_type,entity_id,created_at
FROM audit_logs ORDER BY audit_id DESC LIMIT 10;
SHOW TRIGGERS FROM caretrack;
```

The refresh procedure owns an independent transaction and a named advisory lock. Do not call it inside a transaction containing unrelated writes. It uses DELETE + INSERT, not TRUNCATE, to retain atomic snapshot replacement. MySQL has no `CREATE MATERIALIZED VIEW`, as confirmed by the [official MySQL views FAQ](https://dev.mysql.com/doc/refman/8.4/en/faqs-views.html); this is explicitly a materialized-view **equivalent**. A pending follow-up prevents `close_case`. `register_patient`, `close_case`, `schedule_followup`, and `schedule_appointment` leave commit/rollback to the caller; invoke appointment scheduling inside START TRANSACTION so its doctor lock spans overlap checking and insertion.

## Privileges and limitations

The runtime login has SELECT/INSERT/UPDATE/DELETE on operational tables, SELECT/INSERT on `audit_logs`, SELECT on the cache and EXECUTE on routines, without DDL. It must remain private because it serves all API roles. Definer routines/triggers perform constrained internal writes. DCL examples show SQL authorization; JWT authorization and patient/doctor ownership are enforced in the backend. MySQL roles alone do not provide row-level ownership policies.

Do not edit FK checks off to hide import errors. The seed is ordered parents before children, and cases are finalized only after valid initial visits exist. Audit/session context is reset after seeding and at each pooled request boundary.
