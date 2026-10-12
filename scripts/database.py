"""Non-destructive MySQL initialization using schema-scoped privileges only."""
from pathlib import Path
from contextlib import contextmanager
import argparse
import json
import os
import re
import sys
import pymysql
from sqlalchemy.engine import make_url
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env')
sys.path.insert(0, str(ROOT / 'backend'))
from app.database.settings import DatabaseSettings, configure_session, connect_mysql

FILES = ('02_schema.sql', '10_functions.sql', '11_procedures.sql',
         '12_triggers.sql', '09_views.sql', '13_materialized_view_equivalent.sql')


def connection(admin=False):
    config = DatabaseSettings()
    url = config.url()
    if admin:
        # Explicit opt-in for local labs/bootstrap only. Never used on Aiven.
        if url.host not in ('localhost', '127.0.0.1', '::1'):
            raise ValueError('--local-admin is restricted to loopback databases')
        admin_url = make_url(os.environ['MYSQL_ADMIN_URL'])
        if admin_url.host not in ('localhost', '127.0.0.1', '::1'):
            raise ValueError('MYSQL_ADMIN_URL must target loopback for local bootstrap')
        url = admin_url.set(database=url.database)
    conn = connect_mysql(config, url=url, autocommit=True)
    try:
        configure_session(conn, require_tls=config.tls_enabled())
        with conn.cursor() as cursor:
            cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
        return conn
    except Exception:
        conn.close()
        raise


@contextmanager
def initialization_lock(conn):
    name = DatabaseSettings().lock_name()
    with conn.cursor() as cursor:
        cursor.execute('SELECT GET_LOCK(%s, 30)', (name,))
        if cursor.fetchone()[0] != 1:
            raise RuntimeError('Another database initialization is running; retry later')
    try:
        yield
    finally:
        with conn.cursor() as cursor:
            cursor.execute('SELECT RELEASE_LOCK(%s)', (name,))


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

def migrate(conn=None):
    if conn is None:
        with connection() as owned, initialization_lock(owned):
            return migrate(owned)
    schema = DatabaseSettings().url().database
    with conn.cursor() as cursor:
        cursor.execute('SELECT VERSION()')
        version = cursor.fetchone()[0]
        parts = tuple(int(x) for x in version.split('-')[0].split('.')[:3])
        if parts < (8, 0, 31):
            raise RuntimeError('MySQL 8.0.31+ is required')
        objects = set()
        for query, params in (
            ('SELECT table_type, table_name FROM information_schema.tables WHERE table_schema=%s', (schema,)),
            ('SELECT routine_type, routine_name FROM information_schema.routines WHERE routine_schema=%s', (schema,)),
            ("SELECT 'TRIGGER', trigger_name FROM information_schema.triggers WHERE trigger_schema=%s", (schema,)),
        ):
            cursor.execute(query, params)
            objects.update(('TABLE' if kind == 'BASE TABLE' else kind, name.lower())
                           for kind, name in cursor.fetchall())
        for filename in FILES:
            installed = 0
            for statement in statements(ROOT / 'database' / filename):
                match = re.match(r'CREATE (TABLE|FUNCTION|PROCEDURE|TRIGGER|VIEW) `?(\w+)`?', statement, re.I)
                if not match:
                    raise RuntimeError(f'Unexpected initialization SQL in {filename}; refusing to execute')
                identity = (match[1].upper(), match[2].lower())
                if identity in objects:
                    continue  # Preserve existing definitions and every existing row.
                try:
                    cursor.execute(statement)
                except pymysql.MySQLError as exc:
                    code = exc.args[0]
                    if code in (1419, 1227):
                        raise RuntimeError('Managed MySQL rejected stored-object creation. Check provider routine/trigger permissions and log_bin_trust_function_creators; no SET GLOBAL or SUPER request was attempted.') from None
                    raise RuntimeError(f'Could not install {identity[0]} {identity[1]} (MySQL error {code}); resolve schema privileges/compatibility and rerun init') from None
                objects.add(identity)
                installed += 1
            print(f'{filename}: {installed} new objects installed; existing objects preserved')
    print(f'MySQL {version}: schema initialization complete')


def initialize(seed_demo=True, local_admin=False, seed_only=False):
    with connection(admin=local_admin) as conn, initialization_lock(conn):
        if not seed_only:
            migrate(conn)
        if seed_demo:
            from seed import seed
            seed()  # Advisory lock remains held across the seed transaction.


def export_seed():
    catalog=json.loads((ROOT/'database/schema_catalog.json').read_text())
    conn=connection(); output=['-- Verified fictional seed. Run on an empty migrated schema with triggers installed.',"SET @caretrack_user_id=NULL,@caretrack_system='SEED';",'START TRANSACTION;']
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

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['init', 'migrate', 'seed', 'export-seed'])
    parser.add_argument('--local-admin', action='store_true', help='Use loopback MYSQL_ADMIN_URL for local schema bootstrap only')
    args = parser.parse_args()
    try:
        if args.command == 'export-seed':
            export_seed()
        else:
            initialize(seed_demo=args.command != 'migrate', local_admin=args.local_admin,
                       seed_only=args.command == 'seed')
    except Exception as exc:
        # Driver/SQLAlchemy exceptions can contain connection details or SQL values.
        if isinstance(exc, (ValueError, RuntimeError)):
            print(f'Initialization failed: {exc}', file=sys.stderr)
        else:
            print(f'Initialization failed ({type(exc).__name__}); check database connectivity, TLS certificate and schema permissions. Credentials were not logged.', file=sys.stderr)
        sys.exit(1)
