from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.database.settings import configure_session, connect_mysql

engine = create_engine(settings.url(), creator=lambda: connect_mysql(settings),
                       pool_pre_ping=True, pool_recycle=300, pool_size=3, max_overflow=2,
                       isolation_level='READ COMMITTED')

@event.listens_for(engine, 'connect')
def configure_connection(connection, _):
    configure_session(connection, require_tls=settings.tls_enabled())

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

def get_db():
    db = SessionLocal()
    try:
        db.execute(text('SET @caretrack_user_id = NULL, @caretrack_system = NULL'))
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        try:
            db.execute(text('SET @caretrack_user_id = NULL, @caretrack_system = NULL'))
            db.commit()
        finally:
            db.close()
