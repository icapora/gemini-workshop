"""
Pytest configuration and fixtures
"""

import os
from collections.abc import AsyncGenerator

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

# Set test environment variables before importing app
os.environ["GEMINI_API_KEY"] = "test-api-key-for-testing"

from main import app  # noqa: E402


@pytest.fixture
def test_client() -> TestClient:
    """Synchronous test client for FastAPI"""
    return TestClient(app)


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Async test client for FastAPI"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def mock_gemini_api_key(monkeypatch):
    """Mock API key for testing"""
    from app.config import Settings

    monkeypatch.setenv("GEMINI_API_KEY", "test-mock-api-key")
    # Create new settings instance with mocked env var
    new_settings = Settings()
    # Patch settings in both app.config and app.services.gemini_live
    monkeypatch.setattr("app.config.settings", new_settings)
    monkeypatch.setattr("app.services.gemini_live.settings", new_settings)


@pytest.fixture
def mock_gemini_service(mocker):
    """Mock GeminiLiveService for WebSocket tests"""
    from unittest.mock import AsyncMock

    mock_service_class = mocker.patch("app.routers.websocket.GeminiLiveService")
    mock_instance = AsyncMock()
    mock_instance.connect.return_value = True
    mock_instance.disconnect.return_value = None

    async def empty_responses():
        if False:  # Never yield anything
            yield

    mock_instance.receive_responses.return_value = empty_responses()
    mock_service_class.return_value = mock_instance

    return mock_instance


@pytest.fixture
def mock_genai_client(mocker):
    """Mock google.genai.Client for service tests"""
    from unittest.mock import AsyncMock

    mock_client = mocker.Mock()
    mock_session = AsyncMock()
    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__.return_value = mock_session
    mock_context_manager.__aexit__.return_value = None
    mock_client.aio.live.connect.return_value = mock_context_manager

    return mock_client, mock_session


@pytest.fixture
def audio_test_data():
    """Provide test audio data of various sizes"""
    return {
        "small_chunk": b"x" * 512,
        "medium_chunk": b"x" * 16000,
        "large_chunk": b"x" * 160000,
        "empty": b"",
    }
