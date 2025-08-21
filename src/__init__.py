"""
Whisper Transcriber
===================

Real-time audio transcription with Whisper AI and translation support.
Supports desktop GUI, web interface, and console modes.
"""

__version__ = "1.0.0"
__author__ = "Marcus Pereira"
__email__ = "marcus@example.com"
__license__ = "MIT"

from .app import WhisperApplication, create_app
from .config.settings import get_config_manager

__all__ = [
    "WhisperApplication",
    "create_app",
    "get_config_manager",
    "__version__",
]
