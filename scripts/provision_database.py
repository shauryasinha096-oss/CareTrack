"""Provision runtime login from .env; admin password is never printed or stored in code."""
from database import DatabaseSettings
from dotenv import load_dotenv
from pathlib import Path
import pymysql
load_dotenv(Path(__file__).resolve().parents[1]/'.env')
from sqlalchemy.engine import make_url
import os
url=make_url(os.environ['DATABASE_URL'])
if url.username!='caretrack_app': raise SystemExit('Use the documented caretrack_app runtime username.')
if not url.password or url.password=='CHANGE_ME': raise SystemExit('Set a random runtime password in .env first.')
if url.host not in ('localhost','127.0.0.1','::1'):
    raise SystemExit('This provisioning helper is local-only. For Aiven run database.py init.')
admin=make_url(os.environ['MYSQL_ADMIN_URL'])
if admin.host not in ('localhost','127.0.0.1','::1'):
    raise SystemExit('MYSQL_ADMIN_URL must be loopback for local provisioning.')
if not url.database or not url.database.replace('_','').isalnum():
    raise SystemExit('Choose an alphanumeric/underscore local schema name.')
conn=pymysql.connect(host=admin.host,port=admin.port or 3306,user=admin.username,password=admin.password,
                     database=admin.database,autocommit=True,**DatabaseSettings().connect_args())
with conn.cursor() as c:
    c.execute(f"CREATE DATABASE IF NOT EXISTS `{url.database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci")
    c.execute("CREATE USER IF NOT EXISTS 'caretrack_app'@'127.0.0.1' IDENTIFIED BY %s",(url.password,))
    from database import initialize
    initialize(seed_demo=False, local_admin=True)
    # Explicit local setup grants only; never invoked by managed initialization.
    catalog=__import__('json').loads((Path(__file__).resolve().parents[1]/'database/schema_catalog.json').read_text())
    try:
        c.execute(f"REVOKE ALL PRIVILEGES ON `{url.database}`.* FROM 'caretrack_app'@'127.0.0.1'")
    except pymysql.MySQLError as exc:
        if exc.args[0] != 1141: raise
    c.execute(f"GRANT EXECUTE ON `{url.database}`.* TO 'caretrack_app'@'127.0.0.1'")
    for table in catalog:
        name=table['name']
        privileges='SELECT,INSERT' if name=='audit_logs' else 'SELECT' if name=='monthly_case_statistics' else 'SELECT,INSERT,UPDATE,DELETE'
        c.execute(f"GRANT {privileges} ON `{url.database}`.`{name}` TO 'caretrack_app'@'127.0.0.1'")
conn.close()
print('Local runtime login provisioned; run database.py init --local-admin next.')
