"""
Tests for GeminiLiveService
"""

import pytest

from app.exceptions import SessionNotActiveError
from app.services.gemini_live import GeminiLiveService


def test_gemini_service_initialization_with_api_key(mock_gemini_api_key):
    """Test that service initializes correctly with API key"""
    service = GeminiLiveService()
    assert service.api_key == "test-mock-api-key"
    assert service.model == "gemini-2.0-flash-exp"


def test_gemini_service_raises_without_api_key(monkeypatch, tmp_path):
    """Test that service raises ValidationError without API key"""
    from pydantic import ValidationError

    from app.config import Settings

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    # Change to temp directory so .env file is not found
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValidationError):
        Settings()


def test_gemini_service_config_structure(mock_gemini_api_key):
    """Test that service configuration has correct structure"""
    service = GeminiLiveService()
    config = service.config

    assert "response_modalities" in config
    assert "AUDIO" in config["response_modalities"]
    assert "speech_config" in config
    assert "realtime_input_config" in config


@pytest.mark.asyncio
async def test_send_audio_requires_active_session(mock_gemini_api_key):
    """Test that sending audio without session raises error"""
    service = GeminiLiveService()

    with pytest.raises(SessionNotActiveError, match="No active session"):
        await service.send_audio(b"fake audio data")


@pytest.mark.asyncio
async def test_send_text_requires_active_session(mock_gemini_api_key):
    """Test that sending text without session raises error"""
    service = GeminiLiveService()

    with pytest.raises(SessionNotActiveError, match="No active session"):
        await service.send_text("Hello")


@pytest.mark.asyncio
async def test_send_activity_start_requires_session(mock_gemini_api_key):
    """Test that activity_start requires active session"""
    service = GeminiLiveService()

    with pytest.raises(SessionNotActiveError, match="No active session"):
        await service.send_activity_start()


@pytest.mark.asyncio
async def test_send_activity_end_requires_session(mock_gemini_api_key):
    """Test that activity_end requires active session"""
    service = GeminiLiveService()

    with pytest.raises(SessionNotActiveError, match="No active session"):
        await service.send_activity_end()


# Connection lifecycle tests


@pytest.mark.asyncio
async def test_connect_success(mock_gemini_api_key, mocker):
    """Test successful connection to Gemini API"""
    from unittest.mock import AsyncMock

    service = GeminiLiveService()

    mock_session = AsyncMock()
    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__.return_value = mock_session

    service.client.aio.live.connect = mocker.Mock(return_value=mock_context_manager)

    result = await service.connect()

    assert result is True
    assert service.session == mock_session
    assert service._context_manager == mock_context_manager
    service.client.aio.live.connect.assert_called_once_with(
        model="gemini-2.0-flash-exp", config=service.config
    )


@pytest.mark.asyncio
async def test_connect_raises_gemini_api_error(mock_gemini_api_key, mocker):
    """Test connection failure raises GeminiAPIError"""
    from app.exceptions import GeminiAPIError

    service = GeminiLiveService()
    service.client.aio.live.connect = mocker.Mock(
        side_effect=Exception("Connection failed")
    )

    with pytest.raises(GeminiAPIError, match="Failed to connect"):
        await service.connect()


@pytest.mark.asyncio
async def test_disconnect_success(mock_gemini_api_key, mocker):
    """Test successful disconnection"""
    from unittest.mock import AsyncMock

    mock_session = AsyncMock()
    mock_context_manager = AsyncMock()

    service = GeminiLiveService()
    service.session = mock_session
    service._context_manager = mock_context_manager

    await service.disconnect()

    mock_context_manager.__aexit__.assert_called_once_with(None, None, None)
    assert service.session is None
    assert service._context_manager is None


@pytest.mark.asyncio
async def test_disconnect_handles_errors(mock_gemini_api_key, mocker, caplog):
    """Test disconnect handles errors gracefully"""
    from unittest.mock import AsyncMock

    mock_context_manager = AsyncMock()
    mock_context_manager.__aexit__.side_effect = Exception("Disconnect error")

    service = GeminiLiveService()
    service._context_manager = mock_context_manager

    await service.disconnect()
    assert "Error closing connection" in caplog.text


# Text message tests


@pytest.mark.asyncio
async def test_send_text_success(mock_gemini_api_key, mocker):
    """Test sending text message successfully"""
    from unittest.mock import AsyncMock

    mock_session = AsyncMock()
    service = GeminiLiveService()
    service.session = mock_session

    await service.send_text("Hello Gemini")

    mock_session.send.assert_called_once_with(input="Hello Gemini", end_of_turn=True)


@pytest.mark.asyncio
async def test_send_text_raises_on_error(mock_gemini_api_key, mocker):
    """Test send_text exception handling"""
    from unittest.mock import AsyncMock

    mock_session = AsyncMock()
    mock_session.send.side_effect = Exception("Send failed")

    service = GeminiLiveService()
    service.session = mock_session

    with pytest.raises(Exception, match="Send failed"):
        await service.send_text("Hello")


# Activity signal tests


@pytest.mark.asyncio
async def test_send_activity_start_success(mock_gemini_api_key, mocker):
    """Test sending activity start signal"""
    from unittest.mock import AsyncMock

    mock_session = AsyncMock()
    service = GeminiLiveService()
    service.session = mock_session

    await service.send_activity_start()

    mock_session.send_realtime_input.assert_called_once()
    assert service._last_activity_start_time is not None


@pytest.mark.asyncio
async def test_send_activity_end_success(mock_gemini_api_key, mocker):
    """Test sending activity end signal"""
    from unittest.mock import AsyncMock

    mock_session = AsyncMock()
    service = GeminiLiveService()
    service.session = mock_session
    service._last_activity_start_time = 1000.0
    service._bytes_since_last_activity_end = 1024

    await service.send_activity_end()

    mock_session.send_realtime_input.assert_called_once()
    assert service._bytes_since_last_activity_end == 0
    assert service._last_activity_start_time is None
    assert service._activity_cycles == 1


@pytest.mark.asyncio
async def test_activity_start_raises_on_error(mock_gemini_api_key, mocker):
    """Test activity_start error handling"""
    from unittest.mock import AsyncMock

    mock_session = AsyncMock()
    mock_session.send_realtime_input.side_effect = Exception("Failed")

    service = GeminiLiveService()
    service.session = mock_session

    with pytest.raises(Exception, match="Failed"):
        await service.send_activity_start()


@pytest.mark.asyncio
async def test_activity_end_raises_on_error(mock_gemini_api_key, mocker):
    """Test activity_end error handling"""
    from unittest.mock import AsyncMock

    mock_session = AsyncMock()
    mock_session.send_realtime_input.side_effect = Exception("Failed")

    service = GeminiLiveService()
    service.session = mock_session

    with pytest.raises(Exception, match="Failed"):
        await service.send_activity_end()


# Audio processing tests


@pytest.mark.asyncio
async def test_send_audio_success(mock_gemini_api_key, mocker):
    """Test sending audio data successfully"""
    from unittest.mock import AsyncMock

    mock_session = AsyncMock()
    service = GeminiLiveService()
    service.session = mock_session

    audio_data = b"fake audio data"
    await service.send_audio(audio_data)

    mock_session.send_realtime_input.assert_called_once_with(
        audio={"data": audio_data, "mime_type": "audio/pcm;rate=16000"}
    )
    assert service._total_audio_bytes == len(audio_data)


@pytest.mark.asyncio
async def test_send_audio_tracks_bytes(mock_gemini_api_key, mocker):
    """Test audio byte tracking"""
    from unittest.mock import AsyncMock

    mock_session = AsyncMock()
    service = GeminiLiveService()
    service.session = mock_session

    audio_data1 = b"x" * 100
    audio_data2 = b"x" * 200

    await service.send_audio(audio_data1)
    await service.send_audio(audio_data2)

    assert service._total_audio_bytes == 300
    assert service._bytes_since_last_activity_end == 300


@pytest.mark.asyncio
async def test_send_audio_diagnostics_logging(mock_gemini_api_key, mocker, caplog):
    """Test audio diagnostics logging at flush intervals"""
    from unittest.mock import AsyncMock

    from app.config import settings

    mock_session = AsyncMock()
    service = GeminiLiveService()
    service.session = mock_session

    flush_interval = settings.flush_interval_bytes
    audio_chunk = b"x" * (flush_interval // 2)

    await service.send_audio(audio_chunk)
    await service.send_audio(audio_chunk)

    assert "Accumulated audio" in caplog.text


@pytest.mark.asyncio
async def test_send_audio_raises_audio_processing_error(mock_gemini_api_key, mocker):
    """Test audio processing error handling"""
    from unittest.mock import AsyncMock

    from app.exceptions import AudioProcessingError

    mock_session = AsyncMock()
    mock_session.send_realtime_input.side_effect = Exception("Send failed")

    service = GeminiLiveService()
    service.session = mock_session

    with pytest.raises(AudioProcessingError, match="Failed to send audio"):
        await service.send_audio(b"data")


# Async generator tests - receive_responses()


@pytest.mark.asyncio
async def test_receive_responses_requires_session(mock_gemini_api_key):
    """Test receive_responses requires active session"""
    service = GeminiLiveService()

    with pytest.raises(SessionNotActiveError, match="No active session"):
        async for _ in service.receive_responses():
            pass


@pytest.mark.asyncio
async def test_receive_responses_input_transcription(mock_gemini_api_key, mocker):
    """Test receiving input transcription responses"""
    from unittest.mock import AsyncMock

    mock_response = mocker.Mock()
    mock_response.server_content = mocker.Mock()
    mock_response.server_content.input_transcription = mocker.Mock(text="Hello")
    mock_response.server_content.output_transcription = None
    mock_response.server_content.model_turn = None
    mock_response.server_content.turn_complete = None
    mock_response.server_content.interrupted = None
    mock_response.server_content.grounding_metadata = None

    mock_session = AsyncMock()

    async def mock_turn():
        yield mock_response

    # Make receive() return an awaitable that returns the async iterator
    mock_session.receive = mocker.Mock(return_value=mock_turn())

    service = GeminiLiveService()
    service.session = mock_session

    responses = []
    async for response in service.receive_responses():
        responses.append(response)
        break

    assert len(responses) == 1
    assert responses[0]["input_transcription"] == "Hello"


@pytest.mark.asyncio
async def test_receive_responses_output_transcription(mock_gemini_api_key, mocker):
    """Test receiving output transcription responses"""
    from unittest.mock import AsyncMock

    mock_response = mocker.Mock()
    mock_response.server_content = mocker.Mock()
    mock_response.server_content.input_transcription = None
    mock_response.server_content.output_transcription = mocker.Mock(text="Response")
    mock_response.server_content.model_turn = None
    mock_response.server_content.turn_complete = None
    mock_response.server_content.interrupted = None
    mock_response.server_content.grounding_metadata = None

    mock_session = AsyncMock()

    async def mock_turn():
        yield mock_response

    mock_session.receive = mocker.Mock(return_value=mock_turn())

    service = GeminiLiveService()
    service.session = mock_session

    responses = []
    async for response in service.receive_responses():
        responses.append(response)
        break

    assert responses[0]["output_transcription"] == "Response"


@pytest.mark.asyncio
async def test_receive_responses_model_turn_with_audio(mock_gemini_api_key, mocker):
    """Test receiving model turn with audio data"""
    from unittest.mock import AsyncMock

    mock_part = mocker.Mock()
    mock_part.inline_data = mocker.Mock(data=b"audio bytes")
    mock_part.text = None

    mock_response = mocker.Mock()
    mock_response.server_content = mocker.Mock()
    mock_response.server_content.input_transcription = None
    mock_response.server_content.output_transcription = None
    mock_response.server_content.model_turn = mocker.Mock(parts=[mock_part])
    mock_response.server_content.turn_complete = None
    mock_response.server_content.interrupted = None
    mock_response.server_content.grounding_metadata = None

    mock_session = AsyncMock()

    async def mock_turn():
        yield mock_response

    mock_session.receive = mocker.Mock(return_value=mock_turn())

    service = GeminiLiveService()
    service.session = mock_session

    responses = []
    async for response in service.receive_responses():
        responses.append(response)
        break

    assert responses[0]["audio"] == b"audio bytes"
    assert responses[0]["model_state"] == "speaking"


@pytest.mark.asyncio
async def test_receive_responses_model_turn_with_text(mock_gemini_api_key, mocker):
    """Test receiving model turn with text"""
    from unittest.mock import AsyncMock

    mock_part = mocker.Mock()
    mock_part.text = "Model response text"
    mock_part.inline_data = None

    mock_response = mocker.Mock()
    mock_response.server_content = mocker.Mock()
    mock_response.server_content.input_transcription = None
    mock_response.server_content.output_transcription = None
    mock_response.server_content.model_turn = mocker.Mock(parts=[mock_part])
    mock_response.server_content.turn_complete = None
    mock_response.server_content.interrupted = None
    mock_response.server_content.grounding_metadata = None

    mock_session = AsyncMock()

    async def mock_turn():
        yield mock_response

    mock_session.receive = mocker.Mock(return_value=mock_turn())

    service = GeminiLiveService()
    service.session = mock_session

    responses = []
    async for response in service.receive_responses():
        responses.append(response)
        break

    assert responses[0]["output_transcription"] == "Model response text"
    assert responses[0]["model_state"] == "speaking"


@pytest.mark.asyncio
async def test_receive_responses_turn_complete(mock_gemini_api_key, mocker):
    """Test turn complete signal"""
    from unittest.mock import AsyncMock

    mock_response = mocker.Mock()
    mock_response.server_content = mocker.Mock()
    mock_response.server_content.input_transcription = None
    mock_response.server_content.output_transcription = None
    mock_response.server_content.model_turn = None
    mock_response.server_content.turn_complete = True
    mock_response.server_content.interrupted = None
    mock_response.server_content.grounding_metadata = None

    mock_session = AsyncMock()

    async def mock_turn():
        yield mock_response

    mock_session.receive = mocker.Mock(return_value=mock_turn())

    service = GeminiLiveService()
    service.session = mock_session

    responses = []
    async for response in service.receive_responses():
        responses.append(response)
        break

    assert responses[0]["turn_complete"] is True
    assert responses[0]["model_state"] == "listening"


@pytest.mark.asyncio
async def test_receive_responses_interrupted(mock_gemini_api_key, mocker):
    """Test interruption signal"""
    from unittest.mock import AsyncMock

    mock_response = mocker.Mock()
    mock_response.server_content = mocker.Mock()
    mock_response.server_content.input_transcription = None
    mock_response.server_content.output_transcription = None
    mock_response.server_content.model_turn = None
    mock_response.server_content.turn_complete = None
    mock_response.server_content.interrupted = True
    mock_response.server_content.grounding_metadata = None

    mock_session = AsyncMock()

    async def mock_turn():
        yield mock_response

    mock_session.receive = mocker.Mock(return_value=mock_turn())

    service = GeminiLiveService()
    service.session = mock_session

    responses = []
    async for response in service.receive_responses():
        responses.append(response)
        break

    assert responses[0]["interrupted"] is True
    assert responses[0]["model_state"] == "listening"


@pytest.mark.asyncio
async def test_receive_responses_grounding_metadata(mock_gemini_api_key, mocker):
    """Test grounding metadata (thinking state)"""
    from unittest.mock import AsyncMock

    mock_response = mocker.Mock()
    mock_response.server_content = mocker.Mock()
    mock_response.server_content.input_transcription = None
    mock_response.server_content.output_transcription = None
    mock_response.server_content.model_turn = None
    mock_response.server_content.turn_complete = None
    mock_response.server_content.interrupted = None
    mock_response.server_content.grounding_metadata = mocker.Mock()

    mock_session = AsyncMock()

    async def mock_turn():
        yield mock_response

    mock_session.receive = mocker.Mock(return_value=mock_turn())

    service = GeminiLiveService()
    service.session = mock_session

    responses = []
    async for response in service.receive_responses():
        responses.append(response)
        break

    assert responses[0]["model_state"] == "thinking"


@pytest.mark.asyncio
async def test_receive_responses_handles_cancellation(mock_gemini_api_key, mocker):
    """Test that receive_responses handles cancellation gracefully"""
    import asyncio
    from unittest.mock import AsyncMock

    mock_session = AsyncMock()

    async def mock_turn():
        raise asyncio.CancelledError()
        yield  # Make it a generator

    mock_session.receive = mocker.Mock(return_value=mock_turn())

    service = GeminiLiveService()
    service.session = mock_session

    with pytest.raises(asyncio.CancelledError):
        async for _ in service.receive_responses():
            pass


@pytest.mark.asyncio
async def test_receive_responses_handles_errors(mock_gemini_api_key, mocker):
    """Test error handling in receive_responses"""
    from unittest.mock import AsyncMock

    mock_session = AsyncMock()

    async def mock_turn():
        raise Exception("Network error")
        yield  # Make it a generator

    mock_session.receive = mocker.Mock(return_value=mock_turn())

    service = GeminiLiveService()
    service.session = mock_session

    with pytest.raises(Exception, match="Network error"):
        async for _ in service.receive_responses():
            pass


@pytest.mark.asyncio
async def test_receive_responses_multiple_turns(mock_gemini_api_key, mocker):
    """Test receiving multiple conversation turns"""
    from unittest.mock import AsyncMock

    mock_response1 = mocker.Mock()
    mock_response1.server_content = mocker.Mock()
    mock_response1.server_content.input_transcription = mocker.Mock(text="Turn 1")
    mock_response1.server_content.output_transcription = None
    mock_response1.server_content.model_turn = None
    mock_response1.server_content.turn_complete = None
    mock_response1.server_content.interrupted = None
    mock_response1.server_content.grounding_metadata = None

    mock_response2 = mocker.Mock()
    mock_response2.server_content = mocker.Mock()
    mock_response2.server_content.input_transcription = mocker.Mock(text="Turn 2")
    mock_response2.server_content.output_transcription = None
    mock_response2.server_content.model_turn = None
    mock_response2.server_content.turn_complete = None
    mock_response2.server_content.interrupted = None
    mock_response2.server_content.grounding_metadata = None

    mock_session = AsyncMock()

    turn_count = [0]

    def mock_receive():
        async def mock_turn1():
            yield mock_response1

        async def mock_turn2():
            yield mock_response2

        turn_count[0] += 1
        if turn_count[0] == 1:
            return mock_turn1()
        else:
            return mock_turn2()

    mock_session.receive = mocker.Mock(side_effect=mock_receive)

    service = GeminiLiveService()
    service.session = mock_session

    responses = []
    async for response in service.receive_responses():
        responses.append(response)
        if len(responses) == 2:
            break

    assert len(responses) == 2
    assert responses[0]["input_transcription"] == "Turn 1"
    assert responses[1]["input_transcription"] == "Turn 2"


@pytest.mark.asyncio
@pytest.mark.timeout(5)
async def test_receive_responses_empty_response_not_yielded(
    mock_gemini_api_key, mocker
):
    """Test that empty responses are not yielded"""
    import asyncio
    from unittest.mock import AsyncMock

    mock_response = mocker.Mock()
    mock_response.server_content = mocker.Mock()
    mock_response.server_content.input_transcription = None
    mock_response.server_content.output_transcription = None
    mock_response.server_content.model_turn = None
    mock_response.server_content.turn_complete = None
    mock_response.server_content.interrupted = None
    mock_response.server_content.grounding_metadata = None

    mock_session = AsyncMock()

    call_count = [0]

    def mock_receive_func():
        async def mock_turn():
            # Only yield once, then the generator ends
            call_count[0] += 1
            if call_count[0] == 1:
                yield mock_response
            else:
                # On subsequent calls, block forever (test will timeout if we reach here)
                await asyncio.sleep(999)
                return  # Never reached
                yield  # Make it a generator

        return mock_turn()

    mock_session.receive = mocker.Mock(side_effect=mock_receive_func)

    service = GeminiLiveService()
    service.session = mock_session

    responses = []

    # Use asyncio.wait_for to limit the test time
    try:

        async def collect_responses():
            async for response in service.receive_responses():
                responses.append(response)
                # Break after checking one turn completes without yielding
                break

        await asyncio.wait_for(collect_responses(), timeout=1.0)
    except asyncio.TimeoutError:
        # Expected - we should timeout because empty response causes
        # the loop to go to next turn which blocks forever
        pass

    assert len(responses) == 0  # Empty response should not be yielded
