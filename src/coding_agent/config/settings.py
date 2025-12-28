"""Application settings and configuration."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="CODING_AGENT_",
        extra="ignore",
    )

    # API Configuration
    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_api_base: str = Field(
        default="https://api.openai.com/v1",
        description="OpenAI-compatible API base URL",
    )
    model_name: str = Field(
        default="gpt-4-turbo-preview",
        description="Model name for the agent",
    )
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1)

    # Agent Configuration
    max_iterations: int = Field(default=10, ge=1, description="Max agent iterations")
    enable_reflection: bool = Field(default=True, description="Enable reflection node")

    # Memory and Context Management
    max_turns_in_context: int = Field(
        default=10,
        ge=1,
        description="Maximum conversation turns to keep in context",
    )
    max_tokens_per_turn: int = Field(
        default=8000,
        ge=1000,
        description="Maximum tokens per turn for context management",
    )
    auto_save_session: bool = Field(
        default=True,
        description="Automatically save session after each turn",
    )

    # MCP Server Configuration
    mcp_host: str = Field(default="localhost", description="MCP server host")
    mcp_port: int = Field(default=8000, ge=1024, le=65535, description="MCP server port")

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")
    log_file: Path | None = Field(default=None, description="Log file path")

    # Usage Tracking
    track_usage: bool = Field(default=True, description="Enable usage tracking")

    # Cost calculation (USD per 1M tokens)
    cost_per_million_input_tokens: float = Field(default=10.0)
    cost_per_million_output_tokens: float = Field(default=30.0)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
