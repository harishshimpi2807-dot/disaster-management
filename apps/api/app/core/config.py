from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../../.env"), extra="ignore")

    app_name: str = "Sentinel Recovery"
    secret_key: str = "dev-only-change-me"
    access_token_expire_minutes: int = 480
    api_cors_origins: str = "http://localhost:3000"
    database_url: str = "sqlite:///./data/sentinel.db"
    storage_backend: str = "local"
    storage_local_path: str = "./data/uploads"
    s3_endpoint_url: str = ""
    s3_bucket: str = "sentinel-evidence"
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_region: str = "us-east-1"
    change_detection_url: str = ""
    damage_classifier_url: str = ""
    anomaly_model_url: str = ""
    similarity_model_url: str = ""

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.api_cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
