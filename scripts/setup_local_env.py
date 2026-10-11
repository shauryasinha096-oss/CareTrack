"""Provision credentials for the isolated loopback MySQL instance (first run only)."""
from pathlib import Path
import secrets
import pymysql

ROOT=Path(__file__).resolve().parents[1]
env=ROOT/'.env'
if env.exists():
    raise SystemExit('.env already exists; preserved. Use its configured database credentials.')
admin_password=secrets.token_urlsafe(32)
app_password=secrets.token_urlsafe(32)
conn=pymysql.connect(unix_socket='/private/tmp/caretrack-mysql.sock',user='root',autocommit=True)
with conn.cursor() as c:
    c.execute('CREATE DATABASE IF NOT EXISTS caretrack CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci')
    c.execute("CREATE USER 'caretrack_app'@'127.0.0.1' IDENTIFIED BY %s",(app_password,))
    c.execute("GRANT SELECT,INSERT,UPDATE,DELETE,EXECUTE ON caretrack.* TO 'caretrack_app'@'127.0.0.1'")
    c.execute("ALTER USER 'root'@'localhost' IDENTIFIED BY %s",(admin_password,))
conn.close()
env.write_text(f'DATABASE_URL=mysql+pymysql://caretrack_app:{app_password}@127.0.0.1:3307/caretrack\nMYSQL_ADMIN_URL=mysql+pymysql://root:{admin_password}@127.0.0.1:3307/mysql\nJWT_SECRET={secrets.token_urlsafe(48)}\nJWT_EXPIRE_MINUTES=480\nCORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]\nDEMO_PASSWORD=CareTrackDemo2026!\n')
env.chmod(0o600)
print('Provisioned an isolated database and generated credentials in ignored .env (not printed).')
