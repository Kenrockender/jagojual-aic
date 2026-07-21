from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Konfigurasi runtime. Semua bisa di-override lewat env var berprefix JAGOJUAL_."""

    model_config = SettingsConfigDict(env_prefix="JAGOJUAL_", env_file=".env", extra="ignore")

    mode: str = "mock"  # "mock" (tanpa GPU) | "local" (LLM + adapter LoRA)
    base_model_id: str = "Qwen/Qwen2.5-7B-Instruct"
    adapter_path: str = "../model/checkpoints"
    cors_origins: str = "http://localhost:3000"

    # --- MODE=local ---
    # 4-bit wajib untuk GPU demo 6GB; matikan hanya kalau VRAM lega.
    load_4bit: bool = True
    # Hanya dipakai mode Pelanggan. Mode Pelatih selalu greedy supaya penilaian
    # atas percakapan yang sama tidak berubah-ubah saat juri mengulang demo.
    temperature: float = 0.8
    max_new_tokens_chat: int = 160
    max_new_tokens_evaluate: int = 512


settings = Settings()
