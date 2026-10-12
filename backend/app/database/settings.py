"""Shared connection settings for SQLAlchemy, PyMySQL and deployment scripts."""
from hashlib import sha256
from pathlib import Path
import ssl
import pymysql
from pymysql.constants import CLIENT

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL, make_url

ROOT = Path(__file__).resolve().parents[3]


class TLSRequiredConnection(pymysql.connections.Connection):
    """PyMySQL 1.1.1 otherwise permits servers to omit TLS during handshake."""

    def _request_authentication(self):
        if self.ssl and not self.server_capabilities & CLIENT.SSL:
            raise pymysql.OperationalError(2026, 'Server does not support required TLS; authentication refused')
        return super()._request_authentication()


def connect_mysql(config, url=None, autocommit=False):
    url = url or config.url()
    args = config.connect_args()
    connect = TLSRequiredConnection if 'ssl' in args else pymysql.connect
    return connect(host=url.host or '127.0.0.1', port=url.port or 3306,
                   user=url.username, password=url.password, database=url.database,
                   autocommit=autocommit, **args)


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT / '.env', extra='ignore', hide_input_in_errors=True,
    )
    database_url: str | None = None
    db_host: str | None = None
    db_port: int = 3306
    db_name: str | None = None
    db_user: str | None = None
    db_password: SecretStr | None = None
    database_ssl: bool | None = None
    database_ssl_ca: str | None = None

    def url(self) -> URL:
        # Structured variables take precedence, avoiding URL-encoding passwords.
        if self.db_host:
            if not all((self.db_name, self.db_user, self.db_password)):
                raise ValueError('DB_HOST requires DB_NAME, DB_USER and DB_PASSWORD')
            return URL.create('mysql+pymysql', host=self.db_host, port=self.db_port,
                              username=self.db_user,
                              password=self.db_password.get_secret_value(), database=self.db_name)
        if not self.database_url:
            raise ValueError('Set DATABASE_URL or the DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD variables')
        try:
            url = make_url(self.database_url)
        except Exception:
            raise ValueError('DATABASE_URL must be a valid MySQL/PyMySQL URL') from None
        if url.drivername != 'mysql+pymysql' or not url.database:
            raise ValueError('DATABASE_URL requires mysql+pymysql:// and a database name')
        if url.query:
            raise ValueError('Configure TLS with DATABASE_SSL and DATABASE_SSL_CA, without URL query options')
        return url

    def tls_enabled(self) -> bool:
        local = self.url().host in ('127.0.0.1', 'localhost', '::1')
        if self.database_ssl is False and not local:
            raise ValueError('Remote MySQL connections require verified TLS')
        return self.database_ssl if self.database_ssl is not None else not local

    def connect_args(self) -> dict:
        args = dict(charset='utf8mb4', connect_timeout=10, read_timeout=60, write_timeout=60)
        if self.tls_enabled():
            context = ssl.create_default_context(cafile=self.database_ssl_ca or None)
            context.minimum_version = ssl.TLSVersion.TLSv1_2
            args['ssl'] = context  # CERT_REQUIRED and hostname verification remain enabled.
        return args

    def lock_name(self) -> str:
        return 'caretrack.init.' + sha256(self.url().database.encode()).hexdigest()[:40]


def configure_session(connection, require_tls=False):
    with connection.cursor() as cursor:
        if require_tls:
            cursor.execute("SHOW SESSION STATUS LIKE 'Ssl_cipher'")
            row = cursor.fetchone()
            if not row or not row[1]:
                raise RuntimeError('MySQL did not negotiate TLS; connection refused')
        cursor.execute("SET time_zone = '+00:00'")
        cursor.execute("SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION,ONLY_FULL_GROUP_BY'")
        cursor.execute('SET @caretrack_user_id = NULL, @caretrack_system = NULL')
