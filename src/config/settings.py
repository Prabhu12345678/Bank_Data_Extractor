from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Database
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "extractor"
    db_password: str = "extractorpass"
    db_name: str = "extractor_db"

    # LLM Orchestration (Highly Configurable)
    # Supported: "claude", "openai", "ollama", "aggregator"
    llm_provider: str = "aggregator"

    # Secrets for proprietary / hosted LLMs
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

    # Endpoint details for Localized LLMs or Aggregators
    local_llm_url: str = "http://localhost:11434/v1"
    local_llm_model: str = "llama3"

    aggregator_api_key: Optional[str] = None
    aggregator_url: str = "https://api.aggregator.io/v1"
    aggregator_model: str = "auto/best-fast"

    # Extraction Confidence Threshold
    confidence_threshold: float = 0.85

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
