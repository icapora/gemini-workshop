"""
Service for connecting to Google GenAI Live API
Handles bidirectional WebSocket connection and audio/transcription processing
"""

import asyncio
import logging
import time
from collections.abc import AsyncGenerator
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.config import settings
from app.exceptions import AudioProcessingError, GeminiAPIError, SessionNotActiveError

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeminiLiveService:
    """Service for handling connections with Google GenAI Live API"""

    def __init__(self) -> None:
        self.api_key: str = settings.gemini_api_key
        self.client: genai.Client = genai.Client(api_key=self.api_key)
        self.model: str = settings.gemini_model
        self._context_manager: Any | None = None  # The context manager
        self.session: Any | None = None  # The actual session

        # Diagnostics for detecting degradation
        self._bytes_since_last_activity_end: int = 0
        self._last_activity_start_time: float | None = None
        self._total_audio_bytes: int = 0
        self._activity_cycles: int = 0  # Start/end cycle counter

        # Session configuration
        self.config: dict[str, Any] = {
            "response_modalities": ["AUDIO"],
            "speech_config": {
                "voice_config": {"prebuilt_voice_config": {"voice_name": "Aoede"}},
                "language_code": "es-US",
            },
            "input_audio_transcription": {},
            "output_audio_transcription": {},
            # Disable automatic VAD - we use client-side VAD
            "realtime_input_config": {
                "automatic_activity_detection": {"disabled": True}
            },
        }

    async def connect(self) -> bool:
        """Establishes connection with Google GenAI Live API"""
        try:
            logger.info(f"Connecting to Gemini Live API with model {self.model}")
            # Create the context manager
            self._context_manager = self.client.aio.live.connect(
                model=self.model, config=self.config
            )
            # Enter the context manager and get the actual session
            self.session = await self._context_manager.__aenter__()
            logger.info("Connection established with Gemini Live API")
            return True
        except Exception as e:
            logger.error(f"Error connecting to Gemini Live API: {e}")
            raise GeminiAPIError(f"Failed to connect to Gemini API: {e}") from e

    async def disconnect(self) -> None:
        """Closes the connection with Google GenAI Live API"""
        if self._context_manager:
            try:
                await self._context_manager.__aexit__(None, None, None)
                self.session = None
                self._context_manager = None
                logger.info("Connection closed with Gemini Live API")
            except Exception as e:
                logger.error(f"Error closing connection: {e}")

    async def send_audio(self, audio_data: bytes) -> None:
        """
        Sends audio data to Gemini Live API using realtime input

        Args:
            audio_data: Audio bytes in PCM 16kHz mono format
        """
        if not self.session:
            raise SessionNotActiveError("No active session. Call connect() first")

        try:
            # Diagnostics: tracking bytes sent
            self._bytes_since_last_activity_end += len(audio_data)
            self._total_audio_bytes += len(audio_data)

            # Log every ~5 seconds of audio (using configurable flush interval)
            if (
                self._bytes_since_last_activity_end > 0
                and self._bytes_since_last_activity_end % settings.flush_interval_bytes
                < len(audio_data)
            ):
                duration_since_start = ""
                if self._last_activity_start_time:
                    elapsed = time.time() - self._last_activity_start_time
                    duration_since_start = f", {elapsed:.1f}s since activity_start"
                logger.info(
                    f"📊 Accumulated audio: {self._bytes_since_last_activity_end / 1024:.1f}KB since last activity_end"
                    f"{duration_since_start}, total session: {self._total_audio_bytes / 1024:.1f}KB"
                )

            # Use send_realtime_input for continuous audio streaming
            # IMPORTANT: Specify rate in mime_type for better processing
            await self.session.send_realtime_input(
                audio={"data": audio_data, "mime_type": "audio/pcm;rate=16000"}
            )
        except Exception as e:
            logger.error(f"Error sending audio: {e}")
            raise AudioProcessingError(f"Failed to send audio: {e}") from e

    async def receive_responses(self) -> AsyncGenerator[dict[str, Any], None]:
        """
        Async generator that receives responses from Gemini Live API

        Yields:
            dict: Responses with audio and/or transcriptions and states
        """
        if not self.session:
            raise SessionNotActiveError("No active session. Call connect() first")

        try:
            is_speaking = False
            turn_count = 0

            # Infinite loop - each iteration is a conversation turn
            while True:
                # Get new iterator for each turn
                turn = self.session.receive()

                async for response in turn:
                    response_data = {}

                    # Detailed log for debug
                    logger.info(f"Response received: {type(response).__name__}")

                    # Process server content
                    if hasattr(response, "server_content") and response.server_content:
                        server_content = response.server_content

                        # Input transcription (what the user said)
                        if (
                            hasattr(server_content, "input_transcription")
                            and server_content.input_transcription
                            and hasattr(server_content.input_transcription, "text")
                        ):
                            response_data[
                                "input_transcription"
                            ] = server_content.input_transcription.text

                        # Output transcription (what the model says)
                        if (
                            hasattr(server_content, "output_transcription")
                            and server_content.output_transcription
                            and hasattr(server_content.output_transcription, "text")
                        ):
                            response_data[
                                "output_transcription"
                            ] = server_content.output_transcription.text

                        # Model turn - contains audio and/or text
                        if (
                            hasattr(server_content, "model_turn")
                            and server_content.model_turn
                        ):
                            # Indicate that the model is speaking
                            if not is_speaking:
                                is_speaking = True
                                response_data["model_state"] = "speaking"

                            parts = getattr(server_content.model_turn, "parts", None)
                            for part in parts or []:
                                if hasattr(part, "text") and part.text:
                                    response_data["output_transcription"] = part.text

                                # Response audio
                                if hasattr(part, "inline_data") and part.inline_data:
                                    response_data["audio"] = part.inline_data.data

                        # Turn complete
                        if (
                            hasattr(server_content, "turn_complete")
                            and server_content.turn_complete
                        ):
                            turn_count += 1
                            logger.info(f"=== TURN {turn_count} COMPLETED ===")
                            response_data["turn_complete"] = True
                            is_speaking = False
                            response_data["model_state"] = "listening"

                        # Interruption state
                        if (
                            hasattr(server_content, "interrupted")
                            and server_content.interrupted
                        ):
                            response_data["interrupted"] = True
                            is_speaking = False
                            response_data["model_state"] = "listening"

                        # Grounding metadata (the model is processing)
                        if (
                            hasattr(server_content, "grounding_metadata")
                            and server_content.grounding_metadata
                        ):
                            response_data["model_state"] = "thinking"

                    # Emit response if there's data
                    if response_data:
                        yield response_data

        except asyncio.CancelledError:
            logger.info("Response reception cancelled")
            raise
        except Exception as e:
            logger.error(f"Error receiving responses: {e}")
            raise

    async def send_text(self, text: str) -> None:
        """
        Sends a text message to Gemini

        Args:
            text: Text message
        """
        if not self.session:
            raise SessionNotActiveError("No active session. Call connect() first")

        try:
            await self.session.send(input=text, end_of_turn=True)
        except Exception as e:
            logger.error(f"Error sending text: {e}")
            raise

    async def send_activity_start(self) -> None:
        """Sends voice activity start signal (manual VAD)"""
        if not self.session:
            raise SessionNotActiveError("No active session. Call connect() first")

        try:
            self._last_activity_start_time = time.time()
            await self.session.send_realtime_input(activity_start=types.ActivityStart())
            logger.info(f"▶️ Sent: activity_start (cycle #{self._activity_cycles + 1})")
        except Exception as e:
            logger.error(f"Error sending activity_start: {e}")
            raise

    async def send_activity_end(self) -> None:
        """Sends voice activity end signal (manual VAD)"""
        if not self.session:
            raise SessionNotActiveError("No active session. Call connect() first")

        try:
            duration = ""
            if self._last_activity_start_time:
                elapsed = time.time() - self._last_activity_start_time
                duration = f" (duration: {elapsed:.1f}s)"

            self._activity_cycles += 1
            logger.info(
                f"⏹️ Sent: activity_end{duration}, "
                f"audio sent: {self._bytes_since_last_activity_end / 1024:.1f}KB, "
                f"cycle #{self._activity_cycles}"
            )

            # Reset counter for next cycle
            self._bytes_since_last_activity_end = 0
            self._last_activity_start_time = None

            await self.session.send_realtime_input(activity_end=types.ActivityEnd())
        except Exception as e:
            logger.error(f"Error sending activity_end: {e}")
            raise
