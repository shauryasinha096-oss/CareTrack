"""Non-destructive MySQL initialization using schema-scoped privileges only."""
from pathlib import Path
from contextlib import contextmanager
import argparse
import json
import os
import re
import sys
import traceback
import pymysql
from sqlalchemy.engine import make_url
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env')
sys.path.insert(0, str(ROOT / 'backend'))
from app.database.settings import DatabaseSettings, configure_session, connect_mysql

FILES = ('02_schema.sql', '10_functions.sql', '11_procedures.sql',
         '12_triggers.sql', '09_views.sql', '13_materialized_view_equivalent.sql')


def initialization_error(exc):
    """Report useful diagnostics without SQL, parameters or driver messages."""
    driver = getattr(exc, 'orig', exc)
    args = getattr(driver, 'args', ())
    code = args[0] if isinstance(driver, pymysql.MySQLError) and args and type(args[0]) is int else None
    hints = {
        1044: 'Database access denied; check the database name and schema permissions.',
        1045: 'Database authentication rejected; check the Render database credentials.',
        1049: 'Configured database does not exist.',
        1054: 'A column expected by the backend is missing from the existing schema.',
        1062: 'A unique value already exists; existing data was preserved.',
        1064: 'MySQL rejected SQL syntax; the source location below identifies the failing step.',
        1142: 'The database user lacks permission for this operation.',
        1146: 'A table expected by the backend does not exist in the selected database.',
        1227: 'MySQL rejected an operation requiring additional privileges.',
        1305: 'A required stored procedure or function does not exist.',
        1370: 'The database user lacks permission to execute a stored routine.',
        1419: 'Provider policy rejected stored-object creation.',
        1452: 'A referenced database row is missing.',
        1644: 'A database trigger or procedure rejected the operation.',
        2003: 'Database host or port could not be reached.',
        2013: 'The database connection was lost.',
        2026: 'TLS negotiation or certificate verification failed.',
    }
    if code is not None:
        message = f'Initialization failed (MySQL error {code}, {type(exc).__name__}). '
        message += hints.get(code, 'Check database compatibility and schema permissions.')
    elif isinstance(exc, FileNotFoundError):
        message = 'Initialization failed: a required file is missing; check DATABASE_SSL_CA and the Render Secret File.'
    elif isinstance(exc, (ValueError, RuntimeError)):
        # These configuration/initialization errors have controlled messages.
        message = f'Initialization failed: {exc}'
    else:
        message = f'Initialization failed ({type(exc).__name__}); check configuration and database connectivity.'
    locations = []
    for frame, line in traceback.walk_tb(exc.__traceback__):
        try:
            relative = Path(frame.f_code.co_filename).resolve().relative_to(ROOT)
        except ValueError:
            continue
        if relative.parts[0] in ('scripts', 'backend') and not any(part in ('.venv', 'site-packages') for part in relative.parts):
            locations.append(f'{relative.as_posix()}:{line}')
    if locations:
        message += ' Source: ' + ' -> '.join(locations) + '.'
    return message + ' Credentials, SQL and row values were not logged.'


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
            print(f'{filename}: {installed} new objects installed; existing objects preserved', flush=True)
    print(f'MySQL {version}: schema initialization complete', flush=True)


def initialize(seed_demo=True, local_admin=False, seed_only=False):
    with connection(admin=local_admin) as conn, initialization_lock(conn):
        if not seed_only:
            migrate(conn)
        if seed_demo:
            print('Starting fictional account/data initialization; existing rows and passwords will be preserved.', flush=True)
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
        print(initialization_error(exc), file=sys.stderr, flush=True)
        sys.exit(1)
    
