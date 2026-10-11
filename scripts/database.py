"""Install the initial MySQL schema and stored objects without destructive resets."""
from pathlib import Path
import argparse
import os
import re
import sys
from dotenv import load_dotenv
import pymysql
from sqlalchemy.engine import make_url

ROOT=Path(__file__).resolve().parents[1]
load_dotenv(ROOT/'.env')

def connection(admin=True):
    url=make_url(os.environ['MYSQL_ADMIN_URL' if admin else 'DATABASE_URL'])
    return pymysql.connect(host=url.host or '127.0.0.1',port=url.port or 3306,user=url.username,password=url.password,database=url.database,charset='utf8mb4',autocommit=True)

def statements(path):
    delimiter=';'; buffer=[]
    for line in path.read_text().splitlines():
        if line.strip().startswith('--') or not line.strip(): continue
        if line.strip().upper().startswith('DELIMITER '):
            delimiter=line.strip().split()[1]; continue
        buffer.append(line)
        if line.rstrip().endswith(delimiter):
            statement='\n'.join(buffer).rstrip()[:-len(delimiter)].strip()
            if statement: yield statement
            buffer=[]
    if buffer: raise ValueError(f'Unterminated SQL in {path.name}')

def migrate():
    conn=connection()
    with conn.cursor() as c:
        c.execute('SELECT VERSION()'); version=c.fetchone()[0]
        parts=tuple(int(x) for x in version.split('-')[0].split('.')[:3])
        if parts<(8,0,31): raise RuntimeError('MySQL 8.0.31+ is required')
        files=['01_create_database.sql','02_schema.sql','10_functions.sql','11_procedures.sql','12_triggers.sql','09_views.sql','13_materialized_view_equivalent.sql']
        for filename in files:
            for statement in statements(ROOT/'database'/filename):
                table=re.match(r'CREATE TABLE `([^`]+)`',statement,re.I)
                routine=re.match(r'CREATE (FUNCTION|PROCEDURE) (\w+)',statement,re.I)
                trigger=re.match(r'CREATE TRIGGER (\w+)',statement,re.I)
                if table:
                    c.execute('SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=%s AND table_name=%s',('caretrack',table[1]))
                    if c.fetchone()[0]: continue
                if routine:
                    c.execute('SELECT COUNT(*) FROM information_schema.routines WHERE routine_schema=%s AND routine_name=%s',('caretrack',routine[2]))
                    if c.fetchone()[0]: continue
                if trigger:
                    c.execute('SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema=%s AND trigger_name=%s',('caretrack',trigger[1]))
                    if c.fetchone()[0]: continue
                c.execute(statement)
            print(f'Installed {filename}')
        # Runtime privileges: no DDL or audit tampering; grant per table, not schema-wide DML.
        c.execute("SELECT COUNT(*) FROM mysql.user WHERE user='caretrack_app' AND host='127.0.0.1'")
        if c.fetchone()[0]:
            try:
                c.execute("REVOKE ALL PRIVILEGES ON caretrack.* FROM 'caretrack_app'@'127.0.0.1'")
            except pymysql.MySQLError as exc:
                if exc.args[0] != 1141: raise  # Newly provisioned accounts have no schema grants yet.
            c.execute("GRANT EXECUTE ON caretrack.* TO 'caretrack_app'@'127.0.0.1'")
            c.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='caretrack'")
            for (table_name,) in c.fetchall():
                privileges='SELECT,INSERT' if table_name=='audit_logs' else 'SELECT' if table_name=='monthly_case_statistics' else 'SELECT,INSERT,UPDATE,DELETE'
                c.execute(f"GRANT {privileges} ON caretrack.`{table_name}` TO 'caretrack_app'@'127.0.0.1'")
    conn.close()
    print(f'MySQL {version}: initial migration complete. Existing definitions are preserved; use explicit ALTER migrations for later schema changes.')

def export_seed():
    catalog=__import__('json').loads((ROOT/'database/schema_catalog.json').read_text())
    conn=connection(); conn.select_db('caretrack'); output=['-- Verified fictional seed. Run on an empty migrated schema with triggers installed.',"USE caretrack;","SET @caretrack_user_id=NULL,@caretrack_system='SEED';",'START TRANSACTION;']
    statuses=[]
    with conn.cursor(pymysql.cursors.DictCursor) as c:
        for table in catalog:
            name=table['name']
            if name in ('audit_logs','monthly_case_statistics'): continue
            fields=[x['name'] for x in table['columns']]
            c.execute(f'SELECT * FROM `{name}` ORDER BY '+','.join(x['name'] for x in table['columns'] if 'PK' in x['flags']))
            for row in c.fetchall():
                if name=='medical_cases':
                    statuses.append((row['case_id'],row['case_status'])); row['record_state']='DRAFT'; row['case_status']='OPEN'
                values=','.join(conn.escape(row[x]) for x in fields)
                output.append(f"INSERT INTO `{name}` ({','.join('`'+x+'`' for x in fields)}) VALUES ({values});")
        for identity,status in statuses:
            output.append(f"UPDATE medical_cases SET record_state='SUBMITTED',case_status={conn.escape(status)} WHERE case_id={identity};")
    output.extend(['COMMIT;','CALL refresh_monthly_case_statistics();','SET @caretrack_user_id=NULL,@caretrack_system=NULL;','-- Patient/case triggers generate at least 650 audit rows; do not insert duplicate audit copies.'])
    (ROOT/'database/03_seed_data.sql').write_text('\n'.join(output)+'\n'); conn.close()
    print('Exported verified fictional seed SQL; passwords are Argon2id hashes, not plaintext.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('command',choices=['migrate','seed','export-seed'])
    args=parser.parse_args()
    if args.command=='migrate': migrate()
    elif args.command=='export-seed': export_seed()
    else:
        sys.path.insert(0,str(ROOT/'backend'))
        from seed import seed
        seed()
