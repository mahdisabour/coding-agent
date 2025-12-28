"""Tests for configuration."""

import os
from unittest.mock import patch

from coding_agent.config.settings import Settings


def test_settings_defaults():
    """Test default settings values."""
    with patch.dict(os.environ, {"CODING_AGENT_OPENAI_API_KEY": "test-key"}):
        settings = Settings()

        assert settings.openai_api_key == "test-key"
        assert settings.model_name == "gpt-4-turbo-preview"
        assert settings.temperature == 0.1
        assert settings.max_iterations == 10
        assert settings.enable_reflection is True
        assert settings.track_usage is True


def test_settings_from_env():
    """Test loading settings from environment variables."""
    env_vars = {
        "CODING_AGENT_OPENAI_API_KEY": "custom-key",
        "CODING_AGENT_MODEL_NAME": "gpt-4",
        "CODING_AGENT_TEMPERATURE": "0.5",
        "CODING_AGENT_MAX_ITERATIONS": "5",
    }

    with patch.dict(os.environ, env_vars):
        settings = Settings()

        assert settings.openai_api_key == "custom-key"
        assert settings.model_name == "gpt-4"
        assert settings.temperature == 0.5
        assert settings.max_iterations == 5
