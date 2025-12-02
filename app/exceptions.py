"""
Custom exception classes for better error handling and debugging
Provides a clear exception hierarchy for different types of errors
"""


class GeminiWorkshopError(Exception):
    """Base exception for all application errors"""

    pass


class GeminiAPIError(GeminiWorkshopError):
    """Raised when Gemini API operations fail"""

    pass


class SessionNotActiveError(GeminiWorkshopError):
    """Raised when operations require an active session but none exists"""

    pass


class ConfigurationError(GeminiWorkshopError):
    """Raised when application configuration is invalid"""

    pass


class AudioProcessingError(GeminiWorkshopError):
    """Raised when audio processing fails"""

    pass
