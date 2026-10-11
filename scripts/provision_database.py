"""Provision runtime login from .env; admin password is never printed or stored in code."""
from database import connection
from sqlalchemy.engine import make_url
import os
url=make_url(os.environ['DATABASE_URL'])
if url.username!='caretrack_app': raise SystemExit('Use the documented caretrack_app runtime username.')
if not url.password or url.password=='CHANGE_ME': raise SystemExit('Set a random runtime password in .env first.')
conn=connection()
with conn.cursor() as c:
    c.execute("CREATE DATABASE IF NOT EXISTS caretrack CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci")
    c.execute("CREATE USER IF NOT EXISTS 'caretrack_app'@'127.0.0.1' IDENTIFIED BY %s",(url.password,))
conn.close()
print('Runtime login provisioned; run database.py migrate next to install privileges.')
