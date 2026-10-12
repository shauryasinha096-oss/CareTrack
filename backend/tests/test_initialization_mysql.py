"""Opt-in checks: caller must provision a NEW disposable schema and schema-only user."""
from pathlib import Path
import os
import sys
import pytest
from sqlalchemy import select, text, func
from app.database.connection import engine, SessionLocal
from app.database.settings import DatabaseSettings
from app.models import User, Patient, Doctor, MODELS
from app.utils.security import hash_password, verify_password

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from database import initialize, connection
pytestmark = pytest.mark.skipif(os.getenv('CARETRACK_INIT_TEST') != '1', reason='requires explicitly provisioned disposable MySQL schema')

def assert_disposable_empty():
    assert DatabaseSettings().url().database.startswith('caretrack_deploy_test_')
    with connection() as conn, conn.cursor() as cursor:
        cursor.execute('SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE()')
        assert cursor.fetchone()[0] == 0
        cursor.execute('SHOW GRANTS')
        assert all('SUPER' not in str(row) and 'ALL PRIVILEGES ON *.*' not in str(row) for row in cursor.fetchall())

def snapshot():
    with engine.connect() as conn:
        return {name: conn.execute(text(f'SELECT * FROM `{name}`')).fetchall() for name in MODELS}

def test_empty_schema_repeatable_full_initialization():
    assert_disposable_empty()
    initialize()
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Patient)) == 150
        assert db.scalar(select(func.count()).select_from(User)) == 22
        assert db.scalar(select(func.count()).select_from(Doctor)) == 20
        admin = db.scalar(select(User).where(User.username == 'admin'))
        assert verify_password(os.environ['DEMO_PASSWORD'], admin.password_hash)
        admin.password_hash = hash_password('AChangedFictionalPassword2026!')
        admin.is_active = False
        db.commit()
    before = snapshot()
    initialize()
    assert snapshot() == before
    with connection() as conn, conn.cursor() as cursor:
        cursor.execute('SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema=DATABASE()')
        assert cursor.fetchone()[0] >= 3
        cursor.execute('SELECT COUNT(*) FROM information_schema.routines WHERE routine_schema=DATABASE()')
        assert cursor.fetchone()[0] >= 10
        cursor.execute('SELECT COUNT(*) FROM monthly_case_statistics')
        assert cursor.fetchone()[0] > 0

def test_existing_user_only_database_does_not_import_fixed_ids():
    assert_disposable_empty()
    initialize(seed_demo=False)
    with SessionLocal() as db:
        db.add(User(user_id=901, username='existing_account', email='existing@example.com', password_hash='preserve-this-value', role='ADMIN'))
        db.commit()
    initialize()
    with SessionLocal() as db:
        assert db.get(User, 901).password_hash == 'preserve-this-value'
        assert db.scalar(select(func.count()).select_from(Patient)) == 0
        assert db.scalar(select(func.count()).select_from(User)) == 23
        assert db.scalar(select(func.count()).select_from(Doctor)) == 20
    before = snapshot()
    initialize()
    assert snapshot() == before
