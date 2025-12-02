"""Tests for configuration validation"""

import pytest
from pydantic import ValidationError

from app.config import Settings


def test_api_key_whitespace_only_raises_error(monkeypatch, tmp_path):
    """Test that whitespace-only API key raises ValidationError"""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GEMINI_API_KEY", "   ")

    with pytest.raises(ValidationError, match="cannot be empty"):
        Settings()


def test_api_key_empty_string_raises_error(monkeypatch, tmp_path):
    """Test that empty string API key raises ValidationError"""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GEMINI_API_KEY", "")

    with pytest.raises(ValidationError, match="cannot be empty"):
        Settings()


def test_log_level_lowercase_is_accepted(monkeypatch, tmp_path):
    """Test that lowercase log levels are converted to uppercase"""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("LOG_LEVEL", "debug")

    settings = Settings()
    assert settings.log_level == "DEBUG"


def test_log_level_invalid_raises_error(monkeypatch, tmp_path):
    """Test that invalid log level raises ValidationError"""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("LOG_LEVEL", "INVALID")

    with pytest.raises(ValidationError, match="LOG_LEVEL must be one of"):
        Settings()


def test_port_boundary_minimum(monkeypatch, tmp_path):
    """Test port = 1 (minimum valid)"""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("PORT", "1")

    settings = Settings()
    assert settings.port == 1


def test_port_boundary_maximum(monkeypatch, tmp_path):
    """Test port = 65535 (maximum valid)"""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("PORT", "65535")

    settings = Settings()
    assert settings.port == 65535


def test_port_below_minimum_raises_error(monkeypatch, tmp_path):
    """Test port = 0 raises ValidationError"""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("PORT", "0")

    with pytest.raises(ValidationError, match="PORT must be between"):
        Settings()


def test_port_above_maximum_raises_error(monkeypatch, tmp_path):
    """Test port = 65536 raises ValidationError"""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("PORT", "65536")

    with pytest.raises(ValidationError, match="PORT must be between"):
        Settings()


def test_all_default_values(monkeypatch, tmp_path):
    """Test that all defaults are correctly set"""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    settings = Settings()

    assert settings.gemini_model == "gemini-2.0-flash-exp"
    assert settings.host == "0.0.0.0"
    assert settings.port == 8000
    assert settings.reload is True
    assert settings.audio_sample_rate == 16000
    assert settings.audio_chunk_size == 512
    assert settings.log_level == "INFO"
    assert settings.flush_interval_bytes == 160000


def test_custom_values_override_defaults(monkeypatch, tmp_path):
    """Test that custom values override defaults"""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GEMINI_API_KEY", "custom-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-custom")
    monkeypatch.setenv("HOST", "127.0.0.1")
    monkeypatch.setenv("PORT", "9000")
    monkeypatch.setenv("RELOAD", "false")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    settings = Settings()

    assert settings.gemini_api_key == "custom-key"
    assert settings.gemini_model == "gemini-custom"
    assert settings.host == "127.0.0.1"
    assert settings.port == 9000
    assert settings.reload is False
    assert settings.log_level == "DEBUG"


def test_log_level_case_insensitive(monkeypatch, tmp_path):
    """Test that log level validation is case insensitive"""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("LOG_LEVEL", "warning")

    settings = Settings()
    assert settings.log_level == "WARNING"


def test_reload_string_values(monkeypatch, tmp_path):
    """Test reload accepts various string representations"""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    # Test 'true'
    monkeypatch.setenv("RELOAD", "true")
    settings = Settings()
    assert settings.reload is True

    # Test 'false'
    monkeypatch.setenv("RELOAD", "false")
    settings = Settings()
    assert settings.reload is False
