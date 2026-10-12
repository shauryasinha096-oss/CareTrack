from pydantic import Field, field_validator
from app.database.settings import DatabaseSettings

class Settings(DatabaseSettings):
    jwt_secret: str = Field(min_length=32)
    jwt_expire_minutes: int = 480
    cors_origins: list[str] = ['https://care-track-jet.vercel.app', 'http://localhost:5173', 'http://127.0.0.1:5173']

    @field_validator('cors_origins')
    @classmethod
    def include_production_origin(cls, origins):
        # Existing local .env files may contain only the original local origins.
        return list(dict.fromkeys([*origins, 'https://care-track-jet.vercel.app']))

settings = Settings()
