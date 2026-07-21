from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Konfigurasi runtime. Semua bisa di-override lewat env var berprefix JAGOJUAL_."""

    model_config = SettingsConfigDict(env_prefix="JAGOJUAL_", env_file=".env", extra="ignore")

    mode: str = "mock"  # "mock" (tanpa GPU) | "local" (LLM + adapter, M3)
    base_model_id: str = "Qwen/Qwen2.5-7B-Instruct"
    adapter_path: str = "../model/checkpoints"
    cors_origins: str = "http://localhost:3000"


settings = Settings()
