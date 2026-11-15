"""Cấu hình máy từ .env ngoài Git; không đưa bí mật vào log."""
from functools import lru_cache
from pathlib import Path
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / '.env', env_file_encoding='utf-8', extra='ignore')
    database_url: SecretStr
    jwt_secret: SecretStr
    company_tz: str = 'Asia/Ho_Chi_Minh'
    hub_public_url: str = 'http://10.0.2.2:8000'
    cors_origins: str = 'http://localhost:5173'
    hub_data_dir: Path = Path('C:/facegate-data')
    infer_device: str = 'cpu'
    log_level: str = 'INFO'
    enroll_max_cos_similarity: float = 0.98


@lru_cache
def get_settings() -> Settings:
    return Settings()
