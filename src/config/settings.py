"""Application settings and configuration."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "Code Agent"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1

    # Local LLM (Ollama)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gpt-oss:20b"  # Your installed model
    ollama_embedding_model: str = "nomic-embed-text"

    # Anthropic Claude
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-5-20250929"
    anthropic_temperature: float = 0.2
    anthropic_max_tokens: int = 10000

    # LLM Provider Selection: "ollama" or "anthropic"
    llm_provider: Literal["ollama", "anthropic"] = "anthropic"

    # Agent Configuration
    agent_max_iterations: int = 50
    agent_timeout: int = 300  # seconds
    agent_memory_enabled: bool = True

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/code_agent.db"
    redis_url: str = "redis://localhost:6379/0"

    # Paths
    workspace_root: Path = Field(default_factory=lambda: Path.cwd())
    data_dir: Path = Field(default_factory=lambda: Path("./data"))

    # Terminal
    terminal_shell: str = Field(default="powershell.exe")  # Windows default
    terminal_timeout: int = 120  # seconds

    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    def model_post_init(self, __context) -> None:
        """Create necessary directories after initialization."""
        self.data_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
