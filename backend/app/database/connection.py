from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True, isolation_level='READ COMMITTED')

@event.listens_for(engine, 'connect')
def configure_connection(connection, _):
    with connection.cursor() as c:
        c.execute("SET time_zone = '+00:00'")
        c.execute("SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION,ONLY_FULL_GROUP_BY'")
        c.execute('SET @caretrack_user_id = NULL, @caretrack_system = NULL')

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
