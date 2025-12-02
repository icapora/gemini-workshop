"""
WebSocket router for handling browser audio connections
"""

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.gemini_live import GeminiLiveService

router: APIRouter = APIRouter()
logger: logging.Logger = logging.getLogger(__name__)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for bidirectional communication with the browser
    - Receives: PCM audio from user's microphone
    - Sends: Response audio and transcriptions from Gemini
    """
    await websocket.accept()
    logger.info("WebSocket client connected")

    # Create Gemini service instance
    gemini_service = GeminiLiveService()

    try:
        # Connect to Gemini Live API
        await gemini_service.connect()
        await websocket.send_json(
            {"type": "status", "message": "Connected to Gemini Live API"}
        )

        # Chunk counter using closure variable (better than function attribute mutation)
        chunk_count: int = 0

        # Task to receive audio from browser and send to Gemini
        async def receive_from_browser() -> None:
            nonlocal chunk_count

            try:
                while True:
                    # Receive data from browser (can be JSON text or bytes)
                    data: dict[str, Any] = await websocket.receive()

                    # If it's text (control message)
                    if "text" in data:
                        message: dict[str, Any] = json.loads(data["text"])

                        if message.get("type") == "text":
                            # Send text message to Gemini
                            await gemini_service.send_text(message.get("content", ""))

                        elif message.get("type") == "ping":
                            # Respond to ping to keep connection alive
                            await websocket.send_json({"type": "pong"})

                        elif message.get("type") == "activity_start":
                            # Manual VAD: speech start
                            await gemini_service.send_activity_start()
                            logger.info("VAD: activity_start received")

                        elif message.get("type") == "activity_end":
                            # Manual VAD: speech end
                            await gemini_service.send_activity_end()
                            logger.info("VAD: activity_end received")

                    # If it's bytes (audio)
                    elif "bytes" in data:
                        audio_data: bytes = data["bytes"]
                        # Send audio to Gemini (log every 50 chunks to avoid saturation)
                        chunk_count += 1
                        if chunk_count % 50 == 0:
                            logger.debug(
                                f"Sending audio chunk #{chunk_count}, size: {len(audio_data)} bytes"
                            )
                        await gemini_service.send_audio(audio_data)

            except WebSocketDisconnect:
                logger.info("Client disconnected")
            except Exception as e:
                logger.error(f"Error receiving from browser: {e}")
                raise

        # Task to receive responses from Gemini and send to browser
        async def send_to_browser() -> None:
            try:
                async for response in gemini_service.receive_responses():
                    # Send model state (thinking, speaking, listening)
                    if "model_state" in response:
                        await websocket.send_json(
                            {"type": "model_state", "state": response["model_state"]}
                        )

                    # Send input transcription (what the user says)
                    if "input_transcription" in response:
                        await websocket.send_json(
                            {
                                "type": "input_transcription",
                                "text": response["input_transcription"],
                            }
                        )

                    # Send output transcription (what Gemini says)
                    if "output_transcription" in response:
                        await websocket.send_json(
                            {
                                "type": "output_transcription",
                                "text": response["output_transcription"],
                            }
                        )

                    # Send response audio
                    if "audio" in response:
                        await websocket.send_bytes(response["audio"])

                    # Notify turn complete
                    if response.get("turn_complete"):
                        await websocket.send_json({"type": "turn_complete"})

                    # Notify interruption
                    if response.get("interrupted"):
                        await websocket.send_json({"type": "interrupted"})

            except Exception as e:
                logger.error(f"Error sending to browser: {e}")
                raise

        # Execute both tasks in parallel
        await asyncio.gather(receive_from_browser(), send_to_browser())

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"Error in WebSocket: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            # WebSocket may already be closed, safe to ignore
            logger.debug("Could not send error message, WebSocket likely closed")
    finally:
        # Clean up resources
        await gemini_service.disconnect()
        logger.info("Resources released")
