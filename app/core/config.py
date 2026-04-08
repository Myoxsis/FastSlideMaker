"""Runtime configuration for LLM-backed slide generation."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven application settings."""

    app_name: str = "Fast Slide Maker"
    app_env: str = "development"

    ollama_host: str = Field(default="http://localhost:11434", alias="OLLAMA_HOST")
    ollama_model: str = Field(default="llama3.1", alias="OLLAMA_MODEL")
    ollama_temperature: float = Field(default=0.4, alias="OLLAMA_TEMPERATURE")
    ollama_top_p: float = Field(default=0.9, alias="OLLAMA_TOP_P")
    ollama_max_tokens: int = Field(default=1200, alias="OLLAMA_MAX_TOKENS")

    enable_mock_mode: bool = Field(default=True, alias="ENABLE_MOCK_MODE")
    request_timeout_seconds: int = Field(default=20, alias="REQUEST_TIMEOUT_SECONDS")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
