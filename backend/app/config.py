from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Smart Plant Doctor API"
    api_v1_prefix: str = "/api/v1"

    # Supabase — set DATABASE_URL to your Supabase Postgres connection string (Session pooler)
    supabase_url: str = ""
    supabase_jwt_secret: str = ""

    database_url: str = "sqlite:///./data/app.db"

    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    uploads_dir: str = "uploads"
    model_path: str = "../ai/exports/smart_plant_doctor_model.pth"
    confidence_threshold: float = 0.70
    model_temperature: float = 1.0

    gemini_api_key: str = ""
    gemini_chat_models: str = "gemma-4-31b-it,gemma-4-4b-it,gemma-4-26b-a4b-it"

    blynk_auth_token: str = ""
    blynk_server: str = "https://blynk.cloud"

    public_api_url: str = "http://localhost:8000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def use_supabase_auth(self) -> bool:
        return bool(self.supabase_jwt_secret)


@lru_cache
def get_settings() -> Settings:
    return Settings()
