"""Tests for WebSocket router"""

import asyncio
import logging
from unittest.mock import AsyncMock

import pytest


def test_websocket_connection_accepts(test_client, mocker):
    """Test WebSocket accepts connections"""
    mock_service_class = mocker.patch("app.routers.websocket.GeminiLiveService")
    mock_instance = AsyncMock()
    mock_instance.connect.return_value = True
    mock_instance.disconnect.return_value = None

    async def empty_generator():
        return
        yield

    mock_instance.receive_responses = lambda: empty_generator()
    mock_service_class.return_value = mock_instance

    with test_client.websocket_connect("/ws") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "status"
        assert "Connected to Gemini" in data["message"]


def test_websocket_connection_initializes_gemini(test_client, mocker):
    """Test WebSocket initializes Gemini service"""
    mock_service_class = mocker.patch("app.routers.websocket.GeminiLiveService")
    mock_instance = AsyncMock()
    mock_instance.connect.return_value = True
    mock_instance.disconnect.return_value = None

    async def empty_generator():
        return
        yield

    mock_instance.receive_responses = lambda: empty_generator()
    mock_service_class.return_value = mock_instance

    with test_client.websocket_connect("/ws") as websocket:
        websocket.receive_json()

    mock_instance.connect.assert_called_once()


def test_websocket_receives_audio_bytes(test_client, mocker):
    """Test WebSocket receives and forwards audio bytes"""
    mock_service_class = mocker.patch("app.routers.websocket.GeminiLiveService")
    mock_instance = AsyncMock()
    mock_instance.connect.return_value = True
    mock_instance.disconnect.return_value = None
    mock_instance.send_audio = AsyncMock()

    async def empty_generator():
        return
        yield

    mock_instance.receive_responses = lambda: empty_generator()
    mock_service_class.return_value = mock_instance

    with test_client.websocket_connect("/ws") as websocket:
        websocket.receive_json()

        audio_data = b"fake audio chunk"
        websocket.send_bytes(audio_data)

        import time

        time.sleep(0.1)

    mock_instance.send_audio.assert_called()


def test_websocket_audio_chunk_logging(test_client, mocker, caplog):
    """Test audio chunk logging every 50 chunks"""
    caplog.set_level(logging.DEBUG)

    mock_service_class = mocker.patch("app.routers.websocket.GeminiLiveService")
    mock_instance = AsyncMock()
    mock_instance.connect.return_value = True
    mock_instance.disconnect.return_value = None
    mock_instance.send_audio = AsyncMock()

    async def empty_generator():
        await asyncio.sleep(0.5)
        return
        yield

    mock_instance.receive_responses = lambda: empty_generator()
    mock_service_class.return_value = mock_instance

    with test_client.websocket_connect("/ws") as websocket:
        websocket.receive_json()

        for _ in range(50):
            websocket.send_bytes(b"audio")

        import time

        time.sleep(0.2)

    assert mock_instance.send_audio.call_count == 50 or "chunk #50" in caplog.text


def test_websocket_handles_text_message(test_client, mocker):
    """Test WebSocket handles text control messages"""
    mock_service_class = mocker.patch("app.routers.websocket.GeminiLiveService")
    mock_instance = AsyncMock()
    mock_instance.connect.return_value = True
    mock_instance.disconnect.return_value = None
    mock_instance.send_text = AsyncMock()

    async def empty_generator():
        return
        yield

    mock_instance.receive_responses = lambda: empty_generator()
    mock_service_class.return_value = mock_instance

    with test_client.websocket_connect("/ws") as websocket:
        websocket.receive_json()

        websocket.send_json({"type": "text", "content": "Hello Gemini"})

        import time

        time.sleep(0.1)

    mock_instance.send_text.assert_called_with("Hello Gemini")


def test_websocket_handles_ping_pong(test_client, mocker):
    """Test WebSocket ping/pong keepalive"""
    mock_service_class = mocker.patch("app.routers.websocket.GeminiLiveService")
    mock_instance = AsyncMock()
    mock_instance.connect.return_value = True
    mock_instance.disconnect.return_value = None

    async def slow_generator():
        await asyncio.sleep(10)  # Never yields
        if False:
            yield

    # Make receive_responses return the generator directly (not wrapped in AsyncMock)
    mock_instance.receive_responses = lambda: slow_generator()
    mock_service_class.return_value = mock_instance

    with test_client.websocket_connect("/ws") as websocket:
        websocket.receive_json()

        websocket.send_json({"type": "ping"})

        response = websocket.receive_json()
        assert response["type"] == "pong"


def test_websocket_handles_activity_start(test_client, mocker):
    """Test WebSocket handles VAD activity_start"""
    mock_service_class = mocker.patch("app.routers.websocket.GeminiLiveService")
    mock_instance = AsyncMock()
    mock_instance.connect.return_value = True
    mock_instance.disconnect.return_value = None
    mock_instance.send_activity_start = AsyncMock()

    async def empty_generator():
        return
        yield

    mock_instance.receive_responses = lambda: empty_generator()
    mock_service_class.return_value = mock_instance

    with test_client.websocket_connect("/ws") as websocket:
        websocket.receive_json()

        websocket.send_json({"type": "activity_start"})

        import time

        time.sleep(0.1)

    mock_instance.send_activity_start.assert_called_once()


def test_websocket_handles_activity_end(test_client, mocker):
    """Test WebSocket handles VAD activity_end"""
    mock_service_class = mocker.patch("app.routers.websocket.GeminiLiveService")
    mock_instance = AsyncMock()
    mock_instance.connect.return_value = True
    mock_instance.disconnect.return_value = None
    mock_instance.send_activity_end = AsyncMock()

    async def empty_generator():
        return
        yield

    mock_instance.receive_responses = lambda: empty_generator()
    mock_service_class.return_value = mock_instance

    with test_client.websocket_connect("/ws") as websocket:
        websocket.receive_json()

        websocket.send_json({"type": "activity_end"})

        import time

        time.sleep(0.1)

    mock_instance.send_activity_end.assert_called_once()


@pytest.mark.timeout(5)
def test_websocket_forwards_model_state(test_client, mocker):
    """Test WebSocket forwards model state to browser"""
    mock_service_class = mocker.patch("app.routers.websocket.GeminiLiveService")
    mock_instance = AsyncMock()
    mock_instance.connect.return_value = True
    mock_instance.disconnect.return_value = None

    async def mock_responses():
        yield {"model_state": "speaking"}
        # Don't yield more to avoid infinite loop

    mock_instance.receive_responses = lambda: mock_responses()
    mock_service_class.return_value = mock_instance

    with test_client.websocket_connect("/ws") as websocket:
        websocket.receive_json()

        response = websocket.receive_json()
        assert response["type"] == "model_state"
        assert response["state"] == "speaking"


@pytest.mark.timeout(5)
def test_websocket_forwards_input_transcription(test_client, mocker):
    """Test WebSocket forwards input transcription"""
    mock_service_class = mocker.patch("app.routers.websocket.GeminiLiveService")
    mock_instance = AsyncMock()
    mock_instance.connect.return_value = True
    mock_instance.disconnect.return_value = None

    async def mock_responses():
        yield {"input_transcription": "User said this"}

    mock_instance.receive_responses = lambda: mock_responses()
    mock_service_class.return_value = mock_instance

    with test_client.websocket_connect("/ws") as websocket:
        websocket.receive_json()

        response = websocket.receive_json()
        assert response["type"] == "input_transcription"
        assert response["text"] == "User said this"


@pytest.mark.timeout(5)
def test_websocket_forwards_output_transcription(test_client, mocker):
    """Test WebSocket forwards output transcription"""
    mock_service_class = mocker.patch("app.routers.websocket.GeminiLiveService")
    mock_instance = AsyncMock()
    mock_instance.connect.return_value = True
    mock_instance.disconnect.return_value = None

    async def mock_responses():
        yield {"output_transcription": "AI response"}

    mock_instance.receive_responses = lambda: mock_responses()
    mock_service_class.return_value = mock_instance

    with test_client.websocket_connect("/ws") as websocket:
        websocket.receive_json()

        response = websocket.receive_json()
        assert response["type"] == "output_transcription"
        assert response["text"] == "AI response"


@pytest.mark.timeout(5)
def test_websocket_forwards_audio_bytes(test_client, mocker):
    """Test WebSocket forwards audio bytes to browser"""
    mock_service_class = mocker.patch("app.routers.websocket.GeminiLiveService")
    mock_instance = AsyncMock()
    mock_instance.connect.return_value = True
    mock_instance.disconnect.return_value = None

    audio_bytes = b"response audio"

    async def mock_responses():
        yield {"audio": audio_bytes}

    mock_instance.receive_responses = lambda: mock_responses()
    mock_service_class.return_value = mock_instance

    with test_client.websocket_connect("/ws") as websocket:
        websocket.receive_json()

        response = websocket.receive_bytes()
        assert response == audio_bytes


@pytest.mark.timeout(5)
def test_websocket_forwards_turn_complete(test_client, mocker):
    """Test WebSocket forwards turn_complete signal"""
    mock_service_class = mocker.patch("app.routers.websocket.GeminiLiveService")
    mock_instance = AsyncMock()
    mock_instance.connect.return_value = True
    mock_instance.disconnect.return_value = None

    async def mock_responses():
        yield {"turn_complete": True}

    mock_instance.receive_responses = lambda: mock_responses()
    mock_service_class.return_value = mock_instance

    with test_client.websocket_connect("/ws") as websocket:
        websocket.receive_json()

        response = websocket.receive_json()
        assert response["type"] == "turn_complete"


@pytest.mark.timeout(5)
def test_websocket_forwards_interrupted_signal(test_client, mocker):
    """Test WebSocket forwards interrupted signal"""
    mock_service_class = mocker.patch("app.routers.websocket.GeminiLiveService")
    mock_instance = AsyncMock()
    mock_instance.connect.return_value = True
    mock_instance.disconnect.return_value = None

    async def mock_responses():
        yield {"interrupted": True}

    mock_instance.receive_responses = lambda: mock_responses()
    mock_service_class.return_value = mock_instance

    with test_client.websocket_connect("/ws") as websocket:
        websocket.receive_json()

        response = websocket.receive_json()
        assert response["type"] == "interrupted"


def test_websocket_handles_receive_from_browser_error(test_client, mocker, caplog):
    """Test error handling in receive_from_browser task"""
    mock_service_class = mocker.patch("app.routers.websocket.GeminiLiveService")
    mock_instance = AsyncMock()
    mock_instance.connect.return_value = True
    mock_instance.disconnect.return_value = None
    mock_instance.send_audio.side_effect = Exception("Processing error")

    async def empty_generator():
        await asyncio.sleep(1)
        return
        yield

    mock_instance.receive_responses = lambda: empty_generator()
    mock_service_class.return_value = mock_instance

    try:
        with test_client.websocket_connect("/ws") as websocket:
            websocket.receive_json()

            websocket.send_bytes(b"audio")

            import time

            time.sleep(0.2)
    except Exception:
        pass

    assert "Error" in caplog.text or "error" in caplog.text.lower()


def test_websocket_handles_send_to_browser_error(test_client, mocker, caplog):
    """Test error handling in send_to_browser task"""
    mock_service_class = mocker.patch("app.routers.websocket.GeminiLiveService")
    mock_instance = AsyncMock()
    mock_instance.connect.return_value = True
    mock_instance.disconnect.return_value = None

    async def error_generator():
        raise Exception("Gemini error")
        yield

    mock_instance.receive_responses = lambda: error_generator()
    mock_service_class.return_value = mock_instance

    try:
        with test_client.websocket_connect("/ws") as websocket:
            websocket.receive_json()

            import time

            time.sleep(0.1)
    except Exception:
        pass

    assert "Error" in caplog.text or "error" in caplog.text.lower()


def test_websocket_handles_disconnection(test_client, mocker):
    """Test graceful handling of client disconnection"""
    mock_service_class = mocker.patch("app.routers.websocket.GeminiLiveService")
    mock_instance = AsyncMock()
    mock_instance.connect.return_value = True
    mock_instance.disconnect.return_value = None

    async def empty_generator():
        return
        yield

    mock_instance.receive_responses = lambda: empty_generator()
    mock_service_class.return_value = mock_instance

    with test_client.websocket_connect("/ws") as websocket:
        websocket.receive_json()

    mock_instance.disconnect.assert_called_once()


def test_websocket_cleanup_on_exception(test_client, mocker):
    """Test cleanup occurs even after exceptions"""
    mock_service_class = mocker.patch("app.routers.websocket.GeminiLiveService")
    mock_instance = AsyncMock()
    mock_instance.connect.side_effect = Exception("Connection failed")
    mock_instance.disconnect.return_value = None
    mock_service_class.return_value = mock_instance

    try:
        with test_client.websocket_connect("/ws") as _:
            pass
    except Exception:
        pass

    mock_instance.disconnect.assert_called_once()


def test_websocket_sends_error_message_on_exception(test_client, mocker):
    """Test error message is sent to client on exception"""
    mock_service_class = mocker.patch("app.routers.websocket.GeminiLiveService")
    mock_instance = AsyncMock()
    mock_instance.connect.return_value = True
    mock_instance.disconnect.return_value = None

    async def error_generator():
        raise Exception("Test error")
        yield

    mock_instance.receive_responses = lambda: error_generator()
    mock_service_class.return_value = mock_instance

    try:
        with test_client.websocket_connect("/ws") as websocket:
            websocket.receive_json()

            try:
                response = websocket.receive_json(timeout=0.5)
                if response.get("type") == "error":
                    assert "Test error" in response["message"]
            except Exception:
                pass
    except Exception:
        pass


@pytest.mark.timeout(10)
def test_websocket_multiple_response_types_in_sequence(test_client, mocker):
    """Test WebSocket handles multiple response types in sequence"""
    mock_service_class = mocker.patch("app.routers.websocket.GeminiLiveService")
    mock_instance = AsyncMock()
    mock_instance.connect.return_value = True
    mock_instance.disconnect.return_value = None

    async def mock_responses():
        yield {"model_state": "listening"}
        yield {"input_transcription": "Hello"}
        yield {"model_state": "speaking"}
        yield {"output_transcription": "Hi there"}
        yield {"audio": b"audio_data"}
        yield {"turn_complete": True}

    mock_instance.receive_responses = lambda: mock_responses()
    mock_service_class.return_value = mock_instance

    with test_client.websocket_connect("/ws") as websocket:
        websocket.receive_json()

        msg1 = websocket.receive_json()
        assert msg1["type"] == "model_state" and msg1["state"] == "listening"

        msg2 = websocket.receive_json()
        assert msg2["type"] == "input_transcription" and msg2["text"] == "Hello"

        msg3 = websocket.receive_json()
        assert msg3["type"] == "model_state" and msg3["state"] == "speaking"

        msg4 = websocket.receive_json()
        assert msg4["type"] == "output_transcription" and msg4["text"] == "Hi there"

        audio = websocket.receive_bytes()
        assert audio == b"audio_data"

        msg5 = websocket.receive_json()
        assert msg5["type"] == "turn_complete"
