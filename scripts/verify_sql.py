"""Execute the isolated SQL labs and validate the exact seeded relational graph."""
from pathlib import Path
from database import connection, statements, ROOT
import json

conn=connection(admin=True)
with conn.cursor() as c:
    c.execute('SET SESSION time_zone = "+00:00"')
    for filename in ('04_ddl_examples.sql','05_dml_examples.sql','06_dcl_examples.sql','07_tcl_examples.sql','08_dql_queries.sql'):
        count=0
        for sql in statements(ROOT/'database'/filename):
            c.execute(sql)
            if c.description:
                rows=c.fetchall()
                if 'remaining_owned_history' in sql or 'prescription_should_be_zero' in sql or 'patient_should_be_zero' in sql: assert rows[0][0]==0
                if 'CALL dml_restrict_lab' in sql: assert rows[0][0]==1
            while c.nextset(): pass
            count+=1
        print(f'{filename}: {count} statements passed')
    minima={'patients':150,'doctors':20,'symptoms':40,'medicines':40,'medical_cases':250,'visits':400,'case_symptoms':500,'diagnoses':300,'prescriptions':200,'prescription_medicines':500,'appointments':300,'follow_ups':150,'medical_history':200,'allergies':100,'audit_logs':500}
    counts={}
    for table,minimum in minima.items():
        c.execute(f'SELECT COUNT(*) FROM `{table}`');counts[table]=c.fetchone()[0];assert counts[table]>=minimum,(table,counts[table])
    print(json.dumps(counts,indent=2))
    c.execute("SELECT COUNT(*) FROM information_schema.referential_constraints WHERE constraint_schema=DATABASE()");assert c.fetchone()[0]==21
conn.close()

# Optional clean-room SQL seed restore. This never drops the operational schema.
import sys
if '--seed-import' in sys.argv:
    target='caretrack_seed_verification'
    check=connection(admin=True)
    try:
        with check.cursor() as c:
            c.execute('SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name=%s',(target,))
            if c.fetchone()[0]: raise RuntimeError('Seed verification database already exists; inspect it before retrying.')
            c.execute(f'CREATE DATABASE `{target}` CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci')
            check.select_db(target)
            for filename in ('02_schema.sql','10_functions.sql','11_procedures.sql','12_triggers.sql','09_views.sql','13_materialized_view_equivalent.sql','03_seed_data.sql'):
                for sql in statements(ROOT/'database'/filename):
                    c.execute(sql)
                    while c.nextset(): pass
            for table,minimum in minima.items():
                c.execute(f'SELECT COUNT(*) FROM `{table}`'); actual=c.fetchone()[0]
                assert actual>=minimum,(table,actual)
            c.execute('SELECT COUNT(*) FROM monthly_case_statistics');assert c.fetchone()[0]==12
            print('Clean schema + SQL seed restore passed all seeded minima and summary refresh.')
            c.execute('USE mysql')
            c.execute(f'DROP DATABASE `{target}`')
    finally:
        check.close()
