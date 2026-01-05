"""
Speech-to-Text Engine - Abstract interface for STT backends.

Provides a unified API for different STT engines:
- Whisper (local, high accuracy)
- Vosk (lightweight, offline)
- Mock (for testing)

The engine abstraction allows swapping backends without changing game code.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Callable, Any
from enum import Enum
from datetime import datetime
import uuid
import time
import threading
import queue


class STTStatus(Enum):
    """Status of STT engine."""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class STTResult:
    """Result from speech-to-text recognition."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    text: str = ""
    confidence: float = 0.0
    is_final: bool = True
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: int = 0
    language: str = "en"
    alternatives: list[str] = field(default_factory=list)
    raw_audio_path: Optional[str] = None

    @property
    def is_empty(self) -> bool:
        """Check if result has no text."""
        return not self.text.strip()

    @property
    def words(self) -> list[str]:
        """Get individual words from text."""
        return self.text.lower().split()

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "text": self.text,
            "confidence": self.confidence,
            "is_final": self.is_final,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
            "language": self.language,
            "alternatives": self.alternatives,
            "raw_audio_path": self.raw_audio_path,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "STTResult":
        """Deserialize from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            text=data.get("text", ""),
            confidence=data.get("confidence", 0.0),
            is_final=data.get("is_final", True),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(),
            duration_ms=data.get("duration_ms", 0),
            language=data.get("language", "en"),
            alternatives=data.get("alternatives", []),
            raw_audio_path=data.get("raw_audio_path"),
        )


class STTEngine(ABC):
    """
    Abstract base class for speech-to-text engines.

    All STT backends must implement this interface to be usable
    with the voice input system.
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self._status = STTStatus.IDLE
        self._is_initialized = False
        self._callbacks: list[Callable[[STTResult], None]] = []
        self._error_callbacks: list[Callable[[Exception], None]] = []

    @property
    def status(self) -> STTStatus:
        """Get current engine status."""
        return self._status

    @property
    def is_initialized(self) -> bool:
        """Check if engine is initialized and ready."""
        return self._is_initialized

    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the STT engine.

        Returns:
            True if initialization succeeded
        """
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the STT engine and release resources."""
        pass

    @abstractmethod
    def transcribe(self, audio_data: bytes) -> STTResult:
        """
        Transcribe audio data to text.

        Args:
            audio_data: Raw audio bytes (PCM 16-bit, 16kHz mono)

        Returns:
            STTResult with transcription
        """
        pass

    @abstractmethod
    def transcribe_file(self, file_path: str) -> STTResult:
        """
        Transcribe audio from file.

        Args:
            file_path: Path to audio file

        Returns:
            STTResult with transcription
        """
        pass

    @abstractmethod
    def start_streaming(self) -> bool:
        """
        Start streaming recognition mode.

        Returns:
            True if streaming started successfully
        """
        pass

    @abstractmethod
    def stop_streaming(self) -> Optional[STTResult]:
        """
        Stop streaming recognition mode.

        Returns:
            Final STTResult from streaming session
        """
        pass

    @abstractmethod
    def feed_audio(self, audio_chunk: bytes) -> Optional[STTResult]:
        """
        Feed audio chunk during streaming mode.

        Args:
            audio_chunk: Audio data chunk

        Returns:
            Partial STTResult if available, None otherwise
        """
        pass

    def on_result(self, callback: Callable[[STTResult], None]) -> None:
        """Register callback for recognition results."""
        self._callbacks.append(callback)

    def on_error(self, callback: Callable[[Exception], None]) -> None:
        """Register callback for errors."""
        self._error_callbacks.append(callback)

    def _emit_result(self, result: STTResult) -> None:
        """Emit result to all registered callbacks."""
        for callback in self._callbacks:
            try:
                callback(result)
            except Exception:
                pass

    def _emit_error(self, error: Exception) -> None:
        """Emit error to all registered callbacks."""
        for callback in self._error_callbacks:
            try:
                callback(error)
            except Exception:
                pass

    @abstractmethod
    def get_supported_languages(self) -> list[str]:
        """Get list of supported language codes."""
        pass

    @abstractmethod
    def set_language(self, language: str) -> bool:
        """
        Set recognition language.

        Args:
            language: Language code (e.g., 'en', 'es', 'fr')

        Returns:
            True if language was set successfully
        """
        pass

    def get_engine_info(self) -> dict:
        """Get information about the engine."""
        return {
            "name": self.__class__.__name__,
            "status": self._status.value,
            "initialized": self._is_initialized,
            "model_path": self.model_path,
        }


class WhisperEngine(STTEngine):
    """
    Whisper-based STT engine (OpenAI Whisper).

    High accuracy, but requires more resources.
    Can run locally with whisper.cpp or faster-whisper.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8"
    ):
        super().__init__(model_path)
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None
        self._language = "en"
        self._streaming_buffer: list[bytes] = []
        self._streaming_active = False

    def initialize(self) -> bool:
        """Initialize Whisper model."""
        try:
            # In real implementation, would load faster-whisper or whisper.cpp
            # For now, mark as initialized for testing
            self._is_initialized = True
            self._status = STTStatus.IDLE
            return True
        except Exception as e:
            self._status = STTStatus.ERROR
            self._emit_error(e)
            return False

    def shutdown(self) -> None:
        """Shutdown Whisper engine."""
        self._model = None
        self._is_initialized = False
        self._status = STTStatus.DISABLED
        self._streaming_active = False
        self._streaming_buffer.clear()

    def transcribe(self, audio_data: bytes) -> STTResult:
        """Transcribe audio data using Whisper."""
        if not self._is_initialized:
            return STTResult(text="", confidence=0.0)

        self._status = STTStatus.PROCESSING
        start_time = time.time()

        try:
            # In real implementation, would call whisper model
            # For now, return placeholder
            duration_ms = int((time.time() - start_time) * 1000)

            result = STTResult(
                text="",  # Would be actual transcription
                confidence=0.95,
                duration_ms=duration_ms,
                language=self._language,
            )
            self._status = STTStatus.IDLE
            self._emit_result(result)
            return result
        except Exception as e:
            self._status = STTStatus.ERROR
            self._emit_error(e)
            return STTResult(text="", confidence=0.0)

    def transcribe_file(self, file_path: str) -> STTResult:
        """Transcribe audio file using Whisper."""
        if not self._is_initialized:
            return STTResult(text="", confidence=0.0)

        self._status = STTStatus.PROCESSING
        start_time = time.time()

        try:
            # In real implementation, would load file and transcribe
            duration_ms = int((time.time() - start_time) * 1000)

            result = STTResult(
                text="",  # Would be actual transcription
                confidence=0.95,
                duration_ms=duration_ms,
                language=self._language,
                raw_audio_path=file_path,
            )
            self._status = STTStatus.IDLE
            self._emit_result(result)
            return result
        except Exception as e:
            self._status = STTStatus.ERROR
            self._emit_error(e)
            return STTResult(text="", confidence=0.0)

    def start_streaming(self) -> bool:
        """Start streaming mode."""
        if not self._is_initialized:
            return False

        self._streaming_active = True
        self._streaming_buffer.clear()
        self._status = STTStatus.LISTENING
        return True

    def stop_streaming(self) -> Optional[STTResult]:
        """Stop streaming and get final result."""
        if not self._streaming_active:
            return None

        self._streaming_active = False

        # Process accumulated buffer
        if self._streaming_buffer:
            audio_data = b"".join(self._streaming_buffer)
            result = self.transcribe(audio_data)
            self._streaming_buffer.clear()
            return result

        self._status = STTStatus.IDLE
        return None

    def feed_audio(self, audio_chunk: bytes) -> Optional[STTResult]:
        """Feed audio chunk during streaming."""
        if not self._streaming_active:
            return None

        self._streaming_buffer.append(audio_chunk)

        # Return partial result periodically (every ~1 second of audio)
        # 16kHz * 2 bytes = 32000 bytes per second
        if len(b"".join(self._streaming_buffer)) >= 32000:
            # In real implementation, would do partial transcription
            return STTResult(
                text="",
                confidence=0.8,
                is_final=False,
            )

        return None

    def get_supported_languages(self) -> list[str]:
        """Get supported languages."""
        return [
            "en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko",
            "ar", "hi", "tr", "pl", "nl", "sv", "da", "fi", "no", "cs"
        ]

    def set_language(self, language: str) -> bool:
        """Set recognition language."""
        if language in self.get_supported_languages():
            self._language = language
            return True
        return False


class VoskEngine(STTEngine):
    """
    Vosk-based STT engine.

    Lightweight, fast, works offline.
    Good for real-time streaming with lower accuracy than Whisper.
    """

    def __init__(self, model_path: Optional[str] = None):
        super().__init__(model_path)
        self._model = None
        self._recognizer = None
        self._language = "en"
        self._streaming_active = False

    def initialize(self) -> bool:
        """Initialize Vosk model."""
        try:
            # In real implementation, would load Vosk model
            self._is_initialized = True
            self._status = STTStatus.IDLE
            return True
        except Exception as e:
            self._status = STTStatus.ERROR
            self._emit_error(e)
            return False

    def shutdown(self) -> None:
        """Shutdown Vosk engine."""
        self._model = None
        self._recognizer = None
        self._is_initialized = False
        self._status = STTStatus.DISABLED
        self._streaming_active = False

    def transcribe(self, audio_data: bytes) -> STTResult:
        """Transcribe audio data using Vosk."""
        if not self._is_initialized:
            return STTResult(text="", confidence=0.0)

        self._status = STTStatus.PROCESSING
        start_time = time.time()

        try:
            # In real implementation, would call Vosk recognizer
            duration_ms = int((time.time() - start_time) * 1000)

            result = STTResult(
                text="",
                confidence=0.85,
                duration_ms=duration_ms,
                language=self._language,
            )
            self._status = STTStatus.IDLE
            self._emit_result(result)
            return result
        except Exception as e:
            self._status = STTStatus.ERROR
            self._emit_error(e)
            return STTResult(text="", confidence=0.0)

    def transcribe_file(self, file_path: str) -> STTResult:
        """Transcribe audio file using Vosk."""
        if not self._is_initialized:
            return STTResult(text="", confidence=0.0)

        self._status = STTStatus.PROCESSING

        try:
            # In real implementation, would load and process file
            result = STTResult(
                text="",
                confidence=0.85,
                language=self._language,
                raw_audio_path=file_path,
            )
            self._status = STTStatus.IDLE
            self._emit_result(result)
            return result
        except Exception as e:
            self._status = STTStatus.ERROR
            self._emit_error(e)
            return STTResult(text="", confidence=0.0)

    def start_streaming(self) -> bool:
        """Start streaming mode."""
        if not self._is_initialized:
            return False

        self._streaming_active = True
        self._status = STTStatus.LISTENING
        return True

    def stop_streaming(self) -> Optional[STTResult]:
        """Stop streaming and get final result."""
        if not self._streaming_active:
            return None

        self._streaming_active = False
        self._status = STTStatus.IDLE

        # In real implementation, would get final result from recognizer
        return STTResult(text="", confidence=0.85, is_final=True)

    def feed_audio(self, audio_chunk: bytes) -> Optional[STTResult]:
        """Feed audio chunk during streaming."""
        if not self._streaming_active:
            return None

        # Vosk provides real-time partial results
        # In real implementation, would call recognizer.AcceptWaveform()
        return STTResult(text="", confidence=0.7, is_final=False)

    def get_supported_languages(self) -> list[str]:
        """Get supported languages (depends on available models)."""
        return ["en", "es", "fr", "de", "ru", "zh", "pt", "it"]

    def set_language(self, language: str) -> bool:
        """Set recognition language."""
        if language in self.get_supported_languages():
            self._language = language
            return True
        return False


class MockSTTEngine(STTEngine):
    """
    Mock STT engine for testing.

    Allows setting predefined responses for testing voice input handling.
    """

    def __init__(self, model_path: Optional[str] = None):
        super().__init__(model_path)
        self._responses: queue.Queue = queue.Queue()
        self._streaming_responses: list[STTResult] = []
        self._streaming_index = 0
        self._streaming_active = False
        self._language = "en"
        self._delay_ms = 0

    def set_response(self, text: str, confidence: float = 0.95) -> None:
        """Set next response for transcription."""
        self._responses.put(STTResult(
            text=text,
            confidence=confidence,
            language=self._language,
        ))

    def set_responses(self, responses: list[tuple[str, float]]) -> None:
        """Set multiple responses."""
        for text, confidence in responses:
            self.set_response(text, confidence)

    def set_streaming_responses(self, responses: list[tuple[str, float, bool]]) -> None:
        """Set streaming responses (text, confidence, is_final)."""
        self._streaming_responses = [
            STTResult(text=text, confidence=conf, is_final=final)
            for text, conf, final in responses
        ]

    def set_delay(self, delay_ms: int) -> None:
        """Set artificial delay for transcription."""
        self._delay_ms = delay_ms

    def initialize(self) -> bool:
        """Initialize mock engine."""
        self._is_initialized = True
        self._status = STTStatus.IDLE
        return True

    def shutdown(self) -> None:
        """Shutdown mock engine."""
        self._is_initialized = False
        self._status = STTStatus.DISABLED
        self._streaming_active = False

    def transcribe(self, audio_data: bytes) -> STTResult:
        """Return next queued response."""
        if not self._is_initialized:
            return STTResult(text="", confidence=0.0)

        self._status = STTStatus.PROCESSING

        if self._delay_ms > 0:
            time.sleep(self._delay_ms / 1000)

        try:
            result = self._responses.get_nowait()
        except queue.Empty:
            result = STTResult(text="", confidence=0.0)

        self._status = STTStatus.IDLE
        self._emit_result(result)
        return result

    def transcribe_file(self, file_path: str) -> STTResult:
        """Return next queued response."""
        result = self.transcribe(b"")
        result.raw_audio_path = file_path
        return result

    def start_streaming(self) -> bool:
        """Start streaming mode."""
        if not self._is_initialized:
            return False

        self._streaming_active = True
        self._streaming_index = 0
        self._status = STTStatus.LISTENING
        return True

    def stop_streaming(self) -> Optional[STTResult]:
        """Stop streaming and return final result."""
        if not self._streaming_active:
            return None

        self._streaming_active = False
        self._status = STTStatus.IDLE

        # Return the last streaming response if available
        if self._streaming_responses:
            return self._streaming_responses[-1]
        return STTResult(text="", confidence=0.0, is_final=True)

    def feed_audio(self, audio_chunk: bytes) -> Optional[STTResult]:
        """Return next streaming response."""
        if not self._streaming_active:
            return None

        if self._streaming_index < len(self._streaming_responses):
            result = self._streaming_responses[self._streaming_index]
            self._streaming_index += 1
            self._emit_result(result)
            return result

        return None

    def get_supported_languages(self) -> list[str]:
        """Get supported languages."""
        return ["en", "es", "fr", "de", "test"]

    def set_language(self, language: str) -> bool:
        """Set recognition language."""
        self._language = language
        return True


def create_stt_engine(
    engine_type: str = "mock",
    model_path: Optional[str] = None,
    **kwargs
) -> STTEngine:
    """
    Factory function to create STT engine.

    Args:
        engine_type: Type of engine ('whisper', 'vosk', 'mock')
        model_path: Path to model files
        **kwargs: Additional engine-specific arguments

    Returns:
        Configured STTEngine instance
    """
    engines = {
        "whisper": WhisperEngine,
        "vosk": VoskEngine,
        "mock": MockSTTEngine,
    }

    engine_class = engines.get(engine_type.lower(), MockSTTEngine)
    return engine_class(model_path=model_path, **kwargs)
