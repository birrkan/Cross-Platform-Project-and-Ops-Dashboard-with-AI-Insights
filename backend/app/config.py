# ─────────────────────────────────────────────────────────
# config.py — Application settings from environment variables
# ─────────────────────────────────────────────────────────
# This is the SINGLE source of truth for all configurable values.
# No hardcoded strings anywhere else in the codebase.
#
# Reference: https://docs.pydantic.dev/latest/concepts/pydantic_settings/#usage
# ─────────────────────────────────────────────────────────

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# Going up 3 directories from backend/app/config.py reaches the project root
ROOT_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "AI Operations Command Center"
    debug: bool = False
    server_port: int = 7222

    llamacpp_base_url: str = "http://127.0.0.1:3535/v1"
    llamacpp_model: str = "MaziyarPanahi/Qwen3-14B-GGUF:Q4_K_M"

    glpi_api_url: str = "http://192.168.122.10:7001"
    glpi_api_path: str = "/api.php/v2.3"
    glpi_app_token: str = ""
    glpi_client_id: str = ""
    glpi_client_secret: str = ""
    glpi_username: str = ""
    glpi_password: str = ""

    openproject_url: str = "http://192.168.122.10:7003"
    openproject_api_token: str = ""

    xwiki_url: str = "http://192.168.122.10:7002"
    xwiki_username: str = ""
    xwiki_password: str = ""

settings = Settings()
