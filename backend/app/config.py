from pathlib import Path
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / '.env', extra='ignore')
    database_url: str
    jwt_secret: str = Field(min_length=32)
    jwt_expire_minutes: int = 480
    cors_origins: list[str] = ['http://localhost:5173','http://127.0.0.1:5173']

    @field_validator('database_url')
    @classmethod
    def mysql_only(cls, value):
        if not value.startswith('mysql+pymysql://'):
            raise ValueError('CareTrack requires a MySQL/PyMySQL database URL')
        return value

settings = Settings()
