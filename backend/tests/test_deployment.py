"""Deployment contracts without live database or network access."""
from pathlib import Path
import ssl
import sys
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient
from app.database.settings import DatabaseSettings, configure_session, TLSRequiredConnection
import app.database.settings as database_settings
from app.main import app

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import database

@pytest.fixture
def clean_env(monkeypatch):
    for name in ('DATABASE_URL', 'DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DATABASE_SSL', 'DATABASE_SSL_CA'):
        monkeypatch.delenv(name, raising=False)

def test_structured_aiven_settings_preserve_special_password(clean_env):
    config = DatabaseSettings(_env_file=None, db_host='service.example.com', db_port=11641, db_name='defaultdb', db_user='avnadmin', db_password='a@b:/% p', database_url='mysql+pymysql://local:ignored@localhost/localdb')
    url = config.url()
    assert (url.host, url.port, url.database, url.username, url.password) == ('service.example.com', 11641, 'defaultdb', 'avnadmin', 'a@b:/% p')
    context = config.connect_args()['ssl']
    assert context.verify_mode == ssl.CERT_REQUIRED and context.check_hostname
    assert context.minimum_version >= ssl.TLSVersion.TLSv1_2

def test_local_connection_and_remote_tls_enforcement(clean_env):
    local = DatabaseSettings(_env_file=None, database_url='mysql+pymysql://demo:example@127.0.0.1:3307/localdb')
    assert 'ssl' not in local.connect_args()
    remote = DatabaseSettings(_env_file=None, database_url='mysql+pymysql://demo:example@remote.example.com/defaultdb', database_ssl=False)
    with pytest.raises(ValueError, match='require verified TLS'):
        remote.connect_args()

def test_invalid_ca_fails_closed(clean_env):
    config = DatabaseSettings(_env_file=None, database_url='mysql+pymysql://demo:example@remote.example.com/defaultdb', database_ssl_ca='/nonexistent/ca.pem')
    with pytest.raises(FileNotFoundError):
        config.connect_args()

@pytest.mark.parametrize('url', ['sqlite:///demo.db', 'mysql+pymysql://user:pass@host', 'mysql+pymysql://user:pass@host/db?ssl_disabled=true'])
def test_unsupported_database_or_query_is_rejected(clean_env, url):
    with pytest.raises(ValueError):
        DatabaseSettings(_env_file=None, database_url=url).url()

def test_tls_downgrade_is_rejected():
    conn = MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = ('Ssl_cipher', '')
    with pytest.raises(RuntimeError, match='did not negotiate TLS'):
        configure_session(conn, require_tls=True)
    cursor.fetchone.return_value = ('Ssl_cipher', 'TLS_AES_256_GCM_SHA384')
    configure_session(conn, require_tls=True)
    assert any('time_zone' in str(call) for call in cursor.execute.call_args_list)

def test_raw_pymysql_uses_shared_verified_tls(monkeypatch, clean_env):
    config = DatabaseSettings(_env_file=None, database_url='mysql+pymysql://demo:example@remote.example.com:11641/defaultdb')
    monkeypatch.setattr(database, 'DatabaseSettings', lambda: config)
    connect = MagicMock()
    monkeypatch.setattr(database_settings, 'TLSRequiredConnection', connect)
    monkeypatch.setattr(database, 'configure_session', MagicMock())
    database.connection()
    args = connect.call_args.kwargs
    assert args['database'] == 'defaultdb' and args['port'] == 11641
    assert args['ssl'].check_hostname and args['ssl'].verify_mode == ssl.CERT_REQUIRED
    database.configure_session.assert_called_once_with(connect.return_value, require_tls=True)

def test_server_without_tls_is_rejected_before_authentication():
    conn = TLSRequiredConnection(defer_connect=True)
    conn.ssl = True
    conn.server_capabilities = 0
    with pytest.raises(database.pymysql.OperationalError, match='authentication refused'):
        conn._request_authentication()

def test_vercel_cors_preflight_without_database():
    with TestClient(app) as client:
        headers = {'Origin': 'https://care-track-jet.vercel.app', 'Access-Control-Request-Method': 'POST', 'Access-Control-Request-Headers': 'authorization,content-type'}
        response = client.options('/api/auth/login', headers=headers)
        assert response.status_code == 200
        assert response.headers['access-control-allow-origin'] == headers['Origin']
        response = client.options('/api/auth/login', headers={**headers, 'Origin': 'https://untrusted.example.com'})
        assert response.status_code == 400
        assert 'access-control-allow-origin' not in response.headers

def test_initialization_sql_is_schema_agnostic():
    for name in database.FILES:
        for statement in database.statements(ROOT / 'database' / name):
            assert statement.startswith(('CREATE TABLE', 'CREATE FUNCTION', 'CREATE PROCEDURE', 'CREATE TRIGGER', 'CREATE VIEW'))
            assert 'USE caretrack' not in statement and 'DEFINER=' not in statement
    assert 'USE caretrack' not in (ROOT / 'database/03_seed_data.sql').read_text()
    assert 'CREATE DATABASE' not in (ROOT / 'database/schema.sql').read_text()

def test_initialization_lock_is_released_on_failure(monkeypatch, clean_env):
    config = DatabaseSettings(_env_file=None, database_url='mysql+pymysql://demo:example@localhost/defaultdb')
    monkeypatch.setattr(database, 'DatabaseSettings', lambda: config)
    conn = MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = (1,)
    with pytest.raises(RuntimeError, match='interrupted'):
        with database.initialization_lock(conn):
            raise RuntimeError('interrupted')
    calls = cursor.execute.call_args_list
    assert calls[0].args == ('SELECT GET_LOCK(%s, 30)', (config.lock_name(),))
    assert calls[-1].args == ('SELECT RELEASE_LOCK(%s)', (config.lock_name(),))
